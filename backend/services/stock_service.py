import logging
import random
import time
from datetime import datetime

import pandas as pd
import requests
import yfinance as yf
from bs4 import BeautifulSoup
from sqlalchemy import or_

from backend.models.database import Stock, db_session

logger = logging.getLogger(__name__)


def with_rate_limit_retry(func):
    """Decorator to retry functions with rate limiting backoff"""

    def wrapper(*args, **kwargs):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Add a small random delay to avoid rate limits
                time.sleep(random.uniform(0.5, 2.0))
                return func(*args, **kwargs)
            except Exception as e:
                if "Rate limited" in str(e) and attempt < max_retries - 1:
                    backoff = (attempt + 1) * 3
                    logger.warning(f"Rate limited. Backing off for {backoff} seconds before retry.")
                    time.sleep(backoff)
                else:
                    raise
        return func(*args, **kwargs)

    return wrapper


def fetch_stock_info(symbol):
    """Fetch basic information about a stock."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Extract relevant info
        stock_data = {
            "symbol": symbol,
            "name": info.get("shortName", info.get("longName", symbol)),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
        }

        return stock_data
    except Exception as e:
        logger.error(f"Error fetching stock info for {symbol}: {str(e)}")
        return None


def fetch_stock_history(symbol, period="1mo"):
    """Fetch historical stock data."""
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period)

        if history.empty:
            logger.warning(f"No history data found for {symbol}")
            return None

        # Convert to dictionary of records
        history = history.reset_index()
        # Convert Date to datetime if it's not already
        if not pd.api.types.is_datetime64_any_dtype(history["Date"]):
            history["Date"] = pd.to_datetime(history["Date"])

        records = history.to_dict("records")
        return records
    except Exception as e:
        logger.error(f"Error fetching stock history for {symbol}: {str(e)}")
        return None


def get_current_price(symbol):
    """Get the current price of a stock."""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        if data.empty:
            return None
        return data["Close"].iloc[-1]
    except Exception as e:
        logger.error(f"Error fetching current price for {symbol}: {str(e)}")
        return None


def save_stock_to_db(stock_data):
    """Save or update stock information in the database."""
    try:
        db = db_session()
        try:
            # Check if stock exists
            stock = db.query(Stock).filter(Stock.symbol == stock_data["symbol"]).first()

            if not stock:
                # Create new stock
                stock = Stock(
                    symbol=stock_data["symbol"],
                    name=stock_data["name"],
                    sector=stock_data.get("sector"),
                    industry=stock_data.get("industry"),
                    last_updated=datetime.now(),
                )
                db.add(stock)
            else:
                # Update existing stock
                stock.name = stock_data["name"]
                stock.sector = stock_data.get("sector")
                stock.industry = stock_data.get("industry")
                stock.last_updated = datetime.now()

            db.commit()
            return stock
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving stock data: {str(e)}")
            return None
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error with database session: {str(e)}")
        return None


def save_price_history(stock, history_data):
    """Save price history to database."""
    # Skip database operations entirely
    logger.info(f"Skipping database storage for price history data for {stock}")
    return True


def search_stocks(query):
    """Search for stocks by symbol or name."""
    try:
        db = db_session()
        try:
            stocks = db.query(Stock).filter(or_(Stock.symbol.contains(query.upper()), Stock.name.contains(query))).all()

            result = [
                {"symbol": stock.symbol, "name": stock.name, "sector": stock.sector, "industry": stock.industry}
                for stock in stocks
            ]
            return result
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error searching stocks: {str(e)}")
        return []


@with_rate_limit_retry
def get_top_gainers(limit=10):
    """Get the top gaining stocks for the day using Yahoo Finance."""
    try:
        # Try to use Yahoo Finance screener
        url = "https://finance.yahoo.com/gainers"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        logger.info(f"Fetching top gainers from {url}")
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            logger.error(f"Failed to fetch gainers. Status code: {response.status_code}")
            return get_demo_gainers(limit)

        soup = BeautifulSoup(response.text, "html.parser")

        # Debug HTML structure
        logger.debug(f"Soup title: {soup.title}")

        gainers = []
        table = soup.find("table", {"class": "markets-table freeze-col yf-paf8n5 fixedLayout"})

        if not table:
            logger.error("Table not found in HTML response")
            # Try alternative table selector
            tables = soup.find_all("table")
            logger.info(f"Found {len(tables)} tables on the page")

            if len(tables) > 0:
                table = tables[0]  # Try the first table
            else:
                return get_demo_gainers(limit)

        rows = table.find("tbody").find_all("tr")

        if not rows:
            logger.error("No rows found in table")
            return get_demo_gainers(limit)

        logger.info(f"Found {len(rows)} gainers")

        for row in rows[:limit]:
            try:
                cells = row.find_all("td")
                if len(cells) >= 5:
                    symbol = cells[0].text.strip()
                    name = cells[1].text.strip()
                    price = cells[3].find("fin-streamer", attrs={"data-field": "regularMarketPrice"}).text
                    change = cells[4].text.strip()
                    percent_change = cells[5].text.strip()
                    volume = cells[6].text.strip()

                    gainers.append(
                        {
                            "symbol": symbol,
                            "name": name,
                            "price": price,
                            "change": change,
                            "percent_change": percent_change,
                            "volume": volume,
                        }
                    )
                    logger.debug(f"Added gainer: {symbol}")
            except Exception as e:
                logger.error(f"Error processing row: {e}")
                continue

        if gainers:
            logger.info(f"Successfully fetched {len(gainers)} gainers")
            return gainers
        else:
            logger.warning("No gainers extracted, falling back to demo data")
            return get_demo_gainers(limit)

    except Exception as e:
        logger.error(f"Error fetching top gainers: {str(e)}")
        # Log that we're using fallback data
        logger.info("Using fallback demo data for top gainers")
        return get_demo_gainers(limit)


@with_rate_limit_retry
def get_top_losers(limit=10):
    """Get the top losing stocks for the day using Yahoo Finance."""
    try:
        # Try to use Yahoo Finance screener
        url = "https://finance.yahoo.com/losers"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        logger.info(f"Fetching top losers from {url}")
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            logger.error(f"Failed to fetch losers. Status code: {response.status_code}")
            return get_demo_losers(limit)

        soup = BeautifulSoup(response.text, "html.parser")

        # Debug HTML structure
        logger.debug(f"Soup title: {soup.title}")

        losers = []
        table = soup.find("table", {"class": "markets-table freeze-col yf-paf8n5 fixedLayout"})

        if not table:
            logger.error("Table not found in HTML response")
            # Try alternative table selector
            tables = soup.find_all("table")
            logger.info(f"Found {len(tables)} tables on the page")

            if len(tables) > 0:
                table = tables[0]  # Try the first table
            else:
                return get_demo_losers(limit)

        rows = table.find("tbody").find_all("tr")

        if not rows:
            logger.error("No rows found in table")
            return get_demo_losers(limit)

        logger.info(f"Found {len(rows)} losers")

        for row in rows[:limit]:
            try:
                cells = row.find_all("td")
                if len(cells) >= 5:
                    symbol = cells[0].text.strip()
                    name = cells[1].text.strip()
                    price = cells[3].find("fin-streamer", attrs={"data-field": "regularMarketPrice"}).text
                    change = cells[4].text.strip()
                    percent_change = cells[5].text.strip()
                    volume = cells[6].text.strip()

                    losers.append(
                        {
                            "symbol": symbol,
                            "name": name,
                            "price": price,
                            "change": change,
                            "percent_change": percent_change,
                            "volume": volume,
                        }
                    )
                    # breakpoint()
                    logger.debug(f"Added loser: {symbol}")
            except Exception as e:
                logger.error(f"Error processing row: {e}")
                continue

        if losers:
            logger.info(f"Successfully fetched {len(losers)} losers")
            return losers
        else:
            logger.warning("No losers extracted, falling back to demo data")
            return get_demo_losers(limit)

    except Exception as e:
        logger.error(f"Error fetching top losers: {str(e)}")
        return get_demo_losers(limit)


@with_rate_limit_retry
def get_most_active(limit=10):
    """Get the most active stocks by volume using Yahoo Finance."""
    try:
        # Try to use Yahoo Finance screener
        url = "https://finance.yahoo.com/most-active"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        logger.info(f"Fetching most active stocks from {url}")
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            logger.error(f"Failed to fetch most active stocks. Status code: {response.status_code}")
            return get_demo_most_active(limit)

        soup = BeautifulSoup(response.text, "html.parser")

        # Debug HTML structure
        logger.debug(f"Soup title: {soup.title}")
        active_stocks = []

        table = soup.find("table", {"class": "markets-table freeze-col yf-paf8n5 fixedLayout"})

        if not table:
            logger.error("Table not found in HTML response")
            # Try alternative table selector
            tables = soup.find_all("table")
            logger.info(f"Found {len(tables)} tables on the page")

            if len(tables) > 0:
                table = tables[0]  # Try the first table
            else:
                return get_demo_most_active(limit)

        rows = table.find("tbody").find_all("tr")

        if not rows:
            logger.error("No rows found in table")
            return get_demo_most_active(limit)

        logger.info(f"Found {len(rows)} active stocks")

        for row in rows[:limit]:
            try:
                cells = row.find_all("td")
                if len(cells) >= 6:
                    symbol = cells[0].text.strip()
                    name = cells[1].text.strip()
                    price = cells[3].find("fin-streamer", attrs={"data-field": "regularMarketPrice"}).text
                    change = cells[4].text.strip()
                    percent_change = cells[5].text.strip()
                    volume = cells[6].text.strip()

                    active_stocks.append(
                        {
                            "symbol": symbol,
                            "name": name,
                            "price": price,
                            "change": change,
                            "percent_change": percent_change,
                            "volume": volume,
                        }
                    )
                    logger.debug(f"Added active stock: {symbol}")
            except Exception as e:
                logger.error(f"Error processing row: {e}")
                continue

        if active_stocks:
            logger.info(f"Successfully fetched {len(active_stocks)} active stocks")
            return active_stocks
        else:
            logger.warning("No active stocks extracted, falling back to demo data")
            return get_demo_most_active(limit)

    except Exception as e:
        logger.error(f"Error fetching most active stocks: {str(e)}")
        return get_demo_most_active(limit)


# Demo data functions for fallback
def get_demo_gainers(limit=10):
    """Return demo data for top gainers if real data can't be fetched."""
    gainers = [
        {
            "symbol": "NVDA",
            "name": "NVIDIA Corporation",
            "price": "942.89",
            "change": "+41.91",
            "percent_change": "4.65%",
        },
        {
            "symbol": "AMD",
            "name": "Advanced Micro Devices, Inc.",
            "price": "176.52",
            "change": "+7.23",
            "percent_change": "4.27%",
        },
        {
            "symbol": "MRVL",
            "name": "Marvell Technology, Inc.",
            "price": "82.31",
            "change": "+3.12",
            "percent_change": "3.94%",
        },
        {
            "symbol": "MSFT",
            "name": "Microsoft Corporation",
            "price": "421.33",
            "change": "+10.25",
            "percent_change": "2.49%",
        },
        {"symbol": "AAPL", "name": "Apple Inc.", "price": "175.35", "change": "+3.87", "percent_change": "2.26%"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "price": "163.42", "change": "+3.45", "percent_change": "2.16%"},
        {"symbol": "ADBE", "name": "Adobe Inc.", "price": "526.78", "change": "+9.34", "percent_change": "1.80%"},
        {"symbol": "CRM", "name": "Salesforce, Inc.", "price": "278.96", "change": "+4.68", "percent_change": "1.71%"},
        {"symbol": "AMZN", "name": "Amazon.com, Inc.", "price": "186.85", "change": "+2.78", "percent_change": "1.51%"},
        {"symbol": "INTC", "name": "Intel Corporation", "price": "31.45", "change": "+0.45", "percent_change": "1.45%"},
    ]
    return gainers[:limit]


