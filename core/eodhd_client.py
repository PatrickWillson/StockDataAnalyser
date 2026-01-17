"""
EODHD API Client

Fetches financial data from EODHD API and normalizes it into a standardized format.
Handles currency conversions, data sanitization, and quality validation.
"""

import requests
import sys
from typing import Dict, Any, Optional, List
from core.base_client import BaseAPIClient
from core.fx_client import FXClient


class EODHDClient(BaseAPIClient):
    """Client for fetching and processing financial data from EODHD API."""
    
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
    
    def _sanitize_value(self, value: Any) -> float:
        """
        Convert "NA" strings and null values to 0.0.
        
        Args:
            value: Raw value from API
            
        Returns:
            Sanitized float value
        """
        if value is None or value == "" or value == "NA" or value == "N/A":
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
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

    def _extract_ceo_name(self, data: Dict[str, Any]) -> str:
        """Extract CEO name from General.Officers field."""
        try:
            officers = data.get('General', {}).get('Officers', [])
            if officers and len(officers) > 0:
                return officers[0].get('Name', 'N/A')
        except (KeyError, TypeError, IndexError):
            pass
        return 'N/A'
    
    def _extract_shares_outstanding(self, data: Dict[str, Any]) -> float:
        """Extract shares outstanding from SharesStats."""
        try:
            shares = data.get('SharesStats', {}).get('SharesOutstanding', 0)
            return self._sanitize_value(shares)
        except (KeyError, TypeError):
            return 0.0
    
    def _parse_balance_sheet(self, data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Parse and sort yearly Balance Sheet data by date descending.
        
        Returns:
            Dictionary with year as key and financial data as value
        """
        result = {}
        try:
            yearly_data = data.get('Financials', {}).get('Balance_Sheet', {}).get('yearly', {})
            
            # Sort by date descending
            sorted_years = sorted(yearly_data.keys(), reverse=True)
            
            for year in sorted_years:
                year_data = yearly_data[year]
                result[year] = {
                    'total_equity': self._sanitize_value(year_data.get('totalStockholderEquity')),
                    'intangible_assets': self._sanitize_value(year_data.get('intangibleAssets')),
                    'goodwill': self._sanitize_value(year_data.get('goodwill')),
                    'current_assets': self._sanitize_value(year_data.get('totalCurrentAssets')),
                    'current_liabilities': self._sanitize_value(year_data.get('totalCurrentLiabilities')),
                    'total_liabilities': self._sanitize_value(year_data.get('totalLiab')),
                    'long_term_debt': self._sanitize_value(year_data.get('longTermDebt')),
                }
        except (KeyError, TypeError, AttributeError):
            pass
        
        return result
    
    def _parse_income_statement(self, data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Parse and sort yearly Income Statement data by date descending.
        
        Returns:
            Dictionary with year as key and financial data as value
        """
        result = {}
        try:
            yearly_data = data.get('Financials', {}).get('Income_Statement', {}).get('yearly', {})
            
            # Sort by date descending
            sorted_years = sorted(yearly_data.keys(), reverse=True)
            
            for year in sorted_years:
                year_data = yearly_data[year]
                result[year] = {
                    'revenue': self._sanitize_value(year_data.get('totalRevenue')),
                    'net_income': self._sanitize_value(year_data.get('netIncome')),
                    'eps': self._sanitize_value(year_data.get('eps')),
                }
        except (KeyError, TypeError, AttributeError):
            pass
        
        return result
    
    def _parse_dividend_history(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract dividend history from SplitsDividends.NumberDividendsByYear.
        
        Returns:
            Dictionary with year as key and dividend count as value
        """
        result = {}
        try:
            div_data = data.get('SplitsDividends', {}).get('NumberDividendsByYear', {})
            for year, count in div_data.items():
                result[year] = self._sanitize_value(count)
        except (KeyError, TypeError, AttributeError):
            pass
        
        return result
    
    def _get_current_price(self, data: Dict[str, Any]) -> float:
        """Extract current price from API data."""
        try:
            # Try to get from Highlights first
            price = data.get('Highlights', {}).get('SharePrice')
            if price:
                return self._sanitize_value(price)
            
            # Fallback to General section
            price = data.get('General', {}).get('SharePrice')
            if price:
                return self._sanitize_value(price)
        except (KeyError, TypeError):
            pass
        
        return 0.0
    
    def _merge_financial_data(self, balance_sheet: Dict, income_statement: Dict, 
                              dividend_history: Dict, shares_outstanding: float) -> Dict[str, Dict[str, float]]:
        """
        Merge balance sheet, income statement, and dividend data by year.
        
        Returns:
            Dictionary with year as key and merged financial data as value
        """
        all_years = set(balance_sheet.keys()) | set(income_statement.keys())
        result = {}
        
        for year in all_years:
            bs_data = balance_sheet.get(year, {})
            is_data = income_statement.get(year, {})
            
            # Extract year from date string (e.g., '2023-09-30' -> '2023')
            year_only = year.split('-')[0] if '-' in year else year
            div_count = dividend_history.get(year_only, 0.0)
            
            result[year] = {
                'revenue': is_data.get('revenue', 0.0),
                'net_income': is_data.get('net_income', 0.0),
                'eps': is_data.get('eps', 0.0),
                'dividend': div_count,
                'total_equity': bs_data.get('total_equity', 0.0),
                'intangible_assets': bs_data.get('intangible_assets', 0.0),
                'goodwill': bs_data.get('goodwill', 0.0),
                'shares_outstanding': shares_outstanding,
                'current_assets': bs_data.get('current_assets', 0.0),
                'current_liabilities': bs_data.get('current_liabilities', 0.0),
                'total_liabilities': bs_data.get('total_liabilities', 0.0),
                'long_term_debt': bs_data.get('long_term_debt', 0.0),
            }
        
        return result

    def _apply_london_fix(self, price: float, eps: float, exchange: str, warnings: List[str]) -> float:
        """
        Apply London Fix for LSE tickers with GBp vs GBP mismatch.
        
        Args:
            price: Current stock price
            eps: Earnings per share
            exchange: Stock exchange
            warnings: List to append warnings to
            
        Returns:
            Adjusted price
        """
        if exchange == "LSE" and eps > 0:
            pe_ratio = price / eps
            if pe_ratio > 500:
                price = price / 100
                warnings.append(f"London Fix Applied: Price divided by 100 (GBp → GBP conversion)")
        
        return price
    
    def _apply_currency_conversion(self, price: float, price_currency: str, 
                                   financials_currency: str, warnings: List[str]) -> float:
        """
        Convert price to financials currency if they differ using live FX rates.
        
        Args:
            price: Current stock price
            price_currency: Currency of the price
            financials_currency: Currency of the financial statements
            warnings: List to append warnings to
            
        Returns:
            Converted price
        """
        if price_currency != financials_currency:
            # Try to get live FX rate
            fx_rate = self.fx_client.get_rate(price_currency, financials_currency)
            
            if fx_rate:
                price = price * fx_rate
                warnings.append(f"Currency Conversion: {price_currency} → {financials_currency} at rate {fx_rate:.4f} (live)")
            else:
                warnings.append(f"Currency Mismatch: {price_currency} vs {financials_currency} (conversion rate unavailable)")
        
        return price
    
    def _validate_data_quality(self, history: Dict[str, Dict[str, float]], warnings: List[str]) -> None:
        """
        Validate data quality and add warnings.
        
        Args:
            history: Financial history data
            warnings: List to append warnings to
        """
        if not history:
            warnings.append("No financial history data available")
            return
        
        # Check for insufficient history
        if len(history) < 10:
            warnings.append(f"Insufficient History Warning: Only {len(history)} years of data available (minimum 10 recommended)")
        
        # Check for missing required fields
        required_fields = ['revenue', 'net_income', 'eps', 'total_equity']
        sorted_years = sorted(history.keys(), reverse=True)
        
        for year in sorted_years:
            year_data = history[year]
            missing_fields = [field for field in required_fields if year_data.get(field, 0.0) == 0.0]
            if missing_fields:
                warnings.append(f"Year {year}: Incomplete data (missing: {', '.join(missing_fields)})")
        
        # Check for data gaps (3+ consecutive years)
        if len(sorted_years) > 3:
            years_as_int = [int(y.split('-')[0]) for y in sorted_years if y.split('-')[0].isdigit()]
            years_as_int.sort(reverse=True)
            
            gap_count = 0
            for i in range(len(years_as_int) - 1):
                if years_as_int[i] - years_as_int[i + 1] > 1:
                    gap_count += 1
                    if gap_count >= 3:
                        warnings.append(f"Data Gap Warning: Multiple consecutive years missing")
                        break
                else:
                    gap_count = 0
    
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
        ceo_name = self._extract_ceo_name(data)
        
        # Check if delisted
        is_delisted = general.get('IsDelisted', False)
        if is_delisted:
            warnings.append("WARNING: Company is delisted")
        
        # Extract shares outstanding
        shares_outstanding = self._extract_shares_outstanding(data)
        if shares_outstanding == 0.0:
            warnings.append("WARNING: Shares outstanding data unavailable")
        
        # Parse financial statements
        balance_sheet = self._parse_balance_sheet(data)
        income_statement = self._parse_income_statement(data)
        dividend_history = self._parse_dividend_history(data)
        
        # Merge financial data
        history = self._merge_financial_data(balance_sheet, income_statement, 
                                             dividend_history, shares_outstanding)
        
        # Get current price
        price = self._get_current_price(data)
        
        # Get most recent EPS for London Fix
        most_recent_eps = 0.0
        if history:
            sorted_years = sorted(history.keys(), reverse=True)
            if sorted_years:
                most_recent_eps = history[sorted_years[0]].get('eps', 0.0)
        
        # Apply London Fix
        price = self._apply_london_fix(price, most_recent_eps, exchange, warnings)
        
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
            price = self._apply_currency_conversion(price, price_currency, financials_currency, warnings)
        
        # Validate data quality
        self._validate_data_quality(history, warnings)
        
        return {
            'ticker': ticker_code,
            'exchange': exchange,
            'currency': currency,
            'price': price,
            'ceo_name': ceo_name,
            'history': history,
            'warnings': warnings
        }
