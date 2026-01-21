"""
FX Rate Client

Fetches live foreign exchange rates from Frankfurter API (free, no API key required).
Frankfurter is backed by European Central Bank data.
"""

import requests
from typing import Optional
from clients.base_client import BaseAPIClient


class FXClient(BaseAPIClient):
    """Client for fetching live foreign exchange rates."""
    
    API_BASE_URL = "https://api.frankfurter.app/latest"
    
    def __init__(self):
        """Initialize FX client with retry logic and caching."""
        super().__init__(timeout=10, max_retries=3, backoff_factor=1.0)
        self._cache = {}  # Cache rates to minimize API calls
    
    def get_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Get live exchange rate from one currency to another.
        
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
            return self._cache[cache_key]
        
        try:
            # Fetch rate from Frankfurter API
            params = {
                'from': from_currency,
                'to': to_currency
            }
            
            response = self._make_request(self.API_BASE_URL, params=params)
            
            if response.status_code == 200:
                data = response.json()
                rate = data.get('rates', {}).get(to_currency)
                
                if rate:
                    # Cache the rate
                    self._cache[cache_key] = float(rate)
                    return float(rate)
            
            # If API call fails, return None
            return None
            
        except (requests.exceptions.RequestException, ValueError, KeyError, Exception):
            # On any error, return None (caller will handle fallback)
            return None
    
    def clear_cache(self):
        """Clear the FX rate cache. Useful for getting fresh rates."""
        self._cache.clear()