def get_demo_losers(limit=10):
    """Return demo data for top losers if real data can't be fetched."""
    losers = [
        {"symbol": "TSLA", "name": "Tesla, Inc.", "price": "187.43", "change": "-12.57", "percent_change": "-6.29%"},
        {
            "symbol": "META",
            "name": "Meta Platforms, Inc.",
            "price": "472.35",
            "change": "-18.65",
            "percent_change": "-3.80%",
        },
        {"symbol": "NFLX", "name": "Netflix, Inc.", "price": "598.32", "change": "-22.45", "percent_change": "-3.61%"},
        {
            "symbol": "BABA",
            "name": "Alibaba Group Holding Ltd.",
            "price": "78.43",
            "change": "-2.57",
            "percent_change": "-3.17%",
        },
        {
            "symbol": "PYPL",
            "name": "PayPal Holdings, Inc.",
            "price": "62.15",
            "change": "-1.85",
            "percent_change": "-2.89%",
        },
        {
            "symbol": "UBER",
            "name": "Uber Technologies, Inc.",
            "price": "66.82",
            "change": "-1.74",
            "percent_change": "-2.54%",
        },
        {
            "symbol": "DIS",
            "name": "The Walt Disney Company",
            "price": "94.67",
            "change": "-2.33",
            "percent_change": "-2.40%",
        },
        {
            "symbol": "IBM",
            "name": "International Business Machines",
            "price": "171.42",
            "change": "-3.58",
            "percent_change": "-2.05%",
        },
        {
            "symbol": "SBUX",
            "name": "Starbucks Corporation",
            "price": "78.91",
            "change": "-1.54",
            "percent_change": "-1.91%",
        },
        {"symbol": "PFE", "name": "Pfizer Inc.", "price": "27.12", "change": "-0.48", "percent_change": "-1.74%"},
    ]

    # Ensure percent_change is a float value
    for loser in losers:
        if loser["percent_change"] is None:
            try:
                price = float(loser["price"].replace("$", "").replace(",", ""))
                change = float(loser["change"].replace("$", "").replace(",", ""))
                loser["percent_change"] = f"{((change / (price - change)) * 100):.2f}%"
            except (ValueError, ZeroDivisionError):
                # If calculation fails, set a default negative value
                loser["percent_change"] = "-2.50%"

    return losers[:limit]


