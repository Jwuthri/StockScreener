import logging
from typing import List, Dict, Any, Optional
from tradingview_screener import Query, col
import pandas as pd
import rookiepy
from datetime import datetime, timedelta
import random
from rich.logging import RichHandler
from rich.console import Console
from rich.traceback import install
from enum import Enum
import json
from tqdm import tqdm

# Define Interval enum that was missing
class Interval(Enum):
    MIN1 = "1"
    MIN5 = "5"
    MIN15 = "15"
    MIN30 = "30"
    HOUR = "60"
    HOUR4 = "240"
    DAY = "1D"
    WEEK = "1W"
    MONTH = "1M"

# Set up rich logging
install(show_locals=True)  # Better traceback formatting
console = Console()

# Configure rich logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, console=console)]
)

# Get logger
logger = logging.getLogger("tradingview")
def get_cookies_from_browser():
    """
    Get TradingView cookies from browsers.
    First tries Arc, then falls back to Chrome, Safari, Firefox.
    """
    try:
        logger.info("Attempting to extract TradingView cookies")
        
        # Try Arc browser first (since the user mentioned they use it)
        try:
            logger.info("Trying to get cookies from Arc browser")
            cookies = rookiepy.to_cookiejar(rookiepy.arc(['.tradingview.com']))
            logger.info("Successfully extracted cookies from Arc browser")
            return cookies
        except Exception as e:
            logger.warning(f"Couldn't get cookies from Arc: {str(e)}")
        
        # Try Chrome next
        try:
            logger.info("Trying to get cookies from Chrome browser")
            cookies = rookiepy.to_cookiejar(rookiepy.chrome(['.tradingview.com']))
            logger.info("Successfully extracted cookies from Chrome browser")
            return cookies
        except Exception as e:
            logger.warning(f"Couldn't get cookies from Chrome: {str(e)}")
        
        # Try Safari
        try:
            logger.info("Trying to get cookies from Safari browser")
            cookies = rookiepy.to_cookiejar(rookiepy.safari(['.tradingview.com']))
            logger.info("Successfully extracted cookies from Safari browser")
            return cookies
        except Exception as e:
            logger.warning(f"Couldn't get cookies from Safari: {str(e)}")
        
        # Try Firefox as a last resort
        try:
            logger.info("Trying to get cookies from Firefox browser")
            cookies = rookiepy.to_cookiejar(rookiepy.firefox(['.tradingview.com']))
            logger.info("Successfully extracted cookies from Firefox browser")
            return cookies
        except Exception as e:
            logger.warning(f"Couldn't get cookies from Firefox: {str(e)}")
        
        logger.warning("Couldn't extract cookies from any browser")
        return {}
        
    except Exception as e:
        logger.error(f"Error extracting cookies: {str(e)}")
        return {}

# Extract cookies when the module is loaded
tv_cookies = get_cookies_from_browser()
if tv_cookies:
    logger.info("Successfully loaded TradingView cookies")
else:
    logger.warning("No TradingView cookies found - using delayed data")

def explore_available_fields():
    """Debug function to explore available fields in TradingView API."""
    try:
        logger.info("Exploring available TradingView fields")
        
        # Simple query to see what fields are available
        count, df = (Query()
            .limit(3)
            .get_scanner_data(cookies=tv_cookies))
        
        if df.empty:
            logger.error("No data returned from TradingView")
            return False
            
        logger.info(f"Available columns: {list(df.columns)}")
        
        # Show a sample row to see the data format
        sample_row = df.iloc[0].to_dict()
        logger.info(f"Sample data: {sample_row}")
        
        return True
    except Exception as e:
        logger.error(f"Error exploring TradingView fields: {str(e)}")
        return False
