import asyncio
import logging
from datetime import datetime, timedelta, timezone

from backend.services.alpaca_service import AlpacaService
from backend.services.stock_screener_service import StockScreenerService
from backend.services.tradingview_service import get_stock_price_tv

logger = logging.getLogger(__name__)


class TradingStrategyService:
    def __init__(self):
        self.alpaca = AlpacaService()
        self.screener = StockScreenerService()
        self.active_strategies = {}
        now = datetime.now()
        # Market hours: 6:30 AM - 1:00 PM PST
        self.market_open_time = datetime(now.year, now.month, now.day, hour=6, minute=30, second=0).replace(
            tzinfo=timezone(timedelta(hours=-8))
        )
        self.market_close_time = datetime(now.year, now.month, now.day, hour=13, minute=0, second=0).replace(
            tzinfo=timezone(timedelta(hours=-8))
        )

    def calculate_position_size(self, account_info, risk_percentage, stop_loss_percentage):
        """Calculate position size based on account risk management"""
        buying_power = float(account_info["buying_power"])
        risk_amount = buying_power * (risk_percentage / 100)
        return risk_amount / (stop_loss_percentage / 100)

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
                    account, params.get("position_size_percentage", 5), params.get("stop_loss_percentage", 2)
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
                    account, params.get("position_size_percentage", 5), params.get("stop_loss_percentage", 2)
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

    async def execute_open_below_prev_high_strategy(self, params):
        """
        Strategy that buys stocks that opened below previous day's high

        Modified strategy flow:
        1. After first 5 minutes of market open, scan for stocks meeting parameters
        2. For each stock, monitor until price reaches previous day's high + 0.5%
        3. Buy the stock when target price is reached
        4. Hold for exactly 5 minutes, then sell

        params:
        - max_positions: Maximum number of positions to take
        - position_size_percentage: Percentage of buying power to use per position
        - min_price: Minimum stock price
        - max_price: Maximum stock price
        - min_volume: Minimum volume
        - min_diff_percent: Minimum percentage below previous high
        - max_diff_percent: Maximum percentage below previous high
        """
        try:
            # Get account info
            account = self.alpaca.get_account_info()

            # Get current positions
            current_positions = self.alpaca.get_positions()
            current_symbols = [p["symbol"] for p in current_positions]

            # Get stocks that opened below previous day's high
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

            # Wait until 5 minutes after market open (6:30 AM PST + 5 minutes)
            now = datetime.now()
            market_open_time = datetime(now.year, now.month, now.day, hour=6, minute=30, second=0).replace(
                tzinfo=timezone(timedelta(hours=-8))
            )  # PST timezone

            five_min_after_open = market_open_time + timedelta(minutes=5)
            current_time = datetime.now(timezone(timedelta(hours=-8)))

            if current_time < five_min_after_open:
                wait_seconds = (five_min_after_open - current_time).total_seconds() - 10
                logger.info(f"Waiting {wait_seconds} seconds until 5 minutes after market open")
                await asyncio.sleep(wait_seconds)

            # Get stocks that opened below previous day's high
            stocks = await self.screener.get_stocks_open_below_prev_high(screener_params)
            processed_stocks = self.screener.process_screener_results(stocks, params.get("max_positions", 10))

            # Filter out stocks we already have positions in
            new_opportunities = [stock for stock in processed_stocks if stock["symbol"] not in current_symbols]

            # Calculate how many new positions we can take
            max_new_positions = params.get("max_positions", 10) - len(current_positions)

            if max_new_positions <= 0:
                logger.info("Maximum positions reached, not taking new trades")
                return {
                    "success": True,
                    "message": "Maximum positions reached, not taking new trades",
                    "positions_taken": 0,
                }

            # Take positions in new opportunities
            positions_taken = 0
            monitoring_tasks = []

            for stock in new_opportunities[:max_new_positions]:
                symbol = stock["symbol"]
                current_price = float(stock["price"])
                prev_day_high = float(stock["prev_day_high"])

                # Calculate target price (previous day's high + 0.5%)
                target_price = prev_day_high * 1.0005

                # Calculate position size
                position_size = self.calculate_position_size(account, params.get("position_size_percentage", 10), 100)

                # Calculate number of shares
                shares = int(position_size / target_price)

                if shares < 1:
                    logger.info(f"Not enough buying power to purchase {symbol}")
                    continue

                # Create a task to monitor this stock
                task = asyncio.create_task(self._monitor_and_trade_stock(symbol, target_price, shares, position_size))
                monitoring_tasks.append(task)

            # Wait for all monitoring tasks to complete
            if monitoring_tasks:
                results = await asyncio.gather(*monitoring_tasks, return_exceptions=True)
                positions_taken = sum(1 for r in results if isinstance(r, dict) and r.get("success", False))

            return {
                "success": True,
                "message": f"Strategy executed successfully. Took {positions_taken} new positions.",
                "positions_taken": positions_taken,
            }

        except Exception as e:
            logger.error(f"Error executing open below prev high strategy: {str(e)}")
            return {"success": False, "message": f"Error executing strategy: {str(e)}", "positions_taken": 0}

    async def _monitor_and_trade_stock(self, symbol, target_price, shares, position_size):
        """
        Monitor a stock until it reaches the target price, then buy and hold for 5 minutes

        Args:
            symbol: Stock symbol
            target_price: Price at which to buy (prev day high + 0.5%)
            shares: Number of shares to buy
            position_size: Dollar amount to invest
        """
        try:
            logger.info(f"Monitoring {symbol} for target price of ${target_price}")

            # Monitor the stock price until it reaches the target
            while True:
                try:
                    current_price = self.alpaca.get_current_price(symbol)
                except Exception:
                    current_price = get_stock_price_tv(symbol)["price"]

                if current_price >= target_price:
                    logger.info(f"{symbol} reached target price of ${target_price}")
                    break

                # Check if we're still in market hours (6:30 AM - 1:00 PM PST)
                now = datetime.now()
                current_time = now.replace(tzinfo=timezone(timedelta(hours=-8)))  # Convert to PST
                if current_time < self.market_open_time or current_time > self.market_close_time:
                    logger.info(f"Market closed before {symbol} reached target price")
                    return {"success": False, "message": "Market closed before target price reached"}

                # Wait for next price update through WebSocket
                await asyncio.sleep(5)  # Reduced sleep time for faster updates

            # Place market buy order
            order = self.alpaca.place_market_order(symbol, shares, "buy")
            logger.info(f"Bought {shares} shares of {symbol} at ${current_price}")

            # Wait exactly 5 minutes
            logger.info(f"Holding {symbol} for 5 minutes")
            await asyncio.sleep(300)  # 5 minutes in seconds

            # Sell the position
            sell_order = self.alpaca.place_market_order(symbol, shares, "sell")
            logger.info(f"Sold {shares} shares of {symbol} after 5-minute hold")

            return {
                "success": True,
                "message": f"Successfully traded {symbol}: bought at ${current_price}, held for 5 minutes",
            }

        except Exception as e:
            logger.error(f"Error monitoring and trading {symbol}: {str(e)}")
            return {"success": False, "message": str(e)}

    async def backtest_open_below_prev_high_strategy(self, params, start_date, end_date):
        """
        Backtest the open below previous day's high strategy using historical data

        Args:
            params: Strategy parameters (same as execute_open_below_prev_high_strategy)
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

                    # Calculate target price (previous day's high + 0.5%)
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

                    # Find if and when price reached target
                    reached_target = False
                    entry_time = None
                    entry_price = 0

                    # Skip first 5 minutes of trading day (market open + 5 min)
                    for i, bar in enumerate(bars[5:], 5):
                        if bar["c"] > target_price:
                            reached_target = True
                            entry_time = bar["t"]
                            entry_price = bar["c"]
                            break

                    if not reached_target:
                        logger.info(f"{symbol} did not reach target price on {day}")
                        continue

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

                    # Record trade
                    trade = {
                        "date": day,
                        "symbol": symbol.symbol,
                        "entry_time": entry_time,
                        "entry_price": entry_price,
                        "exit_time": exit_time,
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
                        f"Backtested trade: {symbol} on {day}, P/L: ${profit_loss:.2f} ({profit_loss_percent:.2f}%)"
                    )

            # Calculate final metrics
            if backtest_results["total_trades"] > 0:
                backtest_results["win_rate"] = (
                    backtest_results["winning_trades"] / backtest_results["total_trades"]
                ) * 100
                backtest_results["average_profit_per_trade"] = (
                    backtest_results["total_profit_loss"] / backtest_results["total_trades"]
                )
                backtest_results["max_drawdown"] = (
                    (max_balance - min(account_balance, max_balance)) / max_balance
                ) * 100

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


if __name__ == "__main__":
    x = TradingStrategyService()
    res = asyncio.run(
        x.backtest_open_below_prev_high_strategy(
            params={
                "min_price": 1,
                "max_price": 20,
            },
            start_date="2025-03-07",
            end_date="2025-03-07",
        )
    )
    logger.info(res)
