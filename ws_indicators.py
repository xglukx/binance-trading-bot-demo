import numpy as np
import pandas as pd
import logging
from datetime import datetime
from collections import deque
import random  # Added for mock strategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("DemoIndicators")

class TechnicalIndicators:
    """
    Demo technical indicators calculator that works with real-time WebSocket data.
    This is for demonstration purposes only and should not be used for actual trading.
    """
    
    def __init__(self, max_length=500):
        """
        Initialize the indicators calculator.
        
        Args:
            max_length: Maximum number of candles to store
        """
        self.max_length = max_length
        self.candles = {}  # Symbol -> DataFrame mapping
        self.subscribers = {}  # Symbol -> callback list mapping
        self.last_update = {}  # Symbol -> timestamp mapping
        
    def initialize_symbol(self, symbol, timeframe="5m"):
        """Initialize data structure for a symbol."""
        if symbol not in self.candles:
            self.candles[symbol] = pd.DataFrame(
                columns=['open_time', 'open', 'high', 'low', 'close', 'volume']
            )
            self.subscribers[symbol] = []
            self.last_update[symbol] = None
            logger.info(f"Initialized indicators for {symbol} ({timeframe})")
            
    def update_candle(self, symbol, candle_data):
        """
        Update candle data for a symbol from WebSocket data.
        
        Args:
            symbol: The trading symbol
            candle_data: Candle data from WebSocket (exchange format)
        """
        try:
            # Ensure symbol is initialized
            if symbol not in self.candles:
                self.initialize_symbol(symbol)
                
            # Convert WebSocket data to DataFrame format
            # Standard format: [start_time, open, high, low, close, volume, ...]
            open_time = candle_data['t']  # kline start time
            
            # Create candle data
            new_candle = {
                'open_time': open_time,
                'open': float(candle_data['o']),
                'high': float(candle_data['h']),
                'low': float(candle_data['l']),
                'close': float(candle_data['c']),
                'volume': float(candle_data['v'])
            }
            
            # Check if this candle already exists
            if len(self.candles[symbol]) > 0 and self.candles[symbol].iloc[-1]['open_time'] == open_time:
                # Update existing candle
                self.candles[symbol].iloc[-1] = pd.Series(new_candle)
            else:
                # Add new candle
                self.candles[symbol] = pd.concat([
                    self.candles[symbol],
                    pd.DataFrame([new_candle])
                ], ignore_index=True)
                
                # Trim to max length
                if len(self.candles[symbol]) > self.max_length:
                    self.candles[symbol] = self.candles[symbol].iloc[-self.max_length:]
            
            # Update timestamp
            self.last_update[symbol] = datetime.now()
            
            # Calculate indicators
            self._calculate_indicators(symbol)
            
            # Notify subscribers
            for callback in self.subscribers[symbol]:
                try:
                    callback(symbol, self.candles[symbol])
                except Exception as e:
                    logger.error(f"Error in subscriber callback for {symbol}: {e}")
                    
        except Exception as e:
            logger.error(f"Error updating candle for {symbol}: {e}")
            
    def _calculate_indicators(self, symbol):
        """Calculate demo technical indicators for a symbol."""
        if symbol not in self.candles or len(self.candles[symbol]) < 10:
            # Not enough data yet
            return
            
        try:
            # Calculate RSI
            closes = self.candles[symbol]['close'].values
            self.candles[symbol]['rsi'] = self._calculate_rsi(closes, 14)
            
            # Calculate simple moving averages
            self.candles[symbol]['sma_20'] = self._calculate_sma(closes, 20)
            self.candles[symbol]['sma_50'] = self._calculate_sma(closes, 50)
            
            # Calculate demo momentum indicator
            self.candles[symbol]['momentum'] = self._calculate_momentum(closes, 10)
            
            # Calculate demo volatility indicator
            self.candles[symbol]['volatility'] = self._calculate_volatility(
                self.candles[symbol]['high'].values,
                self.candles[symbol]['low'].values,
                10
            )
            
        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {e}")
            
    def _calculate_rsi(self, prices, period=14):
        """Calculate Relative Strength Index."""
        if len(prices) <= period:
            # Not enough data
            return np.nan
            
        # Calculate price changes
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        
        # Calculate gains and losses
        up = seed[seed>=0].sum()/period
        down = -seed[seed<0].sum()/period
        
        if down == 0:  # Avoid division by zero
            return 100
            
        rs = up/down
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100./(1.+rs)
        
        # Calculate RSI
        for i in range(period, len(prices)):
            delta = deltas[i-1]
            
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
                
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            
            rs = up/down if down != 0 else 100
            rsi[i] = 100. - 100./(1.+rs)
            
        return rsi
    
    def _calculate_sma(self, prices, period):
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return np.array([np.nan] * len(prices))
            
        sma = np.zeros_like(prices)
        sma[:period] = np.nan
        
        for i in range(period, len(prices) + 1):
            sma[i-1] = np.mean(prices[i-period:i])
            
        return sma
    
    def _calculate_momentum(self, prices, period):
        """
        Calculate momentum indicator (current price / price n periods ago).
        This is a simple demo indicator.
        """
        if len(prices) <= period:
            return np.array([np.nan] * len(prices))
            
        momentum = np.zeros_like(prices)
        momentum[:period] = np.nan
        
        for i in range(period, len(prices)):
            momentum[i] = prices[i] / prices[i-period] - 1
            
        return momentum * 100  # Convert to percentage
        
    def _calculate_volatility(self, highs, lows, period):
        """
        Calculate a simple volatility indicator based on high-low range.
        This is a demo indicator for educational purposes.
        """
        if len(highs) < period or len(lows) < period:
            return np.array([np.nan] * len(highs))
            
        volatility = np.zeros_like(highs)
        volatility[:period] = np.nan
        
        for i in range(period, len(highs)):
            # Calculate average true range over the period
            ranges = highs[i-period:i] - lows[i-period:i]
            volatility[i] = np.mean(ranges) / np.mean(highs[i-period:i]) * 100
            
        return volatility
    
    def _generate_random_signal(self):
        """
        Generate a random trading signal for demo purposes.
        Returns a value between -100 and 100.
        """
        return random.uniform(-100, 100)
            
    def subscribe(self, symbol, callback):
        """
        Subscribe to indicator updates for a symbol.
        
        Args:
            symbol: The trading symbol
            callback: Function to call when indicators are updated
        """
        if symbol not in self.subscribers:
            self.initialize_symbol(symbol)
            
        if callback not in self.subscribers[symbol]:
            self.subscribers[symbol].append(callback)
            logger.info(f"Subscribed to indicator updates for {symbol}")
            
    def unsubscribe(self, symbol, callback):
        """Unsubscribe from indicator updates."""
        if symbol in self.subscribers and callback in self.subscribers[symbol]:
            self.subscribers[symbol].remove(callback)
            logger.info(f"Unsubscribed from indicator updates for {symbol}")
            
    def get_current_indicators(self, symbol):
        """
        Get the latest indicators for a symbol.
        
        Returns:
            dict: Dictionary with current indicator values
        """
        if symbol not in self.candles or len(self.candles[symbol]) == 0:
            return {
                'rsi': None,
                'sma_20': None,
                'sma_50': None,
                'momentum': None,
                'volatility': None,
                'random_signal': self._generate_random_signal(),
                'price': None,
                'timestamp': None
            }
            
        last_candle = self.candles[symbol].iloc[-1]
        
        return {
            'rsi': last_candle.get('rsi'),
            'sma_20': last_candle.get('sma_20'),
            'sma_50': last_candle.get('sma_50'),
            'momentum': last_candle.get('momentum'),
            'volatility': last_candle.get('volatility'),
            'random_signal': self._generate_random_signal(),
            'price': last_candle['close'],
            'timestamp': last_candle['open_time']
        }
        
    def is_ready(self, symbol):
        """
        Check if indicators are ready for trading decisions.
        
        Returns:
            bool: True if indicators are calculated and ready
        """
        if symbol not in self.candles or len(self.candles[symbol]) < 50:
            return False
            
        indicators = self.get_current_indicators(symbol)
        return (
            indicators['rsi'] is not None and
            indicators['sma_20'] is not None and
            indicators['sma_50'] is not None and
            indicators['momentum'] is not None and
            indicators['volatility'] is not None and
            not np.isnan(indicators['rsi']) and
            not np.isnan(indicators['sma_20']) and
            not np.isnan(indicators['sma_50']) and
            not np.isnan(indicators['momentum']) and
            not np.isnan(indicators['volatility'])
        ) 