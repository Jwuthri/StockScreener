import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from backend.models.database import SessionLocal, Stock, TakenTrade
from backend.services.alpaca_service import AlpacaService
from backend.services.alpaca_service_paper import AlpacaPaperService
from backend.services.stock_screener_service import StockScreenerService
from backend.services.tradingview_service import get_stock_price_tv, get_stocks_first_candle_near_prev_high

logger = logging.getLogger(__name__)


class TradingStrategyService:
    def __init__(self, paper: bool = False):
        if paper:
            self.alpaca = AlpacaPaperService()
        else:
            self.alpaca = AlpacaService()
        self.screener = StockScreenerService()
        self.active_strategies = {}
        self.monitored_stocks: Dict[str, dict] = {}  # Track monitored stocks and their states
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
        buying_power = float(self.account["buying_power"])
        risk_amount = buying_power * (risk_percentage / 100)
        return risk_amount / (stop_loss_percentage / 100)

    def has_enough_buying_power(self, position_size_percentage, stop_loss_percentage):
        return self.calculate_position_size(position_size_percentage, stop_loss_percentage) > 0

    def _position_closed_callback(self, symbol):
        """Callback function when a position is closed"""
        logger.info(f"Position in {symbol} closed")
        # Reset the in_position flag to allow new entries
        if symbol in self.monitored_stocks:
            self.monitored_stocks[symbol]["in_position"] = False

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
            five_min_after_open = market_open_time + timedelta(minutes=1)
            current_time = datetime.now().replace(tzinfo=tz)

            if current_time < five_min_after_open:
                wait_seconds = (five_min_after_open - current_time).total_seconds()
                logger.info(f"Waiting {wait_seconds} seconds until 1 minutes after market open")
                await asyncio.sleep(wait_seconds)
            logger.info("Market open wait complete")

            # Get stocks that opened below previous day's high
            logger.info("Fetching stocks from screener...")
            stocks = await self.screener.get_stocks_open_below_prev_high(screener_params)
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

            # Prepare stocks data for batch monitoring
            stocks_to_monitor = []
            for stock in new_opportunities[:max_new_positions]:
                symbol = stock["symbol"]
                current_price = float(stock["current_price"])
                prev_day_high = float(stock["prev_day_high"])
                target_price = prev_day_high * 1.0005  # Add 0.05% buffer
                position_size = self.calculate_position_size(params.get("position_size_percentage", 10), 100)
                shares = int(position_size / target_price)

                if shares < 1:
                    logger.info(f"Not enough buying power to purchase {symbol}")
                    continue

                stocks_to_monitor.append(
                    {
                        "symbol": symbol,
                        "target_price": target_price,
                        "shares": shares,
                        "position_size": position_size,
                        "hold_time": 300,
                        "strategy_name": "execute_open_below_prev_high_strategy",
                    }
                )

            # breakpoint()
            if not stocks_to_monitor:
                logger.info("No stocks to monitor")
                return {"success": True, "message": "No stocks to monitor", "positions_taken": 0}

            # Start batch monitoring
            logger.info(f"Starting batch monitoring for {len(stocks_to_monitor)} stocks")
            monitoring_result = await self._monitor_stocks_batch(stocks_to_monitor)

            # Count positions taken
            positions_taken = sum(
                1 for symbol in self.monitored_stocks if self.monitored_stocks[symbol]["trades_today"] > 0
            )

            return {
                "success": True,
                "message": f"Strategy executed successfully. Took {positions_taken} new positions.",
                "positions_taken": positions_taken,
            }

        except Exception as e:
            logger.error(f"Error executing open below prev high strategy: {str(e)}")
            return {"success": False, "message": f"Error executing strategy: {str(e)}", "positions_taken": 0}
        finally:
            # Cleanup monitored stocks
            self.monitored_stocks.clear()

    async def _monitor_stocks_batch(self, stocks_data: List[dict]):
        """
        Monitor a batch of stocks using latest quotes API

        Args:
            stocks_data: List of dictionaries containing stock data with keys:
                - symbol: Stock symbol
                - target_price: Price threshold
                - shares: Number of shares to buy
                - position_size: Dollar amount to invest
        """
        try:
            # Initialize monitoring state for each stock
            for stock in stocks_data:
                symbol = stock["symbol"]
                if symbol not in self.monitored_stocks:
                    self.monitored_stocks[symbol] = {
                        "active": True,
                        "in_position": False,
                        "last_price": None,
                        "trades_today": 0,
                        "target_price": stock["target_price"],
                        "shares": stock["shares"],
                        "position_size": stock["position_size"],
                        "hold_time": stock["hold_time"],
                        "strategy_name": stock.get("strategy_name", ""),
                    }

            symbols = [stock["symbol"] for stock in stocks_data]
            logger.info(f"Starting batch monitoring for {len(symbols)} symbols")
            # breakpoint()
            while True:
                # Check if we're still in market hours
                now = datetime.now()
                current_time = now.replace(tzinfo=timezone(timedelta(hours=-8)))
                if current_time > self.market_close_time:
                    logger.info("Market closed, ending batch monitoring")
                    break

                # Get latest quotes for all symbols
                try:
                    quotes = self.alpaca.latest_quotes(symbols)
                    # breakpoint()
                    logger.info(f"Fetched {len(quotes['quotes'])} quotes....")

                    # Process each quote
                    for symbol, quote_data in quotes["quotes"].items():
                        if symbol not in self.monitored_stocks or not self.monitored_stocks[symbol]["active"]:
                            continue

                        stock_state = self.monitored_stocks[symbol]
                        current_price = float(quote_data.get("bp", 0))

                        if current_price <= 0:
                            continue

                        # Check if we've reached max trades for this stock
                        if stock_state["trades_today"] >= 3:  # max 5 trades per day per stock
                            self.monitored_stocks[symbol]["active"] = False
                            continue

                        last_price = stock_state["last_price"]
                        target_price = stock_state["target_price"]

                        # Detect crossing above target price
                        if (
                            last_price is not None
                            and last_price < target_price
                            and current_price >= target_price
                            and not stock_state["in_position"]
                        ):
                            # Price has crossed above target
                            logger.info(f"{symbol} crossed above target price of ${target_price}")

                            # Place market buy order
                            account_info = self.alpaca.get_account_info()
                            buying_power = float(account_info["buying_power"])
                            if buying_power < stock_state["position_size"]:
                                logger.info(f"Not enough buying power to purchase {symbol}")
                                continue

                            order = self.alpaca.place_market_order(symbol, stock_state["shares"], "buy")
                            logger.info(f"Bought {stock_state['shares']} shares of {symbol} at ${current_price}")

                            # Add trade to database
                            try:
                                # Get the stock record
                                _stock = self.db.query(Stock).filter(Stock.name == symbol).first()
                                if not _stock:
                                    # Create stock record if it doesn't exist
                                    _stock = Stock(symbol=symbol, name=symbol)
                                    self.db.add(_stock)
                                    self.db.commit()

                                # Create new trade record
                                new_trade = TakenTrade(
                                    stock_id=_stock.id,
                                    user_id=1,  # Assuming admin user for now
                                    strategy_name="open_below_prev_high",
                                    entry_timestamp=current_time,
                                    entry_price=current_price,
                                    prev_day_high=target_price / 1.0005,  # Remove the 0.05% buffer
                                    target_price=target_price,
                                    shares=stock_state["shares"],
                                    total_cost=current_price * stock_state["shares"],
                                    position_size_percentage=stock_state["position_size"] / buying_power * 100,
                                    is_open=True,
                                )
                                self.db.add(new_trade)
                                self.db.commit()
                                logger.info(f"Added trade record for {symbol} to database")
                            except Exception as e:
                                logger.error(f"Error adding trade to database: {str(e)}")

                            # Update state
                            self.monitored_stocks[symbol]["in_position"] = True
                            self.monitored_stocks[symbol]["trades_today"] += 1

                            # Create a task to sell after 15 minutes
                            asyncio.create_task(
                                self._sell_after_delay(
                                    symbol,
                                    stock_state["shares"],
                                    current_price,
                                    stock_state["hold_time"],  # Now uses 15 minutes (900 seconds)
                                )
                            )

                        # Update last price
                        self.monitored_stocks[symbol]["last_price"] = current_price

                except Exception as e:
                    logger.error(f"Error fetching quotes: {str(e)}")

                # Wait before next update
                await asyncio.sleep(5)  # Check every 5 seconds

            return {"success": True, "message": "Batch monitoring completed"}

        except Exception as e:
            logger.error(f"Error in batch monitoring: {str(e)}")
            return {"success": False, "message": str(e)}

    async def execute_first_candle_breakout_strategy(self, params):
        try:
            logger.info("Executing first candle breakout strategy")

            # Get current positions
            logger.info("Getting current positions...")
            current_symbols = [p["symbol"] for p in self.current_positions]
            logger.info(f"Current positions: {current_symbols}")

            # Set up screener parameters
            screener_params = {
                "min_price": params.get("min_price", 1),
                "max_price": params.get("max_price", 20),
                "min_volume": params.get("min_volume", 500_000),
                "min_diff_percent": params.get("min_diff_percent", 1),
                "max_diff_percent": params.get("max_diff_percent", 100),
                "min_change_percent": params.get("min_change_percent", 1),
                "max_change_percent": params.get("max_change_percent", 100),
                "limit": params.get("limit", 1000),
                "max_above_percent": params.get("max_above_percent", 5.0),
            }

            # Wait until market open
            now = datetime.now()
            tz = timezone(timedelta(hours=-8))
            market_open_time = datetime(now.year, now.month, now.day, hour=6, minute=30, second=0).replace(tzinfo=tz)
            current_time = datetime.now().replace(tzinfo=tz)

            if current_time < market_open_time:
                wait_seconds = (market_open_time - current_time).total_seconds()
                logger.info(f"Waiting {wait_seconds} seconds until market open")
                await asyncio.sleep(wait_seconds)

            # Get initial stock list at market open
            logger.info("Fetching initial stock list...")
            stocks = await get_stocks_first_candle_near_prev_high(screener_params)
            processed_stocks = self.screener.process_screener_results(stocks, params.get("max_positions", 1000))

            # Prepare stocks data for batch monitoring
            stocks_to_monitor = []
            for stock in processed_stocks:
                symbol = stock["symbol"]
                current_high_price = float(stock["open_high"])
                target_price = current_high_price * 1.0005  # Add 0.05% buffer
                position_size = self.calculate_position_size(params.get("position_size_percentage", 10), 100)
                shares = int(position_size / target_price)

                if shares < 1:
                    logger.info(f"Not enough buying power to purchase {symbol}")
                    continue

                stocks_to_monitor.append(
                    {
                        "symbol": symbol,
                        "target_price": target_price,
                        "shares": shares,
                        "position_size": position_size,
                        "hold_time": 900,
                    }
                )

            # Modify the monitoring state initialization
            for stock in processed_stocks:
                symbol = stock["symbol"]
                if symbol not in self.monitored_stocks:
                    self.monitored_stocks[symbol] = {
                        "active": True,
                        "in_position": False,
                        "last_price": None,
                        "trades_today": 0,
                        "target_price": stock["target_price"],
                        "shares": stock["shares"],
                        "position_size": stock["position_size"],
                        "hold_time": 900,  # 15 minutes in seconds
                        "strategy_name": "execute_first_candle_breakout_strategy",
                    }

            # Start batch monitoring
            logger.info(f"Starting batch monitoring for {len(stocks_to_monitor)} stocks")
            monitoring_result = await self._monitor_stocks_batch(stocks_to_monitor)

            positions_taken = sum(
                1 for symbol in self.monitored_stocks if self.monitored_stocks[symbol]["trades_today"] > 0
            )

            return {
                "success": True,
                "message": f"Strategy executed successfully. Took {positions_taken} new positions.",
                "positions_taken": positions_taken,
            }

        except Exception as e:
            logger.error(f"Error executing first candle breakout strategy: {str(e)}")
            return {"success": False, "message": f"Error executing strategy: {str(e)}", "positions_taken": 0}
        finally:
            self.monitored_stocks.clear()


if __name__ == "__main__":
    x = TradingStrategyService(False)
    res = asyncio.run(
        x.execute_first_candle_breakout_strategy(
            params={
                "min_price": 0.1,
                "max_price": 10,
                "min_volume": 10_000,
                "min_diff_percent": 2,
                "max_diff_percent": 1000,
                "min_change_percent": -10,
                "max_change_percent": 1000,
                "limit": 1000,
                "max_positions": 1000,
                "position_size_percentage": 0.01,
            }
        )
    )
    res = asyncio.run(
        x.execute_open_below_prev_high_strategy(
            params={
                "min_price": 0.1,
                "max_price": 10,
                "min_volume": 10_000,
                "min_diff_percent": 2,
                "max_diff_percent": 1000,
                "min_change_percent": -10,
                "max_change_percent": 1000,
                "limit": 1000,
                "max_positions": 1000,
                "position_size_percentage": 0.01,
            }
        )
    )
    # logger.info(res)