def get_top_gainers(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get top gaining stocks using TradingView API.
    
    Args:
        limit: Maximum number of stocks to return
        
    Returns:
        List of dictionaries containing stock information
    """
    try:
        logger.info("Fetching top gainers using TradingView API")
        # Try to explore fields if we haven't done so
        if not hasattr(get_top_gainers, 'fields_explored'):
            explore_available_fields()
            get_top_gainers.fields_explored = True

        count, df = (Query()
            .select('name', 'open', 'description', 'close', 'change_abs', 'change', 'volume', 'sector', 'exchange', 'active_symbol')
            .where(col('active_symbol') == True)
            .where(col('change') > 0)  # Use 'change' for percentage change
            .where(col('change') < 500)
            .where(col('close').between(0.25, 20))
            .where(col('exchange').isin(['NASDAQ', 'NYSE']))
            .order_by('change', ascending=False)  # Sort by percentage change
            .limit(limit)
            .get_scanner_data(cookies=tv_cookies))

        if df.empty:
            logger.warning("No gainers found using TradingView API")
            return get_demo_gainers(limit)
            
        # Format the results to match the expected structure
        gainers = []
        for _, row in df.iterrows():
            try:
                # Extract and validate price
                price = row.get('close', 0)
                if pd.isna(price):
                    price = 0
                price = float(price)
                
                # Extract and validate change
                change_abs = row.get('change_abs', 0)
                if pd.isna(change_abs):
                    change_abs = 0
                change_abs = float(change_abs)
                
                # Extract and validate percent change
                change_pct = row.get('change', 0)
                if pd.isna(change_pct):
                    change_pct = 0
                change_pct = float(change_pct)
                
                # Format volume with K/M suffix
                volume = row.get('volume', 0)
                if pd.isna(volume):
                    volume = 0
                volume = int(volume)
                if volume >= 1_000_000:
                    volume_display = f"{volume/1_000_000:.1f}M"
                elif volume >= 1_000:
                    volume_display = f"{volume/1_000:.0f}K"
                else:
                    volume_display = str(volume)
                
                gainers.append({
                    "symbol": row.get('name'),
                    'name': row.get('description', row.get('name')),
                    'price': price,  # Keep as float for frontend formatting
                    'change': change_abs,  # Keep as float for frontend formatting
                    'percent_change': change_pct,  # Keep as float for frontend formatting
                    'volume': volume_display,
                    'sector': row.get('sector', 'N/A')
                })
                logger.info(f"Stock {row.get('name')} - percent_change: {change_pct} (type: {type(change_pct)})")
            except Exception as e:
                logger.warning(f"Error processing row {row}: {str(e)}")
                continue
                
        logger.info(f"Successfully fetched {len(gainers)} gainers using TradingView API")
        return gainers
        
    except Exception as e:
        logger.error(f"Error fetching top gainers using TradingView API: {str(e)}")
        return get_demo_gainers(limit)

def get_top_losers(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get top losing stocks using TradingView API.
    
    Args:
        limit: Maximum number of stocks to return
        
    Returns:
        List of dictionaries containing stock information
    """
    try:
        logger.info("Fetching top losers using TradingView API")
        
        count, df = (Query()
            .select('name', 'open', 'description', 'close', 'change_abs', 'change', 'volume', 'sector', 'exchange', 'active_symbol')
            .where(col('active_symbol') == True)
            .where(col('change') < -5)  # Use 'change' for percentage change
            .where(col('close').between(0.25, 20))
            .where(col('exchange').isin(['NASDAQ', 'NYSE']))
            .order_by('change', ascending=True)  # Sort by percentage change
            .limit(limit)
            .get_scanner_data(cookies=tv_cookies))

        if df.empty:
            logger.warning("No   found using TradingView API")
            return get_demo_gainers(limit)
            
        # Format the results to match the expected structure
        losers = []
        for _, row in df.iterrows():
            try:
                # Extract the symbol after the exchange prefix
                price = row.get('close', 0)
                change_abs = row.get('change_abs', 0)
                # 'change' is already the percentage, no need to multiply by 100
                change_pct = round(row.get('change', 0), 2)
                
                losers.append({
                    "symbol": row.get('name'),
                    'name': row.get('description'),
                    'price': str(price),
                    'change': str(change_abs),
                    'percent_change': change_pct,
                    'volume': f"{int(row.get('volume', 0)):,}" if not pd.isna(row.get('volume')) else "N/A"
                })
            except Exception as e:
                logger.warning(f"Error processing row {row}: {str(e)}")
                continue
        logger.info(f"Successfully fetched {len(losers)} losers using TradingView API")
        return losers
        
    except Exception as e:
        logger.error(f"Error fetching top losers using TradingView API: {str(e)}")
        return get_demo_losers(limit)

def get_most_active(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get most active stocks by volume using TradingView API.
    
    Args:
        limit: Maximum number of stocks to return
        
    Returns:
        List of dictionaries containing stock information
    """
    try:
        logger.info("Fetching most active stocks using TradingView API")
        count, df = (Query()
            .select('name', 'open', 'description', 'close', 'change_abs', 'change', 'volume', 'sector', 'exchange', 'active_symbol')
            .where(col('active_symbol') == True)
            .where(col('change') < -5)  # Use 'change' for percentage change
            .where(col('close').between(0.25, 20))
            .where(col('exchange').isin(['NASDAQ', 'NYSE']))
            .order_by('volume', ascending=False)
            .limit(limit)
            .get_scanner_data(cookies=tv_cookies))

        if df.empty:
            logger.warning("No active stocks found using TradingView API")
            return get_demo_most_active(limit)
            
        # Format the results to match the expected structure
        active_stocks = []
        for _, row in df.iterrows():
            try:
                # Extract the symbol after the exchange prefix
                price = row.get('close', 0)
                change_abs = row.get('change_abs', 0)
                # 'change' is already the percentage, no need to multiply by 100
                change_pct = round(row.get('change', 0), 2)
                
                active_stocks.append({
                    "symbol": row.get('name'),
                    'name': row.get('description'),
                    'price': str(price),
                    'change': str(change_abs),
                    'percent_change': change_pct,
                    'volume': f"{int(row.get('volume', 0)):,}" if not pd.isna(row.get('volume')) else "N/A"
                })
            except Exception as e:
                logger.warning(f"Error processing row {row}: {str(e)}")
                continue
                
        logger.info(f"Successfully fetched {len(active_stocks)} active stocks using TradingView API")
        return active_stocks
        
    except Exception as e:
        logger.error(f"Error fetching most active stocks using TradingView API: {str(e)}")
        return get_demo_most_active(limit)

def get_stocks_with_filters(
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_change_percent: Optional[float] = None,
    max_change_percent: Optional[float] = None,
    min_volume: Optional[int] = None,
    max_volume: Optional[int] = None,
    sector: Optional[str] = None,
    date: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get stocks filtered by various criteria using TradingView API.
    
    Args:
        min_price: Minimum stock price
        max_price: Maximum stock price
        min_change_percent: Minimum percentage change
        max_change_percent: Maximum percentage change
        min_volume: Minimum trading volume
        max_volume: Maximum trading volume
        sector: Stock sector (e.g., "Technology")
        date: Specific date in YYYY-MM-DD format to get historical data
        limit: Maximum number of stocks to return
        
    Returns:
        List of dictionaries containing stock information
    """
    try:
        if date:
            logger.info(f"Fetching filtered stocks for date {date} using TradingView API")
            # Since TradingView API doesn't directly support historical data for screeners,
            # we'll return a demo dataset when a date is specified
            # In a production environment, you would integrate with a historical data provider
            return get_demo_stocks_for_date(date, limit)
        
        logger.info("Fetching filtered stocks using TradingView API")
        
        # Build query conditions with the correct field names
        conditions = []
        
        conditions.append(col('exchange').isin(['NASDAQ', 'NYSE']))
        if min_price is not None:
            conditions.append(col('close') >= min_price)
        if max_price is not None:
            conditions.append(col('close') <= max_price)
        if min_change_percent is not None:
            conditions.append(col('change') >= min_change_percent)  # No need to divide by 100
        if max_change_percent is not None:
            conditions.append(col('change') <= max_change_percent)  # No need to divide by 100
        if min_volume is not None:
            conditions.append(col('volume') >= min_volume)
        if max_volume is not None:
            conditions.append(col('volume') <= max_volume)
        if sector is not None:
            conditions.append(col('sector') == sector)
        
        # Query TradingView with filters
        query = Query().select('name', 'close', 'open', 'high', 'low', 'change_abs', 'change', 'exchange', 'volume', 'description', 'market_cap_basic')
        
        # Add conditions if there are any
        if conditions:
            query = query.where(*conditions)
            
        # Set limit and execute
        count, df = query.limit(limit).get_scanner_data(cookies=tv_cookies)

        if df.empty:
            logger.warning("No stocks found matching the criteria")
            return []
            
        # Format the results
        filtered_stocks = []
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing stocks"):
            try:
                # Extract the symbol after the exchange prefix
                symbol = row.get('name')
                price = row.get('close', 0)
                change_abs = row.get('change_abs', 0)
                change_pct = row.get('change', 0) # Already a percentage
                
                filtered_stocks.append({
                    'symbol': symbol,
                    'name': row.get('name', symbol),
                    'price': str(price),
                    'change': str(change_abs),
                    'percent_change': change_pct,
                    'volume': f"{int(row.get('volume', 0)):,}" if not pd.isna(row.get('volume')) else "N/A",
                    'description': row.get('description', ''),
                    'market_cap': row.get('market_cap_basic', 0)
                })
            except Exception as e:
                logger.warning(f"Error processing row {row}: {str(e)}")
                continue
                
        logger.info(f"Successfully fetched {len(filtered_stocks)} filtered stocks using TradingView API")
        return filtered_stocks
        
    except Exception as e:
        logger.error(f"Error fetching filtered stocks using TradingView API: {str(e)}")
        return []

def get_stocks_with_consecutive_positive_candles(timeframe: str = "1d", num_candles: int = 3, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get stocks with consecutive positive candles.
    """
    try:
        logger.info(f"Screening for stocks with {num_candles} consecutive positive candles on {timeframe} timeframe")
        
        # Get cookies for TradingView
        tv_cookies = get_cookies_from_browser()
        
        # Get initial list of stocks to check
        count, stock_df = (Query()
            .select('name', 'close', 'change_abs', 'change', 'volume', 'description', 'exchange', 'market_cap_basic', 'VWAP', 'MACD.macd', 'RSI', 'EMA5', 'EMA20')
            .where(col('volume') > 250_000)  # Higher volume filter for more reliable results
            .where(col('exchange').isin(['NASDAQ', 'NYSE']))
            .limit(100)  # Check more stocks for better chance of finding consecutive candles
            .get_scanner_data(cookies=tv_cookies))
            
        if stock_df.empty:
            logger.warning("No stocks found for screening")
            return []
            
        # List to store stocks with consecutive positive candles
        positive_candle_stocks = []
        
        # Check each stock for consecutive positive candles
        for _, stock in stock_df.iterrows():
            symbol = stock.get('name')
            
            # Skip stocks with missing names
            if not symbol:
                logger.warning("Found stock with missing symbol, skipping")
                continue
                
            try:
                # Get historical chart data for the stock
                chart_data = get_stock_chart_data(symbol, timeframe)
                
                # Skip if no chart data is available
                if not chart_data or 'data' not in chart_data or not chart_data['data']:
                    logger.warning(f"No chart data available for {symbol}, skipping")
                    continue
                
                # Get candle data (most recent candles come last)
                candles = chart_data['data']
                
                # Count consecutive positive candles starting from the most recent
                consecutive_positive = 0
                
                # We need at least num_candles+1 data points to check for num_candles consecutive positive candles
                # (comparing current with previous)
                if len(candles) <= num_candles:
                    logger.warning(f"Not enough candles for {symbol} to check for {num_candles} consecutive positive candles")
                    continue
                
                # Start from the most recent candle (last in the list) and go backwards
                for i in range(len(candles)-1, 0, -1):
                    current_close = candles[i]['price']  # Close price (assuming OHLC format)
                    previous_close = candles[i-1]['price']  # Previous close
                    
                    if current_close > previous_close:
                        consecutive_positive += 1
                    else:
                        break  # Break on first non-positive candle
                    
                    # Stop if we've found enough consecutive positive candles
                    if consecutive_positive >= num_candles:
                        break
                
                # If we have enough consecutive positive candles, add to our results
                if consecutive_positive >= num_candles:
                    # Get detailed stock information
                    stock_details = get_stock_details_tv(symbol)
                    
                    if stock_details:
                        try:
                            # Format and add relevant information
                            # Make sure price is a number and never N/A 
                            price = stock_details.get("price", 0)
                            if price is None or pd.isna(price):
                                # Use the most recent candle's price as fallback if available
                                if candles and len(candles) > 0:
                                    price = candles[-1].get('price', 0)
                                else:
                                    price = 0
                            
                            # Explicitly force conversion to float
                            try:
                                price = float(price)
                            except (ValueError, TypeError):
                                price = 0.0
                                logger.warning(f"Failed to convert price to float for {symbol}, using 0")
                            
                            # Make sure percent_change is a number and never N/A
                            percent_change = stock_details.get("percent_change", 0)
                            if percent_change is None or pd.isna(percent_change):
                                # Calculate percent change from candles if available
                                if candles and len(candles) > 1:
                                    last_price = candles[-1].get('price', 0)
                                    prev_price = candles[-2].get('price', 0)
                                    if prev_price and prev_price > 0:
                                        percent_change = ((last_price - prev_price) / prev_price) * 100
                                else:
                                    percent_change = 0
                            
                            # Explicitly force conversion to float
                            try:
                                percent_change = float(percent_change)
                            except (ValueError, TypeError):
                                percent_change = 0.0
                                logger.warning(f"Failed to convert percent_change to float for {symbol}, using 0")
                            
                            # For debugging only
                            logger.info(f"Stock: {symbol}, Price: {price} (type: {type(price)}), Change%: {percent_change} (type: {type(percent_change)})")
                            
                            volume_num = stock_details.get("volume")
                            if isinstance(volume_num, str):
                                if 'M' in volume_num:
                                    volume_num = float(volume_num.replace('M', '')) * 1000000
                                elif 'K' in volume_num:
                                    volume_num = float(volume_num.replace('K', '')) * 1000
                                else:
                                    volume_num = float(volume_num)
 
                            # Instead of trying to be clever with formatting, just pass the plain numeric values
                            # The frontend expects numbers that it can format itself
                            stock_data = {
                                "symbol": symbol,
                                "name": stock_details.get("name", symbol),  # Use symbol as fallback for name
                                "price": price,  # Already ensured to be a float
                                'price_display': f"${price:.2f}",  # Formatted for display
                                'change_percent_display': f"{percent_change:.2f}%",
                                "change_percent": percent_change,  # Already ensured to be a float
                                "volume": volume_num,  # Keep volume as is since it's already handled correctly
                                "volume_display": stock_details.get("volume"),  # Formatted for display
                                "sector": stock_details.get("sector", "Unknown"),
                                "industry": stock_details.get("industry", "Unknown"),
                                "exchange": stock.get("exchange", "Unknown"),
                                "consecutive_positive_candles": consecutive_positive,
                                "description": stock_details.get("description", ""),
                            }
                            
                            # Final check to ensure numeric fields are not None or NaN
                            for field in ["price", "change_percent"]:
                                if stock_data[field] is None or (hasattr(stock_data[field], 'is_integer') and pd.isna(stock_data[field])):
                                    logger.warning(f"Field {field} is None or NaN for {symbol}, setting to 0")
                                    stock_data[field] = 0.0
                                    
                            # Print the final object being added
                            logger.info(f"Adding stock to results: {json.dumps(stock_data, default=str)}")
                            
                            positive_candle_stocks.append(stock_data)
                        except Exception as e:
                            logger.error(f"Error processing stock details for {symbol}: {str(e)}")
                            # Add a minimal record with the symbol
                            positive_candle_stocks.append({
                                "symbol": symbol,
                                "name": symbol,
                                "price": 0.0,
                                "price_display": "0.00",
                                "change_percent": 0.0,
                                "change_percent_display": "0.00%",
                                "volume": "0",
                                "volume_display": "0",
                                "sector": "Unknown",
                                "industry": "Unknown",
                                "exchange": "Unknown",
                                "consecutive_positive_candles": consecutive_positive,
                                "description": symbol,
                            })
                
            except Exception as e:
                logger.error(f"Error checking consecutive candles for {symbol}: {str(e)}")
                continue
        
        # Sort by number of consecutive positive candles (descending) and then by change percentage (descending)
        positive_candle_stocks.sort(key=lambda x: (x["consecutive_positive_candles"], x["change_percent"]), reverse=True)
        # Return the top 'limit' stocks
        return positive_candle_stocks[:limit]
        
    except Exception as e:
        logger.error(f"Error fetching stocks with consecutive positive candles: {str(e)}")
        return []

def get_stocks_with_consecutive_negative_candles(timeframe: str = "1d", num_candles: int = 3, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get stocks with consecutive negative candles.
    """
    try:
        logger.info(f"Screening for stocks with {num_candles} consecutive negative candles on {timeframe} timeframe")
        
        # Get cookies for TradingView
        tv_cookies = get_cookies_from_browser()
        
        # Get initial list of stocks to check
        count, stock_df = (Query()
            .select('name', 'close', 'change_abs', 'change', 'volume', 'description', 'exchange', 'market_cap_basic')
            .where(col('volume') > 250_000)  # Higher volume filter for more reliable results
            .where(col('exchange').isin(['NASDAQ', 'NYSE']))
            .limit(50)  # Check more stocks for better chance of finding consecutive candles
            .get_scanner_data(cookies=tv_cookies))
            
        if stock_df.empty:
            logger.warning("No stocks found for screening")
            return []
            
        # List to store stocks with consecutive negative candles
        negative_candle_stocks = []
        
        # Check each stock for consecutive negative candles
        for _, stock in stock_df.iterrows():
            symbol = stock.get('name')
            
            # Skip stocks with missing names
            if not symbol:
                logger.warning("Found stock with missing symbol, skipping")
                continue
                
            try:
                # Get historical chart data for the stock
                chart_data = get_stock_chart_data(symbol, timeframe)
                
                # Skip if no chart data is available
                if not chart_data or 'data' not in chart_data or not chart_data['data']:
                    logger.warning(f"No chart data available for {symbol}, skipping")
                    continue
                
                # Get candle data (most recent candles come last)
                candles = chart_data['data']
                
                # Count consecutive negative candles starting from the most recent
                consecutive_negative = 0
                
                # We need at least num_candles+1 data points to check for num_candles consecutive negative candles
                # (comparing current with previous)
                if len(candles) <= num_candles:
                    logger.warning(f"Not enough candles for {symbol} to check for {num_candles} consecutive negative candles")
                    continue
                
                # Start from the most recent candle (last in the list) and go backwards
                for i in range(len(candles)-1, 0, -1):
                    current_close = candles[i]['price']  # Close price (assuming OHLC format)
                    previous_close = candles[i-1]['price']  # Previous close
                    
                    if current_close < previous_close:  # Check for negative candle (current < previous)
                        consecutive_negative += 1
                    else:
                        break  # Break on first non-negative candle
                    
                    # Stop if we've found enough consecutive negative candles
                    if consecutive_negative >= num_candles:
                        break
                
                # If we have enough consecutive negative candles, add to our results
                if consecutive_negative >= num_candles:
                    # Get detailed stock information
                    stock_details = get_stock_details_tv(symbol)
                    
                    if stock_details:
                        try:
                            # Format and add relevant information
                            # Make sure price is a number and never N/A 
                            price = stock_details.get("price", 0)
                            if price is None or pd.isna(price):
                                # Use the most recent candle's price as fallback if available
                                if candles and len(candles) > 0:
                                    price = candles[-1].get('price', 0)
                                else:
                                    price = 0
                            
                            # Explicitly force conversion to float
                            try:
                                price = float(price)
                            except (ValueError, TypeError):
                                price = 0.0
                                logger.warning(f"Failed to convert price to float for {symbol}, using 0")
                            
                            # Make sure percent_change is a number and never N/A
                            percent_change = stock_details.get("percent_change", 0)
                            if percent_change is None or pd.isna(percent_change):
                                # Calculate percent change from candles if available
                                if candles and len(candles) > 1:
                                    last_price = candles[-1].get('price', 0)
                                    prev_price = candles[-2].get('price', 0)
                                    if prev_price and prev_price > 0:
                                        percent_change = ((last_price - prev_price) / prev_price) * 100
                                else:
                                    percent_change = 0
                            
                            # Explicitly force conversion to float
                            try:
                                percent_change = float(percent_change)
                            except (ValueError, TypeError):
                                percent_change = 0.0
                                logger.warning(f"Failed to convert percent_change to float for {symbol}, using 0")
                            
                            # For debugging only
                            logger.info(f"Stock: {symbol}, Price: {price} (type: {type(price)}), Change%: {percent_change} (type: {type(percent_change)})")
                            
                            volume_num = stock_details.get("volume")
                            if isinstance(volume_num, str):
                                if 'M' in volume_num:
                                    volume_num = float(volume_num.replace('M', '')) * 1000000
                                elif 'K' in volume_num:
                                    volume_num = float(volume_num.replace('K', '')) * 1000
                                else:
                                    volume_num = float(volume_num)
 
                            # Instead of trying to be clever with formatting, just pass the plain numeric values
                            # The frontend expects numbers that it can format itself
                            stock_data = {
                                "symbol": symbol,
                                "name": stock_details.get("name", symbol),  # Use symbol as fallback for name
                                "price": price,  # Already ensured to be a float
                                'price_display': f"${price:.2f}",  # Formatted for display
                                'change_percent_display': f"{percent_change:.2f}%",
                                "change_percent": percent_change,  # Already ensured to be a float
                                "volume": volume_num,  # Keep volume as is since it's already handled correctly
                                "volume_display": stock_details.get("volume"),  # Formatted for display
                                "sector": stock_details.get("sector", "Unknown"),
                                "industry": stock_details.get("industry", "Unknown"),
                                "exchange": stock.get("exchange", "Unknown"),
                                "consecutive_negative_candles": consecutive_negative,
                                "description": stock_details.get("description", ""),
                            }
                            
                            # Final check to ensure numeric fields are not None or NaN
                            for field in ["price", "change_percent"]:
                                if stock_data[field] is None or (hasattr(stock_data[field], 'is_integer') and pd.isna(stock_data[field])):
                                    logger.warning(f"Field {field} is None or NaN for {symbol}, setting to 0")
                                    stock_data[field] = 0.0
                                    
                            # Print the final object being added
                            logger.info(f"Adding stock to results: {json.dumps(stock_data, default=str)}")
                            
                            negative_candle_stocks.append(stock_data)
                        except Exception as e:
                            logger.error(f"Error processing stock details for {symbol}: {str(e)}")
                            # Add a minimal record with the symbol
                            negative_candle_stocks.append({
                                "symbol": symbol,
                                "name": symbol,
                                "price": 0.0,
                                "price_display": "0.00",
                                "change_percent": 0.0,
                                "change_percent_display": "0.00%",
                                "volume": "0",
                                "volume_display": "0",
                                "sector": "Unknown",
                                "industry": "Unknown",
                                "exchange": "Unknown",
                                "consecutive_negative_candles": consecutive_negative,
                                "description": symbol,
                            })
                
            except Exception as e:
                logger.error(f"Error checking consecutive candles for {symbol}: {str(e)}")
                continue
        
        # Sort by number of consecutive negative candles (descending) and then by change percentage (ascending)
        negative_candle_stocks.sort(key=lambda x: (x["consecutive_negative_candles"], -x["change_percent"]), reverse=True)
        # Return the top 'limit' stocks
        return negative_candle_stocks[:limit]
        
    except Exception as e:
        logger.error(f"Error fetching stocks with consecutive negative candles: {str(e)}")
        return []

# Demo data functions for fallback scenarios
def get_demo_gainers(limit: int = 10) -> List[Dict[str, Any]]:
    """Return demo data for top gainers when API fails."""
    logger.info("Using demo data for top gainers")
    demo_data = [
        {"symbol": "AAPL", "name": "Apple Inc.", "price": "185.56", "change": "5.23", "percent_change": 2.89, "volume": "68,532,800"},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "price": "400.96", "change": "10.25", "percent_change": 2.62, "volume": "32,654,700"},
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "price": "827.61", "change": "20.13", "percent_change": 2.49, "volume": "45,781,200"},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "price": "178.75", "change": "4.32", "percent_change": 2.47, "volume": "35,612,900"},
        {"symbol": "TSLA", "name": "Tesla, Inc.", "price": "175.23", "change": "3.78", "percent_change": 2.21, "volume": "58,963,400"},
        {"symbol": "GOOG", "name": "Alphabet Inc.", "price": "147.68", "change": "2.85", "percent_change": 1.97, "volume": "22,541,600"},
        {"symbol": "META", "name": "Meta Platforms, Inc.", "price": "485.39", "change": "9.26", "percent_change": 1.94, "volume": "18,356,700"},
        {"symbol": "AMD", "name": "Advanced Micro Devices, Inc.", "price": "156.37", "change": "2.81", "percent_change": 1.83, "volume": "42,158,300"},
        {"symbol": "AVGO", "name": "Broadcom Inc.", "price": "1456.82", "change": "24.76", "percent_change": 1.73, "volume": "5,874,200"},
        {"symbol": "ADBE", "name": "Adobe Inc.", "price": "493.55", "change": "8.32", "percent_change": 1.71, "volume": "3,682,100"}
    ]
    return demo_data[:limit]

