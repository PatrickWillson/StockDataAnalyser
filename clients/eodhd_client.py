"""
EODHD API Client

Fetches financial data from EODHD API.
Delegates data processing to FinancialDataProcessor for separation of concerns.
"""

import requests
import sys
from typing import Dict, Any, Optional
from clients.base_client import BaseAPIClient
from clients.fx_client import FXClient
from core.financial_data_processor import FinancialDataProcessor


class EODHDClient(BaseAPIClient):
    """Client for fetching financial data from EODHD API."""
    
    API_BASE_URL = "https://eodhd.com/api/fundamentals/{ticker}"
    
    def __init__(self, api_key: str, fx_client: Optional[FXClient] = None):
        """
        Initialize EODHD client with retry logic.
        
        Args:
            api_key: EODHD API key
            fx_client: Optional FX client for currency conversion (creates one if not provided)
        """
        super().__init__(timeout=30, max_retries=3, backoff_factor=1.0)
        self.api_key = api_key
        self.fx_client = fx_client or FXClient()
        self.processor = FinancialDataProcessor(fx_client=self.fx_client)
    
    def _make_eodhd_request(self, ticker: str) -> Dict[str, Any]:
        """
        Make API request to EODHD with error handling.
        
        Args:
            ticker: Stock ticker with exchange suffix
            
        Returns:
            API response as dictionary
            
        Raises:
            SystemExit: On API errors
        """
        url = self.API_BASE_URL.format(ticker=ticker)
        params = {
            'api_token': self.api_key,
            'fmt': 'json'
        }
        
        try:
            response = self._make_request(url, params=params)
            
            # Handle EODHD-specific errors
            if response.status_code == 401:
                print(f"[ERROR] Authentication failed. Check your EODHD_API_KEY.")
                sys.exit(1)
            elif response.status_code == 429:
                print(f"[ERROR] Rate limit exceeded. Please wait and try again.")
                sys.exit(1)
            elif response.status_code != 200:
                print(f"[ERROR] API request failed with status {response.status_code}: {response.text}")
                sys.exit(1)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] {str(e)}")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Unexpected error during API request: {str(e)}")
            sys.exit(1)
    
    def fetch_all_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch all required financial data for a ticker.
        
        Args:
            ticker: Stock ticker with exchange suffix (e.g., AAPL.US, VOD.L)
            
        Returns:
            Standardized dictionary containing:
                - ticker: str
                - exchange: str
                - currency: str
                - price: float
                - ceo_name: str
                - history: Dict[year, financial_data]
                - warnings: List[str]
        """
        warnings = []
        
        # Fetch data from API
        data = self._make_eodhd_request(ticker)
        
        # Extract general information
        general = data.get('General', {})
        ticker_code = general.get('Code', ticker.split('.')[0])
        exchange = general.get('Exchange', 'UNKNOWN')
        currency = general.get('CurrencyCode', 'USD')
        ceo_name = self.processor.extract_ceo_name(data)
        
        # Check if delisted
        is_delisted = general.get('IsDelisted', False)
        if is_delisted:
            warnings.append("WARNING: Company is delisted")
        
        # Extract shares outstanding
        shares_outstanding = self.processor.extract_shares_outstanding(data)
        if shares_outstanding == 0.0:
            warnings.append("WARNING: Shares outstanding data unavailable")
        
        # Parse financial statements using processor
        balance_sheet = self.processor.parse_balance_sheet(data)
        income_statement = self.processor.parse_income_statement(data)
        dividend_history = self.processor.parse_dividend_history(data)
        
        # Merge financial data
        history = self.processor.merge_financial_data(balance_sheet, income_statement, 
                                                      dividend_history, shares_outstanding)
        
        # Get current price
        price = self.processor.get_current_price(data)
        
        # Get most recent EPS for London Fix
        most_recent_eps = 0.0
        if history:
            sorted_years = sorted(history.keys(), reverse=True)
            if sorted_years:
                most_recent_eps = history[sorted_years[0]].get('eps', 0.0)
        
        # Apply London Fix
        price = self.processor.apply_london_fix(price, most_recent_eps, exchange, warnings)
        
        # Apply currency conversion (if needed)
        # Extract price currency from Highlights or General section
        price_currency = currency  # Default to general currency
        try:
            highlights_currency = data.get('Highlights', {}).get('CurrencyCode')
            if highlights_currency:
                price_currency = highlights_currency
        except (KeyError, TypeError):
            pass
        
        # Get financials currency (from balance sheet or income statement)
        financials_currency = currency
        
        # Apply currency conversion if currencies differ
        if price_currency != financials_currency:
            price = self.processor.apply_currency_conversion(price, price_currency, financials_currency, warnings)
        
        # Validate data quality
        self.processor.validate_data_quality(history, warnings)
        
        return {
            'ticker': ticker_code,
            'exchange': exchange,
            'currency': currency,
            'price': price,
            'ceo_name': ceo_name,
            'history': history,
            'warnings': warnings
        }
