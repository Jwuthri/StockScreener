import requests
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Get API key from environment variables
POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY")
BASE_URL = "https://api.polygon.io"

def get_stocks_with_filters(
    min_price=None, 
    max_price=None, 
    min_change_percent=None,
    max_change_percent=None,
    min_volume=None,
    sector=None,
    limit=50
):
    """
    Filter stocks using Polygon.io API
    """
    if not POLYGON_API_KEY:
        logger.error("Polygon API key is not configured")
        return []
        
    try:
        logger.info(f"Fetching filtered stocks from Polygon.io")
        
        # First get today's ticker data using Snapshot API
        snapshot_url = f"{BASE_URL}/v2/snapshot/locale/us/markets/stocks/tickers"
        snapshot_params = {
            "apiKey": POLYGON_API_KEY
        }
        
        snapshot_response = requests.get(snapshot_url, params=snapshot_params)
        snapshot_response.raise_for_status()
        
        snapshot_data = snapshot_response.json()
        
        if 'tickers' not in snapshot_data:
            logger.error(f"Invalid response from Polygon API: {snapshot_data}")
            return []
            
        # Process all tickers and apply filters
        filtered_stocks = []
        
        for ticker in snapshot_data.get('tickers', []):
            symbol = ticker.get('ticker')
            day_data = ticker.get('day', {})
            last_quote = ticker.get('lastQuote', {})
            
            # Get price from last quote if available, otherwise from day data
            price = last_quote.get('p') or day_data.get('c')
            prev_close = day_data.get('o')  # Previous close price
            volume = day_data.get('v')      # Volume
            
            # Calculate percentage change
            if price and prev_close and prev_close > 0:
                change_percent = ((price - prev_close) / prev_close) * 100
            else:
                change_percent = 0
            
            # Apply our filters
            if (min_price is None or price >= min_price) and \
               (max_price is None or price <= max_price) and \
               (min_change_percent is None or change_percent >= min_change_percent) and \
               (max_change_percent is None or change_percent <= max_change_percent) and \
               (min_volume is None or volume >= min_volume):
                
                # Get additional ticker details
                details_url = f"{BASE_URL}/v3/reference/tickers/{symbol}"
                details_params = {
                    "apiKey": POLYGON_API_KEY
                }
                
                try:
                    details_response = requests.get(details_url, params=details_params)
                    details_response.raise_for_status()
                    details_data = details_response.json().get('results', {})
                    
                    ticker_sector = details_data.get('sic_description')
                    ticker_name = details_data.get('name')
                    
                    # Apply sector filter if provided
                    if sector and ticker_sector and sector.lower() not in ticker_sector.lower():
                        continue
                    
                    filtered_stocks.append({
                        'symbol': symbol,
                        'name': ticker_name or symbol,
                        'price': price,
                        'percent_change': round(change_percent, 2),
                        'volume': volume,
                        'sector': ticker_sector or 'Unknown'
                    })
                    
                    # Stop once we reach the limit
                    if len(filtered_stocks) >= limit:
                        break
                        
                except Exception as e:
                    logger.warning(f"Couldn't get details for {symbol}: {str(e)}")
                    continue
        
        return filtered_stocks
        
    except Exception as e:
        logger.error(f"Error filtering stocks with Polygon.io: {str(e)}")
        return []

def get_ticker_details(symbol):
    """
    Get detailed information about a specific ticker
    """
    if not POLYGON_API_KEY:
        logger.error("Polygon API key is not configured")
        return None
    
    try:
        # Get ticker details
        details_url = f"{BASE_URL}/v3/reference/tickers/{symbol}"
        details_params = {
            "apiKey": POLYGON_API_KEY
        }
        
        details_response = requests.get(details_url, params=details_params)
        details_response.raise_for_status()
        details_data = details_response.json().get('results', {})
        
        # Get latest price data
        quote_url = f"{BASE_URL}/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
        quote_params = {
            "apiKey": POLYGON_API_KEY
        }
        
        quote_response = requests.get(quote_url, params=quote_params)
        quote_response.raise_for_status()
        quote_data = quote_response.json().get('ticker', {})
        
        day_data = quote_data.get('day', {})
        
        return {
            'symbol': symbol,
            'name': details_data.get('name'),
            'description': details_data.get('description'),
            'sector': details_data.get('sic_description'),
            'exchange': details_data.get('primary_exchange'),
            'market_cap': details_data.get('market_cap'),
            'price': day_data.get('c'),
            'change': day_data.get('c') - day_data.get('o') if day_data.get('c') and day_data.get('o') else 0,
            'percent_change': ((day_data.get('c') - day_data.get('o')) / day_data.get('o') * 100) if day_data.get('c') and day_data.get('o') and day_data.get('o') > 0 else 0,
            'volume': day_data.get('v'),
            'open': day_data.get('o'),
            'high': day_data.get('h'),
            'low': day_data.get('l'),
            'close': day_data.get('c')
        }
        
    except Exception as e:
        logger.error(f"Error getting details for {symbol}: {str(e)}")
        return None