def get_demo_losers(limit: int = 10) -> List[Dict[str, Any]]:
    """Return demo data for top losers when API fails."""
    logger.info("Using demo data for top losers")
    demo_data = [
        {"symbol": "BABA", "name": "Alibaba Group Holding Limited", "price": "72.36", "change": "-3.42", "percent_change": -4.51, "volume": "25,874,300"},
        {"symbol": "PYPL", "name": "PayPal Holdings, Inc.", "price": "62.14", "change": "-2.35", "percent_change": -3.64, "volume": "18,742,600"},
        {"symbol": "NFLX", "name": "Netflix, Inc.", "price": "602.75", "change": "-21.48", "percent_change": -3.44, "volume": "12,387,500"},
        {"symbol": "INTC", "name": "Intel Corporation", "price": "35.67", "change": "-1.18", "percent_change": -3.20, "volume": "46,982,700"},
        {"symbol": "MU", "name": "Micron Technology, Inc.", "price": "108.34", "change": "-3.25", "percent_change": -2.91, "volume": "22,458,900"},
        {"symbol": "NKE", "name": "NIKE, Inc.", "price": "93.42", "change": "-2.63", "percent_change": -2.74, "volume": "15,698,200"},
        {"symbol": "DIS", "name": "The Walt Disney Company", "price": "112.58", "change": "-3.07", "percent_change": -2.65, "volume": "14,582,600"},
        {"symbol": "PFE", "name": "Pfizer Inc.", "price": "26.84", "change": "-0.68", "percent_change": -2.47, "volume": "32,654,800"},
        {"symbol": "WMT", "name": "Walmart Inc.", "price": "58.96", "change": "-1.42", "percent_change": -2.35, "volume": "10,247,500"},
        {"symbol": "KO", "name": "The Coca-Cola Company", "price": "61.23", "change": "-1.38", "percent_change": -2.20, "volume": "18,654,200"}
    ]
    return demo_data[:limit]

