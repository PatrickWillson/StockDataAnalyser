"""
EODHD API Client

Fetches financial data from EODHD API.
Delegates data processing to FinancialDataProcessor for separation of concerns.
"""

import requests
import logging
from typing import Dict, Any, Optional, List
from clients.base_client import BaseAPIClient
from core.errors import EODHDAuthError, EODHDRateLimitError, EODHDRequestError
from clients.fx_client import FXClient
from core.currency_converter import CurrencyConverter
from core.financial_data_assembler import FinancialDataAssembler
from core.financial_data_processor import FinancialDataProcessor

logger = logging.getLogger(__name__)


class EODHDClient(BaseAPIClient):
    """Client for fetching financial data from EODHD API."""
    
    API_BASE_URL = "https://eodhd.com/api/fundamentals/{ticker}"
    
    def __init__(self, api_key: str, fx_client: Optional[FXClient] = None, debug: bool = False):
        """
        Initialize EODHD client with retry logic.
        
        Args:
            api_key: EODHD API key
            fx_client: Optional FX client for currency conversion (creates one if not provided)
            debug: Enable debug logging (default: False)
        """
        super().__init__(timeout=30, max_retries=3, backoff_factor=1.0)
        self.api_key = api_key
        self.fx_client = fx_client or FXClient()
        self.currency_converter = CurrencyConverter(fx_client=self.fx_client)
        self.debug = debug
        self.processor = FinancialDataProcessor(currency_converter=self.currency_converter, debug=debug)
        self.assembler = FinancialDataAssembler(self.processor, self.currency_converter, self.fx_client, debug=debug)
    
    def _make_eodhd_request(self, ticker: str) -> Dict[str, Any]:
        """
        Make API request to EODHD with error handling.
        
        Args:
            ticker: Stock ticker with exchange suffix
            
        Returns:
            API response as dictionary
            
        Raises:
            EODHDAuthError: HTTP 401
            EODHDRateLimitError: HTTP 429
            EODHDRequestError: network failure, other HTTP status, or invalid JSON
        """
        url = self.API_BASE_URL.format(ticker=ticker)
        params = {
            'api_token': self.api_key,
            'fmt': 'json'
        }
        
        try:
            response = self._make_request(url, params=params)
        except requests.exceptions.RequestException as e:
            raise EODHDRequestError(str(e)) from e
        except Exception as e:
            raise EODHDRequestError(f"Unexpected error during API request: {str(e)}") from e
        
        # Handle EODHD-specific errors
        if response.status_code == 401:
            raise EODHDAuthError("Authentication failed. Check your EODHD_API_KEY.")
        if response.status_code == 429:
            raise EODHDRateLimitError("Rate limit exceeded. Please wait and try again.")
        if response.status_code != 200:
            raise EODHDRequestError(f"API request failed with status {response.status_code}: {response.text}")
        
        try:
            return response.json()
        except Exception as e:
            raise EODHDRequestError(f"Unexpected error during API request: {str(e)}") from e
    
    def _fetch_dividend_history(self, ticker: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch dividend history from EODHD Dividend API.
        
        Args:
            ticker: Stock ticker with exchange suffix (e.g., AAPL.US, VOD.LSE)
            
        Returns:
            List of dividend records with date, value, declarationDate, paymentDate, etc.
            Returns None if API call fails (403, 404, etc.)
        """
        url = f"https://eodhd.com/api/div/{ticker}"
        params = {
            'api_token': self.api_key,
            'fmt': 'json'
        }
        
        try:
            response = self._make_request(url, params=params)
            
            # Handle expected failures gracefully (403 = subscription tier, 404 = no data)
            if response.status_code == 403:
                if self.debug:
                    logger.debug("Dividend API returned 403 (requires higher subscription tier)")
                return None
            elif response.status_code == 404:
                if self.debug:
                    logger.debug("Dividend API returned 404 (no dividend data available)")
                return None
            elif response.status_code != 200:
                if self.debug:
                    logger.debug(f"Dividend API failed with status {response.status_code}")
                return None
            
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                if self.debug:
                    logger.debug(f"Dividend API returned {len(data)} dividend records")
                return data
            else:
                if self.debug:
                    logger.debug("Dividend API returned empty data")
                return None
                
        except Exception as e:
            if self.debug:
                logger.debug(f"Dividend API request failed: {str(e)}")
            return None
    
    def fetch_all_data(self, ticker: str, yf_client: Optional[Any] = None) -> Dict[str, Any]:
        """
        Fetch the fundamentals and dividend history for a ticker and assemble financial_data.
        
        Args:
            ticker: Stock ticker with exchange suffix (e.g., AAPL.US, YU.LSE)
            yf_client: Optional yfinance client for price fetching (primary source)
            
        Returns:
            financial_data dict (see FinancialDataAssembler.assemble)
        """
        logger.info(f"Fetching data for {ticker}...")
        data = self._make_eodhd_request(ticker)
        
        # Save raw API response to file when debug mode is enabled
        if self.debug:
            import json
            debug_file = f"data/{ticker.replace('.', '_')}_raw_api_response.json"
            try:
                with open(debug_file, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.debug(f"Raw API response saved to: {debug_file}")
            except Exception as e:
                logger.debug(f"Could not save raw API response: {e}")
        
        # Fetch dividend history from Dividend API (primary dividend source)
        logger.info("Fetching dividend history...")
        dividend_api_data = self._fetch_dividend_history(ticker)
        
        return self.assembler.assemble(data, dividend_api_data, ticker, yf_client=yf_client)
