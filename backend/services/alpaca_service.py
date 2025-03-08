import os
import logging
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.enums import AssetStatus, AssetClass
from datetime import datetime, timedelta
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

class AlpacaService:
    def __init__(self):
        # Get API keys from environment variables
        self.api_key = os.environ.get('ALPACA_API_KEY')
        self.api_secret = os.environ.get('ALPACA_API_SECRET')
        self.paper_trading = os.environ.get('ALPACA_PAPER_TRADING', 'true').lower() == 'true'
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API key and secret must be set in environment variables")
        
        # Initialize Alpaca clients
        self.trading_client = TradingClient(self.api_key, self.api_secret, paper=self.paper_trading)
        self.data_client = StockHistoricalDataClient(self.api_key, self.api_secret)
        assets = self.trading_client.get_all_assets()
        self.active_assets = [asset for asset in assets if asset.status == AssetStatus.ACTIVE and asset.tradable]
        logger.info(f"Alpaca service initialized (Paper Trading: {self.paper_trading})")

    def find_symbol(self, symbol):
        matching_symbols = [asset for asset in self.active_assets if symbol.upper() in asset.symbol.upper() or (asset.name and symbol.upper() in asset.name.upper())]
        for asset in matching_symbols:
            print(f"Symbol: {asset.symbol} - Name: {asset.name}")

        return matching_symbols

    def get_account_info(self):
        """Get account information from Alpaca"""
        try:
            account = self.trading_client.get_account()
            return {
                'id': account.id,
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'buying_power': float(account.buying_power),
                'equity': float(account.equity),
                'currency': account.currency,
                'status': account.status,
                'pattern_day_trader': account.pattern_day_trader,
                'trading_blocked': account.trading_blocked,
                'paper_trading': self.paper_trading
            }
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            raise
    
    def get_positions(self):
        """Get current positions"""
        try:
            positions = self.trading_client.get_all_positions()
            return [{
                'symbol': position.symbol,
                'qty': float(position.qty),
                'avg_entry_price': float(position.avg_entry_price),
                'market_value': float(position.market_value),
                'cost_basis': float(position.cost_basis),
                'unrealized_pl': float(position.unrealized_pl),
                'unrealized_plpc': float(position.unrealized_plpc),
                'current_price': float(position.current_price),
                'change_today': float(position.change_today)
            } for position in positions]
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            raise
    
    def get_orders(self, status=None):
        """Get orders with optional status filter"""
        try:
            orders = self.trading_client.get_orders(status=status)
            return [{
                'id': order.id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side.value,
                'type': order.type.value,
                'time_in_force': order.time_in_force.value,
                'status': order.status,
                'created_at': order.created_at.isoformat(),
                'filled_at': order.filled_at.isoformat() if order.filled_at else None,
                'filled_qty': float(order.filled_qty) if order.filled_qty else 0,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None,
                'limit_price': float(order.limit_price) if order.limit_price else None,
                'stop_price': float(order.stop_price) if order.stop_price else None
            } for order in orders]
        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            raise
    
    def place_market_order(self, symbol, qty, side, time_in_force=TimeInForce.DAY):
        """Place a market order"""
        try:
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide(side),
                time_in_force=time_in_force
            )
            order = self.trading_client.submit_order(order_data=order_data)
            logger.info(f"Market order placed: {symbol} {side} {qty} shares")
            return {
                'id': order.id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side.value,
                'type': order.type.value,
                'time_in_force': order.time_in_force.value,
                'status': order.status,
                'created_at': order.created_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error placing market order: {str(e)}")
            raise
    
    def place_limit_order(self, symbol, qty, side, limit_price, time_in_force=TimeInForce.DAY):
        """Place a limit order"""
        try:
            order_data = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide(side),
                limit_price=limit_price,
                time_in_force=time_in_force
            )
            order = self.trading_client.submit_order(order_data=order_data)
            logger.info(f"Limit order placed: {symbol} {side} {qty} shares at ${limit_price}")
            return {
                'id': order.id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side.value,
                'type': order.type.value,
                'limit_price': float(order.limit_price),
                'time_in_force': order.time_in_force.value,
                'status': order.status,
                'created_at': order.created_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error placing limit order: {str(e)}")
            raise
    
    def place_stop_order(self, symbol, qty, side, stop_price, time_in_force=TimeInForce.DAY):
        """Place a stop order"""
        try:
            order_data = StopOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide(side),
                stop_price=stop_price,
                time_in_force=time_in_force
            )
            order = self.trading_client.submit_order(order_data=order_data)
            logger.info(f"Stop order placed: {symbol} {side} {qty} shares at stop ${stop_price}")
            return {
                'id': order.id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side.value,
                'type': order.type.value,
                'stop_price': float(order.stop_price),
                'time_in_force': order.time_in_force.value,
                'status': order.status,
                'created_at': order.created_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error placing stop order: {str(e)}")
            raise
    
    def cancel_order(self, order_id):
        """Cancel an order by ID"""
        try:
            self.trading_client.cancel_order_by_id(order_id)
            logger.info(f"Order cancelled: {order_id}")
            return {"success": True, "message": f"Order {order_id} cancelled successfully"}
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            raise
    
    def cancel_all_orders(self):
        """Cancel all open orders"""
        try:
            self.trading_client.cancel_orders()
            logger.info("All orders cancelled")
            return {"success": True, "message": "All orders cancelled successfully"}
        except Exception as e:
            logger.error(f"Error cancelling all orders: {str(e)}")
            raise
    
    def get_historical_bars(self, symbol, timeframe, start_date=None, end_date=None, limit=None):
        """Get historical price bars for a symbol"""
        try:
            # Set default dates if not provided
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=7)
            
            # Convert timeframe string to TimeFrame enum
            tf_mapping = {
                "1m": TimeFrame.Minute,
                "5m": TimeFrame.Minute,
                "15m": TimeFrame.Minute,
                "30m": TimeFrame.Minute,
                "1h": TimeFrame.Hour,
                "1d": TimeFrame.Day
            }
            
            # Handle special cases for minute-based timeframes
            multiplier = 1
            if timeframe in ["5m", "15m", "30m"]:
                multiplier = int(timeframe.replace("m", ""))
                timeframe = "1m"
            
            tf = tf_mapping.get(timeframe, TimeFrame.Day)
            
            # Create request
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=tf,
                start=start_date,
                end=end_date,
                limit=limit
            )
            
            # Get bars
            bars = self.data_client.get_stock_bars(request_params)
            
            # Process and return the data
            if symbol in bars:
                bar_data = bars[symbol]
                
                # Apply multiplier for minute-based timeframes if needed
                if multiplier > 1:
                    # Group bars by multiplier and aggregate
                    aggregated_bars = []
                    for i in range(0, len(bar_data), multiplier):
                        group = bar_data[i:i+multiplier]
                        if group:
                            open_price = group[0].open
                            high_price = max(bar.high for bar in group)
                            low_price = min(bar.low for bar in group)
                            close_price = group[-1].close
                            volume = sum(bar.volume for bar in group)
                            timestamp = group[0].timestamp
                            
                            aggregated_bars.append({
                                'timestamp': timestamp.isoformat(),
                                'open': float(open_price),
                                'high': float(high_price),
                                'low': float(low_price),
                                'close': float(close_price),
                                'volume': int(volume)
                            })
                    return aggregated_bars
                
                return [{
                    'timestamp': bar.timestamp.isoformat(),
                    'open': float(bar.open),
                    'high': float(bar.high),
                    'low': float(bar.low),
                    'close': float(bar.close),
                    'volume': int(bar.volume)
                } for bar in bar_data]
            return []
        except Exception as e:
            logger.error(f"Error getting historical bars: {str(e)}")
            raise 