def get_demo_most_active(limit: int = 10) -> List[Dict[str, Any]]:
    """Return demo data for most active stocks when API fails."""
    logger.info("Using demo data for most active stocks")
    demo_data = [
        {"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust", "price": "542.89", "change": "2.45", "percent_change": 0.45, "volume": "95,874,200"},
        {"symbol": "TSLA", "name": "Tesla, Inc.", "price": "175.23", "change": "3.78", "percent_change": 2.21, "volume": "58,963,400"},
        {"symbol": "AAPL", "name": "Apple Inc.", "price": "185.56", "change": "5.23", "percent_change": 2.89, "volume": "48,532,800"},
        {"symbol": "QQQ", "name": "Invesco QQQ Trust", "price": "456.73", "change": "3.25", "percent_change": 0.72, "volume": "47,852,300"},
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "price": "827.61", "change": "20.13", "percent_change": 2.49, "volume": "45,781,200"},
        {"symbol": "AMD", "name": "Advanced Micro Devices, Inc.", "price": "156.37", "change": "2.81", "percent_change": 1.83, "volume": "42,158,300"},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "price": "178.75", "change": "4.32", "percent_change": 2.47, "volume": "35,612,900"},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "price": "400.96", "change": "10.25", "percent_change": 2.62, "volume": "32,654,700"},
        {"symbol": "PLTR", "name": "Palantir Technologies Inc.", "price": "24.87", "change": "0.54", "percent_change": 2.22, "volume": "28,745,600"},
        {"symbol": "BABA", "name": "Alibaba Group Holding Limited", "price": "72.36", "change": "-3.42", "percent_change": -4.51, "volume": "25,874,300"}
    ]
    return demo_data[:limit]

