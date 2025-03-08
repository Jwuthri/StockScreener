import logging
from datetime import datetime
from services.alpaca_service import AlpacaService
from services.stock_screener_service import StockScreenerService
import asyncio

logger = logging.getLogger(__name__)

class TradingStrategyService:
    def __init__(self):
        self.alpaca = AlpacaService()
        self.screener = StockScreenerService()
        self.active_strategies = {}
        now = datetime.now()
        # Market hours: 6:30 AM - 1:00 PM PST
        self.market_open_time = datetime(
            now.year, now.month, now.day, 
            hour=6, minute=30, second=0
        ).replace(tzinfo=datetime.timezone(-datetime.timedelta(hours=8)))
        
        self.market_close_time = datetime(
            now.year, now.month, now.day, 
            hour=13, minute=0, second=0
        ).replace(tzinfo=datetime.timezone(-datetime.timedelta(hours=8)))
    
    def calculate_position_size(self, account_info, risk_percentage, stop_loss_percentage):
        """Calculate position size based on account risk management"""
        buying_power = float(account_info['buying_power'])
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
            current_symbols = [p['symbol'] for p in current_positions]
            
            # Get stocks breaking above previous day high
            screener_params = {
                'min_price': params.get('min_price', 5),
                'max_price': params.get('max_price', 100),
                'min_volume': params.get('min_volume', 500000),
                'limit': params.get('max_positions', 5)
            }
            
            stocks = await self.screener.get_stocks_crossing_prev_day_high(screener_params)
            processed_stocks = self.screener.process_screener_results(stocks, params.get('max_positions', 5))
            
            # Filter out stocks we already have positions in
            new_opportunities = [stock for stock in processed_stocks if stock['symbol'] not in current_symbols]
            
            # Calculate how many new positions we can take
            max_new_positions = params.get('max_positions', 5) - len(current_positions)
            
            if max_new_positions <= 0:
                logger.info("Maximum positions reached, not taking new trades")
                return {
                    "success": True,
                    "message": "Maximum positions reached, not taking new trades",
                    "positions_taken": 0
                }
            
            # Take positions in new opportunities
            positions_taken = 0
            for stock in new_opportunities[:max_new_positions]:
                symbol = stock['symbol']
                current_price = float(stock['price'])
                
                # Calculate position size
                position_size = self.calculate_position_size(
                    account,
                    params.get('position_size_percentage', 5),
                    params.get('stop_loss_percentage', 2)
                )
                
                # Calculate number of shares
                shares = int(position_size / current_price)
                
                if shares < 1:
                    logger.info(f"Not enough buying power to purchase {symbol}")
                    continue
                
                # Calculate stop loss and take profit prices
                stop_loss_price = current_price * (1 - params.get('stop_loss_percentage', 2) / 100)
                take_profit_price = current_price * (1 + params.get('take_profit_percentage', 5) / 100)
                
                # Place market order
                order = self.alpaca.place_market_order(symbol, shares, 'buy')
                
                # Place stop loss order
                self.alpaca.place_stop_order(symbol, shares, 'sell', stop_loss_price)
                
                # Place take profit (limit) order
                self.alpaca.place_limit_order(symbol, shares, 'sell', take_profit_price)
                
                logger.info(f"Took position in {symbol}: {shares} shares at ${current_price}")
                positions_taken += 1
            
            return {
                "success": True,
                "message": f"Strategy executed successfully. Took {positions_taken} new positions.",
                "positions_taken": positions_taken
            }
        
        except Exception as e:
            logger.error(f"Error executing prev day high strategy: {str(e)}")
            return {
                "success": False,
                "message": f"Error executing strategy: {str(e)}",
                "positions_taken": 0
            }
    
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
            current_symbols = [p['symbol'] for p in current_positions]
            
            # Get stocks with consecutive positive candles
            screener_params = {
                'min_price': params.get('min_price', 5),
                'max_price': params.get('max_price', 100),
                'min_volume': params.get('min_volume', 500000),
                'timeframe': params.get('timeframe', '15m'),
                'num_candles': params.get('num_candles', 3),
                'limit': params.get('max_positions', 5)
            }
            
            stocks = await self.screener.get_stocks_with_consecutive_positive_candles(screener_params)
            processed_stocks = self.screener.process_screener_results(stocks, params.get('max_positions', 5))
            
            # Filter out stocks we already have positions in
            new_opportunities = [stock for stock in processed_stocks if stock['symbol'] not in current_symbols]
            
            # Calculate how many new positions we can take
            max_new_positions = params.get('max_positions', 5) - len(current_positions)
            
            if max_new_positions <= 0:
                logger.info("Maximum positions reached, not taking new trades")
                return {
                    "success": True,
                    "message": "Maximum positions reached, not taking new trades",
                    "positions_taken": 0
                }
            
            # Take positions in new opportunities
            positions_taken = 0
            for stock in new_opportunities[:max_new_positions]:
                symbol = stock['symbol']
                current_price = float(stock['price'])
                
                # Calculate position size
                position_size = self.calculate_position_size(
                    account,
                    params.get('position_size_percentage', 5),
                    params.get('stop_loss_percentage', 2)
                )
                
                # Calculate number of shares
                shares = int(position_size / current_price)
                
                if shares < 1:
                    logger.info(f"Not enough buying power to purchase {symbol}")
                    continue
                
                # Calculate stop loss and take profit prices
                stop_loss_price = current_price * (1 - params.get('stop_loss_percentage', 2) / 100)
                take_profit_price = current_price * (1 + params.get('take_profit_percentage', 5) / 100)
                
                # Place market order
                order = self.alpaca.place_market_order(symbol, shares, 'buy')
                
                # Place stop loss order
                self.alpaca.place_stop_order(symbol, shares, 'sell', stop_loss_price)
                
                # Place take profit (limit) order
                self.alpaca.place_limit_order(symbol, shares, 'sell', take_profit_price)
                
                logger.info(f"Took position in {symbol}: {shares} shares at ${current_price}")
                positions_taken += 1
            
            return {
                "success": True,
                "message": f"Strategy executed successfully. Took {positions_taken} new positions.",
                "positions_taken": positions_taken
            }
        
        except Exception as e:
            logger.error(f"Error executing consecutive positive candles strategy: {str(e)}")
            return {
                "success": False,
                "message": f"Error executing strategy: {str(e)}",
                "positions_taken": 0
            }
    
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
            current_symbols = [p['symbol'] for p in current_positions]
            
            # Get stocks that opened below previous day's high
            screener_params = {
                'min_price': params.get('min_price', 1),
                'max_price': params.get('max_price', 20),
                'min_volume': params.get('min_volume', 500_000),
                'min_diff_percent': params.get('min_diff_percent', 1),
                'max_diff_percent': params.get('max_diff_percent', 100),
                'min_change_percent': params.get('min_change_percent', 1),
                'max_change_percent': params.get('max_change_percent', 100),
                'limit': 100
            }
            
            # Wait until 5 minutes after market open (6:30 AM PST + 5 minutes)
            now = datetime.now()
            market_open_time = datetime(
                now.year, now.month, now.day, 
                hour=6, minute=30, second=0
            ).replace(tzinfo=datetime.timezone(-datetime.timedelta(hours=8)))  # PST timezone
            
            five_min_after_open = market_open_time + datetime.timedelta(minutes=5)
            current_time = datetime.now(datetime.timezone.utc)

            if current_time < five_min_after_open:
                wait_seconds = (five_min_after_open - current_time).total_seconds() - 10
                logger.info(f"Waiting {wait_seconds} seconds until 5 minutes after market open")
                await asyncio.sleep(wait_seconds)
            
            # Get stocks that opened below previous day's high
            stocks = await self.screener.get_stocks_open_below_prev_high(screener_params)
            processed_stocks = self.screener.process_screener_results(stocks, params.get('max_positions', 100))
            
            # Filter out stocks we already have positions in
            new_opportunities = [stock for stock in processed_stocks if stock['symbol'] not in current_symbols]
            
            # Calculate how many new positions we can take
            max_new_positions = params.get('max_positions', 10) - len(current_positions)
            
            if max_new_positions <= 0:
                logger.info("Maximum positions reached, not taking new trades")
                return {
                    "success": True,
                    "message": "Maximum positions reached, not taking new trades",
                    "positions_taken": 0
                }
            
            # Take positions in new opportunities
            positions_taken = 0
            monitoring_tasks = []
            
            for stock in new_opportunities[:max_new_positions]:
                symbol = stock['symbol']
                current_price = float(stock['price'])
                prev_day_high = float(stock['prev_day_high'])
                
                # Calculate target price (previous day's high + 0.5%)
                target_price = prev_day_high * 1.005
                
                # Calculate position size
                position_size = self.calculate_position_size(
                    account,
                    params.get('position_size_percentage', 5),
                    2  # Default stop loss percentage
                )
                
                # Calculate number of shares
                shares = int(position_size / target_price)
                
                if shares < 1:
                    logger.info(f"Not enough buying power to purchase {symbol}")
                    continue
                
                # Create a task to monitor this stock
                task = asyncio.create_task(
                    self._monitor_and_trade_stock(symbol, target_price, shares, position_size)
                )
                monitoring_tasks.append(task)
            
            # Wait for all monitoring tasks to complete
            if monitoring_tasks:
                results = await asyncio.gather(*monitoring_tasks, return_exceptions=True)
                positions_taken = sum(1 for r in results if isinstance(r, dict) and r.get('success', False))
            
            return {
                "success": True,
                "message": f"Strategy executed successfully. Took {positions_taken} new positions.",
                "positions_taken": positions_taken
            }
        
        except Exception as e:
            logger.error(f"Error executing open below prev high strategy: {str(e)}")
            return {
                "success": False,
                "message": f"Error executing strategy: {str(e)}",
                "positions_taken": 0
            }

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
                current_price = self.alpaca.get_current_price(symbol)
                
                if current_price >= target_price:
                    logger.info(f"{symbol} reached target price of ${target_price}")
                    break
                    
                # Check if we're still in market hours (6:30 AM - 1:00 PM PST)
                now = datetime.now()
                current_time = now.replace(tzinfo=datetime.timezone(-datetime.timedelta(hours=8)))  # Convert to PST
                if current_time < self.market_open_time or current_time > self.market_close_time:
                    logger.info(f"Market closed before {symbol} reached target price")
                    return {"success": False, "message": "Market closed before target price reached"}
                    
                # Wait before checking again (5 seconds)
                await asyncio.sleep(5)
            
            # Place market buy order
            order = self.alpaca.place_market_order(symbol, shares, 'buy')
            logger.info(f"Bought {shares} shares of {symbol} at ${current_price}")
            
            # Wait exactly 5 minutes
            logger.info(f"Holding {symbol} for 5 minutes")
            await asyncio.sleep(300)  # 5 minutes in seconds
            
            # Sell the position
            sell_order = self.alpaca.place_market_order(symbol, shares, 'sell')
            logger.info(f"Sold {shares} shares of {symbol} after 5-minute hold")
            
            return {
                "success": True,
                "message": f"Successfully traded {symbol}: bought at ${current_price}, held for 5 minutes"
            }
            
        except Exception as e:
            logger.error(f"Error monitoring and trading {symbol}: {str(e)}")
            return {"success": False, "message": str(e)}
