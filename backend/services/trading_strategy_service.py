import logging
from datetime import datetime
from services.alpaca_service import AlpacaService
from services.stock_screener_service import StockScreenerService

logger = logging.getLogger(__name__)

class TradingStrategyService:
    def __init__(self):
        self.alpaca = AlpacaService()
        self.screener = StockScreenerService()
        self.active_strategies = {}
    
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
        
        params:
        - max_positions: Maximum number of positions to take
        - position_size_percentage: Percentage of buying power to use per position
        - stop_loss_percentage: Stop loss percentage below entry
        - take_profit_percentage: Take profit percentage above entry
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
                'min_volume': params.get('min_volume', 250000),
                'min_diff_percent': params.get('min_diff_percent', -10),
                'max_diff_percent': params.get('max_diff_percent', -2),
                'limit': params.get('max_positions', 5)
            }
            
            stocks = await self.screener.get_stocks_open_below_prev_high(screener_params)
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
            logger.error(f"Error executing open below prev high strategy: {str(e)}")
            return {
                "success": False,
                "message": f"Error executing strategy: {str(e)}",
                "positions_taken": 0
            }