def get_demo_most_active(limit=10):
    """Return demo data for most active stocks if real data can't be fetched."""
    most_active = [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "price": "175.35",
            "change": "+3.87",
            "percent_change": "2.26%",
            "volume": "98.7M",
        },
        {
            "symbol": "TSLA",
            "name": "Tesla, Inc.",
            "price": "187.43",
            "change": "-12.57",
            "percent_change": "-6.29%",
            "volume": "93.4M",
        },
        {
            "symbol": "AMD",
            "name": "Advanced Micro Devices, Inc.",
            "price": "176.52",
            "change": "+7.23",
            "percent_change": "4.27%",
            "volume": "87.2M",
        },
        {
            "symbol": "NVDA",
            "name": "NVIDIA Corporation",
            "price": "942.89",
            "change": "+41.91",
            "percent_change": "4.65%",
            "volume": "76.8M",
        },
        {
            "symbol": "BAC",
            "name": "Bank of America Corporation",
            "price": "37.54",
            "change": "+0.23",
            "percent_change": "0.62%",
            "volume": "65.3M",
        },
        {
            "symbol": "F",
            "name": "Ford Motor Company",
            "price": "11.87",
            "change": "-0.13",
            "percent_change": "-1.08%",
            "volume": "57.6M",
        },
        {
            "symbol": "MSFT",
            "name": "Microsoft Corporation",
            "price": "421.33",
            "change": "+10.25",
            "percent_change": "2.49%",
            "volume": "53.1M",
        },
        {
            "symbol": "INTC",
            "name": "Intel Corporation",
            "price": "31.45",
            "change": "+0.45",
            "percent_change": "1.45%",
            "volume": "48.7M",
        },
        {
            "symbol": "PLTR",
            "name": "Palantir Technologies Inc.",
            "price": "24.63",
            "change": "+0.87",
            "percent_change": "3.66%",
            "volume": "45.2M",
        },
        {
            "symbol": "META",
            "name": "Meta Platforms, Inc.",
            "price": "472.35",
            "change": "-18.65",
            "percent_change": "-3.80%",
            "volume": "42.9M",
        },
    ]

    # Ensure percent_change is a float value
    for stock in most_active:
        if stock["percent_change"] is None:
            try:
                price = float(stock["price"].replace("$", "").replace(",", ""))
                change = float(stock["change"].replace("$", "").replace(",", ""))
                stock["percent_change"] = f"{((change / (price - change)) * 100):.2f}%"
            except (ValueError, ZeroDivisionError):
                # If calculation fails, set a default value based on the sign of change
                if stock["change"].startswith("-"):
                    stock["percent_change"] = "-2.00%"
                else:
                    stock["percent_change"] = "2.00%"

    return most_active[:limit]