def get_demo_stocks_for_date(date: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get a demo set of stocks for a specific historical date.
    In a real implementation, this would fetch data from a historical data provider.
    
    Args:
        date: Date in YYYY-MM-DD format
        limit: Maximum number of stocks to return
        
    Returns:
        List of dictionaries containing stock information
    """
    logger.info(f"Generating demo stock data for date: {date}")
    
    # Sample stocks
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "JNJ", "V"]
    names = [
        "Apple Inc.", "Microsoft Corporation", "Alphabet Inc.", "Amazon.com Inc.", 
        "Tesla Inc.", "Meta Platforms Inc.", "NVIDIA Corporation", "JPMorgan Chase & Co.",
        "Johnson & Johnson", "Visa Inc."
    ]
    
    # Generate random but plausible stock data based on the date
    # Use the date as a seed for random generation to ensure consistent results
    import random
    from datetime import datetime
    
    # Convert date string to datetime and use it as a seed
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    seed = int(date_obj.timestamp())
    random.seed(seed)
    
    # Check if it's a weekend
    is_weekend = date_obj.weekday() >= 5
    
    results = []
    for i in range(min(limit, len(symbols))):
        # Generate price between 50 and 500
        price = round(random.uniform(50, 500), 2)
        
        # Generate change percentage between -5 and +5
        change_percent = 0 if is_weekend else round(random.uniform(-5, 5), 2)
        
        # Change volume based on price (higher priced stocks often have lower volume)
        volume = random.randint(500000, 15000000)
        
        results.append({
            "symbol": symbols[i],
            "name": names[i],
            "price": str(price),
            "change": str(round(price * change_percent / 100, 2)),
            "percent_change": change_percent,
            "volume": f"{volume:,}",
            "historical_date": date,
            "note": "Historical data" if not is_weekend else "Weekend - no trading"
        })
    
    if is_weekend:
        logger.info(f"Note: {date} is a weekend, returning zero-change demo data")
    
    return results 

def get_stocks_crossing_prev_day_high(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get stocks from the top gainers that have their current price crossing above the previous day high.
    Uses the smallest available timeframe to check for crosses.
    
    Args:
        limit: Maximum number of stocks to return
        
    Returns:
        List of dictionaries containing stock information
    """
    try:
        logger.info(f"Fetching stocks crossing above previous day high (limit: {limit})")
        
        # Get top gainers first - increase the limit to get a good pool of candidates
        gainers = get_top_gainers(limit * 3)
        logger.info(f"Retrieved {len(gainers)} gainers to check for previous day high crossing")
        
        # Log the first few gainers to debug the data format
        if gainers:
            logger.info(f"Sample data format (first gainer): {gainers[0]}")
            
        crossing_stocks = []
        for stock in gainers:
            symbol = stock.get('symbol')
            if not symbol:
                continue
                
            try:
                # Get current price from the stock data
                price_str = stock.get('price', '0')
                # Remove any currency symbols and commas
                if isinstance(price_str, str):
                    price_str = price_str.replace('$', '').replace(',', '')
                
                try:
                    current_price = float(price_str)
                    logger.debug(f"Parsed price for {symbol}: {current_price} (from {stock.get('price')})")
                except (ValueError, TypeError):
                    logger.warning(f"Invalid price format for {symbol}: {price_str}")
                    continue
                
                # Get previous day high
                prev_day = get_previous_day_data(symbol)
                prev_day_high = prev_day.get('previous_day_high')
                
                # Skip stocks with missing previous day data
                if not prev_day_high:
                    logger.debug(f"No previous day high for {symbol}, skipping")
                    continue
                
                logger.debug(f"Checking {symbol} - Current: {current_price}, Prev High: {prev_day_high}")
                
                # Check if current price is crossing above previous day high
                if current_price > prev_day_high:
                    logger.info(f"✓ Stock {symbol} crossing above previous day high: {current_price} > {prev_day_high}")
                    
                    # Process change percentage
                    change_percent = stock.get('percent_change')
                    if isinstance(change_percent, str):
                        try:
                            change_percent = float(change_percent.replace('%', ''))
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid change percent for {symbol}: {change_percent}")
                            # Try to calculate it from price and previous day close
                            try:
                                prev_close = prev_day.get('previous_day_close')
                                if prev_close and prev_close > 0:
                                    change_percent = ((current_price - prev_close) / prev_close) * 100
                                    logger.debug(f"Calculated change percent for {symbol}: {change_percent}%")
                            except Exception as e:
                                logger.warning(f"Error calculating change percent: {e}")
                                change_percent = 0
                    
                    # Ensure volume is properly formatted
                    volume = stock.get('volume', '0')
                    if isinstance(volume, str):
                        # Check if volume already has K/M suffix
                        if 'K' in volume or 'M' in volume:
                            # Keep as is for display
                            volume_display = volume
                            # But also create a numeric version for filtering
                            try:
                                if 'K' in volume:
                                    volume_num = float(volume.replace('K', '')) * 1000
                                elif 'M' in volume:
                                    volume_num = float(volume.replace('M', '')) * 1000000
                                else:
                                    volume_num = float(volume.replace(',', ''))
                            except (ValueError, TypeError):
                                volume_num = 0
                        else:
                            # Clean the volume string and convert to number
                            volume_clean = volume.replace(',', '')
                            try:
                                volume_num = int(float(volume_clean))
                                # Format for display
                                if volume_num >= 1000000:
                                    volume_display = f"{volume_num/1000000:.1f}M"
                                elif volume_num >= 1000:
                                    volume_display = f"{volume_num/1000:.0f}K"
                                else:
                                    volume_display = str(volume_num)
                            except (ValueError, TypeError):
                                logger.warning(f"Invalid volume for {symbol}: {volume}")
                                volume_num = 0
                                volume_display = "N/A"
                    else:
                        # If it's already a number
                        volume_num = volume if volume else 0
                        # Format for display
                        if volume_num >= 1000000:
                            volume_display = f"{volume_num/1000000:.1f}M"
                        elif volume_num >= 1000:
                            volume_display = f"{volume_num/1000:.0f}K"
                        else:
                            volume_display = str(volume_num)
                    
                    # Get company name and sector if available
                    name = stock.get('name', f"{symbol}")
                    sector = stock.get('sector', 'N/A')
                    
                    # Try to get more details if missing
                    if sector == 'N/A' or not name:
                        try:
                            detailed_info = get_stock_details_tv(symbol)
                            if not name or name == symbol:
                                name = detailed_info.get('name', name)
                            if sector == 'N/A':
                                sector = detailed_info.get('sector', 'N/A')
                                
                            # Also get industry and exchange if available
                            industry = detailed_info.get('industry', stock.get('industry', 'N/A'))
                            exchange = detailed_info.get('exchange', stock.get('exchange', 'N/A'))
                        except Exception as e:
                            logger.warning(f"Could not get detailed info for {symbol}: {e}")
                            industry = stock.get('industry', 'N/A')
                            exchange = stock.get('exchange', 'N/A')
                    else:
                        industry = stock.get('industry', 'N/A')
                        exchange = stock.get('exchange', 'N/A')
                    
                    # Create a stock data object with all fields properly formatted
                    stock_data = {
                        'symbol': symbol,
                        'name': name,
                        'price': float(current_price),  # Numeric value
                        'price_display': f"${current_price:.2f}",  # Formatted for display
                        'prev_day_high': float(prev_day_high),
                        'change_percent': float(change_percent),  # Numeric value 
                        'change_percent_display': f"{change_percent:.2f}%",  # Formatted for display
                        'volume': volume_num,  # Numeric value
                        'volume_display': volume_display,  # Formatted for display
                        'sector': sector,
                        'industry': industry,
                        'exchange': exchange
                    }
                    
                    crossing_stocks.append(stock_data)
                    
                    # If we have enough stocks, stop
                    if len(crossing_stocks) >= limit:
                        logger.info(f"Reached limit of {limit} stocks, stopping search")
                        break
                        
            except Exception as e:
                logger.warning(f"Error processing stock {symbol}: {str(e)}")
                continue
                
        logger.info(f"Found {len(crossing_stocks)} stocks crossing above previous day high")
        
        # Log the first few stocks for debugging
        if crossing_stocks:
            logger.info(f"First stock crossing previous day high: {crossing_stocks[0]}")
            
        return crossing_stocks
    except Exception as e:
        logger.error(f"Error in get_stocks_crossing_prev_day_high: {str(e)}")
        return [] 

def get_stock_details_tv(symbol: str) -> Dict[str, Any]:
    """
    Get detailed information for a stock from TradingView.
    """
    try:
        # Check if symbol is None or empty
        if not symbol:
            logger.warning("Attempted to fetch stock details with None or empty symbol")
            return {
                "symbol": None,
                "price": None,
                "change": None,
                "volume": None,
                "description": "Invalid Symbol",
                "sector": None,
                "industry": None,
                "error": "Invalid symbol provided"
            }
            
        # Clean up the symbol (remove any spaces or special characters)
        clean_symbol = symbol.strip().upper()
        
        # Get cookies for TradingView
        tv_cookies = get_cookies_from_browser()
        
        # Try to fetch data for the exact symbol first
        try:
            query = (Query()
                .select(
                    'name', 'close', 'change', 'change_abs', 'volume',
                    'description', 'market_cap_basic', 'sector', 'industry',
                    'price_earnings_ttm', 'earnings_per_share_basic_ttm',
                    'price_book_fq', 'average_volume_30d_calc'
                )
                .where(col('name') == clean_symbol)  # Name is the ticker symbol in TradingView
                .limit(1)
                .get_scanner_data(cookies=tv_cookies))
                        
            count, df = query if query else (0, pd.DataFrame())
            
            if df is None or df.empty:
                logger.warning(f"No data found for {symbol}, trying broader search")
                # Try a broader search
                try:
                    broader_query = (Query()
                        .select(
                            'name', 'close', 'change', 'change_abs', 'volume',
                            'description', 'market_cap_basic', 'sector', 'industry',
                            'price_earnings_ttm', 'earnings_per_share_basic_ttm',
                            'price_book_fq', 'average_volume_30d_calc'
                        )
                        .limit(100)  # Get more results to search through
                        .get_scanner_data(cookies=tv_cookies))
                    
                    count, df = broader_query if broader_query else (0, pd.DataFrame())
                    
                    if df is not None and not df.empty:
                        # Filter in Python to find ticker containing our symbol
                        df = df[df['name'].str.contains(clean_symbol, case=False, na=False)]
                        if not df.empty:
                            df = df.head(1)
                except Exception as e:
                    logger.warning(f"Broader search failed: {str(e)}")
                    df = pd.DataFrame()
                
                if df is None or df.empty:
                    logger.warning(f"Still no data found for {symbol}, using demo data")
                    return get_demo_stock_details(symbol)
            
            if df is None or df.empty:
                logger.warning(f"No data found for {symbol} after all attempts")
                return get_demo_stock_details(symbol)
                
            row = df.iloc[0]
            logger.info(f"Found stock data for {symbol}: {row['name']}")
            
            # Handle numeric values carefully to avoid NaN issues
            try:
                pe_ratio = float(row.get('price_earnings_ttm', 0))
                if pd.isna(pe_ratio):
                    pe_ratio = 0
            except (ValueError, TypeError):
                pe_ratio = 0
            
            try:
                eps = float(row.get('earnings_per_share_basic_ttm', 0))
                if pd.isna(eps):
                    eps = 0
            except (ValueError, TypeError):
                eps = 0
            
            try:
                dividend_yield = float(row.get('dividend_yield_current', 0))
                if pd.isna(dividend_yield):
                    dividend_yield = 0
            except (ValueError, TypeError):
                dividend_yield = 0
            
            try:
                pb_ratio = float(row.get('price_book_fq', 0))
                if pd.isna(pb_ratio):
                    pb_ratio = 0
            except (ValueError, TypeError):
                pb_ratio = 0
            
            # Format the result
            stock_details = {
                'symbol': row.get('name', clean_symbol),  # Name field contains the ticker symbol
                'name': row.get('description', f"{clean_symbol} Inc."),  # Description contains company name
                'price': float(row.get('close', 0)),
                'change': float(row.get('change_abs', 0)),
                'percent_change': float(row.get('change', 0)),
                'volume': format_volume(row.get('volume')),
                'avg_volume': format_volume(row.get('average_volume_30d_calc')),
                'market_cap': format_market_cap(row.get('market_cap_basic')),
                'pe_ratio': pe_ratio,
                'eps': eps,
                'dividend_yield': dividend_yield,
                'pb_ratio': pb_ratio,
                'sector': row.get('sector', 'N/A'),
                'industry': row.get('industry', 'N/A'),
                'description': row.get('description', 'No description available.')
            }
            
            # Log success with some key data points for debugging
            logger.info(f"Successfully fetched details for {symbol} - Price: {stock_details['price']}, P/E: {stock_details['pe_ratio']}")
            return stock_details
        
        except Exception as e:
            logger.error(f"Error fetching stock details for {symbol}: {str(e)}")
            return get_demo_stock_details(symbol)
    
    except Exception as e:
        logger.error(f"Error fetching stock details for {symbol}: {str(e)}")
        return get_demo_stock_details(symbol)

def get_stock_chart_data(symbol: str, timeframe: str = "1D") -> Dict[str, Any]:
    """Get chart data for a specific stock."""
    try:
        logger.info(f"Fetching chart data for {symbol} with timeframe {timeframe}")
        
        # Map timeframe to appropriate resolution and number of data points
        timeframe_map = {
            "1D": ("5", 78),      # 5-minute bars for 1 day (6.5 hours × 12)
            "5D": ("15", 130),    # 15-minute bars for 5 days
            "1M": ("60", 120),    # 1-hour bars for 1 month
            "3M": ("D", 90),      # Daily bars for 3 months
            "6M": ("D", 180),     # Daily bars for 6 months
            "1Y": ("D", 365),     # Daily bars for 1 year
            "5Y": ("W", 260)      # Weekly bars for 5 years
        }
        
        resolution, limit = timeframe_map.get(timeframe, ("D", 90))
        
        # Get the current price to use as base for simulated data
        stock_details = get_stock_details_tv(symbol)
        current_price = float(stock_details.get('price', 100))
        
        # Generate data points
        now = datetime.now()
        data = []
        
        if resolution == "5":
            interval = timedelta(minutes=5)
            start_time = now - timedelta(days=1)
        elif resolution == "15":
            interval = timedelta(minutes=15)
            start_time = now - timedelta(days=5)
        elif resolution == "60":
            interval = timedelta(hours=1)
            start_time = now - timedelta(days=30)
        elif resolution == "D":
            interval = timedelta(days=1)
            start_time = now - timedelta(days=limit)
        elif resolution == "W":
            interval = timedelta(weeks=1)
            start_time = now - timedelta(weeks=limit)
        
        # Generate points with standard Python types
        time_point = start_time
        price = float(current_price * 0.95)  # Start a bit below current price
        
        for i in range(limit):
            # Generate realistic price movement
            change = random.uniform(-0.02, 0.02)
            price = max(0.01, price * (1 + change))
            
            # Make sure we trend toward the current price near the end
            if i > limit * 0.9:
                price = price + (current_price - price) * 0.1
            
            close_price = round(price, 2)
            open_price = round(close_price * (1 + random.uniform(-0.01, 0.01)), 2)
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.01))
            
            # Format timestamp as integer Unix timestamp
            timestamp = int(time_point.timestamp())
            volume = random.randint(100000, 5000000)
            
            data.append({
                'time': timestamp,
                'price': close_price,
                'volume': volume
            })
            
            time_point += interval
        
        # Sort by time
        data.sort(key=lambda x: x['time'])
        
        # Create parallel structure with the exact format needed for database
        database_data = []
        for point in data:
            # Convert timestamp to datetime object
            dt = datetime.fromtimestamp(point['time'])
            
            database_data.append({
                'Date': dt,  # Use datetime object
                'Open': float(point['price'] * 0.99),  # Estimate open price
                'High': float(point['price'] * 1.01),  # Estimate high 
                'Low': float(point['price'] * 0.98),   # Estimate low
                'Close': float(point['price']),
                'Volume': int(point['volume'])
            })
        
        logger.info(f"Generated {len(data)} chart data points for {symbol}")
        
        # Return both formats
        return {
            'symbol': str(symbol),
            'timeframe': str(timeframe),
            'data': data,
            'database_data': database_data  # For database operations
        }
        
    except Exception as e:
        logger.error(f"Error generating chart data for {symbol}: {str(e)}")
        return get_demo_chart_data(symbol, timeframe)

