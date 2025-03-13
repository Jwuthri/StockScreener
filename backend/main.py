import os
import sys

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Add the parent directory to the path if running from backend directory
if os.path.basename(os.getcwd()) == "backend":
    sys.path.append(os.path.dirname(os.getcwd()))

import asyncio
import json
import logging
import time
from datetime import datetime

import numpy as np
from api.stock_routes import router as stock_router
from fastapi.responses import JSONResponse, ORJSONResponse

from backend.api.alert_routes import router as alert_router
from backend.api.auth_routes import router as auth_router
from backend.models.database import db_session, initialize_db
from backend.services.alert_service import alert_manager
from backend.services.tradingview_service import (
    check_stocks_cross_above_prev_day_high,
    get_stocks_crossing_prev_day_high,
    get_stocks_with_open_below_prev_day_high,
)

# Configure logging
# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Silence all WebSocket-related logs
logging.getLogger("uvicorn.protocols.websockets").setLevel(logging.ERROR)
logging.getLogger("uvicorn.protocols.websockets.websockets_impl").setLevel(logging.ERROR)
logging.getLogger("uvicorn.protocols.http").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.ERROR)
logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# Create logger
logger = logging.getLogger(__name__)


# Custom JSON encoder to handle NumPy and other special values
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, "isoformat"):  # Handle date/datetime objects
            return obj.isoformat()
        return super().default(obj)


