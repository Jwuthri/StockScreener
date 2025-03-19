#!/usr/bin/env python
"""
Daily job to fetch stocks from TradingView and store them in the database.
This script should be scheduled to run once per day, preferably after market close.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import func

from backend.models.database import PriceHistory, Stock, db_session
from backend.services.tradingview_service import get_stocks_with_filters_no_post_filters

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(Path(__file__).parent / "daily_stock_update.log"), logging.StreamHandler()],
)

logger = logging.getLogger("daily_stock_update")


def fetch_stock_list(min_price=0.25, min_volume=100000, limit=30_000, date: str = None):
    """
    Fetch a list of active stocks from TradingView that meet certain criteria.

    Args:
        min_price: Minimum price filter
        min_volume: Minimum volume filter
        limit: Maximum number of stocks to return

    Returns:
        List of stock data dictionaries
    """
    logger.info(f"Fetching stock list from TradingView (min_price={min_price}, min_volume={min_volume}, limit={limit})")

    try:
        # Fetch stocks from TradingView using filters
        stocks = get_stocks_with_filters_no_post_filters(min_price=0, min_volume=0, limit=limit, date=date)

        logger.info(f"Successfully fetched {len(stocks)} stocks from TradingView")
        return stocks
    except Exception as e:
        logger.error(f"Error fetching stocks from TradingView: {str(e)}")
        return []


def save_stocks_to_db(stocks):
    """
    Save or update stocks in the database.

    Args:
        stocks: List of stock data dictionaries

    Returns:
        Number of stocks added/updated
    """
    logger.info(f"Saving {len(stocks)} stocks to database")

    db = db_session()
    dt = datetime.now().strftime("%Y/%m/%d")
    # dt = "2025/03/18"
    try:
        count = 0
        for _, stock_data in tqdm(stocks.iterrows(), desc="Saving stocks to database"):
            try:
                # Extract relevant data
                symbol = stock_data.get("ticker", "").replace(".", "-")  # Handle symbols with dots
                name = stock_data.get("name", symbol)
                sector = stock_data.get("sector", None)
                industry = stock_data.get("industry", None)
                exchange = stock_data.get("exchange", None)
                description = stock_data.get("description", None)

                # Price data
                price = stock_data.get("close", 0.0)
                open_price = stock_data.get("open", 0.0)
                high = stock_data.get("high", 0.0)
                low = stock_data.get("low", 0.0)
                volume = int(stock_data.get("volume", 0))

                if not symbol:
                    logger.warning(f"Skipping stock with no symbol: {stock_data}")
                    continue

                # Check if stock exists
                stock = db.query(Stock).filter(Stock.symbol == symbol).first()
                if not stock:
                    # Create new stock
                    stock = Stock(
                        symbol=symbol,
                        name=name,
                        description=description,
                        sector=sector,
                        industry=industry,
                        exchange=exchange,
                        created_at=datetime.now(),
                    )
                    db.add(stock)
                    db.flush()  # Flush to get the ID
                    logger.info(f"Added new stock: {symbol}")

                else:
                    # Update existing stock
                    stock.name = name if name else stock.name
                    stock.sector = sector if sector else stock.sector
                    stock.industry = industry if industry else stock.industry
                    stock.exchange = exchange if exchange else stock.exchange
                    stock.description = description if description else stock.description
                    logger.info(f"Updated existing stock: {symbol}")

                # Add price history entry
                today = datetime.now().date()

                # Check if we already have a price entry for today
                existing_price = (
                    db.query(PriceHistory)
                    .filter(PriceHistory.stock_id == stock.id, func.date(PriceHistory.date) == today)
                    .first()
                )

                safe_volume = min(volume, 2147483647) if volume > 2147483647 else volume
                if not existing_price:
                    price_history = PriceHistory(
                        stock_id=stock.id,
                        timeframe="1D",
                        open=open_price,
                        high=high,
                        low=low,
                        close=price,
                        volume=safe_volume,
                        date=dt,
                    )
                    db.add(price_history)
                    logger.info(f"Added price history for {symbol}")
                else:
                    # Update existing price entry
                    existing_price.open = open_price
                    existing_price.high = high
                    existing_price.low = low
                    existing_price.close = price
                    existing_price.volume = safe_volume
                    logger.info(f"Updated price history for {symbol}")

                count += 1
            except Exception as e:
                logger.error(f"Error processing stock {stock_data.get('ticker', 'unknown')}: {str(e)}")
                continue

        db.commit()
        logger.info(f"Successfully saved {count} stocks to database")
        return count
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        return 0
    finally:
        db.close()


def save_previous_day_stocks_to_db(stocks, date):
    """
    Save or update stocks in the database.

    Args:
        stocks: List of stock data dictionaries

    Returns:
        Number of stocks added/updated
    """
    logger.info(f"Saving {len(stocks)} stocks to database")

    db = db_session()
    try:
        count = 0
        for _, stock_data in tqdm(stocks.iterrows(), desc="Saving stocks to database"):
            try:
                # Extract relevant data
                symbol = stock_data.get("ticker", "").split(".")[0].split("-")[0]

                # Price data
                price = stock_data.get("close", 0.0)
                open_price = stock_data.get("open", 0.0)
                high = stock_data.get("high", 0.0)
                low = stock_data.get("low", 0.0)
                volume = int(stock_data.get("volume", 0))

                if not symbol:
                    logger.warning(f"Skipping stock with no symbol: {stock_data}")
                    continue

                # Check if stock exists
                stock = db.query(Stock).filter(Stock.name == symbol).first()
                if not stock:
                    continue

                # Check if we already have a price entry for today
                existing_price = (
                    db.query(PriceHistory)
                    .filter(PriceHistory.stock_id == stock.id, func.date(PriceHistory.date) == date)
                    .first()
                )
                date = date.replace("-", "/")
                safe_volume = min(volume, 2147483647) if volume > 2147483647 else volume
                if not existing_price:
                    price_history = PriceHistory(
                        stock_id=stock.id,
                        timeframe="1D",
                        open=open_price,
                        high=high,
                        low=low,
                        close=price,
                        volume=safe_volume,
                        date=date,
                    )
                    db.add(price_history)
                    logger.info(f"Added price history for {symbol}")
                else:
                    # Update existing price entry
                    existing_price.open = open_price
                    existing_price.high = high
                    existing_price.low = low
                    existing_price.close = price
                    existing_price.volume = safe_volume
                    existing_price.date = date
                    logger.info(f"Updated price history for {symbol}")

                count += 1
            except Exception as e:
                logger.error(f"Error processing stock {stock_data.get('ticker', 'unknown')}: {str(e)}")
                continue

        db.commit()
        logger.info(f"Successfully saved {count} stocks to database")
        return count
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        return 0
    finally:
        db.close()


def run_daily_update(date: str = None):
    """Main function to run the daily stock update."""
    logger.info("Starting daily stock update")
    try:
        # Fetch stocks from TradingView
        stocks = fetch_stock_list(date=date)
        if not len(stocks):
            logger.error("No stocks fetched from TradingView, aborting update")
            return False

        # Save stocks to database
        if date:
            saved_count = save_previous_day_stocks_to_db(stocks, date)
        else:
            saved_count = save_stocks_to_db(stocks)

        logger.info(f"Daily stock update completed successfully. Processed {saved_count} stocks.")
        return True
    except Exception as e:
        logger.error(f"Error in daily stock update: {str(e)}")
        return False


if __name__ == "__main__":
    run_daily_update(date=None)
