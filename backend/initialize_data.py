import logging
import sys
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from backend.models.database import Alert, Stock, db_session, initialize_db
from backend.services.stock_service import fetch_stock_history, fetch_stock_info, save_price_history, save_stock_to_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def initialize_sample_data():
    """Initialize the database with sample stocks and alerts."""
    # Initialize the database
    initialize_db()
    logger.info("Database initialized")

    # Sample stocks to add
    sample_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"]

    for symbol in sample_symbols:
        logger.info(f"Fetching data for {symbol}...")

        # Fetch stock info
        stock_data = fetch_stock_info(symbol)
        if not stock_data:
            logger.warning(f"Could not fetch info for {symbol}, skipping")
            continue

        # Save to database
        stock = save_stock_to_db(stock_data)
        if not stock:
            logger.warning(f"Failed to save {symbol} to database, skipping")
            continue

        logger.info(f"Successfully added {symbol} to database")

        # Fetch and save price history
        history = fetch_stock_history(symbol, period="1mo")
        if history:
            save_price_history(stock, history)
            logger.info(f"Saved price history for {symbol}")
        else:
            logger.warning(f"Could not fetch history for {symbol}")

    # Add sample alerts
    sample_alerts = [
        # {
        #     "stock_symbol": "AAPL",
        #     "user_email": "user@example.com",
        #     "alert_type": "price_above",
        #     "threshold_value": 200.0
        # },
        # {
        #     "stock_symbol": "TSLA",
        #     "user_email": "user@example.com",
        #     "alert_type": "price_below",
        #     "threshold_value": 150.0
        # }
    ]

    db = db_session()
    try:
        for alert_data in sample_alerts:
            try:
                stock = db.query(Stock).filter(Stock.symbol == alert_data["stock_symbol"]).first()
                if not stock:
                    logger.error(f"Stock {alert_data['stock_symbol']} not found")
                    continue

                alert = Alert(
                    stock_id=stock.id,
                    user_email=alert_data["user_email"],
                    alert_type=alert_data["alert_type"],
                    threshold_value=alert_data["threshold_value"],
                    is_active=True,
                )

                db.add(alert)
                logger.info(f"Added alert for {alert_data['stock_symbol']}")
            except Exception as e:
                logger.error(f"Error adding alert: {str(e)}")

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error committing alerts: {str(e)}")
    finally:
        db.close()

    logger.info("Sample data initialization complete")


if __name__ == "__main__":
    initialize_sample_data()
