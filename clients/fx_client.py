"""
FX Rate Client

Fetches live foreign exchange rates using yfinance (Yahoo Finance).
No API key required, no rate limits.
"""

import logging
from typing import Optional


class FXClient:
    """Client for fetching live foreign exchange rates using yfinance."""
    
    def __init__(self, debug: bool = False):
        """
        Initialize FX client with caching.
        
        Args:
            debug: Enable debug logging for troubleshooting
        """
        self._cache = {}  # Cache rates to minimize API calls
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)
    
    def get_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Get live exchange rate from one currency to another using yfinance.
        
        Uses Yahoo Finance FX pairs (e.g., "GBPUSD=X" for GBP to USD).
        
        Args:
            from_currency: Source currency code (e.g., 'EUR', 'GBP', 'USD')
            to_currency: Target currency code (e.g., 'USD', 'EUR', 'GBP')
            
        Returns:
            Exchange rate as float, or None if unavailable
            
        Example:
            >>> client = FXClient()
            >>> rate = client.get_rate('EUR', 'USD')
            >>> print(f"1 EUR = {rate} USD")
        """
        # Return 1.0 if same currency
        if from_currency == to_currency:
            return 1.0
        
        # Check cache first
        cache_key = (from_currency, to_currency)
        if cache_key in self._cache:
            if self.debug:
                self.logger.debug(f"Using cached rate for {from_currency}/{to_currency}: {self._cache[cache_key]}")
            return self._cache[cache_key]
        
        try:
            # Import yfinance here to avoid import errors if not installed
            try:
                import yfinance as yf
            except ImportError:
                self.logger.error("yfinance library not installed. Run: pip install yfinance")
                return None
            
            # Construct FX pair ticker for yfinance
            # Yahoo Finance uses format: "GBPUSD=X" for GBP to USD
            fx_ticker = f"{from_currency}{to_currency}=X"
            
            if self.debug:
                self.logger.debug(f"Fetching FX rate for {fx_ticker} from yfinance...")
            
            # Fetch rate using yfinance
            ticker_obj = yf.Ticker(fx_ticker)
            
            # Use fast_info for better performance
            # Note: fast_info is a lazy-loading dict, so we need to access it properly
            try:
                rate = ticker_obj.fast_info['lastPrice']
            except (KeyError, TypeError, AttributeError):
                # Fallback to info if fast_info doesn't work
                rate = ticker_obj.info.get('regularMarketPrice')
            
            if rate is None or rate <= 0:
                if self.debug:
                    self.logger.debug(f"No valid rate data for {fx_ticker}")
                return None
            
            # Cache the rate
            self._cache[cache_key] = float(rate)
            
            if self.debug:
                self.logger.debug(f"Successfully fetched rate for {fx_ticker}: {rate}")
            
            return float(rate)
            
        except Exception as e:
            # On any error, return None (caller will handle fallback)
            if self.debug:
                self.logger.debug(f"Error fetching FX rate for {from_currency}/{to_currency}: {type(e).__name__}: {str(e)}")
            return None
    
    def clear_cache(self):
        """Clear the FX rate cache. Useful for getting fresh rates."""
        self._cache.clear()
        if self.debug:
            self.logger.debug("FX rate cache cleared")