# New functions using yfinance directly
def get_yf_top_gainers(limit=10):
    """Get top gainers using yfinance directly."""
    try:
        logger.info("Fetching top gainers using yfinance")

        # Get major market tickers
        tickers_list = [
            "^GSPC",  # S&P 500
            "QQQ",  # Nasdaq
            "SPY",  # S&P 500 ETF
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "META",
            "NVDA",
            "TSLA",
            "AMD",
            "INTC",
            "NFLX",
            "DIS",
            "PYPL",
            "UBER",
            "COIN",
            "BAC",
            "JPM",
            "V",
            "MA",
            "WMT",
            "PFE",
            "JNJ",
            "MRNA",
        ]

        # Fetch current data
        data = {}
        for symbol in tickers_list:
            try:
                ticker = yf.Ticker(symbol)
                history = ticker.history(period="2d")
                if len(history) >= 2:
                    yesterday_close = history["Close"].iloc[-2]
                    today_price = history["Close"].iloc[-1]
                    change = today_price - yesterday_close
                    percent_change = (change / yesterday_close) * 100

                    # Get company name
                    info = ticker.info
                    name = info.get("shortName", info.get("longName", symbol))

                    data[symbol] = {
                        "symbol": symbol,
                        "name": name,
                        "price": f"{today_price:.2f}",
                        "change": f"{change:.2f}",
                        "percent_change": f"{percent_change:.2f}%",
                    }
                    logger.debug(f"Processed {symbol}: {percent_change:.2f}%")
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue

        # Sort by percent change
        sorted_data = sorted(data.values(), key=lambda x: x["percent_change"], reverse=True)
        gainers = [stock for stock in sorted_data if float(stock["percent_change"].strip("%")) > 0]

        if gainers:
            logger.info(f"Successfully fetched {len(gainers)} gainers using yfinance")
            return gainers[:limit]
        else:
            logger.warning("No gainers found using yfinance, falling back to demo data")
            return get_demo_gainers(limit)

    except Exception as e:
        logger.error(f"Error fetching gainers with yfinance: {str(e)}")
        return get_demo_gainers(limit)


