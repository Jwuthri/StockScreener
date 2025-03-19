import asyncio
import logging
from datetime import datetime, timedelta, timezone

from backend.models.database import SessionLocal, Stock, TakenTrade
from backend.services.alpaca_service import AlpacaService
from backend.services.alpaca_service_paper import AlpacaPaperService
from backend.services.stock_screener_service import StockScreenerService
from backend.services.tradingview_service import get_stock_price_tv

logger = logging.getLogger(__name__)


class TradingStrategyService:
    def __init__(self, paper: bool = False):
        if paper:
            self.alpaca = AlpacaPaperService()
        else:
            self.alpaca = AlpacaService()
        self.screener = StockScreenerService()
        # self.websocket = AlpacaWebSocketService(paper=paper)
        self.active_strategies = {}
        self.price_monitors = {}
        now = datetime.now()
        self.db = SessionLocal()
        # Market hours: 6:30 AM - 1:00 PM PST
        self.market_open_time = datetime(now.year, now.month, now.day, hour=6, minute=30, second=0).replace(
            tzinfo=timezone(timedelta(hours=-8))
        )
        self.market_close_time = datetime(now.year, now.month, now.day, hour=13, minute=0, second=0).replace(
            tzinfo=timezone(timedelta(hours=-8))
        )
        self.current_positions = self.alpaca.get_positions()
        self.account = self.alpaca.get_account_info()

    def calculate_position_size(self, risk_percentage, stop_loss_percentage):
        """Calculate position size based on account risk management"""
        account_info = self.alpaca.get_account_info()
        buying_power = float(account_info["buying_power"])
        risk_amount = buying_power * (risk_percentage / 100)
        return risk_amount / (stop_loss_percentage / 100)

    async def _monitor_and_trade_stock_base(self, symbol, target_price, shares, position_size):
        """
        Monitor a stock and buy when price crosses above the previous day's high
        (previous check below, current check above), then sell 5 minutes after each entry.

        Args:
            symbol: Stock symbol
            target_price: Price threshold (prev day high)
            shares: Number of shares to buy
            position_size: Dollar amount to invest
        """
        try:
            logger.info(f"Monitoring {symbol} for crosses above ${target_price}")

            # Track when we're in a position to avoid multiple entries at once
            in_position = False
            # Track last price to detect crosses
            last_price = None
            # Track active trades
            active_trades = []
            # Track trades made today
            trades_today = 0
            max_trades_per_day = 5  # Limit trades per day per stock

            # Monitor the stock price until market close
            while True:
                # Check if we're still in market hours
                now = datetime.now()
                current_time = now.replace(tzinfo=timezone(timedelta(hours=-8)))  # Convert to PST
                if current_time > self.market_close_time:
                    logger.info(f"Market closed, ending monitoring for {symbol}")
                    break

                # Check if we've reached max trades for today
                if trades_today >= max_trades_per_day:
                    logger.info(f"Reached maximum trades for {symbol} today")
                    break

                try:
                    current_price = await self.alpaca.get_current_price(symbol)
                except Exception:
                    current_price = get_stock_price_tv(symbol)["price"]

                # Detect crossing above target price (previous check below, current check above)
                if (
                    last_price is not None
                    and last_price < target_price
                    and current_price >= target_price
                    and not in_position
                ):
                    # Price has crossed above target
                    logger.info(f"{symbol} crossed above target price of ${target_price}")

                    # Place market buy order
                    account_info = self.alpaca.get_account_info()
                    buying_power = float(account_info["buying_power"])
                    if buying_power < position_size:
                        logger.info(f"Not enough buying power to purchase {symbol}")
                        return
                    order = self.alpaca.place_market_order(symbol, shares, "buy")
                    logger.info(f"Bought {shares} shares of {symbol} at ${current_price}")

                    # Mark that we're in a position
                    in_position = True
                    trades_today += 1

                    # Create a task to sell after 5 minutes
                    sell_task = asyncio.create_task(
                        self._sell_after_delay(symbol, shares, current_price, 300)  # 5 minutes in seconds
                    )

                    # Add callback to update position status when sell completes
                    sell_task.add_done_callback(lambda _: self._position_closed_callback(symbol))

                    active_trades.append(sell_task)

                # Update last price
                last_price = current_price

                # Wait for next price update
                await asyncio.sleep(5)  # Check price every 5 seconds

            # Wait for any remaining active trades to complete
            if active_trades:
                await asyncio.gather(*active_trades)

            return {
                "success": True,
                "message": f"Successfully monitored {symbol} for the trading day",
            }

        except Exception as e:
            logger.error(f"Error monitoring and trading {symbol}: {str(e)}")
            return {"success": False, "message": str(e)}

    def has_enough_buying_power(self, position_size_percentage, stop_loss_percentage):
        return self.calculate_position_size(position_size_percentage, stop_loss_percentage) > 0

    async def execute_prev_day_high_strategy(self, params):
        """
        Strategy that buys stocks breaking above previous day's high

        params:
        - max_positions: Maximum number of positions to take
        - position_size_percentage: Percentage of buying power to use per position
        - stop_loss_percentage: Stop loss percentage below entry
        - take_profit_percentage: Take profit percentage above entry
        - min_price: Minimum stock price
        - max_price: Maximum stock price
        - min_volume: Minimum volume
        """
        try:
            # Get account info
            account = self.alpaca.get_account_info()

            # Get current positions
            current_positions = self.alpaca.get_positions()
            current_symbols = [p["symbol"] for p in current_positions]

            # Get stocks breaking above previous day high
            screener_params = {
                "min_price": params.get("min_price", 5),
                "max_price": params.get("max_price", 100),
                "min_volume": params.get("min_volume", 500000),
                "limit": params.get("max_positions", 5),
            }

            stocks = await self.screener.get_stocks_crossing_prev_day_high(screener_params)
            processed_stocks = self.screener.process_screener_results(stocks, params.get("max_positions", 5))

            # Filter out stocks we already have positions in
            new_opportunities = [stock for stock in processed_stocks if stock["symbol"] not in current_symbols]

            # Calculate how many new positions we can take
            max_new_positions = params.get("max_positions", 5) - len(current_positions)

            if max_new_positions <= 0:
                logger.info("Maximum positions reached, not taking new trades")
                return {
                    "success": True,
                    "message": "Maximum positions reached, not taking new trades",
                    "positions_taken": 0,
                }

            # Take positions in new opportunities
            positions_taken = 0
            for stock in new_opportunities[:max_new_positions]:
                symbol = stock["symbol"]
                current_price = float(stock["price"])

                # Calculate position size
                position_size = self.calculate_position_size(
                    params.get("position_size_percentage", 5), params.get("stop_loss_percentage", 2)
                )

                # Calculate number of shares
                shares = int(position_size / current_price)

                if shares < 1:
                    logger.info(f"Not enough buying power to purchase {symbol}")
                    continue

                # Calculate stop loss and take profit prices
                stop_loss_price = current_price * (1 - params.get("stop_loss_percentage", 2) / 100)
                take_profit_price = current_price * (1 + params.get("take_profit_percentage", 5) / 100)

                # Place market order
                order = self.alpaca.place_market_order(symbol, shares, "buy")

                # Place stop loss order
                self.alpaca.place_stop_order(symbol, shares, "sell", stop_loss_price)

                # Place take profit (limit) order
                self.alpaca.place_limit_order(symbol, shares, "sell", take_profit_price)

                logger.info(f"Took position in {symbol}: {shares} shares at ${current_price}")
                positions_taken += 1

            return {
                "success": True,
                "message": f"Strategy executed successfully. Took {positions_taken} new positions.",
                "positions_taken": positions_taken,
            }

        except Exception as e:
            logger.error(f"Error executing prev day high strategy: {str(e)}")
            return {"success": False, "message": f"Error executing strategy: {str(e)}", "positions_taken": 0}

    async def execute_consecutive_positive_candles_strategy(self, params):
        """
        Strategy that buys stocks with consecutive positive candles

        params:
        - max_positions: Maximum number of positions to take
        - position_size_percentage: Percentage of buying power to use per position
        - stop_loss_percentage: Stop loss percentage below entry
        - take_profit_percentage: Take profit percentage above entry
        - min_price: Minimum stock price
        - max_price: Maximum stock price
        - min_volume: Minimum volume
        - timeframe: Candle timeframe (e.g., "5m", "15m", "1h")
        - num_candles: Number of consecutive candles required
        """
        try:
            # Get account info
            account = self.alpaca.get_account_info()

            # Get current positions
            current_positions = self.alpaca.get_positions()
            current_symbols = [p["symbol"] for p in current_positions]

            # Get stocks with consecutive positive candles
            screener_params = {
                "min_price": params.get("min_price", 5),
                "max_price": params.get("max_price", 100),
                "min_volume": params.get("min_volume", 500000),
                "timeframe": params.get("timeframe", "15m"),
                "num_candles": params.get("num_candles", 3),
                "limit": params.get("max_positions", 5),
            }

            stocks = await self.screener.get_stocks_with_consecutive_positive_candles(screener_params)
            processed_stocks = self.screener.process_screener_results(stocks, params.get("max_positions", 5))

            # Filter out stocks we already have positions in
            new_opportunities = [stock for stock in processed_stocks if stock["symbol"] not in current_symbols]

            # Calculate how many new positions we can take
            max_new_positions = params.get("max_positions", 5) - len(current_positions)

            if max_new_positions <= 0:
                logger.info("Maximum positions reached, not taking new trades")
                return {
                    "success": True,
                    "message": "Maximum positions reached, not taking new trades",
                    "positions_taken": 0,
                }

            # Take positions in new opportunities
            positions_taken = 0
            for stock in new_opportunities[:max_new_positions]:
                symbol = stock["symbol"]
                current_price = float(stock["price"])

                # Calculate position size
                position_size = self.calculate_position_size(
                    params.get("position_size_percentage", 5), params.get("stop_loss_percentage", 2)
                )

                # Calculate number of shares
                shares = int(position_size / current_price)

                if shares < 1:
                    logger.info(f"Not enough buying power to purchase {symbol}")
                    continue

                # Calculate stop loss and take profit prices
                stop_loss_price = current_price * (1 - params.get("stop_loss_percentage", 2) / 100)
                take_profit_price = current_price * (1 + params.get("take_profit_percentage", 5) / 100)

                # Place market order
                order = self.alpaca.place_market_order(symbol, shares, "buy")

                # Place stop loss order
                self.alpaca.place_stop_order(symbol, shares, "sell", stop_loss_price)

                # Place take profit (limit) order
                self.alpaca.place_limit_order(symbol, shares, "sell", take_profit_price)

                logger.info(f"Took position in {symbol}: {shares} shares at ${current_price}")
                positions_taken += 1

            return {
                "success": True,
                "message": f"Strategy executed successfully. Took {positions_taken} new positions.",
                "positions_taken": positions_taken,
            }

        except Exception as e:
            logger.error(f"Error executing consecutive positive candles strategy: {str(e)}")
            return {"success": False, "message": f"Error executing strategy: {str(e)}", "positions_taken": 0}

    async def _monitor_and_trade_stock(self, symbol, target_price, shares, position_size):
        """Monitor a stock using WebSocket and buy when price crosses above the target price"""
        try:
            logger.info(f"Monitoring {symbol} for crosses above ${target_price}")

            # Track when we're in a position to avoid multiple entries at once
            in_position = False
            last_price = None
            trades_today = 0
            max_trades_per_day = 5

            # Track how long price has been above/below target
            was_below_target = False  # Initialize as False until we confirm it's below
            last_cross_time = None

            # Create an event to signal when we should stop monitoring
            stop_event = asyncio.Event()
            self.price_monitors[symbol] = stop_event

            # Get stock from database
            stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                # Create stock record if it doesn't exist
                stock = Stock(symbol=symbol)
                self.db.add(stock)
                self.db.commit()
                self.db.refresh(stock)

            # Define the callback for price updates
            async def price_callback(price_data):
                nonlocal in_position, last_price, trades_today, was_below_target, last_cross_time

                current_price = price_data["price"]
                logger.info(f"Price callback for {symbol}, current price: {current_price}")
                if current_price is None:
                    return

                # Log price updates for debugging
                logger.debug(
                    f"{symbol} price update: ${current_price} (Target: ${target_price}, Was Below: {was_below_target})"
                )

                # Check if we're still in market hours
                now = datetime.now()
                current_time = now.replace(tzinfo=timezone(timedelta(hours=-8)))
                if current_time > self.market_close_time:
                    logger.info(f"Market closed, ending monitoring for {symbol}")
                    stop_event.set()
                    return

                # Check if we've reached max trades for today
                if trades_today >= max_trades_per_day:
                    logger.info(f"Reached maximum trades for {symbol} today")
                    stop_event.set()
                    return

                # Update price tracking
                if current_price < target_price:
                    # Price is below target
                    was_below_target = True
                    last_cross_time = None  # Reset cross time when price goes below target
                    logger.debug(f"{symbol} price below target (${current_price} < ${target_price})")
                elif current_price >= target_price and was_below_target and not in_position:
                    # Price has just crossed above target from being below
                    current_time = datetime.now()

                    # Check if this is a new cross (not within last 5 minutes)
                    if last_cross_time is None or (current_time - last_cross_time).total_seconds() > 300:
                        logger.critical(
                            f"{symbol} crossed above target price of ${target_price} (Current: ${current_price})"
                        )

                        # Verify buying power
                        account_info = self.alpaca.get_account_info()
                        buying_power = float(account_info["buying_power"])
                        if buying_power < position_size:
                            logger.info(f"Not enough buying power to purchase {symbol}")
                            return

                        # Place market buy order
                        order = self.alpaca.place_market_order(symbol, shares, "buy")
                        logger.critical(f"Bought {shares} shares of {symbol} at ${current_price}")

                        # Record the trade in database
                        try:
                            taken_trade = TakenTrade(
                                stock_id=stock.id,
                                user_id=1,  # Assuming admin user for now
                                strategy_name="open_below_prev_high",
                                entry_timestamp=current_time,
                                entry_price=current_price,
                                prev_day_high=target_price / 1.0005,  # Remove the 0.05% buffer
                                target_price=target_price,
                                shares=shares,
                                total_cost=current_price * shares,
                                position_size_percentage=position_size / buying_power * 100,
                                is_open=True,
                            )
                            self.db.add(taken_trade)
                            self.db.commit()
                            logger.info(f"Recorded trade in database for {symbol}")
                        except Exception as e:
                            logger.error(f"Error recording trade in database: {str(e)}")

                        # Update tracking
                        in_position = True
                        trades_today += 1
                        last_cross_time = current_time
                        was_below_target = False  # Reset for next potential trade

                        # Create a task to sell after 5 minutes
                        asyncio.create_task(self._sell_after_delay(symbol, shares, current_price, 300))
                    else:
                        logger.debug(f"{symbol} crossed target but within cooldown period")

                # Update last price
                last_price = current_price

            # Subscribe to price updates
            await self.websocket.subscribe_to_trades([symbol], price_callback)

            # Wait until stop event is set
            await stop_event.wait()

            # Unsubscribe from price updates
            await self.websocket.unsubscribe_from_trades([symbol])

            return {
                "success": True,
                "message": f"Successfully monitored {symbol} for the trading day",
            }

        except Exception as e:
            logger.error(f"Error monitoring and trading {symbol}: {str(e)}")
            return {"success": False, "message": str(e)}
        finally:
            # Ensure we clean up the monitor
            if symbol in self.price_monitors:
                self.price_monitors[symbol].set()
                self.price_monitors.pop(symbol, None)

    def _position_closed_callback(self, symbol):
        """Callback function when a position is closed"""
        logger.info(f"Position in {symbol} closed")
        # Reset the in_position flag to allow new entries
        self.active_strategies[symbol] = False

    async def _sell_after_delay(self, symbol, shares, entry_price, delay_seconds):
        """
        Sell a position after a specified delay

        Args:
            symbol: Stock symbol
            shares: Number of shares to sell
            entry_price: Price at which the stock was bought
            delay_seconds: Delay before selling in seconds
        """
        try:
            logger.info(f"Holding {symbol} for {delay_seconds/60} minutes")
            await asyncio.sleep(delay_seconds)

            # Sell the position
            sell_order = self.alpaca.place_market_order(symbol, shares, "sell")

            # Get current price for logging
            try:
                current_price = await self.alpaca.get_current_price(symbol)
            except Exception:
                current_price = get_stock_price_tv(symbol)["price"]

            profit_loss = (current_price - entry_price) * shares
            profit_loss_percent = ((current_price / entry_price) - 1) * 100

            # Update the trade record in database
            try:
                # Get the most recent open trade for this symbol
                trade = (
                    self.db.query(TakenTrade)
                    .join(Stock)
                    .filter(Stock.symbol == symbol, TakenTrade.is_open == True)
                    .order_by(TakenTrade.entry_timestamp.desc())
                    .first()
                )

                if trade:
                    trade.is_open = False
                    trade.exit_timestamp = datetime.now()
                    trade.exit_price = current_price
                    trade.profit_loss = profit_loss
                    trade.profit_loss_percentage = profit_loss_percent
                    self.db.commit()
                    logger.info(f"Updated trade record with exit details for {symbol}")
            except Exception as e:
                logger.error(f"Error updating trade record: {str(e)}")

            logger.info(
                f"Sold {shares} shares of {symbol} after {delay_seconds/60}-minute hold. "
                f"P/L: ${profit_loss:.2f} ({profit_loss_percent:.2f}%)"
            )

            return {
                "success": True,
                "symbol": symbol,
                "shares": shares,
                "entry_price": entry_price,
                "exit_price": current_price,
                "profit_loss": profit_loss,
                "profit_loss_percent": profit_loss_percent,
            }

        except Exception as e:
            logger.error(f"Error selling {symbol} after delay: {str(e)}")
            return {"success": False, "message": str(e)}

    async def backtest_open_below_prev_high_strategy(self, params, start_date, end_date):
        """
        Backtest the strategy that buys when price crosses above previous day's high
        (previous bar below, current bar above) and sells 5 minutes later.

        Args:
            params: Strategy parameters
            start_date: Start date for backtesting (YYYY-MM-DD)
            end_date: End date for backtesting (YYYY-MM-DD)

        Returns:
            Dictionary with backtest results including trades and performance metrics
        """
        try:
            logger.info(f"Starting backtest from {start_date} to {end_date}")

            # Get historical data for stocks that meet our criteria
            screener_params = {
                "min_price": params.get("min_price", 1),
                "max_price": params.get("max_price", 20),
                "min_volume": params.get("min_volume", 500_000),
                "min_diff_percent": params.get("min_diff_percent", 1),
                "max_diff_percent": params.get("max_diff_percent", 100),
                "min_change_percent": params.get("min_change_percent", 1),
                "max_change_percent": params.get("max_change_percent", 100),
                "limit": 100,
            }

            # Get list of trading days in the date range
            trading_days = self.alpaca.get_trading_days(start_date, end_date)

            # Initialize results
            backtest_results = {
                "trades": [],
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_profit_loss": 0,
                "win_rate": 0,
                "average_profit_per_trade": 0,
                "max_drawdown": 0,
            }

            # Simulate initial account balance
            account_balance = params.get("initial_balance", 1000)
            max_balance = account_balance
            min_balance = account_balance

            # Set maximum trades per day per stock
            max_trades_per_day = params.get("max_trades_per_day", 5)

            # Process each trading day
            for day in trading_days:
                logger.info(f"Backtesting day: {day}")

                # Get stocks that opened below previous day's high for this day
                stocks = await self.screener.get_historical_stocks_open_below_prev_high(day, screener_params)

                # Skip if no stocks found
                if not stocks:
                    logger.info(f"No stocks found for {day}")
                    continue

                # Process each stock
                for stock in stocks[: params.get("max_positions", 10)]:
                    symbol = stock["symbol"]
                    open_price = float(stock["open"])
                    prev_day_high = float(stock["prev_day_high"])

                    # Calculate target price (previous day's high)
                    target_price = prev_day_high

                    # Get 1-minute bars for this stock on this day
                    try:
                        bars = self.alpaca.get_historical_bar(symbol, day, "1Min")
                    except Exception as e:
                        logger.error(f"Could not get bars for {symbol} on {day}: {str(e)}")
                        continue

                    # Skip if no bars found
                    if not bars:
                        continue

                    # Filter bars to only include market hours
                    bars = [
                        b
                        for b in bars
                        if b["t"].hour >= 14 and b["t"].hour < 21 and (b["t"].hour != 14 or b["t"].minute >= 30)
                    ]

                    if len(bars) < 6:  # Need at least 6 bars (5 for initial wait + 1 for trading)
                        continue

                    # Skip first 5 minutes of trading day
                    start_index = 5

                    # Track trades for this stock today
                    trades_today = 0

                    # Simulate trading throughout the day
                    for i in range(start_index, len(bars) - 1):  # -1 to ensure we have a next bar
                        # Check if we've reached max trades for this stock today
                        # if trades_today >= max_trades_per_day:
                        #     break

                        prev_bar = bars[i - 1]
                        current_bar = bars[i]

                        prev_price = prev_bar["c"]
                        current_price = current_bar["c"]

                        # Check for crossing above target price (prev bar below, current bar above)
                        if prev_price < target_price and current_price >= target_price:
                            # Price has crossed above target - BUY
                            entry_time = current_bar["t"]
                            entry_price = current_price

                            # Calculate position size
                            risk_amount = account_balance * (params.get("position_size_percentage", 10) / 100)
                            shares = int(risk_amount / entry_price)

                            if shares < 1:
                                logger.info(f"Not enough balance to purchase {symbol}")
                                continue

                            # Find exit price (5 minutes after entry)
                            exit_index = min(i + 5, len(bars) - 1)  # 5 minutes later or end of day
                            exit_price = bars[exit_index]["c"]
                            exit_time = bars[exit_index]["t"]

                            # Calculate profit/loss
                            profit_loss = (exit_price - entry_price) * shares
                            profit_loss_percent = (exit_price / entry_price - 1) * 100

                            # Update account balance
                            account_balance += profit_loss
                            max_balance = max(max_balance, account_balance)
                            min_balance = min(min_balance, account_balance)

                            # Record trade
                            trade = {
                                "date": day,
                                "symbol": symbol.symbol,
                                "entry_time": entry_time.isoformat(),
                                "entry_price": entry_price,
                                "exit_time": exit_time.isoformat(),
                                "exit_price": exit_price,
                                "shares": shares,
                                "profit_loss": profit_loss,
                                "profit_loss_percent": profit_loss_percent,
                                "prev_day_high": prev_day_high,
                            }

                            backtest_results["trades"].append(trade)
                            backtest_results["total_trades"] += 1

                            if profit_loss > 0:
                                backtest_results["winning_trades"] += 1
                            else:
                                backtest_results["losing_trades"] += 1

                            backtest_results["total_profit_loss"] += profit_loss

                            logger.info(
                                f"Backtested trade: {symbol} on {day}, Entry: {entry_time}, "
                                f"Exit: {exit_time}, P/L: ${profit_loss:.2f} ({profit_loss_percent:.2f}%)"
                            )

                            # Increment trades counter
                            trades_today += 1

                            # Skip ahead to after the exit time to avoid overlapping trades
                            i = exit_index

            # Calculate final metrics
            if backtest_results["total_trades"] > 0:
                backtest_results["win_rate"] = (
                    backtest_results["winning_trades"] / backtest_results["total_trades"]
                ) * 100
                backtest_results["average_profit_per_trade"] = (
                    backtest_results["total_profit_loss"] / backtest_results["total_trades"]
                )

            # Calculate max drawdown
            if max_balance > min_balance:
                backtest_results["max_drawdown"] = ((max_balance - min_balance) / max_balance) * 100
            else:
                backtest_results["max_drawdown"] = 0

            backtest_results["final_balance"] = account_balance
            backtest_results["total_return_percent"] = (
                (account_balance / params.get("initial_balance", 1000)) - 1
            ) * 100

            return {
                "success": True,
                "message": f"Backtest completed with {backtest_results['total_trades']} trades",
                "results": backtest_results,
            }

        except Exception as e:
            logger.error(f"Error during backtest: {str(e)}")
            return {"success": False, "message": f"Error during backtest: {str(e)}"}

    async def execute_open_below_prev_high_strategy(self, params):
        try:
            logger.info("Executing open below prev high strategy")

            # Get current positions
            logger.info("Getting current positions...")
            current_symbols = [p["symbol"] for p in self.current_positions]
            logger.info(f"Current positions: {current_symbols}")

            # Connect to WebSocket once for all symbols
            logger.info("Connecting to WebSocket...")
            # if not self.websocket.connected:
            #     await self.websocket.connect()
            logger.info("WebSocket connected successfully")

            # Get stocks that opened below previous day's high
            logger.info("Getting stocks that opened below previous day's high...")
            screener_params = {
                "min_price": params.get("min_price", 1),
                "max_price": params.get("max_price", 20),
                "min_volume": params.get("min_volume", 500_000),
                "min_diff_percent": params.get("min_diff_percent", 1),
                "max_diff_percent": params.get("max_diff_percent", 100),
                "min_change_percent": params.get("min_change_percent", 1),
                "max_change_percent": params.get("max_change_percent", 100),
                "limit": params.get("limit", 1000),
            }
            logger.info(f"Screener parameters: {screener_params}")

            # Wait until 5 minutes after market open
            now = datetime.now()
            tz = timezone(timedelta(hours=-8))
            market_open_time = datetime(now.year, now.month, now.day, hour=6, minute=30, second=0).replace(tzinfo=tz)
            five_min_after_open = market_open_time + timedelta(minutes=2)
            current_time = datetime.now().replace(tzinfo=tz)

            if current_time < five_min_after_open:
                wait_seconds = (five_min_after_open - current_time).total_seconds()
                logger.info(f"Waiting {wait_seconds} seconds until 5 minutes after market open")
                await asyncio.sleep(wait_seconds)
            logger.info("Market open wait complete")

            # Get stocks that opened below previous day's high
            logger.info("Fetching stocks from screener...")
            stocks = await self.screener.get_stocks_open_below_prev_high(screener_params)
            # breakpoint()
            logger.info(f"Found {len(stocks)} stocks from screener")

            processed_stocks = self.screener.process_screener_results(stocks, params.get("max_positions", 1000))
            logger.info(f"Processed {len(processed_stocks)} stocks after filtering")

            # Filter out stocks we already have positions in
            new_opportunities = [stock for stock in processed_stocks if stock["symbol"] not in current_symbols]
            logger.info(f"Found {len(new_opportunities)} new opportunities after filtering existing positions")

            # Calculate how many new positions we can take
            max_new_positions = params.get("max_positions", 10000) - len(self.alpaca.get_positions())
            logger.info(f"Can take up to {max_new_positions} new positions")

            if max_new_positions <= 0:
                logger.info("Maximum positions reached, not taking new trades")
                return {
                    "success": True,
                    "message": "Maximum positions reached, not taking new trades",
                    "positions_taken": 0,
                }

            # Initialize tracking dictionary for active strategies
            for stock in new_opportunities[:max_new_positions]:
                symbol = stock["symbol"]
                self.active_strategies[symbol] = False

            # Create a list to store all monitoring tasks
            all_monitoring_tasks = []

            # Create monitoring tasks in batches to avoid rate limits
            batch_size = 10
            logger.info(f"Processing stocks in batches of {batch_size}")

            for i in range(0, len(new_opportunities[:max_new_positions]), batch_size):
                batch = new_opportunities[i : i + batch_size]
                batch_tasks = []
                logger.info(f"Processing batch {i//batch_size + 1} with {len(batch)} stocks")

                for stock in batch:
                    symbol = stock["symbol"]
                    current_price = float(stock["current_price"])
                    prev_day_high = float(stock["prev_day_high"])
                    target_price = prev_day_high * 1.0005
                    position_size = self.calculate_position_size(params.get("position_size_percentage", 10), 100)
                    shares = int(position_size / target_price)

                    if shares < 1:
                        logger.info(f"Not enough buying power to purchase {symbol}")
                        continue

                    logger.info(
                        f"Starting monitor for {symbol} - Current: ${current_price:.2f}, Target: ${target_price:.2f}, Shares: {shares}"
                    )
                    task = asyncio.create_task(
                        self._monitor_and_trade_stock_base(symbol, target_price, shares, position_size)
                    )
                    batch_tasks.append(task)
                    all_monitoring_tasks.append(task)

                if batch_tasks:
                    logger.info("Waiting 1 second between batches to avoid rate limits")
                    await asyncio.sleep(1)

            if all_monitoring_tasks:
                logger.info(f"Monitoring {len(all_monitoring_tasks)} symbols for trading opportunities")

                # Create a task to monitor market close
                async def check_market_close():
                    while True:
                        now = datetime.now()
                        current_time = now.replace(tzinfo=timezone(timedelta(hours=-8)))
                        if current_time > self.market_close_time:
                            logger.info("Market closed, stopping all monitors")
                            # Stop all monitors
                            for symbol in list(self.price_monitors.keys()):
                                if symbol in self.price_monitors:
                                    self.price_monitors[symbol].set()
                            break
                        await asyncio.sleep(60)  # Check every minute

                market_close_task = asyncio.create_task(check_market_close())

                # Wait for all monitoring tasks or market close
                try:
                    logger.info("Waiting for monitoring tasks to complete...")
                    # Wait for all tasks to complete
                    results = await asyncio.gather(*all_monitoring_tasks, return_exceptions=True)

                    # Count successful positions
                    positions_taken = sum(
                        1
                        for r in results
                        if not isinstance(r, Exception) and isinstance(r, dict) and r.get("success", False)
                    )
                    logger.info(f"Monitoring complete. Took {positions_taken} positions.")
                finally:
                    # Cancel market close checker if it's still running
                    if not market_close_task.done():
                        market_close_task.cancel()
                        try:
                            await market_close_task
                        except asyncio.CancelledError:
                            pass

            else:
                positions_taken = 0
                logger.info("No stocks to monitor")

            return {
                "success": True,
                "message": f"Strategy executed successfully. Took {positions_taken} new positions.",
                "positions_taken": positions_taken,
            }

        except Exception as e:
            logger.error(f"Error executing open below prev high strategy: {str(e)}")
            return {"success": False, "message": f"Error executing strategy: {str(e)}", "positions_taken": 0}
        finally:
            # Cleanup any remaining monitors
            for symbol in list(self.price_monitors.keys()):
                if symbol in self.price_monitors:
                    self.price_monitors[symbol].set()
            self.price_monitors.clear()


if __name__ == "__main__":
    x = TradingStrategyService(False)
    res = asyncio.run(x.alpaca.get_current_price("NVDA"))
    breakpoint()
    res = asyncio.run(
        x.execute_open_below_prev_high_strategy(
            params={
                "min_price": 0.1,
                "max_price": 8,
                "min_volume": 200_000,
                "min_diff_percent": 2,
                "max_diff_percent": 1000,
                "min_change_percent": -10,
                "max_change_percent": 1000,
                "limit": 100,
                "max_positions": 1000,
                "position_size_percentage": 0.01,
            }
        )
    )
    logger.info(res)