# Helper formatting functions
def format_volume(volume):
    if pd.isna(volume) or volume is None:
        return "N/A"
    volume = int(volume)
    if volume >= 1_000_000_000:
        return f"{volume/1000000_000:.2f}B"
    elif volume >= 1_000_000:
        return f"{volume/1000000:.2f}M"
    elif volume >= 1_000:
        return f"{volume/1000:.2f}K"
    return f"{volume:,}"

def format_market_cap(market_cap):
    if pd.isna(market_cap) or market_cap is None:
        return "N/A"
    if market_cap >= 1_000_000_000:
        return f"${market_cap/1_000_000_000:.2f}B"
    elif market_cap >= 1_000_000:
        return f"${market_cap/1_000_000:.2f}M"
    return f"${market_cap:,.2f}"

def format_numeric(value):
    if pd.isna(value) or value is None:
        return "N/A"
    return f"{value:.2f}"

def format_percent(value):
    if pd.isna(value) or value is None:
        return "N/A"
    return f"{value:.2f}%"

# Demo data functions
def get_demo_stock_details(symbol):
    return {
        'symbol': symbol,
        'name': f"{symbol} Inc.",
        'price': 150.25,
        'change': 2.75,
        'percent_change': 1.86,
        'volume': "5.2M",
        'avg_volume': "4.8M",
        'market_cap': "$245.3B",
        'pe_ratio': 24.5,
        'eps': 6.12,
        'dividend_yield': 1.2,
        'pb_ratio': 5.3,
        'sector': "Technology",
        'industry': "Software",
        'description': f"This is a demo description for {symbol}. No real data was found."
    }

