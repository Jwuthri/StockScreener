import logging
from webull import webull
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize Webull client
wb = webull()

def get_webull_screener(
    min_price=None,
    max_price=None,
    min_change_percent=None,
    max_change_percent=None,
    min_volume=None,
    region="us",
    limit=50
):
    """
    Screen stocks using Webull's screener
    """
    try:
        logger.info("Fetching stocks from Webull screener")
        
        # Build screen parameters
        screen_params = {
            "regionId": 6 if region == "us" else 0,  # 6 for US
            "pageIndex": 0,
            "pageSize": 100  # Fetch more than we need
        }
        
        # Add price filters
        if min_price is not None:
            screen_params["price_lte"] = float(max_price) if max_price else 1000000
            screen_params["price_gte"] = float(min_price)
            
        # Add volume filter
        if min_volume is not None:
            screen_params["volume_gte"] = float(min_volume)
            
        # Get screener results
        screener_data = wb.get_screener(**screen_params)
        
        if not screener_data:
            logger.error("No data returned from Webull screener")
            return []
            
        filtered_results = []
        
        # Process the results
        for stock in screener_data:
            # Extract basic info
            symbol = stock.get('symbol')
            name = stock.get('name')
            price = stock.get('price')
            change_percent = stock.get('changeRatio', 0) * 100
            volume = stock.get('volume')
            
            # Apply additional filters
            if (min_change_percent is None or change_percent >= min_change_percent) and \
               (max_change_percent is None or change_percent <= max_change_percent):
                
                filtered_results.append({
                    'symbol': symbol,
                    'name': name,
                    'price': price,
                    'percent_change': round(change_percent, 2),
                    'volume': volume,
                    'sector': stock.get('sectorName', '')
                })
        
        # Limit results to requested count
        return filtered_results[:limit]
        
    except Exception as e:
        logger.error(f"Error with Webull screener: {str(e)}")
        return [] 