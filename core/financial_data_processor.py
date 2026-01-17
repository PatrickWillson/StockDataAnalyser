"""
Financial Data Processor

Handles parsing, normalization, and validation of financial data from EODHD API.
Separates data processing logic from API client concerns.
"""

from typing import Dict, Any, List, Optional
from clients.fx_client import FXClient


class FinancialDataProcessor:
    """Processes and normalizes financial data from EODHD API responses."""
    
    def __init__(self, fx_client: Optional[FXClient] = None):
        """
        Initialize processor with optional FX client for currency conversions.
        
        Args:
            fx_client: Optional FX client for currency conversion
        """
        self.fx_client = fx_client or FXClient()
    
    @staticmethod
    def sanitize_value(value: Any) -> float:
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
    
    @staticmethod
    def extract_ceo_name(data: Dict[str, Any]) -> str:
        """Extract CEO name from General.Officers field."""
        try:
            officers = data.get('General', {}).get('Officers', [])
            if officers and len(officers) > 0:
                return officers[0].get('Name', 'N/A')
        except (KeyError, TypeError, IndexError):
            pass
        return 'N/A'
    
    @staticmethod
    def extract_shares_outstanding(data: Dict[str, Any]) -> float:
        """Extract shares outstanding from SharesStats."""
        try:
            shares = data.get('SharesStats', {}).get('SharesOutstanding', 0)
            return FinancialDataProcessor.sanitize_value(shares)
        except (KeyError, TypeError):
            return 0.0
    
    @staticmethod
    def get_current_price(data: Dict[str, Any]) -> float:
        """Extract current price from API data."""
        try:
            # Try to get from Highlights first
            price = data.get('Highlights', {}).get('SharePrice')
            if price:
                return FinancialDataProcessor.sanitize_value(price)
            
            # Fallback to General section
            price = data.get('General', {}).get('SharePrice')
            if price:
                return FinancialDataProcessor.sanitize_value(price)
        except (KeyError, TypeError):
            pass
        
        return 0.0
    
    def parse_balance_sheet(self, data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
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
                    'total_equity': self.sanitize_value(year_data.get('totalStockholderEquity')),
                    'intangible_assets': self.sanitize_value(year_data.get('intangibleAssets')),
                    'goodwill': self.sanitize_value(year_data.get('goodwill')),
                    'current_assets': self.sanitize_value(year_data.get('totalCurrentAssets')),
                    'current_liabilities': self.sanitize_value(year_data.get('totalCurrentLiabilities')),
                    'total_liabilities': self.sanitize_value(year_data.get('totalLiab')),
                    'long_term_debt': self.sanitize_value(year_data.get('longTermDebt')),
                }
        except (KeyError, TypeError, AttributeError):
            pass
        
        return result
    
    def parse_income_statement(self, data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
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
                    'revenue': self.sanitize_value(year_data.get('totalRevenue')),
                    'net_income': self.sanitize_value(year_data.get('netIncome')),
                    'eps': self.sanitize_value(year_data.get('eps')),
                }
        except (KeyError, TypeError, AttributeError):
            pass
        
        return result
    
    def parse_dividend_history(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract dividend history from SplitsDividends.NumberDividendsByYear.
        
        Returns:
            Dictionary with year as key and dividend count as value
        """
        result = {}
        try:
            div_data = data.get('SplitsDividends', {}).get('NumberDividendsByYear', {})
            for year, count in div_data.items():
                result[year] = self.sanitize_value(count)
        except (KeyError, TypeError, AttributeError):
            pass
        
        return result
    
    @staticmethod
    def merge_financial_data(balance_sheet: Dict, income_statement: Dict, 
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

    @staticmethod
    def apply_london_fix(price: float, eps: float, exchange: str, warnings: List[str]) -> float:
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
    
    def apply_currency_conversion(self, price: float, price_currency: str, 
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
    
    @staticmethod
    def validate_data_quality(history: Dict[str, Dict[str, float]], warnings: List[str]) -> None:
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