def get_top_gainers_polygon(limit=10):
    """Get top gaining stocks using Polygon.io API"""
    try:
        logger.info("Fetching top gainers using Polygon.io")
        
        # Get snapshot data for all tickers
        snapshot_url = f"{BASE_URL}/v2/snapshot/locale/us/markets/stocks/tickers"
        snapshot_params = {
            "apiKey": POLYGON_API_KEY
        }
        
        snapshot_response = requests.get(snapshot_url, params=snapshot_params)
        snapshot_response.raise_for_status()
        
        snapshot_data = snapshot_response.json()
        
        if 'tickers' not in snapshot_data:
            logger.error(f"Invalid response from Polygon API: {snapshot_data}")
            return []
        
        # Process tickers to find gainers
        gainers = []
        
        for ticker in snapshot_data.get('tickers', []):
            symbol = ticker.get('ticker')
            day_data = ticker.get('day', {})
            
            price = day_data.get('c')  # current price
            prev_close = day_data.get('o')  # previous close
            volume = day_data.get('v')  # volume
            
            # Calculate percentage change
            if price and prev_close and prev_close > 0:
                change_percent = ((price - prev_close) / prev_close) * 100
                change = price - prev_close
                
                # Only include if it's a gainer
                if change_percent > 0:
                    gainers.append({
                        'symbol': symbol,
                        'name': symbol,  # We'll try to get names for top gainers
                        'price': str(price),
                        'change': str(change),
                        'percent_change': change_percent
                    })
        
        # Sort by percentage change (descending)
        gainers = sorted(gainers, key=lambda x: x.get('percent_change', 0), reverse=True)
        
        # Limit the results
        gainers = gainers[:limit]
        
        # Try to get company names for the top gainers
        for gainer in gainers:
            try:
                details_url = f"{BASE_URL}/v3/reference/tickers/{gainer['symbol']}"
                details_params = {
                    "apiKey": POLYGON_API_KEY
                }
                
                details_response = requests.get(details_url, params=details_params)
                details_response.raise_for_status()
                details_data = details_response.json().get('results', {})
                
                gainer['name'] = details_data.get('name', gainer['symbol'])
            except Exception as e:
                logger.warning(f"Couldn't get name for {gainer['symbol']}: {str(e)}")
        
        logger.info(f"Successfully fetched {len(gainers)} gainers using Polygon.io")
        return gainers
        
    except Exception as e:
        logger.error(f"Error fetching top gainers using Polygon.io: {str(e)}")
        return []

