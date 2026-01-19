"""
Alpha Vantage API Client

Fetches current stock prices from Alpha Vantage API as fallback when EODHD data is unavailable.
"""

import os
import requests
from typing import Optional, Tuple
from clients.base_client import BaseAPIClient


class AlphaVantageClient(BaseAPIClient):
    """
    Alpha Vantage API client for fetching current stock prices.
    Used as fallback when EODHD price data is unavailable.
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    # EODHD → Alpha Vantage exchange code mapping
    # NOTE: These mappings may need updates if Alpha Vantage changes their suffix conventions.
    # Last verified: January 2026
    EXCHANGE_MAPPING = {
        # North America
        'US': '',  # No suffix for US stocks
        'TO': '.TO',  # Toronto Stock Exchange
        'V': '.V',  # TSX Venture
        'MX': '.MEX',  # Mexico (verify: may also be .MX)
        
        # Europe
        'LSE': '.LON',  # London Stock Exchange
        'IL': '.L',  # London International
        'XETRA': '.DE',  # XETRA
        'F': '.F',  # Frankfurt
        'BE': '.BE',  # Berlin
        'PA': '.PA',  # Paris
        'AS': '.AS',  # Amsterdam
        'BR': '.BR',  # Brussels
        'LS': '.LS',  # Lisbon
        'MC': '.MC',  # Madrid
        'MI': '.MI',  # Milan
        'SW': '.SW',  # Switzerland
        'VI': '.VI',  # Vienna
        'IR': '.IR',  # Ireland
        'ST': '.ST',  # Stockholm
        'OL': '.OL',  # Oslo
        'CO': '.CO',  # Copenhagen
        'HE': '.HE',  # Helsinki
        'IC': '.IC',  # Iceland
        'WAR': '.WAR',  # Warsaw
        'BUD': '.BUD',  # Budapest
        'PR': '.PR',  # Prague
        'MCX': '.ME',  # Moscow
        'IS': '.IS',  # Istanbul
        'AT': '.AT',  # Athens
        
        # Asia Pacific
        'AU': '.AX',  # Australia
        'TSE': '.T',  # Tokyo
        'HK': '.HK',  # Hong Kong
        'SHG': '.SS',  # Shanghai
        'SHE': '.SZ',  # Shenzhen
        'NSE': '.NS',  # India NSE
        'BSE': '.BO',  # India BSE
        'KO': '.KS',  # Korea
        'KQ': '.KQ',  # KOSDAQ
        'TW': '.TW',  # Taiwan
        'SG': '.SI',  # Singapore
        'BK': '.BK',  # Bangkok
        'JK': '.JK',  # Jakarta
        'KLSE': '.KL',  # Kuala Lumpur
        
        # Other
        'SA': '.SA',  # Brazil
        'JSE': '.JO',  # Johannesburg
        'SR': '.SAU',  # Saudi Arabia
        'TA': '.TA',  # Tel Aviv
    }
    
    def __init__(self, api_key: Optional[str] = None, debug: bool = False):
        """
        Initialize Alpha Vantage client.
        
        Lazy API key loading: The key is checked when get_price() is called,
        not at initialization. This prevents the system from failing if the
        key is missing but EODHD data is perfect (fallback not needed).
        
        Args:
            api_key: Alpha Vantage API key (from ALPHAVANTAGE_API_KEY env var)
            debug: Enable debug logging
        """
        super().__init__(timeout=30, max_retries=3, backoff_factor=1.0)
        self.api_key = api_key or os.getenv('ALPHAVANTAGE_API_KEY')
        self.debug = debug
    
    def _log(self, message: str) -> None:
        """Log message if debug mode is enabled."""
        if self.debug:
            print(message)
    
    def get_price(self, ticker: str) -> Optional[float]:
        """
        Fetch current price for a ticker using GLOBAL_QUOTE.
        
        Args:
            ticker: Ticker in EODHD format (e.g., "YU.LSE", "AAPL.US")
            
        Returns:
            Current price as float, or None if unavailable
        """
        if not self.api_key:
            self._log("[WARNING] ALPHAVANTAGE_API_KEY not set - fallback unavailable")
            return None
        
        # Parse ticker
        symbol, exchange = self._parse_ticker(ticker)
        if not symbol or not exchange:
            self._log(f"[ERROR] Invalid ticker format: {ticker}")
            return None
        
        # Translate exchange code
        av_symbol = self._translate_ticker(symbol, exchange)
        if not av_symbol:
            return None
        
        # Call API
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': av_symbol,
            'apikey': self.api_key
        }
        
        try:
            response = self._make_request(self.BASE_URL, params)
            
            # Check for errors
            if response.status_code == 401:
                self._log("[ERROR] Alpha Vantage authentication failed - invalid API key")
                return None
            elif response.status_code == 429:
                self._log("[ERROR] Alpha Vantage rate limit exceeded")
                return None
            elif response.status_code != 200:
                self._log(f"[ERROR] Alpha Vantage API error: {response.status_code}")
                return None
            
            # Parse response
            data = response.json()
            
            # Debug: Print full response
            self._log(f"[DEBUG] Alpha Vantage response: {data}")
            
            # Check for API error messages
            if 'Error Message' in data:
                self._log(f"[ERROR] Alpha Vantage error: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                # Rate limit message
                self._log(f"[ERROR] Alpha Vantage rate limit: {data['Note']}")
                return None
            
            if 'Information' in data:
                # Rate limit or other informational message
                info_msg = data['Information']
                if 'rate limit' in info_msg.lower() or '25 requests per day' in info_msg.lower():
                    self._log(f"[ERROR] Alpha Vantage rate limit exceeded (25 requests/day for free tier)")
                else:
                    self._log(f"[ERROR] Alpha Vantage info: {info_msg}")
                return None
            
            # Parse price from Global Quote
            global_quote = data.get('Global Quote', {})
            self._log(f"[DEBUG] Global Quote: {global_quote}")
            
            price_str = global_quote.get('05. price')
            
            if price_str:
                price = float(price_str)
                self._log(f"[SUCCESS] Alpha Vantage price for {av_symbol}: {price}")
                return price
            else:
                self._log(f"[ERROR] No price in Alpha Vantage response for {av_symbol}")
                self._log(f"[DEBUG] Available keys in Global Quote: {list(global_quote.keys())}")
                return None
                
        except requests.exceptions.RequestException as e:
            self._log(f"[ERROR] Alpha Vantage API request error: {e}")
            return None
        except ValueError as e:
            self._log(f"[ERROR] Alpha Vantage response parsing error: {e}")
            return None
        except Exception as e:
            self._log(f"[ERROR] Alpha Vantage unexpected error: {e}")
            return None
    
    def _parse_ticker(self, ticker: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse EODHD ticker into symbol and exchange.
        
        Args:
            ticker: Ticker in EODHD format (e.g., "YU.LSE", "AAPL.US")
            
        Returns:
            Tuple of (symbol, exchange) or (None, None) if invalid
        """
        parts = ticker.split('.')
        if len(parts) != 2:
            return None, None
        return parts[0], parts[1]
    
    def _translate_ticker(self, symbol: str, eodhd_exchange: str) -> Optional[str]:
        """
        Translate EODHD ticker to Alpha Vantage format.
        
        Args:
            symbol: Stock symbol (e.g., "YU", "AAPL")
            eodhd_exchange: EODHD exchange code (e.g., "LSE", "US")
            
        Returns:
            Alpha Vantage ticker (e.g., "YU.LON", "AAPL") or None if unmapped
        """
        av_suffix = self.EXCHANGE_MAPPING.get(eodhd_exchange)
        
        if av_suffix is None:
            self._log(f"[WARNING] Unmapped exchange code: {eodhd_exchange}")
            return None
        
        # US stocks have no suffix
        if av_suffix == '':
            return symbol
        
        return f"{symbol}{av_suffix}"
