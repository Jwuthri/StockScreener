import logging
from datetime import datetime, timedelta

import aiohttp
from alpaca.trading.enums import AssetStatus

from backend.services.alpaca_service import AlpacaService

logger = logging.getLogger(__name__)


class StockScreenerService:
    def __init__(self):
        self.base_url = "http://localhost:8000"  # Your existing backend API
        self.alpaca = AlpacaService()

    async def _fetch_screener_results(self, endpoint, params):
        """Generic method to fetch screener results from your existing API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/stocks/screener/{endpoint}", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("stocks", [])
                    else:
                        error_text = await response.text()
                        logger.error(f"Error fetching screener data: {error_text}")
                        return []
        except Exception as e:
            logger.error(f"Exception in screener fetch: {str(e)}")
            return []

    async def get_stocks_crossing_prev_day_high(self, params):
        """Get stocks that are crossing above previous day's high"""
        return await self._fetch_screener_results("crossing-prev-day-high", params)

    async def get_stocks_crossing_prev_day_low(self, params):
        """Get stocks that are crossing below previous day's low"""
        return await self._fetch_screener_results("crossing-prev-day-low", params)

    async def get_stocks_with_consecutive_positive_candles(self, params):
        """Get stocks with consecutive positive candles"""
        return await self._fetch_screener_results("consecutive-positive", params)

    async def get_stocks_with_consecutive_negative_candles(self, params):
        """Get stocks with consecutive negative candles"""
        return await self._fetch_screener_results("consecutive-negative", params)

    async def get_stocks_open_below_prev_high(self, params):
        """Get stocks that opened below previous day's high"""
        return await self._fetch_screener_results("open-below-prev-high", params)

    async def get_top_gainers(self, params):
        """Get top gaining stocks"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/stocks/top-gainers", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("stocks", [])
                    else:
                        return []
        except Exception as e:
            logger.error(f"Error fetching top gainers: {str(e)}")
            return []

    async def get_top_losers(self, params):
        """Get top losing stocks"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/stocks/top-losers", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("stocks", [])
                    else:
                        return []
        except Exception as e:
            logger.error(f"Error fetching top losers: {str(e)}")
            return []

    async def get_most_active(self, params):
        """Get most active stocks"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/stocks/most-active", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("stocks", [])
                    else:
                        return []
        except Exception as e:
            logger.error(f"Error fetching most active stocks: {str(e)}")
            return []

    async def search_stocks(self, query):
        """Search for stocks by symbol or name"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/stocks/search", params={"query": query}) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("results", [])
                    else:
                        return []
        except Exception as e:
            logger.error(f"Error searching stocks: {str(e)}")
            return []

    def process_screener_results(self, stocks, max_results=10):
        """Process and standardize screener results for trading"""
        processed_stocks = []

        for stock in stocks[:max_results]:
            # Extract price from formatted string if needed
            price = stock.get("price", "0")
            if isinstance(price, str):
                price = price.replace("$", "").replace(",", "")
                try:
                    price = float(price)
                except ValueError:
                    price = 0

            # Extract symbol
            symbol = stock.get("symbol", "")
            if not symbol:
                continue

            # Create standardized stock object
            processed_stock = {
                "symbol": symbol,
                "name": stock.get("name", symbol),
                "price": price,
                "change_percent": stock.get("change_percent", "0%"),
                "volume": stock.get("volume", "0"),
            }

            processed_stocks.append(processed_stock)

        return processed_stocks

    async def get_historical_stocks_open_below_prev_high(self, date, params):
        """
        Get historical stocks that opened below previous day's high on a specific date

        Args:
            date: Date string in format 'YYYY-MM-DD'
            params: Screening parameters

        Returns:
            List of stocks with symbol, open price, and prev_day_high
        """
        try:
            # Convert date to datetime
            dt = datetime.strptime(date, "%Y-%m-%d")

            # Calculate previous trading day
            # Note: This is a simplification. In a real implementation,
            # you would need to account for weekends and holidays
            prev_day = dt - timedelta(days=1)
            if prev_day.weekday() >= 5:  # Saturday or Sunday
                prev_day = dt - timedelta(days=3)  # Go back to Friday

            prev_date = prev_day.strftime("%Y-%m-%d")

            # Get universe of stocks to screen
            universe = await self._get_stock_universe()

            # Filter stocks based on price and volume criteria
            filtered_stocks = []

            for symbol in universe:
                try:
                    # Get daily data for current and previous day
                    current_day_data = self.alpaca.get_historical_bar(symbol, date, "1Day")
                    prev_day_data = self.alpaca.get_historical_bar(symbol, prev_date, "1Day")

                    # Filter data to only include standard market hours (14:30 to 21:00 UTC)
                    current_day_data = [
                        c
                        for c in current_day_data
                        if c["t"].hour >= 14 and c["t"].hour < 21 and (c["t"].hour != 14 or c["t"].minute >= 30)
                    ]
                    prev_day_data = [
                        c
                        for c in prev_day_data
                        if c["t"].hour >= 14 and c["t"].hour < 21 and (c["t"].hour != 14 or c["t"].minute >= 30)
                    ]

                    if not current_day_data or not prev_day_data:
                        continue

                    # Extract relevant data
                    current_open = current_day_data[0]["o"]
                    current_price = current_day_data[5]["c"]
                    current_volume = sum([p["v"] for p in current_day_data]) * 3
                    prev_day_high = max([p["h"] for p in prev_day_data])

                    # Check if price is within range
                    if current_price < params.get("min_price", 1) or current_price > params.get("max_price", 20):
                        continue

                    # Check if volume is sufficient
                    if current_volume < params.get("min_volume", 500000):
                        continue

                    # Check if opened below previous day's high
                    if current_open >= prev_day_high:
                        continue

                    # Calculate percentage below previous high
                    diff_percent = ((prev_day_high - current_open) / prev_day_high) * 100

                    # Check if difference percentage is within range
                    if diff_percent < params.get("min_diff_percent", 1) or diff_percent > params.get(
                        "max_diff_percent", 100
                    ):
                        continue

                    # Calculate change percentage from open
                    change_percent = ((current_price - current_open) / current_open) * 100

                    # # Check if change percentage is within range
                    # if change_percent < params.get("min_change_percent", 1) or change_percent > params.get(
                    #     "max_change_percent", 100
                    # ):
                    #     continue

                    # Add stock to filtered list
                    stock = {
                        "symbol": symbol,
                        "open": current_open,
                        "price": current_price,
                        "volume": current_volume,
                        "prev_day_high": prev_day_high,
                        "diff_percent": diff_percent,
                        "change_percent": change_percent,
                    }

                    filtered_stocks.append(stock)
                except Exception as e:
                    logger.debug(f"Error processing {symbol} for {date}: {str(e)}")
                    continue

            # Sort by volume (descending)
            filtered_stocks.sort(key=lambda x: x["volume"], reverse=True)

            # Limit results
            limit = params.get("limit", 100)
            return filtered_stocks[:limit]

        except Exception as e:
            logger.error(f"Error getting historical stocks for {date}: {str(e)}")
            return []

    async def _get_stock_universe(self):
        """
        Get universe of stocks to screen

        Returns:
            List of stock symbols
        """
        try:
            # For simplicity, we'll use a fixed list of major stocks
            # In a real implementation, you might want to get the actual
            # components of an index like S&P 500 or Russell 2000

            symbols = ["WULF", "FUBO", "PLUG", "RGTI", "CLSK", "DWTX", "WOLF", "SMST", "BITF"]
            # Get assets from Alpaca
            assets = self.alpaca.trading_client.get_all_assets()
            active_assets = [asset for asset in assets if asset.status == AssetStatus.ACTIVE and asset.tradable]
            active_assets = [asset for asset in active_assets if asset.symbol in symbols]
            # Limit to 500 stocks for performance
            return active_assets

        except Exception as e:
            logger.error(f"Error getting stock universe: {str(e)}")
            # Fallback to a small list of major stocks
            return ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "JPM", "V", "JNJ"]