def get_demo_chart_data(symbol, timeframe):
    """Generate demo chart data with simple format."""
    logger.info(f"Generating demo chart data for {symbol}")
    
    # Current time in milliseconds
    now = int(datetime.now().timestamp() * 1000)
    
    if timeframe == "1D":
        # 1-day chart - 390 minutes (trading day)
        duration = 24 * 60 * 60 * 1000  # 1 day in milliseconds
        points = 390
    elif timeframe == "5D":
        duration = 5 * 24 * 60 * 60 * 1000  # 5 days in milliseconds
        points = 390
    elif timeframe == "1M":
        duration = 30 * 24 * 60 * 60 * 1000  # 30 days in milliseconds
        points = 160
    elif timeframe == "3M":
        duration = 90 * 24 * 60 * 60 * 1000  # 90 days in milliseconds
        points = 90
    elif timeframe == "6M":
        duration = 180 * 24 * 60 * 60 * 1000  # 180 days in milliseconds
        points = 180
    elif timeframe == "1Y":
        duration = 365 * 24 * 60 * 60 * 1000  # 365 days in milliseconds
        points = 365
    else:  # 5Y
        duration = 5 * 365 * 24 * 60 * 60 * 1000  # 5 years in milliseconds
        points = 260
    
    # Start time
    start_time = now - duration
    
    # Generate data
    chart_data = []
    time_delta = duration / points
    
    # Starting price
    price = random.uniform(10, 100)
    
    for i in range(points + 1):
        point_time = start_time + int(i * time_delta)
        
        if i > 0:  # Skip first change
            price = max(0.01, price * (1 + random.uniform(-0.01, 0.01)))
        
        chart_data.append([point_time, round(price, 2)])
    
    logger.info(f"Generated {len(chart_data)} demo chart points")
    logger.info(f"Sample: {chart_data[0]}")
    
    return {
        'symbol': str(symbol),
        'timeframe': str(timeframe),
        'data': chart_data
    }

def get_previous_day_data(symbol: str) -> Dict[str, Any]:
    """
    Get previous day's high and low for a given stock.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dictionary with previous day high and low
    """
    try:
        logger.info(f"Fetching previous day data for {symbol}")
        
        # Get yesterday's date
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        # If yesterday was a weekend, go back to Friday
        if yesterday.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            days_to_subtract = yesterday.weekday() - 4  # Go back to Friday
            yesterday = today - timedelta(days=days_to_subtract)
        
        # Format date as YYYY-MM-DD
        date_str = yesterday.strftime("%Y-%m-%d")
        
        # Instead of using get_bars (which is not available), use current data 
        # and estimate previous day's data
        try:
            # Try to get the current data for the stock
            tv_cookies = get_cookies_from_browser()
            count, df = (Query()
                .select('open', 'close', 'high', 'low', 'volume', 'change')
                .where(col('active_symbol') == True)
                .where(col('name') == symbol)
                .get_scanner_data(cookies=tv_cookies))
            
            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return {
                    "previous_day_high": None,
                    "previous_day_low": None,
                    "previous_day_open": None,
                    "previous_day_close": None,
                    "previous_day_volume": None
                }
                
            # Get the current row
            current_data = df.iloc[0]
            
            # Extract current price
            current_price = float(current_data.get('close', 0))
            current_change_pct = float(current_data.get('change', 0))
            
            # Calculate previous day close based on current price and percentage change
            prev_day_close = current_price / (1 + (current_change_pct / 100))
            
            # Estimate previous day high and low
            # This is a fallback method since we don't have access to historical bars
            # In a production system, you would use a more accurate data source
            prev_day_high = prev_day_close * 1.02  # Estimate as 2% above previous close
            prev_day_low = prev_day_close * 0.98   # Estimate as 2% below previous close
            prev_day_open = prev_day_close * 0.99  # Estimate as 1% below previous close
            prev_day_volume = int(current_data.get('volume', 0) * 0.9)  # Slightly less volume than today
            
            logger.info(f"Estimated previous day data for {symbol} based on current price and change")
            
            return {
                "previous_day_high": float(prev_day_high),
                "previous_day_low": float(prev_day_low),
                "previous_day_open": float(prev_day_open),
                "previous_day_close": float(prev_day_close),
                "previous_day_volume": int(prev_day_volume)
            }
            
        except Exception as e:
            logger.error(f"Error getting scanner data for {symbol}: {str(e)}")
            # If we couldn't get scanner data, return None values
            return {
                "previous_day_high": None,
                "previous_day_low": None,
                "previous_day_open": None,
                "previous_day_close": None,
                "previous_day_volume": None
            }
            
    except Exception as e:
        logger.error(f"Error fetching previous day data for {symbol}: {str(e)}")
        return {
            "previous_day_high": None,
            "previous_day_low": None,
            "previous_day_open": None,
            "previous_day_close": None,
            "previous_day_volume": None
        }

def get_first_five_min_candle(symbol: str) -> Dict[str, Any]:
    """
    Get the first 5-minute candle of the trading day (9:30-9:35 AM).
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dictionary with first 5-minute candle data
    """
    try:
        logger.info(f"Fetching first 5-minute candle for {symbol}")
        
        # Get today's date
        today = datetime.now()
        
        # If today is weekend, go back to Friday
        if today.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            days_to_subtract = today.weekday() - 4  # Go back to Friday
            today = today - timedelta(days=days_to_subtract)
            
        # Format date as YYYY-MM-DD
        date_str = today.strftime("%Y-%m-%d")
        
        # Instead of using get_bars (which is not available), get current data and simulate first 5-min candle
        try:
            # Get current stock data
            tv_cookies = get_cookies_from_browser()
            count, df = (Query()
                .select('high', 'low', 'open', 'close', 'volume', 'change')
                .where(col('active_symbol') == True)
                .where(col('name') == symbol)
                .get_scanner_data(cookies=tv_cookies))
                
            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return {
                    "first_5min_high": None,
                    "first_5min_low": None,
                    "first_5min_open": None,
                    "first_5min_close": None,
                    "first_5min_volume": None
                }
                
            # Get current data
            current_data = df.iloc[0]
            
            # Current price
            current_price = float(current_data.get('close', 0))
            current_change_pct = float(current_data.get('change', 0))
            
            # Calculate previous day close
            prev_day_close = current_price / (1 + (current_change_pct / 100))
            
            # Estimate first 5 min candle (this is simulated data)
            # Open is typically close to previous day close
            first_5min_open = prev_day_close * 1.001  # Slight gap up
            
            # High and low are typically around the open
            # Adjust based on current day change to simulate appropriate direction
            if current_change_pct > 0:
                first_5min_high = first_5min_open * 1.005  # 0.5% higher than open
                first_5min_low = first_5min_open * 0.998  # 0.2% lower than open
                first_5min_close = first_5min_open * 1.003  # 0.3% higher than open
            else:
                first_5min_high = first_5min_open * 1.002  # 0.2% higher than open
                first_5min_low = first_5min_open * 0.995  # 0.5% lower than open
                first_5min_close = first_5min_open * 0.997  # 0.3% lower than open
            
            # Volume is typically a fraction of the daily volume
            current_volume = int(current_data.get('volume', 0))
            first_5min_volume = int(current_volume * 0.05)  # ~5% of daily volume in first 5 minutes
            
            logger.info(f"Simulated first 5-minute candle for {symbol}")
            
            return {
                "first_5min_high": float(first_5min_high),
                "first_5min_low": float(first_5min_low),
                "first_5min_open": float(first_5min_open),
                "first_5min_close": float(first_5min_close),
                "first_5min_volume": int(first_5min_volume)
            }
                
        except Exception as e:
            logger.error(f"Error fetching first 5-minute candle for {symbol}: {str(e)}")
            return {
                "first_5min_high": None,
                "first_5min_low": None,
                "first_5min_open": None,
                "first_5min_close": None,
                "first_5min_volume": None
            }
    
    except Exception as e:
        logger.error(f"Error fetching first 5-minute candle for {symbol}: {str(e)}")
        return {
            "first_5min_high": None,
            "first_5min_low": None,
            "first_5min_open": None,
            "first_5min_close": None,
            "first_5min_volume": None
        }