def get_top_losers_polygon(limit=10):
    """Get top losing stocks using Polygon.io API"""
    try:
        logger.info("Fetching top losers using Polygon.io")
        
        # Get snapshot data for all tickers
        snapshot_url = f"{BASE_URL}/v2/snapshot/locale/us/markets/stocks/tickers"
        snapshot_params = {
            "apiKey": POLYGON_API_KEY
        }
        
        snapshot_response = requests.get(snapshot_url, params=snapshot_params)
        snapshot_response.raise_for_status()
        
        snapshot_data = snapshot_response.json()
        
        if 'tickers' not in snapshot_data:
            logger.error(f"Invalid response from Polygon API: {snapshot_data}")
            return []
        
        # Process tickers to find losers
        losers = []
        
        for ticker in snapshot_data.get('tickers', []):
            symbol = ticker.get('ticker')
            day_data = ticker.get('day', {})
            
            price = day_data.get('c')  # current price
            prev_close = day_data.get('o')  # previous close
            volume = day_data.get('v')  # volume
            
            # Calculate percentage change
            if price and prev_close and prev_close > 0:
                change_percent = ((price - prev_close) / prev_close) * 100
                change = price - prev_close
                
                # Only include if it's a loser
                if change_percent < 0:
                    losers.append({
                        'symbol': symbol,
                        'name': symbol,  # We'll try to get names for top losers
                        'price': str(price),
                        'change': str(change),
                        'percent_change': change_percent
                    })
        
        # Sort by percentage change (ascending)
        losers = sorted(losers, key=lambda x: x.get('percent_change', 0))
        
        # Limit the results
        losers = losers[:limit]
        
        # Try to get company names for the top losers
        for loser in losers:
            try:
                details_url = f"{BASE_URL}/v3/reference/tickers/{loser['symbol']}"
                details_params = {
                    "apiKey": POLYGON_API_KEY
                }
                
                details_response = requests.get(details_url, params=details_params)
                details_response.raise_for_status()
                details_data = details_response.json().get('results', {})
                
                loser['name'] = details_data.get('name', loser['symbol'])
            except Exception as e:
                logger.warning(f"Couldn't get name for {loser['symbol']}: {str(e)}")
        
        logger.info(f"Successfully fetched {len(losers)} losers using Polygon.io")
        return losers
        
    except Exception as e:
        logger.error(f"Error fetching top losers using Polygon.io: {str(e)}")
        return []

def get_most_active_polygon(limit=10):
    """Get most active stocks by volume using Polygon.io API"""
    try:
        logger.info("Fetching most active stocks using Polygon.io")
        
        # Get snapshot data for all tickers
        snapshot_url = f"{BASE_URL}/v2/snapshot/locale/us/markets/stocks/tickers"
        snapshot_params = {
            "apiKey": POLYGON_API_KEY
        }
        
        snapshot_response = requests.get(snapshot_url, params=snapshot_params)
        snapshot_response.raise_for_status()
        
        snapshot_data = snapshot_response.json()
        
        if 'tickers' not in snapshot_data:
            logger.error(f"Invalid response from Polygon API: {snapshot_data}")
            return []
        
        # Process tickers to find most active
        active_stocks = []
        
        for ticker in snapshot_data.get('tickers', []):
            symbol = ticker.get('ticker')
            day_data = ticker.get('day', {})
            
            price = day_data.get('c')  # current price
            prev_close = day_data.get('o')  # previous close
            volume = day_data.get('v')  # volume
            
            if price and volume:
                # Calculate percentage change
                change_percent = 0
                change = 0
                if prev_close and prev_close > 0:
                    change_percent = ((price - prev_close) / prev_close) * 100
                    change = price - prev_close
                
                active_stocks.append({
                    'symbol': symbol,
                    'name': symbol,  # We'll try to get names
                    'price': str(price),
                    'change': str(change),
                    'percent_change': change_percent,
                    'volume': volume
                })
        
        # Sort by volume (descending)
        active_stocks = sorted(active_stocks, key=lambda x: x.get('volume', 0), reverse=True)
        
        # Limit the results
        active_stocks = active_stocks[:limit]
        
        # Try to get company names for the most active stocks
        for stock in active_stocks:
            try:
                details_url = f"{BASE_URL}/v3/reference/tickers/{stock['symbol']}"
                details_params = {
                    "apiKey": POLYGON_API_KEY
                }
                
                details_response = requests.get(details_url, params=details_params)
                details_response.raise_for_status()
                details_data = details_response.json().get('results', {})
                
                stock['name'] = details_data.get('name', stock['symbol'])
                # Format volume to match the yfinance format
                stock['volume'] = f"{int(stock['volume']):,}"
            except Exception as e:
                logger.warning(f"Couldn't get name for {stock['symbol']}: {str(e)}")
        
        logger.info(f"Successfully fetched {len(active_stocks)} active stocks using Polygon.io")
        return active_stocks
        
    except Exception as e:
        logger.error(f"Error fetching most active stocks using Polygon.io: {str(e)}")
        return [] 