"""
FX Rate Client

Fetches live foreign exchange rates using yfinance (Yahoo Finance).
No API key required, no rate limits.
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta


class FXClient:
    """Client for fetching live foreign exchange rates using yfinance."""
    
    def __init__(self, debug: bool = False):
        """
        Initialize FX client with caching.
        
        Args:
            debug: Enable debug logging for troubleshooting
        """
        self._cache = {}  # Cache current rates to minimize API calls
        self._historical_cache = {}  # Cache historical rates for session
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
        # Normalize GBX to GBP (GBX is pence, not a real currency code)
        # yfinance doesn't recognize GBX, but GBX = GBP / 100
        if from_currency == "GBX":
            from_currency = "GBP"
        if to_currency == "GBX":
            to_currency = "GBP"
        
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
    
    def fetch_historical_rates(
        self,
        from_currency: str,
        to_currency: str,
        start_date: str,
        end_date: str
    ) -> Optional[Dict[str, float]]:
        """
        Fetch historical exchange rates for a currency pair over a date range.
        
        Uses yfinance's historical data API for FX pairs (e.g., "GBPUSD=X").
        
        Args:
            from_currency: Source currency code (e.g., 'GBP', 'EUR')
            to_currency: Target currency code (e.g., 'USD', 'EUR')
            start_date: ISO date string (e.g., '2004-01-01')
            end_date: ISO date string (e.g., '2024-12-31')
            
        Returns:
            Dict mapping date strings (YYYY-MM-DD) to exchange rates, or None if failed
            Example: {'2024-06-30': 1.2650, '2023-06-30': 1.2100, ...}
        """
        # Normalize GBX to GBP (GBX is pence, not a real currency code)
        if from_currency == "GBX":
            from_currency = "GBP"
        if to_currency == "GBX":
            to_currency = "GBP"
        
        # Return empty dict if same currency (no conversion needed)
        if from_currency == to_currency:
            return {}
        
        # Check cache first
        cache_key = (from_currency, to_currency, start_date, end_date)
        if cache_key in self._historical_cache:
            if self.debug:
                self.logger.debug(f"Using cached historical rates for {from_currency}/{to_currency}")
            return self._historical_cache[cache_key]
        
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
                self.logger.debug(f"Fetching historical FX rates for {fx_ticker} from {start_date} to {end_date}...")
            
            # Fetch historical data using yfinance
            ticker_obj = yf.Ticker(fx_ticker)
            hist = ticker_obj.history(start=start_date, end=end_date, auto_adjust=True)
            
            if hist.empty:
                if self.debug:
                    self.logger.debug(f"No historical FX data available for {fx_ticker}")
                return None
            
            # Convert DataFrame to dict: date_string → close_price (exchange rate)
            rate_dict = {}
            for date_index, row in hist.iterrows():
                date_str = date_index.strftime('%Y-%m-%d')
                rate_dict[date_str] = float(row['Close'])
            
            # Cache the rates
            self._historical_cache[cache_key] = rate_dict
            
            if self.debug:
                self.logger.debug(f"Successfully fetched {len(rate_dict)} days of historical FX rates for {fx_ticker}")
            
            return rate_dict
            
        except Exception as e:
            # On any error, return None (caller will handle fallback)
            if self.debug:
                self.logger.debug(f"Error fetching historical FX rates for {from_currency}/{to_currency}: {type(e).__name__}: {str(e)}")
            return None
    
    def match_fiscal_year_end_rates(
        self,
        rate_data: Dict[str, float],
        fiscal_year_ends: List[str]
    ) -> Dict[str, Optional[float]]:
        """
        Match historical FX rates to fiscal year end dates.
        
        For each fiscal year end date:
        1. Try exact match in rate data
        2. If no match, search backwards up to 7 days
        3. Return None if no rate found within window
        
        This handles cases where fiscal year ends fall on weekends or holidays.
        
        Args:
            rate_data: Dict mapping date strings to FX rates
                Example: {'2024-06-28': 1.2650, '2024-06-29': 1.2700, ...}
            fiscal_year_ends: List of fiscal year end dates (ISO format)
                Example: ['2024-06-30', '2023-06-30', '2022-06-30']
                
        Returns:
            Dict mapping fiscal year end dates to FX rates (or None if not found)
            Example: {'2024-06-30': 1.2700, '2023-06-30': 1.2100, '2022-06-30': None}
            
        Note:
            - Searches backwards (not forwards) to get the last traded rate before year end
            - Returns None for years with no data within 7-day window
        """
        result = {}
        
        for fiscal_end in fiscal_year_ends:
            # Try exact match first
            if fiscal_end in rate_data:
                result[fiscal_end] = rate_data[fiscal_end]
                if self.debug:
                    self.logger.debug(f"{fiscal_end}: Exact match found - {rate_data[fiscal_end]:.4f}")
                continue
            
            # Search backwards up to 7 days for last trading day
            try:
                target = datetime.strptime(fiscal_end, '%Y-%m-%d')
                found = False
                
                for days_back in range(1, 8):
                    search_date = (target - timedelta(days=days_back)).strftime('%Y-%m-%d')
                    if search_date in rate_data:
                        result[fiscal_end] = rate_data[search_date]
                        if self.debug:
                            self.logger.debug(f"{fiscal_end}: Using rate from {search_date} ({days_back} days prior) - {rate_data[search_date]:.4f}")
                        found = True
                        break
                
                if not found:
                    result[fiscal_end] = None
                    if self.debug:
                        self.logger.debug(f"{fiscal_end}: No FX rate data within 7-day window")
                        
            except ValueError as e:
                # Invalid date format
                result[fiscal_end] = None
                if self.debug:
                    self.logger.debug(f"{fiscal_end}: Invalid date format - {e}")
        
        return result