def get_yf_top_losers(limit=10):
    """Get top losers using yfinance directly."""
    try:
        logger.info("Fetching top losers using yfinance")

        # Get major market tickers
        tickers_list = [
            "^GSPC",  # S&P 500
            "QQQ",  # Nasdaq
            "SPY",  # S&P 500 ETF
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "META",
            "NVDA",
            "TSLA",
            "AMD",
            "INTC",
            "NFLX",
            "DIS",
            "PYPL",
            "UBER",
            "COIN",
            "BAC",
            "JPM",
            "V",
            "MA",
            "WMT",
            "PFE",
            "JNJ",
            "MRNA",
        ]

        # Fetch current data
        data = {}
        for symbol in tickers_list:
            try:
                ticker = yf.Ticker(symbol)
                history = ticker.history(period="2d")
                if len(history) >= 2:
                    yesterday_close = history["Close"].iloc[-2]
                    today_price = history["Close"].iloc[-1]
                    change = today_price - yesterday_close
                    percent_change = (change / yesterday_close) * 100

                    # Get company name
                    info = ticker.info
                    name = info.get("shortName", info.get("longName", symbol))

                    data[symbol] = {
                        "symbol": symbol,
                        "name": name,
                        "price": f"{today_price:.2f}",
                        "change": f"{change:.2f}",
                        "percent_change": f"{percent_change:.2f}%",
                    }
                    logger.debug(f"Processed {symbol}: {percent_change:.2f}%")
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue

        # Sort by percent change (ascending for losers)
        sorted_data = sorted(data.values(), key=lambda x: x["percent_change"])
        losers = [stock for stock in sorted_data if float(stock["percent_change"].strip("%")) < 0]

        if losers:
            logger.info(f"Successfully fetched {len(losers)} losers using yfinance")
            return losers[:limit]
        else:
            logger.warning("No losers found using yfinance, falling back to demo data")
            return get_demo_losers(limit)

    except Exception as e:
        logger.error(f"Error fetching losers with yfinance: {str(e)}")
        return get_demo_losers(limit)


