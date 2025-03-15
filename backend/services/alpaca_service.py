import logging
import os
from datetime import datetime

from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import AssetStatus, OrderSide, TimeInForce
from alpaca.trading.requests import GetCalendarRequest, LimitOrderRequest, MarketOrderRequest, StopOrderRequest
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class AlpacaService:
    def __init__(self):
        # Get API keys from environment variables
        self.api_key = os.environ.get("ALPACA_API_KEY")
        self.api_secret = os.environ.get("ALPACA_API_SECRET")
        self.paper_trading = os.environ.get("ALPACA_PAPER_TRADING", "true").lower() == "true"

        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API key and secret must be set in environment variables")

        # Initialize Alpaca clients
        self.trading_client = TradingClient(
            self.api_key, self.api_secret, paper=self.paper_trading, url_override=os.environ.get("ALPACA_BASE_URL")
        )
        self.data_client = StockHistoricalDataClient(self.api_key, self.api_secret)
        assets = self.trading_client.get_all_assets()
        self.active_assets = [asset for asset in assets if asset.status == AssetStatus.ACTIVE and asset.tradable]
        logger.info(f"Alpaca service initialized (Paper Trading: {self.paper_trading})")

    def find_symbol(self, symbol):
        matching_symbols = [
            asset
            for asset in self.active_assets
            if symbol.upper() in asset.symbol.upper() or (asset.name and symbol.upper() in asset.name.upper())
        ]
        for asset in matching_symbols:
            print(f"Symbol: {asset.symbol} - Name: {asset.name}")

        return matching_symbols

    def get_account_info(self):
        """Get account information from Alpaca"""
        try:
            account = self.trading_client.get_account()
            return {
                "id": account.id,
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "buying_power": float(account.buying_power),
                "equity": float(account.equity),
                "currency": account.currency,
                "status": account.status,
                "pattern_day_trader": account.pattern_day_trader,
                "trading_blocked": account.trading_blocked,
                "paper_trading": self.paper_trading,
            }
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            raise

    def get_positions(self):
        """Get current positions"""
        try:
            positions = self.trading_client.get_all_positions()
            return [
                {
                    "symbol": position.symbol,
                    "qty": float(position.qty),
                    "avg_entry_price": float(position.avg_entry_price),
                    "market_value": float(position.market_value),
                    "cost_basis": float(position.cost_basis),
                    "unrealized_pl": float(position.unrealized_pl),
                    "unrealized_plpc": float(position.unrealized_plpc),
                    "current_price": float(position.current_price),
                    "change_today": float(position.change_today),
                }
                for position in positions
            ]
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            raise

    def get_orders(self, status=None):
        """Get orders with optional status filter"""
        try:
            orders = self.trading_client.get_orders(status=status)
            return [
                {
                    "id": order.id,
                    "symbol": order.symbol,
                    "qty": float(order.qty),
                    "side": order.side.value,
                    "type": order.type.value,
                    "time_in_force": order.time_in_force.value,
                    "status": order.status,
                    "created_at": order.created_at.isoformat(),
                    "filled_at": order.filled_at.isoformat() if order.filled_at else None,
                    "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
                    "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                    "limit_price": float(order.limit_price) if order.limit_price else None,
                    "stop_price": float(order.stop_price) if order.stop_price else None,
                }
                for order in orders
            ]
        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            raise

    def place_market_order(self, symbol, qty, side, time_in_force=TimeInForce.DAY):
        """Place a market order"""
        try:
            order_data = MarketOrderRequest(symbol=symbol, qty=qty, side=OrderSide(side), time_in_force=time_in_force)
            order = self.trading_client.submit_order(order_data=order_data)
            logger.info(f"Market order placed: {symbol} {side} {qty} shares")
            return {
                "id": order.id,
                "symbol": order.symbol,
                "qty": float(order.qty),
                "side": order.side.value,
                "type": order.type.value,
                "time_in_force": order.time_in_force.value,
                "status": order.status,
                "created_at": order.created_at.isoformat(),
            }
        except Exception as e:
            logger.error(f"Error placing market order: {str(e)}")
            raise

    def place_limit_order(self, symbol, qty, side, limit_price, time_in_force=TimeInForce.DAY):
        """Place a limit order"""
        try:
            order_data = LimitOrderRequest(
                symbol=symbol, qty=qty, side=OrderSide(side), limit_price=limit_price, time_in_force=time_in_force
            )
            order = self.trading_client.submit_order(order_data=order_data)
            logger.info(f"Limit order placed: {symbol} {side} {qty} shares at ${limit_price}")
            return {
                "id": order.id,
                "symbol": order.symbol,
                "qty": float(order.qty),
                "side": order.side.value,
                "type": order.type.value,
                "limit_price": float(order.limit_price),
                "time_in_force": order.time_in_force.value,
                "status": order.status,
                "created_at": order.created_at.isoformat(),
            }
        except Exception as e:
            logger.error(f"Error placing limit order: {str(e)}")
            raise

    def place_stop_order(self, symbol, qty, side, stop_price, time_in_force=TimeInForce.DAY):
        """Place a stop order"""
        try:
            order_data = StopOrderRequest(
                symbol=symbol, qty=qty, side=OrderSide(side), stop_price=stop_price, time_in_force=time_in_force
            )
            order = self.trading_client.submit_order(order_data=order_data)
            logger.info(f"Stop order placed: {symbol} {side} {qty} shares at stop ${stop_price}")
            return {
                "id": order.id,
                "symbol": order.symbol,
                "qty": float(order.qty),
                "side": order.side.value,
                "type": order.type.value,
                "stop_price": float(order.stop_price),
                "time_in_force": order.time_in_force.value,
                "status": order.status,
                "created_at": order.created_at.isoformat(),
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

    def get_trading_days(self, start_date, end_date):
        """
        Get list of trading days between start and end date

        Args:
            start_date: Start date string in format 'YYYY-MM-DD'
            end_date: End date string in format 'YYYY-MM-DD'

        Returns:
            List of date strings in format 'YYYY-MM-DD'
        """
        try:
            # Convert string dates to datetime objects
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            # Get calendar from Alpaca
            calendar = self.trading_client.get_calendar(filters=GetCalendarRequest(start=start, end=end))

            # Extract dates as strings
            trading_days = [day.date.strftime("%Y-%m-%d") for day in calendar]

            return trading_days

        except Exception as e:
            logger.error(f"Error getting trading days: {str(e)}")
            return []

    def get_historical_bar(self, symbol, date, timeframe):
        """Get historical bars for a symbol on a specific date"""
        try:
            from alpaca.data import StockHistoricalDataClient
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

            # Format date if it's a string
            if isinstance(date, str):
                date = datetime.strptime(date, "%Y-%m-%d").date()

            # Set start and end times for the day
            start = datetime.combine(date, datetime.min.time())
            end = datetime.combine(date, datetime.max.time())

            # Create a market data client
            data_client = StockHistoricalDataClient(self.api_key, self.api_secret)

            # Map timeframe string to TimeFrame object
            timeframe_map = {
                "1Min": TimeFrame(1, TimeFrameUnit.Minute),
                "5Min": TimeFrame(5, TimeFrameUnit.Minute),
                "15Min": TimeFrame(15, TimeFrameUnit.Minute),
                "1H": TimeFrame(1, TimeFrameUnit.Hour),
                "1D": TimeFrame(1, TimeFrameUnit.Day),
            }
            tf = timeframe_map.get(timeframe, TimeFrame.Minute)
            # Create request
            request = StockBarsRequest(symbol_or_symbols=symbol.symbol, timeframe=tf, start=start, end=end)

            # Get bars
            bars_response = data_client.get_stock_bars(request)

            # Convert to list of dictionaries
            bars_list = []
            if bars_response and symbol.symbol in bars_response.data:
                for bar in bars_response.data[symbol.symbol]:
                    bars_list.append(
                        {
                            "t": bar.timestamp,
                            "o": bar.open,
                            "h": bar.high,
                            "l": bar.low,
                            "c": bar.close,
                            "v": bar.volume,
                        }
                    )

            return bars_list
        except Exception as e:
            logger.error(f"Error getting historical bars for {symbol}: {str(e)}")
            return []

    def get_historical_bars(self, symbol, date, timeframe):
        """
        Get historical price bars for a symbol on a specific date

        Args:
            symbol: Stock symbol
            date: Date string in format 'YYYY-MM-DD'
            timeframe: Bar timeframe (e.g., '1Min', '5Min', '1Hour')

        Returns:
            List of bars with OHLCV data and timestamps
        """
        try:
            # Convert timeframe to Alpaca format
            if timeframe == "1Min":
                multiplier = 1
                timespan = "minute"
            elif timeframe == "5Min":
                multiplier = 5
                timespan = "minute"
            elif timeframe == "15Min":
                multiplier = 15
                timespan = "minute"
            elif timeframe == "1Hour":
                multiplier = 1
                timespan = "hour"
            else:
                multiplier = 1
                timespan = "minute"

            # Parse date
            dt = datetime.strptime(date, "%Y-%m-%d")

            # Set start and end time to cover the full trading day
            start = datetime.combine(dt.date(), datetime.min.time())
            end = datetime.combine(dt.date(), datetime.max.time())

            # Get bars from Alpaca
            bars = self.trading_client.get_bars(
                symbol, timeframe=timespan, start=start.isoformat() + "Z", end=end.isoformat() + "Z", adjustment="raw"
            ).df

            # Convert to list of dictionaries
            if bars.empty:
                return []

            result = []
            for index, row in bars.iterrows():
                bar = {
                    "t": index.isoformat(),
                    "o": row["open"],
                    "h": row["high"],
                    "l": row["low"],
                    "c": row["close"],
                    "v": row["volume"],
                }
                result.append(bar)

            return result

        except Exception as e:
            logger.error(f"Error getting historical bars for {symbol} on {date}: {str(e)}")
            return []

    async def get_current_price(self, symbol):
        """
        Get the current price of a stock from Alpaca API

        Args:
            symbol: Stock symbol

        Returns:
            Current price as a float
        """
        try:
            # Get the latest quote for the symbol
            multisymbol_request_params = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quote = self.trading_client.get_stock_latest_quote(multisymbol_request_params)
            return quote[symbol].ask_price
        except Exception:
            # logger.error(f"Error getting current price for {symbol}: {str(e)}")
            raise


if __name__ == "__main__":
    pass
    # api_key = os.environ.get("ALPACA_API_KEY")
    # api_secret = os.environ.get("ALPACA_API_SECRET")
    # # keys required
    # stock_client = StockHistoricalDataClient(api_key, api_secret)
    # multisymbol_request_params = StockLatestQuoteRequest(symbol_or_symbols=["SPY"])
    # latest_multisymbol_quotes = stock_client.get_stock_latest_quote(multisymbol_request_params)
    # print(latest_multisymbol_quotes)
