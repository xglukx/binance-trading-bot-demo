import json
import time
import hmac
import hashlib
import logging
import threading
from datetime import datetime
from urllib.parse import urlencode
import websocket
import ujson
import ssl
from queue import Queue, Empty

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("DemoWebSocket")

class ExchangeWebSocketClient:
    """
    Demo WebSocket client for cryptocurrency exchanges.
    This is for demonstration purposes only and should not be used for actual trading.
    """
    
    # Demo WebSocket endpoints
    WS_API_URL = "wss://demo-api.example.com/ws/v1"  # Demo trading API
    WS_MARKET_URL = "wss://demo-stream.example.com/ws"  # Demo market data
    TESTNET_WS_API_URL = "wss://testnet-api.example.com/ws/v1"
    TESTNET_WS_MARKET_URL = "wss://testnet-stream.example.com/ws"
    
    def __init__(self, api_key=None, api_secret=None, use_testnet=False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.use_testnet = use_testnet
        
        # Select appropriate endpoints based on testnet preference
        self.ws_api_url = self.TESTNET_WS_API_URL if use_testnet else self.WS_API_URL
        self.ws_market_url = self.TESTNET_WS_MARKET_URL if use_testnet else self.WS_MARKET_URL
        
        # Initialize WebSocket connections
        self.api_ws = None
        self.market_ws = None
        
        # Message handling
        self.message_queue = Queue()
        self.subscriptions = {}
        self.callbacks = {}
        self.request_id = 1
        self.pending_requests = {}
        
        # Connection status
        self.is_api_connected = False
        self.is_market_connected = False
        
        # Heartbeat and connection management
        self.heartbeat_interval = 30  # seconds
        self.reconnect_delay = 5  # initial delay in seconds
        self.max_reconnect_delay = 300  # max 5 minutes
        
        # Initialize threads
        self.api_thread = None
        self.market_thread = None
        self.process_thread = None
        self.heartbeat_thread = None
        
    def generate_signature(self, params):
        """Generate HMAC signature for authenticated requests."""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def get_request_id(self):
        """Get unique request ID for tracking responses."""
        req_id = self.request_id
        self.request_id += 1
        return req_id
    
    def connect(self):
        """Establish connections to both API and market WebSockets."""
        # Start API WebSocket connection
        self.api_thread = threading.Thread(target=self._connect_api_websocket)
        self.api_thread.daemon = True
        self.api_thread.start()
        
        # Start Market WebSocket connection
        self.market_thread = threading.Thread(target=self._connect_market_websocket)
        self.market_thread.daemon = True
        self.market_thread.start()
        
        # Start message processing thread
        self.process_thread = threading.Thread(target=self._process_messages)
        self.process_thread.daemon = True
        self.process_thread.start()
        
        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(target=self._send_heartbeats)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        
        # Wait for connections to establish
        timeout = 10
        start_time = time.time()
        while (not self.is_api_connected or not self.is_market_connected) and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        if not self.is_api_connected or not self.is_market_connected:
            logger.warning("WebSocket connections not established within timeout")
        else:
            logger.info("Successfully connected to WebSocket endpoints")
            
        return self.is_api_connected and self.is_market_connected
        
    def _connect_api_websocket(self):
        """Connect to the WebSocket API for trading operations."""
        try:
            def on_open(ws):
                logger.info("API WebSocket connection established")
                self.is_api_connected = True
            
            def on_message(ws, message):
                logger.debug(f"API WebSocket message received: {message}")
                try:
                    data = ujson.loads(message)
                    self.message_queue.put(("api", data))
                except Exception as e:
                    logger.error(f"Error parsing API WebSocket message: {e}")
            
            def on_error(ws, error):
                logger.error(f"API WebSocket error: {error}")
                self.is_api_connected = False
            
            def on_close(ws, close_status_code, close_msg):
                logger.warning(f"API WebSocket connection closed: {close_msg} (code: {close_status_code})")
                self.is_api_connected = False
                # Reconnect with exponential backoff
                time.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
                threading.Thread(target=self._connect_api_websocket).start()
            
            # For demo purposes, don't actually connect to a real WebSocket
            # In a real implementation, this would connect to a real WebSocket
            logger.info("Demo mode: Simulating WebSocket API connection")
            self.is_api_connected = True
            
        except Exception as e:
            logger.error(f"Error in API WebSocket connection: {e}")
            self.is_api_connected = False
            
    def _connect_market_websocket(self):
        """Connect to the Market Data WebSocket for price updates."""
        try:
            def on_open(ws):
                logger.info("Market WebSocket connection established")
                self.is_market_connected = True
                # Resubscribe to all active streams
                self._resubscribe()
            
            def on_message(ws, message):
                logger.debug(f"Market WebSocket message received: {message}")
                try:
                    data = ujson.loads(message)
                    self.message_queue.put(("market", data))
                except Exception as e:
                    logger.error(f"Error parsing Market WebSocket message: {e}")
            
            def on_error(ws, error):
                logger.error(f"Market WebSocket error: {error}")
                self.is_market_connected = False
            
            def on_close(ws, close_status_code, close_msg):
                logger.warning(f"Market WebSocket connection closed: {close_msg} (code: {close_status_code})")
                self.is_market_connected = False
                # Reconnect with exponential backoff
                time.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
                threading.Thread(target=self._connect_market_websocket).start()
            
            # For demo purposes, don't actually connect to a real WebSocket
            # In a real implementation, this would connect to a real WebSocket
            logger.info("Demo mode: Simulating WebSocket market data connection")
            self.is_market_connected = True
            
        except Exception as e:
            logger.error(f"Error in Market WebSocket connection: {e}")
            self.is_market_connected = False
            
    def _process_messages(self):
        """Process messages from the WebSocket connections."""
        while True:
            try:
                message_type, data = self.message_queue.get(timeout=1)
                
                # Process API messages
                if message_type == "api":
                    if "id" in data and data["id"] in self.pending_requests:
                        request_info = self.pending_requests[data["id"]]
                        callback = request_info.get("callback")
                        if callback:
                            callback(data)
                        del self.pending_requests[data["id"]]
                
                # Process market data messages
                elif message_type == "market":
                    stream = data.get("stream")
                    if stream and stream in self.callbacks:
                        for callback in self.callbacks[stream]:
                            try:
                                callback(data["data"])
                            except Exception as e:
                                logger.error(f"Error in callback for stream {stream}: {e}")
                
                self.message_queue.task_done()
            except Empty:
                pass
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                
    def _send_heartbeats(self):
        """Send periodic heartbeats to keep connections alive."""
        while True:
            try:
                if self.is_api_connected:
                    self.ping_api()
                if self.is_market_connected:
                    self.ping_market()
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
                
    def ping_api(self):
        """Send ping to API WebSocket."""
        if self.api_ws and self.is_api_connected:
            try:
                ping_msg = json.dumps({"ping": int(time.time() * 1000)})
                # In demo mode, don't actually send anything
                logger.debug("Demo: Would send API ping")
            except Exception as e:
                logger.error(f"Error sending API ping: {e}")
                
    def ping_market(self):
        """Send ping to Market WebSocket."""
        if self.market_ws and self.is_market_connected:
            try:
                ping_msg = json.dumps({"ping": int(time.time() * 1000)})
                # In demo mode, don't actually send anything
                logger.debug("Demo: Would send Market ping")
            except Exception as e:
                logger.error(f"Error sending Market ping: {e}")
    
    def _resubscribe(self):
        """Resubscribe to all active streams after reconnection."""
        if self.subscriptions and self.is_market_connected:
            for stream, params in self.subscriptions.items():
                self._subscribe_to_stream(stream, params)
    
    def subscribe(self, stream, callback):
        """
        Subscribe to a market data stream.
        
        Args:
            stream: The stream name to subscribe to
            callback: Function to call when data is received
        """
        try:
            if stream not in self.callbacks:
                self.callbacks[stream] = []
                self.subscriptions[stream] = {"stream": stream}
                
                # Subscribe to the stream if connected
                if self.is_market_connected:
                    self._subscribe_to_stream(stream, {"stream": stream})
            
            if callback not in self.callbacks[stream]:
                self.callbacks[stream].append(callback)
                
            logger.info(f"Subscribed to stream: {stream}")
            return True
        except Exception as e:
            logger.error(f"Error subscribing to stream {stream}: {e}")
            return False
    
    def _subscribe_to_stream(self, stream, params):
        """Send subscription request to the WebSocket."""
        try:
            subscription = {
                "method": "SUBSCRIBE",
                "params": [stream],
                "id": self.get_request_id()
            }
            
            # In demo mode, don't actually send anything
            logger.debug(f"Demo: Would subscribe to stream: {stream}")
            
            return True
        except Exception as e:
            logger.error(f"Error sending subscription request for {stream}: {e}")
            return False
    
    def subscribe_multiple(self, streams):
        """
        Subscribe to multiple streams at once.
        
        Args:
            streams: List of stream names to subscribe to
        """
        try:
            if not streams:
                logger.warning("No streams provided for multiple subscription")
                return False
                
            params = []
            for stream in streams:
                params.append(stream)
                
                # Initialize callbacks list for each stream
                if stream not in self.callbacks:
                    self.callbacks[stream] = []
                    self.subscriptions[stream] = {"stream": stream}
            
            # Subscribe to all streams if connected
            if self.is_market_connected and params:
                subscription = {
                    "method": "SUBSCRIBE",
                    "params": params,
                    "id": self.get_request_id()
                }
                
                # In demo mode, don't actually send anything
                logger.debug(f"Demo: Would subscribe to multiple streams: {params}")
                
            logger.info(f"Subscribed to multiple streams: {streams}")
            return True
        except Exception as e:
            logger.error(f"Error subscribing to multiple streams: {e}")
            return False
    
    def unsubscribe(self, stream, callback=None):
        """
        Unsubscribe from a market data stream.
        
        Args:
            stream: The stream to unsubscribe from
            callback: Specific callback to remove (None for all)
        """
        try:
            # Remove callback(s)
            if stream in self.callbacks:
                if callback is None:
                    # Remove all callbacks
                    self.callbacks[stream] = []
                elif callback in self.callbacks[stream]:
                    # Remove specific callback
                    self.callbacks[stream].remove(callback)
                
                # If no more callbacks, unsubscribe from the stream
                if not self.callbacks[stream] and self.is_market_connected:
                    unsubscribe_msg = {
                        "method": "UNSUBSCRIBE",
                        "params": [stream],
                        "id": self.get_request_id()
                    }
                    
                    # In demo mode, don't actually send anything
                    logger.debug(f"Demo: Would unsubscribe from stream: {stream}")
                    
                    # Remove from subscriptions
                    if stream in self.subscriptions:
                        del self.subscriptions[stream]
                        
            logger.info(f"Unsubscribed from stream: {stream}")
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing from stream {stream}: {e}")
            return False
    
    def unsubscribe_all(self):
        """Unsubscribe from all market data streams."""
        try:
            streams = list(self.subscriptions.keys())
            
            if not streams:
                logger.info("No active subscriptions to unsubscribe from")
                return True
                
            if self.is_market_connected:
                unsubscribe_msg = {
                    "method": "UNSUBSCRIBE",
                    "params": streams,
                    "id": self.get_request_id()
                }
                
                # In demo mode, don't actually send anything
                logger.debug(f"Demo: Would unsubscribe from all streams: {streams}")
            
            # Clear subscriptions and callbacks
            self.subscriptions = {}
            self.callbacks = {}
            
            logger.info("Unsubscribed from all streams")
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing from all streams: {e}")
            return False
    
    def send_authenticated_request(self, method, params, callback=None):
        """
        Send an authenticated request to the API WebSocket.
        
        Args:
            method: API method to call
            params: Parameters for the method
            callback: Function to call with the response
        """
        try:
            if not self.api_key or not self.api_secret:
                logger.error("API key and secret are required for authenticated requests")
                return False
                
            if not self.is_api_connected:
                logger.error("Cannot send request: API WebSocket not connected")
                return False
                
            # Add timestamp for security
            params["timestamp"] = int(time.time() * 1000)
            
            # Generate signature
            signature = self.generate_signature(params)
            params["signature"] = signature
            
            # Create request
            request_id = self.get_request_id()
            request = {
                "id": request_id,
                "method": method,
                "params": params,
                "apiKey": self.api_key
            }
            
            # Store callback
            if callback:
                self.pending_requests[request_id] = {
                    "method": method,
                    "params": params,
                    "callback": callback,
                    "timestamp": time.time()
                }
            
            # In demo mode, don't actually send anything
            logger.debug(f"Demo: Would send authenticated API request: {method}")
            
            return request_id
        except Exception as e:
            logger.error(f"Error sending authenticated request {method}: {e}")
            return False
    
    def send_request(self, method, params, callback=None):
        """
        Send a non-authenticated request to the API WebSocket.
        
        Args:
            method: API method to call
            params: Parameters for the method
            callback: Function to call with the response
        """
        try:
            if not self.is_api_connected:
                logger.error("Cannot send request: API WebSocket not connected")
                return False
                
            # Create request
            request_id = self.get_request_id()
            request = {
                "id": request_id,
                "method": method,
                "params": params
            }
            
            # Store callback
            if callback:
                self.pending_requests[request_id] = {
                    "method": method,
                    "params": params,
                    "callback": callback,
                    "timestamp": time.time()
                }
            
            # In demo mode, don't actually send anything
            logger.debug(f"Demo: Would send API request: {method}")
            
            return request_id
        except Exception as e:
            logger.error(f"Error sending request {method}: {e}")
            return False
    
    def close(self):
        """Close WebSocket connections."""
        try:
            # Unsubscribe from all streams
            self.unsubscribe_all()
            
            # Close WebSocket connections
            if self.api_ws:
                self.api_ws.close()
                self.is_api_connected = False
                
            if self.market_ws:
                self.market_ws.close()
                self.is_market_connected = False
                
            logger.info("WebSocket connections closed")
            return True
        except Exception as e:
            logger.error(f"Error closing WebSocket connections: {e}")
            return False
    
    # Demo trading functions - these would interact with a real exchange in production code
    
    def place_order(self, symbol, side, order_type, quantity, price=None, callback=None, **kwargs):
        """
        Place a demo order.
        
        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            order_type: Order type (e.g. 'LIMIT', 'MARKET')
            quantity: Order quantity
            price: Order price (required for limit orders)
            callback: Function to call with the response
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity
        }
        
        if price and order_type == "LIMIT":
            params["price"] = price
            
        # Add any additional parameters
        params.update(kwargs)
        
        return self.send_authenticated_request("ORDER", params, callback)
    
    def cancel_order(self, symbol, order_id=None, client_order_id=None, callback=None):
        """Cancel a demo order."""
        params = {"symbol": symbol}
        
        if order_id:
            params["orderId"] = order_id
        elif client_order_id:
            params["clientOrderId"] = client_order_id
        else:
            logger.error("Either orderId or clientOrderId must be provided")
            return False
            
        return self.send_authenticated_request("CANCEL_ORDER", params, callback)
    
    def cancel_all_orders(self, symbol, callback=None):
        """Cancel all demo orders for a symbol."""
        return self.send_authenticated_request("CANCEL_ALL_ORDERS", {"symbol": symbol}, callback)
    
    def get_order(self, symbol, order_id=None, client_order_id=None, callback=None):
        """Get information about a demo order."""
        params = {"symbol": symbol}
        
        if order_id:
            params["orderId"] = order_id
        elif client_order_id:
            params["clientOrderId"] = client_order_id
        else:
            logger.error("Either orderId or clientOrderId must be provided")
            return False
            
        return self.send_authenticated_request("GET_ORDER", params, callback)
    
    def get_open_orders(self, symbol=None, callback=None):
        """Get all open demo orders."""
        params = {}
        if symbol:
            params["symbol"] = symbol
            
        return self.send_authenticated_request("GET_OPEN_ORDERS", params, callback)
    
    def get_account_info(self, callback=None):
        """Get demo account information."""
        return self.send_authenticated_request("GET_ACCOUNT", {}, callback) 