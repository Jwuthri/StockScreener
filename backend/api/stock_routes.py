from fastapi import APIRouter, HTTPException, Query
from backend.services.stock_service import (
    fetch_stock_info, 
    fetch_stock_history, 
    save_stock_to_db, 
    save_price_history,
    search_stocks,
    get_current_price,
    get_top_gainers,
    get_top_losers,
    get_most_active,
    get_yf_top_gainers,
    get_yf_top_losers,
    get_yf_most_active
)
from backend.models.database import Stock
from typing import List, Optional
import logging
from backend.services.polygon_service import get_stocks_with_filters
from backend.services.tradingview_service import (
    get_top_gainers as get_top_gainers_tv,
    get_top_losers as get_top_losers_tv,
    get_most_active as get_most_active_tv,
    get_stocks_with_filters,
    get_stock_details_tv,
    get_stock_chart_data,
    get_previous_day_data,
    get_first_five_min_candle,
    get_stocks_with_consecutive_positive_candles,
    get_stocks_crossing_prev_day_high
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/search")
async def search(query: str = Query(..., min_length=1)):
    """Search for stocks by symbol or name."""
    results = search_stocks(query)
    return {"results": results}

@router.get("/info/{symbol}")
async def get_stock_info(symbol: str):
    """Get basic information about a stock."""
    # Check if stock exists in our database
    try:
        stock = Stock.get(Stock.symbol == symbol.upper())
        return {
            "symbol": stock.symbol,
            "name": stock.name,
            "sector": stock.sector,
            "industry": stock.industry,
            "last_updated": stock.last_updated
        }
    except Stock.DoesNotExist:
        # Fetch from external API
        stock_data = fetch_stock_info(symbol.upper())
        if not stock_data:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
        
        # Save to database
        db_stock = save_stock_to_db(stock_data)
        if not db_stock:
            raise HTTPException(status_code=500, detail="Failed to save stock data")
            
        return stock_data

@router.get("/price/{symbol}")
async def get_stock_price(symbol: str):
    """Get the current price of a stock."""
    price = get_current_price(symbol.upper())
    if price is None:
        raise HTTPException(status_code=404, detail=f"Could not get price for {symbol}")
        
    return {"symbol": symbol.upper(), "price": price}

@router.get("/history/{symbol}")
async def get_stock_history(symbol: str, period: str = "1mo"):
    """Get historical data for a stock."""
    try:
        # Get stock from database
        stock = Stock.get(Stock.symbol == symbol.upper())
    except Stock.DoesNotExist:
        # Fetch stock info first
        stock_data = fetch_stock_info(symbol.upper())
        if not stock_data:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
            
        stock = save_stock_to_db(stock_data)
        if not stock:
            raise HTTPException(status_code=500, detail="Failed to save stock data")
    
    # Fetch history from API
    history_data = fetch_stock_history(symbol.upper(), period)
    if not history_data:
        raise HTTPException(status_code=404, detail=f"No history found for {symbol}")
        
    # Save to database
    save_price_history(stock, history_data)
    
    # Format the response
    formatted_history = []
    for record in history_data:
        formatted_history.append({
            "date": record["Date"].isoformat(),
            "open": record["Open"],
            "high": record["High"],
            "low": record["Low"],
            "close": record["Close"],
            "volume": record["Volume"]
        })
        
    return {"symbol": symbol.upper(), "history": formatted_history}

@router.get("/popular")
async def get_popular_stocks():
    """Get a list of popular stocks based on market cap and trading volume."""
    try:
        # Get stocks with high market cap and volume
        stocks = get_stocks_with_filters(
            min_volume=1000000,  # Min 1M volume
            limit=10
        )
        
        # Format response
        return {
            "popular_stocks": stocks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gainers")
async def get_gainers(limit: int = 10):
    """Get top gaining stocks using TradingView criteria."""
    try:
        gainers = get_top_gainers(limit=limit)
        return {"gainers": gainers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/losers")
async def get_losers(limit: int = 10):
    """Get top losing stocks using TradingView criteria."""
    try:
        losers = get_top_losers(limit=limit)
        return {"losers": losers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/most-active")
async def get_active_stocks(limit: int = 10):
    """Get most active stocks by volume using TradingView criteria."""
    try:
        active = get_most_active(limit=limit)
        return {"most_active": active}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tradingview/filter")
async def filter_stocks(
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_change_percent: Optional[float] = None,
    max_change_percent: Optional[float] = None,
    min_volume: Optional[int] = None,
    max_volume: Optional[int] = None,
    sector: Optional[str] = None,
    date: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100)
):
    """Filter stocks using TradingView API."""
    stocks = get_stocks_with_filters(
        min_price=min_price,
        max_price=max_price,
        min_change_percent=min_change_percent,
        max_change_percent=max_change_percent,
        min_volume=min_volume,
        max_volume=max_volume,
        sector=sector,
        date=date,
        limit=limit
    )
    return {"stocks": stocks}

@router.get("/polygon/filter")
async def filter_stocks_polygon(
    min_price: float = Query(None, description="Minimum stock price"),
    max_price: float = Query(None, description="Maximum stock price"),
    min_change: float = Query(None, description="Minimum percentage change"),
    max_change: float = Query(None, description="Maximum percentage change"),
    min_volume: int = Query(None, description="Minimum trading volume"),
    sector: str = Query(None, description="Filter by sector"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return")
):
    """Filter stocks based on various criteria using Polygon.io API"""
    from backend.services.polygon_service import get_stocks_with_filters
    
    results = get_stocks_with_filters(
        min_price=min_price, 
        max_price=max_price,
        min_change_percent=min_change,
        max_change_percent=max_change,
        min_volume=min_volume,
        sector=sector,
        limit=limit
    )
    
    return {"results": results}

@router.get("/polygon/details/{symbol}")
async def get_polygon_stock_details(symbol: str):
    """Get detailed information about a stock using Polygon.io API"""
    from backend.services.polygon_service import get_ticker_details
    
    details = get_ticker_details(symbol)
    if not details:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} details not found")
    
    return details

@router.get("/debug/tv-fields")
async def debug_tradingview_fields():
    """Debug endpoint to explore TradingView API fields."""
    from backend.services.tradingview_service import explore_available_fields
    
    success = explore_available_fields()
    return {"success": success, "message": "Check server logs for field information"}

@router.get("/debug/cookies")
async def debug_cookies():
    """Debug endpoint to check TradingView cookie extraction."""
    from backend.services.tradingview_service import tv_cookies, explore_available_fields
    
    has_cookies = bool(tv_cookies)
    fields_check = explore_available_fields()
    
    return {
        "has_cookies": has_cookies,
        "cookie_count": len(tv_cookies) if hasattr(tv_cookies, "__len__") else "unknown",
        "fields_check": fields_check,
        "message": "Check server logs for more details"
    }

@router.get("/details/{symbol}")
async def get_stock_details_endpoint(symbol: str):
    """
    Get detailed information for a specific stock
    """
    try:
        stock_data = get_stock_details_tv(symbol)
        return stock_data
    except Exception as e:
        logger.error(f"Error getting stock details for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving stock details: {str(e)}")

@router.get("/chart/{symbol}")
async def get_stock_chart_endpoint(symbol: str, timeframe: str = "1D"):
    """
    Get chart data for a specific stock
    Timeframe options: 1D, 5D, 1M, 3M, 6M, 1Y, 5Y
    """
    try:
        chart_data = get_stock_chart_data(symbol, timeframe)
        return chart_data
    except Exception as e:
        logger.error(f"Error getting chart data for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving chart data: {str(e)}")

@router.get("/previous-day/{symbol}")
async def get_previous_day_endpoint(symbol: str):
    """
    Get previous trading day's high and low for a specific stock
    """
    try:
        data = get_previous_day_data(symbol)
        return data
    except Exception as e:
        logger.error(f"Error getting previous day data for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving previous day data: {str(e)}")

@router.get("/first-candle/{symbol}")
async def get_first_candle_endpoint(symbol: str):
    """
    Get the first 5-minute candle of the trading day (9:30-9:35 AM) for a specific stock
    """
    try:
        data = get_first_five_min_candle(symbol)
        return data
    except Exception as e:
        logger.error(f"Error getting first 5-minute candle for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving first 5-minute candle: {str(e)}")

@router.get("/screener/consecutive-positive")
async def get_consecutive_positive_screener(
    timeframe: str = Query("5m", description="Timeframe for candles (1m, 5m, 15m, 30m, 1h, 4h, 1d)"),
    num_candles: int = Query(3, ge=2, le=10, description="Number of consecutive positive candles required"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of stocks to return")
):
    """
    Screen for stocks with consecutive positive candles
    """
    try:
        stocks = get_stocks_with_consecutive_positive_candles(timeframe, num_candles, limit)
        
        # Extra validation to ensure no None/null values for numeric fields
        for stock in stocks:
            # Log debugging info about data types
            logger.info(f"Stock {stock.get('symbol')} before processing: price={stock.get('price')} ({type(stock.get('price')).__name__}), change_percent={stock.get('change_percent')} ({type(stock.get('change_percent')).__name__})")
            
            # Ensure price is a valid float
            if stock.get('price') is None or not isinstance(stock.get('price'), (int, float)):
                stock['price'] = 0.0
                logger.info(f"Changed null/invalid price to 0.0 for {stock.get('symbol')}")
            else:
                # Make sure it's a simple float, not a numpy float or other object
                try:
                    stock['price'] = float(stock['price'])
                    logger.info(f"Converted price to float: {stock['price']} for {stock.get('symbol')}")
                except (ValueError, TypeError) as e:
                    logger.error(f"Failed to convert price for {stock.get('symbol')}: {e}")
                    stock['price'] = 0.0
                
            # Ensure change_percent is a valid float
            if stock.get('change_percent') is None or not isinstance(stock.get('change_percent'), (int, float)):
                stock['change_percent'] = 0.0
                logger.info(f"Changed null/invalid change_percent to 0.0 for {stock.get('symbol')}")
            else:
                # Make sure it's a simple float, not a numpy float or other object
                try:
                    stock['change_percent'] = float(stock['change_percent'])
                    logger.info(f"Converted change_percent to float: {stock['change_percent']} for {stock.get('symbol')}")
                except (ValueError, TypeError) as e:
                    logger.error(f"Failed to convert change_percent for {stock.get('symbol')}: {e}")
                    stock['change_percent'] = 0.0
            
            # # Debug full serialized version of stock to check for issues
            # import json
            # try:
            #     serialized = json.dumps(stock)
            #     logger.info(f"Serialized stock data for {stock.get('symbol')}: {serialized[:100]}...")
            # except Exception as e:
            #     logger.error(f"Serialization error for {stock.get('symbol')}: {e}")
                
        logger.info(f"Returning {len(stocks)} stocks with consecutive positive candles")
        
        return {
            "stocks": stocks,
            "count": len(stocks),
            "timeframe": timeframe,
            "consecutive_candles": num_candles
        }
    except Exception as e:
        logger.error(f"Error screening for stocks with consecutive positive candles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error screening for stocks: {str(e)}")

@router.get("/screener/crossing-prev-day-high")
async def get_stocks_crossing_prev_day_high_endpoint(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of stocks to return"),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_change_percent: Optional[float] = None,
    max_change_percent: Optional[float] = None,
    min_volume: Optional[int] = None,
    max_volume: Optional[int] = None,
    sector: Optional[str] = None,
    industry: Optional[str] = None,
    exchange: Optional[str] = None,
    date: Optional[str] = None
):
    """
    Get stocks from top gainers that have their current price crossing above the previous day high.
    Includes filtering options similar to the advanced stock filter.
    """
    try:
        # Helper function to sanitize numeric values that might contain commas
        def sanitize_numeric_value(value):
            if isinstance(value, str):
                # Remove commas and other non-numeric chars (except decimal point)
                cleaned_value = ''.join(c for c in value if c.isdigit() or c == '.')
                return float(cleaned_value) if '.' in cleaned_value else int(cleaned_value)
            return value
            
        # First, get the stocks crossing above previous day high
        stocks = get_stocks_crossing_prev_day_high(limit)
        
        # Apply filters if any are provided
        filtered_stocks = []
        for stock in stocks:
            # Skip if price doesn't meet criteria
            try:
                price = sanitize_numeric_value(stock.get('price', 0))
                if min_price is not None and price < min_price:
                    continue
                if max_price is not None and price > max_price:
                    continue
                    
                # Skip if change percent doesn't meet criteria
                change_percent = sanitize_numeric_value(stock.get('change_percent', 0))
                if min_change_percent is not None and change_percent < min_change_percent:
                    continue
                if max_change_percent is not None and change_percent > max_change_percent:
                    continue
                    
                # Skip if volume doesn't meet criteria
                volume = sanitize_numeric_value(stock.get('volume', 0))
                if min_volume is not None and volume < min_volume:
                    continue
                if max_volume is not None and volume > max_volume:
                    continue
                    
                # Skip if sector doesn't match
                if sector is not None and stock.get('sector', '').lower() != sector.lower():
                    continue
                    
                # Skip if industry doesn't match
                if industry is not None and stock.get('industry', '').lower() != industry.lower():
                    continue
                    
                # Skip if exchange doesn't match
                if exchange is not None and stock.get('exchange', '').lower() != exchange.lower():
                    continue
                    
                # If it passes all filters, add to the filtered list
                filtered_stocks.append(stock)
            except (ValueError, TypeError) as e:
                # Log issues with individual stocks but don't fail the entire request
                logger.warning(f"Error processing stock data: {e} - Stock data: {stock}")
                continue
            
        return {
            "stocks": filtered_stocks,
            "count": len(filtered_stocks),
            "description": "Stocks crossing above previous day high with applied filters"
        }
    except Exception as e:
        logger.error(f"Error getting stocks crossing above previous day high: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching stocks: {str(e)}") 