import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Set

import websockets
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class AlpacaWebSocketService:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, paper: bool = True):
        if not hasattr(self, "initialized"):
            self.api_key = os.environ.get("ALPACA_PAPER_API_KEY" if paper else "ALPACA_API_KEY")
            self.api_secret = os.environ.get("ALPACA_PAPER_API_SECRET" if paper else "ALPACA_API_SECRET")
            # Use the market data WebSocket endpoint instead of trading endpoint
            self.endpoint = "wss://stream.data.alpaca.markets/v2/iex"
            self.websocket: Optional[websockets.WebSocketClientProtocol] = None
            self.subscribed_symbols: Set[str] = set()
            self.price_callbacks: Dict[str, List[callable]] = {}
            self.authenticated = False
            self.connected = False
            self._stop = False
            self._listener_task = None
            self.initialized = True

    async def connect(self):
        """Connect to Alpaca WebSocket and authenticate"""
        async with self._lock:
            if self.connected and self.authenticated:
                return

            try:
                if self.websocket:
                    await self.websocket.close()

                self.websocket = await websockets.connect(self.endpoint)
                self.connected = True
                logger.info("Connected to Alpaca Market Data WebSocket")

                # Authenticate with the new format
                auth_data = {"action": "auth", "key": self.api_key, "secret": self.api_secret}
                await self.websocket.send(json.dumps(auth_data))
                response = await self.websocket.recv()
                auth_response = json.loads(response)

                if isinstance(auth_response, list) and auth_response[0]["msg"] == "connected":
                    self.authenticated = True
                    logger.info("Successfully authenticated with Alpaca Market Data WebSocket")

                    # Start listening for messages if not already running
                    if not self._listener_task or self._listener_task.done():
                        self._listener_task = asyncio.create_task(self._listen_for_messages())
                else:
                    logger.error("Failed to authenticate with Alpaca Market Data WebSocket")
                    await self.disconnect()
                    raise Exception("Authentication failed")

            except Exception as e:
                logger.error(f"Error connecting to Alpaca WebSocket: {str(e)}")
                self.connected = False
                self.authenticated = False
                raise

    async def disconnect(self):
        """Disconnect from WebSocket"""
        async with self._lock:
            self._stop = True
            if self._listener_task:
                self._listener_task.cancel()
                try:
                    await self._listener_task
                except asyncio.CancelledError:
                    pass
            if self.websocket:
                await self.websocket.close()
            self.connected = False
            self.authenticated = False
            self.subscribed_symbols.clear()
            self.price_callbacks.clear()
            logger.info("Disconnected from Alpaca WebSocket")

    async def subscribe_to_trades(self, symbols: List[str], callback: callable):
        """Subscribe to trade updates for specific symbols"""
        async with self._lock:
            if not self.connected or not self.authenticated:
                await self.connect()

            # Add symbols to tracking
            for symbol in symbols:
                if symbol not in self.price_callbacks:
                    self.price_callbacks[symbol] = []
                self.price_callbacks[symbol].append(callback)
                self.subscribed_symbols.add(symbol)

            # Subscribe to trades stream for the symbols
            subscribe_message = {
                "action": "subscribe",
                "trades": symbols,  # Subscribe to trade data
                "quotes": symbols,  # Also subscribe to quotes for more frequent updates
            }
            await self.websocket.send(json.dumps(subscribe_message))
            logger.info(f"Subscribed to market data for symbols: {symbols}")

    async def unsubscribe_from_trades(self, symbols: List[str]):
        """Unsubscribe from trade updates for specific symbols"""
        async with self._lock:
            if not self.authenticated:
                return

            for symbol in symbols:
                if symbol in self.subscribed_symbols:
                    self.subscribed_symbols.remove(symbol)
                    self.price_callbacks.pop(symbol, None)

            if symbols:
                # Unsubscribe from the symbols
                unsubscribe_message = {
                    "action": "unsubscribe",
                    "trades": symbols,
                    "quotes": symbols,
                }
                await self.websocket.send(json.dumps(unsubscribe_message))
                logger.info(f"Unsubscribed from market data for symbols: {symbols}")

    async def _listen_for_messages(self):
        """Listen for incoming WebSocket messages"""
        try:
            while not self._stop and self.websocket:
                try:
                    message = await self.websocket.recv()
                    data = json.loads(message)

                    if isinstance(data, list):
                        for msg in data:
                            if msg.get("T") in ["t", "q"]:  # Trade or quote message
                                await self._handle_market_data(msg)

                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket connection closed")
                    self.connected = False
                    await self._reconnect()
                    break
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {str(e)}")
                    continue

        except asyncio.CancelledError:
            logger.info("WebSocket listener cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in WebSocket message listener: {str(e)}")
            self.connected = False

    async def _handle_market_data(self, data):
        """Handle incoming market data messages"""
        try:
            msg_type = data.get("T")
            symbol = data.get("S")

            if symbol in self.subscribed_symbols:
                price = None
                if msg_type == "t":  # Trade
                    price = float(data["p"])
                elif msg_type == "q":  # Quote
                    # Use the midpoint of bid and ask for quotes
                    price = (float(data["bp"]) + float(data["ap"])) / 2

                if price is not None:
                    price_data = {
                        "symbol": symbol,
                        "price": price,
                        "timestamp": data["t"],
                        "event": "trade" if msg_type == "t" else "quote",
                    }

                    # Call all registered callbacks for this symbol
                    for callback in self.price_callbacks.get(symbol, []):
                        try:
                            await callback(price_data)
                        except Exception as e:
                            logger.error(f"Error in price callback for {symbol}: {str(e)}")

        except Exception as e:
            logger.error(f"Error handling market data: {str(e)}")

    async def _reconnect(self):
        """Attempt to reconnect to WebSocket"""
        max_retries = 5
        retry_delay = 5  # seconds

        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to reconnect (attempt {attempt + 1}/{max_retries})")
                await self.connect()

                # Resubscribe to all symbols
                if self.subscribed_symbols:
                    symbols_list = list(self.subscribed_symbols)
                    callbacks = set()
                    for symbol_callbacks in self.price_callbacks.values():
                        callbacks.update(symbol_callbacks)

                    for callback in callbacks:
                        await self.subscribe_to_trades(symbols_list, callback)

                logger.info("Successfully reconnected")
                return
            except Exception as e:
                logger.error(f"Reconnection attempt {attempt + 1} failed: {str(e)}")
                await asyncio.sleep(retry_delay)

        logger.error("Failed to reconnect after maximum retries")
        raise Exception("Failed to reconnect to WebSocket")