# Function to safely convert objects to JSON-compatible types
def safe_json_serialize(obj):
    if isinstance(obj, dict):
        return {k: safe_json_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [safe_json_serialize(i) for i in obj]
    elif isinstance(obj, tuple):
        return [safe_json_serialize(i) for i in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, "isoformat"):
        return obj.isoformat()
    # Handle special float values
    elif isinstance(obj, float):
        if np.isnan(obj):
            return None  # Convert NaN to null
        elif np.isinf(obj):
            if obj > 0:
                return float(1.7976931348623157e308)  # Max JSON float
            else:
                return float(-1.7976931348623157e308)  # Min JSON float
    else:
        return obj


# Configure FastAPI to use custom JSON encoder
class CustomORJSONResponse(ORJSONResponse):
    media_type = "application/json"

    def render(self, content):
        # Convert all content to safe JSON types first
        safe_content = safe_json_serialize(content)
        return super().render(safe_content)


app = FastAPI(
    title="Stock Screener API",
    description="API for stock screening and real-time alerts",
    version="1.0.0",
    default_response_class=CustomORJSONResponse,
)

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections = []

# Store the last set of stocks crossing above previous day high
previous_crossing_stocks = set()

# Global variable to store stocks with open below prev day high
open_below_prev_high_stocks = []

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(stock_router, prefix="/api/stocks", tags=["stocks"])
app.include_router(alert_router, prefix="/api/alerts", tags=["alerts"])


@app.on_event("startup")
async def startup_event():
    """Initialize the database and start background tasks."""
    try:
        logger.info("Starting up Stock Screener API")
        initialize_db()

        # Start periodic tasks
        # asyncio.create_task(periodic_stock_screener())
        # asyncio.create_task(monitor_open_below_prev_high_stocks())
        # TODO JOBS

        logger.info("Background tasks scheduled")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks and close db connections."""
    logger.info("Shutting down application")
    alert_manager.stop_monitoring()

    # Close any outstanding SQLAlchemy sessions
    db_session.remove()


@app.get("/")
async def root():
    response_data = {"message": "Welcome to Stock Screener API"}
    return JSONResponse(content=safe_json_serialize(response_data))


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    response_data = {"status": "ok", "timestamp": datetime.now().isoformat()}
    return JSONResponse(content=safe_json_serialize(response_data))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Global exception: {exc}", exc_info=True)
    # Use safe serialization for the error response
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."},
        # Use our custom JSON encoder for all responses
        media_type="application/json",
        background=None,
        headers=None,
    )


# Add a middleware to handle NaN/Infinity values in all responses
@app.middleware("http")
async def handle_json_serialization(request: Request, call_next):
    response = await call_next(request)

    # If this is a JSON response, we need to ensure all values are serializable
    if response.headers.get("content-type") == "application/json":
        # Read the response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        if body:
            # Parse the JSON, apply our safe conversion, and re-serialize
            try:
                data = json.loads(body)
                safe_data = safe_json_serialize(data)
                # Create a new response with the safely serialized data
                return JSONResponse(
                    content=safe_data,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )
            except:
                # If there's an error in the process, return the original response
                pass

    return response


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)


async def periodic_stock_screener():
    """Background task to check for stocks crossing above previous day high every 5 minutes."""
    global previous_crossing_stocks

    while True:
        try:
            # Reduced log verbosity

            # Get current stocks crossing above previous day high
            current_stocks = get_stocks_crossing_prev_day_high(limit=50)

            # Create a set of current stock symbols
            current_symbols = {stock["symbol"] for stock in current_stocks}

            # Find new stocks that weren't in the previous set
            new_stocks = []
            if previous_crossing_stocks:
                new_stocks = [stock for stock in current_stocks if stock["symbol"] not in previous_crossing_stocks]
            else:
                # If this is the first run, consider all stocks as new
                new_stocks = current_stocks

            if new_stocks:
                logger.info(f"Found {len(new_stocks)} new stocks crossing above previous day high")

                # Convert NumPy values to Python native types
                safe_new_stocks = safe_json_serialize(new_stocks)

                # Send alerts to all connected clients
                alert_data = {
                    "type": "new_crossing_stocks",
                    "data": safe_new_stocks,
                    "timestamp": datetime.now().isoformat(),
                }

                # Send to all connected WebSockets
                for connection in active_connections:
                    try:
                        await connection.send_text(json.dumps(alert_data, cls=CustomJSONEncoder))
                    except Exception as e:
                        logger.error(f"Error sending to WebSocket: {e}")

            # Update previous stocks set
            previous_crossing_stocks = current_symbols

        except Exception as e:
            logger.error(f"Error in periodic stock screener: {e}")

        # Run every 5 minutes
        await asyncio.sleep(30000)


async def monitor_open_below_prev_high_stocks():
    """
    Background task to:
    1. Fetch stocks with open below previous day high
    2. Monitor these stocks every 5 seconds
    3. Send notifications when they cross above the previous day high
    """
    global open_below_prev_high_stocks

    # First-time fetch delay
    await asyncio.sleep(5)

    # For testing purposes - hard-coded stock list if nothing is returned from the screener
    test_stocks = [
        "AAPL",
        "MSFT",
        "AMZN",
        "GOOGL",
        "META",
        "TSLA",
        "NFLX",
        "AMD",
        "NVDA",
        "KLXE",
        "DOMO",
        "AVGX",
        "AGH",
        "MSC",
    ]

    while True:
        try:
            # Fetch stocks with open below previous day high if list is empty or every 5 minutes
            if not open_below_prev_high_stocks or time.time() % 300 < 5:
                logger.info("Fetching stocks with open below previous day high")
                stocks = get_stocks_with_open_below_prev_day_high(
                    limit=500,
                    min_price=0.25,
                    max_price=100.0,
                    min_volume=100_000,
                    min_diff_percent=1,
                    min_change_percent=1,
                )

                open_below_prev_high_stocks = [stock["symbol"] for stock in stocks]
                # If no stocks found, use test stocks for demonstration purposes
                if not open_below_prev_high_stocks:
                    logger.warning("No stocks found with open below prev day high. Using test stocks.")
                    open_below_prev_high_stocks = test_stocks

                logger.info(f"Found {len(open_below_prev_high_stocks)} stocks with open below previous day high")

            # Check if any stocks crossed above previous day high
            if open_below_prev_high_stocks:
                logger.info(f"Checking {len(open_below_prev_high_stocks)} stocks for crossing above previous day high")
                crossed_stocks = check_stocks_cross_above_prev_day_high(open_below_prev_high_stocks, test_mode=False)

                if crossed_stocks:
                    logger.info(f"Found {len(crossed_stocks)} stocks that crossed above previous day high")

                    # Remove these stocks from the watch list
                    for stock in crossed_stocks:
                        if stock["symbol"] in open_below_prev_high_stocks:
                            open_below_prev_high_stocks.remove(stock["symbol"])

                    # Convert data to safe JSON
                    safe_crossed_stocks = safe_json_serialize(crossed_stocks)

                    # Send alerts to all connected clients
                    alert_data = {
                        "type": "crossed_above_prev_day_high",
                        "data": safe_crossed_stocks,
                        "timestamp": datetime.now().isoformat(),
                    }

                    logger.info(f"Sending alert data to {len(active_connections)} WebSocket connections")

                    # Send to all connected WebSockets
                    for connection in active_connections:
                        try:
                            await connection.send_text(json.dumps(alert_data, cls=CustomJSONEncoder))
                            logger.info("Alert sent successfully via WebSocket")
                        except Exception as e:
                            logger.error(f"Error sending to WebSocket: {e}")
                else:
                    logger.info("No stocks found crossing above previous day high in this check")

        except Exception as e:
            logger.error(f"Error in monitoring open below prev high stocks: {e}")

        # Check every 5 seconds
        await asyncio.sleep(5)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
