import logging
import aiohttp
import asyncio
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class StockScreenerService:
    def __init__(self):
        self.base_url = "http://localhost:8000"  # Your existing backend API
    
    async def _fetch_screener_results(self, endpoint, params):
        """Generic method to fetch screener results from your existing API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/stocks/screener/{endpoint}", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('stocks', [])
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
                        return data.get('stocks', [])
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
                        return data.get('stocks', [])
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
                        return data.get('stocks', [])
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
                        return data.get('results', [])
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
            price = stock.get('price', '0')
            if isinstance(price, str):
                price = price.replace('$', '').replace(',', '')
                try:
                    price = float(price)
                except ValueError:
                    price = 0
            
            # Extract symbol
            symbol = stock.get('symbol', '')
            if not symbol:
                continue
                
            # Create standardized stock object
            processed_stock = {
                'symbol': symbol,
                'name': stock.get('name', symbol),
                'price': price,
                'change_percent': stock.get('change_percent', '0%'),
                'volume': stock.get('volume', '0')
            }
            
            processed_stocks.append(processed_stock)
            
        return processed_stocks