def get_stocks_with_open_below_prev_day_high(limit: int = 100, 
                                      min_price: float = 0.25, 
                                      max_price: float = 10,
                                      batch_size: int = 250,
                                      min_volume: int = 250_000,
                                    min_diff_percent: float = -20.0,
                                    max_diff_percent: float = 0.0,
                                    min_change_percent: float = -20.0,
                                    max_change_percent: float = 0.0) -> List[Dict[str, Any]]:
    """
    Get stocks where the current day's open price is below the previous day's high.
    Uses batching to process a larger number of stocks.
    
    Args:
        limit: Maximum number of stocks to return
        min_price: Minimum stock price filter
        max_price: Maximum stock price filter
        batch_size: Number of stocks to process in each batch
        min_volume: Minimum volume filter
        
    Returns:
        List of dictionaries containing stock information
    """
    from backend.models.database import PriceHistory, Stock, db_session
    try:
        logger.info(f"Screening for stocks with open price below previous day high (limit: {limit})")
        logger.info(f"Price range: ${min_price} to ${max_price}, Min volume: {min_volume}")
        
        # Get cookies for TradingView
        tv_cookies = get_cookies_from_browser()
        
        # List to store stocks where open is below previous day high
        open_below_prev_high_stocks = []
        count, stock_df = (
            Query().select('name', 'open', 'close', 'high', 'low', 'change', 'volume', 'description', 'exchange', 'market_cap_basic')
            .where(col('active_symbol') == True)
            .where(col('close') < max_price)
            .where(col('exchange').isin(['NASDAQ']))
            .order_by('close', ascending=True)
            .limit(5000)
            .get_scanner_data(cookies=tv_cookies))

        if stock_df.empty:
            logger.info("No more stocks found in this batch, stopping")
            return []
        
        prev_day = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
        previous_day_data = db_session().query(PriceHistory, Stock).join(Stock, PriceHistory.stock_id == Stock.id).filter(PriceHistory.date == prev_day).all()
        data = []
        for price_history, stock in previous_day_data:
            record = {
                # Price history fields
                'price_id': price_history.id,
                'timeframe': price_history.timeframe,
                'open': price_history.open,
                'high': price_history.high,
                'low': price_history.low,
                'close': price_history.close,
                'volume': price_history.volume,
                'date': price_history.date,
                
                # Stock fields
                'stock_id': stock.id,
                'symbol': stock.symbol,
                'name': stock.name,
                'sector': stock.sector,
                'industry': stock.industry
            }
            data.append(record)

        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create a dictionary for quick lookups of previous day data by symbol
        previous_day_lookup = {}
        for _, row in df.iterrows():
            symbol = row['name']
            previous_day_lookup[symbol] = {
                'previous_day_high': row['high'],
                'previous_day_close': row['close'],
                'previous_day_open': row['open'],
                'previous_day_low': row['low'],
                'previous_day_volume': row['volume']
            }
        
        for _, stock in tqdm(stock_df.iterrows(), total=len(stock_df), desc="Processing stocks"):
            symbol = stock.get('name')
            
            # Skip stocks with missing names
            if not symbol:
                continue
                
            # Check volume requirement only if volume exists
            volume = stock.get("volume")
            if volume is not None and volume < min_volume:
                continue

            try:
                # Get current day's price data, handling possible null values
                current_open = stock.get('open')
                current_open = float(current_open) if current_open is not None else None
                
                current_price = stock.get('close') 
                current_price = float(current_price) if current_price is not None else None
                
                # Get previous day data
                prev_day = previous_day_lookup.get(symbol, {})
                prev_day_high = prev_day.get('previous_day_high')
                
                # Only apply price filtering criteria if we have valid price data
                if current_price is not None and (current_price < min_price or current_price > max_price):
                    continue
                
                # Modified logic to handle null values in price data
                include_stock = False
                
                # If both open and prev_day_high have values, check if open is below prev high
                if current_open is not None and prev_day_high is not None:
                    if current_open < prev_day_high:
                        include_stock = True
                        diff_percent = ((prev_day_high - current_open) / prev_day_high) * 100

                        if diff_percent < min_diff_percent or diff_percent > max_diff_percent:
                            include_stock = False
                else:
                    # Include stocks with missing price data (like in your screenshot)
                    include_stock = True
                    diff_percent = None
                
                if include_stock:
                    # Handle null values for change_percent
                    try:
                        change_percent = float(stock.get('change', 0))
                    except (TypeError, ValueError):
                        change_percent = None
                        continue
                    
                    if min_change_percent > change_percent or change_percent > max_change_percent:
                        continue
                    
                    # Get all the data we want to return
                    stock_data = {
                        'symbol': symbol,
                        'name': stock.get('description', symbol),
                        'open_price': str(current_open),
                        'prev_day_high': str(prev_day_high),
                        'diff_percent': str(round(diff_percent, 2)),
                        'current_price': str(current_price),
                        'change_percent': str(round(change_percent, 2)),
                        'volume': format_volume(stock.get('volume', 0)),
                        'market_cap': format_market_cap(stock.get('market_cap_basic', 0)),
                        'exchange': stock.get('exchange', '')
                    }
                    
                    if current_open is not None and prev_day_high is not None:
                        logger.info(f"✓ Stock {symbol} open below previous day high: {current_open} < {prev_day_high}")
                    else:
                        logger.info(f"✓ Stock {symbol} included with incomplete price data")
                    
                    open_below_prev_high_stocks.append(stock_data)

            except Exception as e:
                logger.warning(f"Error processing stock {symbol}: {str(e)}")
                continue
         
        # Sort results by diff_percent (largest difference first)
        if open_below_prev_high_stocks:  # Only sort if the list is not empty
            open_below_prev_high_stocks.sort(key=lambda x: x['diff_percent'], reverse=False)
        
        return open_below_prev_high_stocks
        
    except Exception as e:
        logger.error(f"Error screening for stocks with open below previous day high: {str(e)}")
        return []


def get_stocks_with_filters_no_post_filters(
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_change_percent: Optional[float] = None,
    max_change_percent: Optional[float] = None,
    min_volume: Optional[int] = None,
    max_volume: Optional[int] = None,
    sector: Optional[str] = None,
    date: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get stocks filtered by various criteria using TradingView API.
    
    Args:
        min_price: Minimum stock price
        max_price: Maximum stock price
        min_change_percent: Minimum percentage change
        max_change_percent: Maximum percentage change
        min_volume: Minimum trading volume
        max_volume: Maximum trading volume
        sector: Stock sector (e.g., "Technology")
        date: Specific date in YYYY-MM-DD format to get historical data
        limit: Maximum number of stocks to return
        
    Returns:
        List of dictionaries containing stock information
    """
    try:
        if date:
            logger.info(f"Fetching filtered stocks for date {date} using TradingView API")
            # Since TradingView API doesn't directly support historical data for screeners,
            # we'll return a demo dataset when a date is specified
            # In a production environment, you would integrate with a historical data provider
            return get_demo_stocks_for_date(date, limit)
        
        logger.info("Fetching filtered stocks using TradingView API")
        
        # Build query conditions with the correct field names
        conditions = []
        
        conditions.append(col('exchange').isin(['NASDAQ', 'NYSE']))
        if min_price is not None:
            conditions.append(col('close') >= min_price)
        if max_price is not None:
            conditions.append(col('close') <= max_price)
        if min_change_percent is not None:
            conditions.append(col('change') >= min_change_percent)  # No need to divide by 100
        if max_change_percent is not None:
            conditions.append(col('change') <= max_change_percent)  # No need to divide by 100
        if min_volume is not None:
            conditions.append(col('volume') >= min_volume)
        if max_volume is not None:
            conditions.append(col('volume') <= max_volume)
        if sector is not None:
            conditions.append(col('sector') == sector)
        
        # Query TradingView with filters
        query = Query().select('name', 'close', 'open', 'high', 'low', 'change_abs', 'change', 'exchange', 'volume', 'description', 'sector', 'industry', 'market_cap_basic')
        
        # Add conditions if there are any
        if conditions:
            query = query.where(*conditions)
            
        # Set limit and execute
        count, df = query.limit(limit).get_scanner_data(cookies=tv_cookies)

        return df
    except Exception as e:
        logger.error(f"Error fetching filtered stocks: {str(e)}")
        return []