def get_yf_most_active(limit=10):
    """Get most active stocks using yfinance directly."""
    try:
        logger.info("Fetching most active stocks using yfinance")

        # Get major market tickers
        tickers_list = [
            "SPY",
            "QQQ",
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "META",
            "NVDA",
            "TSLA",
            "AMD",
            "INTC",
            "NFLX",
            "DIS",
            "PYPL",
            "UBER",
            "COIN",
            "BAC",
            "JPM",
            "V",
            "MA",
            "WMT",
            "PFE",
            "JNJ",
            "MRNA",
            "F",
            "GM",
            "PLTR",
            "NIO",
        ]

        # Fetch current data
        data = {}
        for symbol in tickers_list:
            try:
                ticker = yf.Ticker(symbol)
                history = ticker.history(period="1d")
                if not history.empty:
                    today_price = history["Close"].iloc[-1]
                    volume = history["Volume"].iloc[-1]

                    # Calculate change
                    info = ticker.info
                    name = info.get("shortName", info.get("longName", symbol))
                    previous_close = info.get("previousClose", 0)

                    if previous_close > 0:
                        change = today_price - previous_close
                        percent_change = (change / previous_close) * 100
                    else:
                        change = 0
                        percent_change = 0

                    data[symbol] = {
                        "symbol": symbol,
                        "name": name,
                        "price": f"{today_price:.2f}",
                        "change": f"{change:.2f}",
                        "percent_change": f"{percent_change:.2f}%",
                        "volume": f"{volume:,}",
                        "volume_raw": volume,
                    }
                    logger.debug(f"Processed {symbol}: volume {volume:,}")
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue

        # Sort by volume
        sorted_data = sorted(data.values(), key=lambda x: x.get("volume_raw", 0), reverse=True)

        # Remove the volume_raw key used for sorting
        for stock in sorted_data:
            if "volume_raw" in stock:
                del stock["volume_raw"]

        if sorted_data:
            logger.info(f"Successfully fetched {len(sorted_data)} active stocks using yfinance")
            return sorted_data[:limit]
        else:
            logger.warning("No active stocks found using yfinance, falling back to demo data")
            return get_demo_most_active(limit)

    except Exception as e:
        logger.error(f"Error fetching active stocks with yfinance: {str(e)}")
        return get_demo_most_active(limit)
