"""
Financial Data Processor

Handles parsing, normalization, and validation of financial data from EODHD API.
Separates data processing logic from API client concerns.
"""

import logging
from typing import Dict, Any, List, Optional
from core.currency_converter import CurrencyConverter

logger = logging.getLogger(__name__)


class FinancialDataProcessor:
    """Processes and normalizes financial data from EODHD API responses."""
    
    def __init__(self, currency_converter: Optional[CurrencyConverter] = None, debug: bool = False):
        """
        Initialize processor with optional currency converter.
        
        Args:
            currency_converter: Optional currency converter for currency conversions
            debug: Enable debug logging (default: False)
        """
        self.currency_converter = currency_converter or CurrencyConverter()
        self.debug = debug
    
    def _log(self, message: str):
        """Print debug message if debug mode is enabled."""
        if self.debug:
            logger.debug(message)
    
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
            officers = data.get('General', {}).get('Officers', {})
            # Officers is a dict with numeric keys ("0", "1", etc.)
            if isinstance(officers, dict) and officers:
                # Try to find CEO by title first
                for key, officer in officers.items():
                    if isinstance(officer, dict):
                        title = officer.get('Title', '').lower()
                        if 'chief executive' in title or 'ceo' in title:
                            return officer.get('Name', 'N/A')
                
                # Fallback: return first officer
                first_officer = officers.get('0', {})
                if isinstance(first_officer, dict):
                    return first_officer.get('Name', 'N/A')
        except (KeyError, TypeError):
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
    def extract_shares_by_year(data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract year-specific shares outstanding from outstandingShares.annual.
        
        Returns:
            Dictionary with year (string) as key and shares as value
        """
        shares_by_year = {}
        try:
            outstanding_shares_data = data.get('outstandingShares', {}).get('annual', {})
            
            if outstanding_shares_data:
                for item in outstanding_shares_data.values():
                    if isinstance(item, dict) and 'date' in item and 'shares' in item:
                        year = str(item['date'])
                        shares = item['shares']
                        if shares and shares > 0:
                            shares_by_year[year] = float(shares)
            
            return shares_by_year
        except (KeyError, TypeError, AttributeError):
            return {}
    
    @staticmethod
    def get_current_price(data: Dict[str, Any], yf_client: Optional[Any] = None,
                         ticker: Optional[str] = None, warnings: Optional[List[str]] = None) -> tuple[float, str, bool]:
        """
        Extract current price with yfinance as primary source.
        
        Priority order:
        1. yfinance (primary - most current)
        2. EODHD Highlights.MarketCapitalization / SharesOutstanding (calculated)
        3. EODHD Highlights.SharePrice
        4. EODHD General.SharePrice
        5. EODHD General.LastPrice
        
        Args:
            data: EODHD API response
            yf_client: Optional yfinance client for price fetching (primary source)
            ticker: Ticker symbol (required for yfinance)
            warnings: List to append warnings to
            
        Returns:
            Tuple of (price, source, is_from_market_cap) where:
                - price: float price value
                - source: 'yfinance', 'EODHD', or 'Missing'
                - is_from_market_cap: True if price was calculated from MarketCap/Shares
            
        Note:
            When is_from_market_cap is True, the price is already in the base currency
            (e.g., GBP for LSE stocks), not in pence (GBX).
        """
        if warnings is None:
            warnings = []
        
        # Try yfinance first (primary source)
        if yf_client and ticker:
            yf_price = yf_client.get_price(ticker)
            if yf_price and yf_price > 0:
                warnings.append("Price Source: yfinance (primary source)")
                return yf_price, 'yfinance', False
        
        # Fall back to EODHD price extraction
        try:
            highlights = data.get('Highlights', {})
            
            # Try to calculate from MarketCapitalization / SharesOutstanding
            # This gives us price in base currency (GBP for LSE, not GBX)
            market_cap = highlights.get('MarketCapitalization')
            shares_stats = data.get('SharesStats', {})
            shares_outstanding = shares_stats.get('SharesOutstanding')
            
            if market_cap and shares_outstanding:
                market_cap = FinancialDataProcessor.sanitize_value(market_cap)
                shares_outstanding = FinancialDataProcessor.sanitize_value(shares_outstanding)
                if market_cap > 0 and shares_outstanding > 0:
                    calculated_price = market_cap / shares_outstanding
                    if yf_client:
                        warnings.append("Price Source: EODHD (calculated from MarketCap / Shares, yfinance unavailable)")
                    else:
                        warnings.append("Price Source: EODHD (calculated from MarketCap / Shares)")
                    return calculated_price, 'EODHD', True  # Mark as from MarketCap
            
            # Try to get from Highlights.SharePrice
            price = highlights.get('SharePrice')
            if price is not None:
                sanitized = FinancialDataProcessor.sanitize_value(price)
                if sanitized > 0:
                    if yf_client:
                        warnings.append("Price Source: EODHD (yfinance unavailable)")
                    return sanitized, 'EODHD', False
            
            # Fallback to General section
            general = data.get('General', {})
            price = general.get('SharePrice')
            if price is not None:
                sanitized = FinancialDataProcessor.sanitize_value(price)
                if sanitized > 0:
                    if yf_client:
                        warnings.append("Price Source: EODHD (yfinance unavailable)")
                    return sanitized, 'EODHD', False
            
            # Try alternative fields
            price = general.get('LastPrice')
            if price is not None:
                sanitized = FinancialDataProcessor.sanitize_value(price)
                if sanitized > 0:
                    if yf_client:
                        warnings.append("Price Source: EODHD (yfinance unavailable)")
                    return sanitized, 'EODHD', False
            
            # All sources failed
            return 0.0, 'Missing', False
            
        except (KeyError, TypeError):
            return 0.0, 'Missing', False
    
    def parse_balance_sheet(self, data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Parse and sort yearly Balance Sheet data by date descending.
        
        Returns:
            Dictionary with year as key and financial data as value
        """
        result = {}
        try:
            yearly_data = data.get('Financials', {}).get('Balance_Sheet', {}).get('yearly', {})
            
            if not yearly_data:
                self._log("[DEBUG] No Balance Sheet yearly data found in API response")
                return result
            
            # Sort by date descending
            sorted_years = sorted(yearly_data.keys(), reverse=True)
            self._log(f"[DEBUG] Found {len(sorted_years)} years of Balance Sheet data")
            
            for year in sorted_years:
                year_data = yearly_data[year]
                result[year] = {
                    'total_equity': self.sanitize_value(year_data.get('totalStockholderEquity')),
                    'intangible_assets': self.sanitize_value(year_data.get('intangibleAssets')),
                    'goodwill': self.sanitize_value(year_data.get('goodWill')),
                    'current_assets': self.sanitize_value(year_data.get('totalCurrentAssets')),
                    'current_liabilities': self.sanitize_value(year_data.get('totalCurrentLiabilities')),
                    'total_liabilities': self.sanitize_value(year_data.get('totalLiab')),
                    'long_term_debt': self.sanitize_value(year_data.get('longTermDebt')),
                }
        except (KeyError, TypeError, AttributeError) as e:
            self._log(f"[DEBUG] Error parsing Balance Sheet: {e}")
        
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
            
            if not yearly_data:
                self._log("[DEBUG] No Income Statement yearly data found in API response")
                return result
            
            # Sort by date descending
            sorted_years = sorted(yearly_data.keys(), reverse=True)
            self._log(f"[DEBUG] Found {len(sorted_years)} years of Income Statement data")
            
            for year in sorted_years:
                year_data = yearly_data[year]
                
                # Try to get EPS directly, or calculate from netIncome / shares
                eps_value = year_data.get('eps')
                if eps_value is None or eps_value == 'NA' or eps_value == '':
                    # Try alternative field names
                    eps_value = year_data.get('basicEPS') or year_data.get('epsBasic')
                    if eps_value:
                        self._log(f"[DEBUG] Year {year}: Using alternative EPS field")
                
                # Use netIncomeFromContinuingOps (Graham's preferred metric) with fallback to netIncome
                # Graham focused on earning power from continuing operations, excluding discontinued ops
                net_income_value = year_data.get('netIncomeFromContinuingOps')
                if net_income_value is None or net_income_value == 'NA' or net_income_value == '':
                    net_income_value = year_data.get('netIncome')
                    if net_income_value:
                        self._log(f"[DEBUG] Year {year}: Using netIncome (netIncomeFromContinuingOps not available)")
                else:
                    self._log(f"[DEBUG] Year {year}: Using netIncomeFromContinuingOps")
                
                result[year] = {
                    'revenue': self.sanitize_value(year_data.get('totalRevenue')),
                    'net_income': self.sanitize_value(net_income_value),
                    'eps': self.sanitize_value(eps_value),
                }
        except (KeyError, TypeError, AttributeError) as e:
            self._log(f"[DEBUG] Error parsing Income Statement: {e}")
        
        return result
    
    def parse_dividend_history(self, data: Dict[str, Any], dividend_api_data: Optional[List[Dict[str, Any]]] = None) -> tuple[Dict[str, float], Optional[float], bool, str, Dict[str, str]]:
        """
        Extract dividend history from EODHD Dividend API (primary) or Cash Flow statements (fallback).
        Returns total dividend amount per share for each year.
        
        Priority Order:
        1. EODHD Dividend API (declared dividends with exact dates)
        2. Cash Flow dividendsPaid (actual cash distributed)
        3. ForwardAnnualDividendRate (for most recent year only if others unavailable)
        
        Args:
            data: Full EODHD fundamentals API response
            dividend_api_data: Optional list of dividend records from EODHD Dividend API
        
        Returns:
            Tuple of (dividend_dict, forward_annual_rate, is_amount_data, dividend_currency, source_indicators)
            - dividend_dict: Dictionary with year as key and dividend per share as value
            - forward_annual_rate: Forward annual dividend rate (if available)
            - is_amount_data: True if values are amounts per share, False if counts
            - dividend_currency: Currency of dividend data
            - source_indicators: Dictionary with year as key and source as value
        """
        result = {}
        source_indicators = {}
        forward_rate = None
        is_amount_data = False
        dividend_currency = data.get('General', {}).get('CurrencyCode', 'USD')  # Default to stock currency
        
        try:
            splits_divs = data.get('SplitsDividends', {})
            
            # Extract forward annual dividend rate
            if splits_divs:
                forward_rate = splits_divs.get('ForwardAnnualDividendRate')
                if forward_rate:
                    forward_rate = self.sanitize_value(forward_rate)
                    self._log(f"[DEBUG] Forward Annual Dividend Rate: {forward_rate}")
            
            # PRIORITY 1: Try EODHD Dividend API data (declared dividends)
            if dividend_api_data and len(dividend_api_data) > 0:
                self._log(f"[DEBUG] Processing {len(dividend_api_data)} dividend records from Dividend API")
                
                # Aggregate dividends by year (sum all payments in each year)
                year_totals = {}
                dividend_currency = dividend_api_data[0].get('currency', dividend_currency)
                
                for div_record in dividend_api_data:
                    # Use payment date if available, otherwise ex-dividend date
                    date_str = div_record.get('paymentDate') or div_record.get('date')
                    if date_str:
                        year = date_str[:4]  # Extract year from YYYY-MM-DD
                        value = self.sanitize_value(div_record.get('value', 0))
                        
                        if value > 0:
                            year_totals[year] = year_totals.get(year, 0.0) + value
                            self._log(f"[DEBUG] Year {year}: Added dividend {value:.4f} (from Dividend API)")
                
                if year_totals:
                    result = year_totals
                    is_amount_data = True
                    for year in year_totals.keys():
                        source_indicators[year] = 'dividend_api'
                    self._log(f"[DEBUG] Aggregated dividends for {len(result)} years from Dividend API (in {dividend_currency})")
                    return result, forward_rate, is_amount_data, dividend_currency, source_indicators
            
            # PRIORITY 2: Try to get dividends from Cash Flow statements (dividendsPaid / shares)
            cash_flow = data.get('Financials', {}).get('Cash_Flow', {}).get('yearly', {})
            outstanding_shares_data = data.get('outstandingShares', {}).get('annual', {})
            
            # Get Cash Flow currency
            cash_flow_currency = data.get('Financials', {}).get('Cash_Flow', {}).get('currency_symbol', 'USD')
            
            if cash_flow:
                self._log(f"[DEBUG] Found Cash Flow data with {len(cash_flow)} years")
                self._log(f"[DEBUG] Cash Flow currency: {cash_flow_currency}")
                
                # Create a lookup for shares by year
                shares_by_year = {}
                if outstanding_shares_data:
                    for item in outstanding_shares_data.values():
                        if isinstance(item, dict) and 'date' in item and 'shares' in item:
                            year = str(item['date'])
                            shares = item['shares']
                            shares_by_year[year] = shares
                
                # Sort years to identify most recent
                sorted_years = sorted(cash_flow.keys(), reverse=True)
                most_recent_year = sorted_years[0].split('-')[0] if sorted_years else None
                
                # Calculate dividend per share from dividendsPaid
                for year, cf_data in cash_flow.items():
                    if isinstance(cf_data, dict):
                        dividends_paid = cf_data.get('dividendsPaid')
                        year_only = year.split('-')[0]
                        
                        if dividends_paid and dividends_paid != 'null':
                            try:
                                div_amount = abs(float(dividends_paid))  # Make positive
                                shares = shares_by_year.get(year_only, 0)
                                
                                if shares > 0 and div_amount > 0:
                                    div_per_share = div_amount / shares
                                    result[year_only] = div_per_share
                                    source_indicators[year_only] = 'cash_flow'
                                    self._log(f"[DEBUG] Year {year_only}: Dividend per share = {div_per_share:.4f} (from {div_amount:,.0f} / {shares:,.0f} shares) [cash_flow]")
                            except (ValueError, TypeError) as e:
                                self._log(f"[DEBUG] Could not parse dividendsPaid for {year}: {e}")
                
                # For most recent year only: use forward rate if cash flow missing
                if most_recent_year and most_recent_year not in result and forward_rate and forward_rate > 0:
                    result[most_recent_year] = forward_rate
                    source_indicators[most_recent_year] = 'forward_rate'
                    self._log(f"[DEBUG] Year {most_recent_year}: Using ForwardAnnualDividendRate = {forward_rate:.4f} [forward_rate]")
                
                if result:
                    is_amount_data = True
                    dividend_currency = cash_flow_currency  # Dividends are in Cash Flow currency
                    self._log(f"[DEBUG] Calculated dividend per share for {len(result)} years from Cash Flow (in {dividend_currency})")
                    return result, forward_rate, is_amount_data, dividend_currency, source_indicators
            
            # Fallback 1: Try Dividends array
            dividend_list = splits_divs.get('Dividends', [])
            
            if dividend_list and isinstance(dividend_list, list) and len(dividend_list) > 0:
                self._log(f"[DEBUG] Found Dividends array with {len(dividend_list)} records")
                
                # Aggregate dividend amounts by year
                year_totals = {}
                for div in dividend_list:
                    if isinstance(div, dict) and 'Date' in div:
                        year = div['Date'][:4]
                        amount = div.get('Value') or div.get('Dividend') or div.get('Amount')
                        if amount:
                            year_totals[year] = year_totals.get(year, 0.0) + float(amount)
                            source_indicators[year] = 'dividends_array'
                
                if year_totals:
                    result = year_totals
                    is_amount_data = True
                    self._log(f"[DEBUG] Aggregated dividend amounts for {len(result)} years from Dividends array")
                    return result, forward_rate, is_amount_data, dividend_currency, source_indicators
            
            # Fallback 2: Use NumberDividendsByYear (counts only)
            div_data = splits_divs.get('NumberDividendsByYear', {})
            
            if isinstance(div_data, dict) and div_data:
                first_key = list(div_data.keys())[0]
                first_value = div_data[first_key]
                
                if isinstance(first_value, dict) and 'Year' in first_value and 'Count' in first_value:
                    logger.warning("Using dividend payment counts (actual amounts not available from API)")
                    self._log(f"[DEBUG] Found indexed dividend count data")
                    for key, value in div_data.items():
                        if isinstance(value, dict) and 'Year' in value and 'Count' in value:
                            year = str(value['Year'])
                            count = value['Count']
                            result[year] = self.sanitize_value(count)
                            source_indicators[year] = 'count'
                    
                    self._log(f"[DEBUG] Parsed {len(result)} years of dividend counts")
                    return result, forward_rate, is_amount_data, dividend_currency, source_indicators
                
                elif all(isinstance(k, str) and k.isdigit() and len(k) == 4 for k in list(div_data.keys())[:3]):
                    logger.warning("Using dividend payment counts (actual amounts not available from API)")
                    self._log(f"[DEBUG] Found year-keyed dividend data")
                    for year, value in div_data.items():
                        result[year] = self.sanitize_value(value)
                        source_indicators[year] = 'count'
                    return result, forward_rate, is_amount_data, dividend_currency, source_indicators
            
            if not result:
                self._log("[DEBUG] No dividend history could be parsed")
                
        except (KeyError, TypeError, AttributeError) as e:
            self._log(f"[DEBUG] Error parsing dividend history: {e}")
        
        return result, forward_rate, is_amount_data, dividend_currency, source_indicators
    
    @staticmethod
    def merge_financial_data(balance_sheet: Dict, income_statement: Dict, 
                            dividend_history: Dict, shares_outstanding: float,
                            outstanding_shares_by_year: Optional[Dict[str, float]] = None) -> Dict[str, Dict[str, float]]:
        """
        Merge balance sheet, income statement, and dividend data by year.
        Calculates EPS from net income if not available.
        
        Args:
            balance_sheet: Balance sheet data by year
            income_statement: Income statement data by year
            dividend_history: Dividend data by year
            shares_outstanding: Default shares outstanding (fallback)
            outstanding_shares_by_year: Optional dict of year-specific shares outstanding
        
        Returns:
            Dictionary with year as key and merged financial data as value
        """
        # Include all years from financial statements AND dividend history
        all_years = set(balance_sheet.keys()) | set(income_statement.keys())
        
        # Detect fiscal year end from existing financial statements
        # This handles companies with non-December fiscal years (e.g., MSFT uses June 30)
        fiscal_year_end = "-12-31"  # Default to December 31
        if balance_sheet or income_statement:
            # Get the most recent date from either source
            sample_dates = list(balance_sheet.keys()) + list(income_statement.keys())
            if sample_dates:
                # Extract month-day from most recent date (e.g., "2025-06-30" -> "-06-30")
                most_recent = sorted(sample_dates, reverse=True)[0]
                if '-' in most_recent:
                    parts = most_recent.split('-')
                    if len(parts) == 3:
                        fiscal_year_end = f"-{parts[1]}-{parts[2]}"
        
        # Add years from dividend history that might not have financial statements yet
        for div_year in dividend_history.keys():
            # Convert year-only format to date format using detected fiscal year end
            if '-' not in div_year:
                div_year_date = f"{div_year}{fiscal_year_end}"
                all_years.add(div_year_date)
        
        result = {}
        
        # Count missing dividends and calculated EPS
        missing_div_count = 0
        calculated_eps_count = 0
        
        for year in all_years:
            bs_data = balance_sheet.get(year, {})
            is_data = income_statement.get(year, {})
            
            # Extract year from date string (e.g., '2023-09-30' -> '2023')
            year_only = year.split('-')[0] if '-' in year else year
            div_amount = dividend_history.get(year_only, 0.0)
            
            if div_amount == 0.0 and year_only not in dividend_history:
                missing_div_count += 1
            
            # Get year-specific shares if available, otherwise use default
            year_shares = shares_outstanding
            if outstanding_shares_by_year and year_only in outstanding_shares_by_year:
                year_shares = outstanding_shares_by_year[year_only]
            
            # Get EPS, or calculate from net income if missing
            eps = is_data.get('eps', 0.0)
            net_income = is_data.get('net_income', 0.0)
            
            # If EPS is missing but we have net income and shares, calculate it
            if eps == 0.0 and net_income != 0.0 and year_shares > 0:
                eps = net_income / year_shares
                calculated_eps_count += 1
            
            result[year] = {
                'revenue': is_data.get('revenue', 0.0),
                'net_income': net_income,
                'eps': eps,
                'dividend': div_amount,
                'total_equity': bs_data.get('total_equity', 0.0),
                'intangible_assets': bs_data.get('intangible_assets', 0.0),
                'goodwill': bs_data.get('goodwill', 0.0),
                'shares_outstanding': year_shares,  # Use year-specific shares
                'current_assets': bs_data.get('current_assets', 0.0),
                'current_liabilities': bs_data.get('current_liabilities', 0.0),
                'total_liabilities': bs_data.get('total_liabilities', 0.0),
                'long_term_debt': bs_data.get('long_term_debt', 0.0),
            }
        
        return result

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
