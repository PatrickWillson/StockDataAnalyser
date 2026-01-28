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
                
                # Extract debt components for total debt calculation
                long_term_debt = self.sanitize_value(year_data.get('longTermDebt', 0))
                short_term_debt = self.sanitize_value(year_data.get('shortTermDebt', 0))
                total_debt_precalc = self.sanitize_value(year_data.get('shortLongTermDebtTotal', 0))
                
                # Calculate total debt (prefer components, fallback to precalculated)
                # Graham emphasized tracking total debt to distinguish companies that grow
                # through retained earnings vs leverage
                if long_term_debt > 0 or short_term_debt > 0:
                    total_debt = long_term_debt + short_term_debt
                elif total_debt_precalc > 0:
                    total_debt = total_debt_precalc
                else:
                    total_debt = 0
                
                # Extract shares outstanding with fallback chain
                # EODHD sometimes uses different field names for share count
                shares_outstanding = (
                    year_data.get('commonStockSharesOutstanding') or
                    year_data.get('weightedAverageShsOut') or
                    year_data.get('weightedAverageShsOutDil') or
                    0
                )
                shares_outstanding = self.sanitize_value(shares_outstanding)
                
                result[year] = {
                    'total_equity': self.sanitize_value(year_data.get('totalStockholderEquity')),
                    'intangible_assets': self.sanitize_value(year_data.get('intangibleAssets')),
                    'goodwill': self.sanitize_value(year_data.get('goodWill')),
                    'current_assets': self.sanitize_value(year_data.get('totalCurrentAssets')),
                    'current_liabilities': self.sanitize_value(year_data.get('totalCurrentLiabilities')),
                    'total_liabilities': self.sanitize_value(year_data.get('totalLiab')),
                    'long_term_debt': long_term_debt,
                    'total_assets': self.sanitize_value(year_data.get('totalAssets')),
                    'total_debt': total_debt,  # NEW: Total debt for Graham trend analysis
                    'shares_outstanding': shares_outstanding,  # NEW: Track dilution/buybacks
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
    
    def parse_quarterly_balance_sheet(self, data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Parse quarterly balance sheet data from EODHD API.
        
        Extracts quarterly balance sheet data from Financials.Balance_Sheet.quarterly,
        sorts periods by date descending (most recent first), and sanitizes all values.
        
        Args:
            data: Full EODHD API response
            
        Returns:
            Dictionary with date as key (e.g., '2025-09-30') and financial data as value.
            Returns empty dict if quarterly data is not available.
            
        Example:
            {
                '2025-09-30': {
                    'total_equity': 363076000000.0,
                    'intangible_assets': 21236000000.0,
                    'goodwill': 119497000000.0,
                    'current_assets': 189066000000.0,
                    'total_liabilities': 273275000000.0,
                    'shares_outstanding': 7466000000.0,
                    ...
                },
                '2025-06-30': { ... },
                ...
            }
        """
        result = {}
        try:
            quarterly_data = data.get('Financials', {}).get('Balance_Sheet', {}).get('quarterly', {})
            
            if not quarterly_data:
                self._log("[DEBUG] No Balance Sheet quarterly data found in API response")
                return result
            
            # Sort by date descending (most recent first)
            sorted_periods = sorted(quarterly_data.keys(), reverse=True)
            self._log(f"[DEBUG] Found {len(sorted_periods)} quarters of Balance Sheet data")
            
            for period in sorted_periods:
                period_data = quarterly_data[period]
                
                # Extract debt components for total debt calculation
                long_term_debt = self.sanitize_value(period_data.get('longTermDebt', 0))
                short_term_debt = self.sanitize_value(period_data.get('shortTermDebt', 0))
                total_debt_precalc = self.sanitize_value(period_data.get('shortLongTermDebtTotal', 0))
                
                # Calculate total debt (prefer components, fallback to precalculated)
                if long_term_debt > 0 or short_term_debt > 0:
                    total_debt = long_term_debt + short_term_debt
                elif total_debt_precalc > 0:
                    total_debt = total_debt_precalc
                else:
                    total_debt = 0
                
                # Extract shares outstanding with fallback chain
                shares_outstanding = (
                    period_data.get('commonStockSharesOutstanding') or
                    period_data.get('weightedAverageShsOut') or
                    period_data.get('weightedAverageShsOutDil') or
                    0
                )
                shares_outstanding = self.sanitize_value(shares_outstanding)
                
                result[period] = {
                    'total_equity': self.sanitize_value(period_data.get('totalStockholderEquity')),
                    'intangible_assets': self.sanitize_value(period_data.get('intangibleAssets')),
                    'goodwill': self.sanitize_value(period_data.get('goodWill')),
                    'current_assets': self.sanitize_value(period_data.get('totalCurrentAssets')),
                    'current_liabilities': self.sanitize_value(period_data.get('totalCurrentLiabilities')),
                    'total_liabilities': self.sanitize_value(period_data.get('totalLiab')),
                    'long_term_debt': long_term_debt,
                    'total_assets': self.sanitize_value(period_data.get('totalAssets')),
                    'total_debt': total_debt,
                    'shares_outstanding': shares_outstanding,
                }
                
                self._log(f"[DEBUG] Period {period}: Equity={result[period]['total_equity']:,.0f}, "
                         f"Shares={result[period]['shares_outstanding']:,.0f}")
        
        except (KeyError, TypeError, AttributeError) as e:
            self._log(f"[DEBUG] Error parsing quarterly Balance Sheet: {e}")
        
        return result
    
    def parse_quarterly_income_statement(self, data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Parse quarterly income statement data from EODHD API.
        
        Extracts quarterly income statement data from Financials.Income_Statement.quarterly,
        sorts periods by date descending (most recent first), and sanitizes all values.
        
        Args:
            data: Full EODHD API response
            
        Returns:
            Dictionary with date as key (e.g., '2025-09-30') and financial data as value.
            Returns empty dict if quarterly data is not available.
            
        Example:
            {
                '2025-09-30': {
                    'revenue': 77673000000.0,
                    'net_income': 27747000000.0,
                    'eps': 3.72,
                    ...
                },
                '2025-06-30': { ... },
                ...
            }
        """
        result = {}
        try:
            quarterly_data = data.get('Financials', {}).get('Income_Statement', {}).get('quarterly', {})
            
            if not quarterly_data:
                self._log("[DEBUG] No Income Statement quarterly data found in API response")
                return result
            
            # Sort by date descending (most recent first)
            sorted_periods = sorted(quarterly_data.keys(), reverse=True)
            self._log(f"[DEBUG] Found {len(sorted_periods)} quarters of Income Statement data")
            
            for period in sorted_periods:
                period_data = quarterly_data[period]
                
                # Try to get EPS directly, or calculate from netIncome / shares
                eps_value = period_data.get('eps')
                if eps_value is None or eps_value == 'NA' or eps_value == '':
                    # Try alternative field names
                    eps_value = period_data.get('basicEPS') or period_data.get('epsBasic')
                    if eps_value:
                        self._log(f"[DEBUG] Period {period}: Using alternative EPS field")
                
                # Use netIncomeFromContinuingOps (Graham's preferred metric) with fallback to netIncome
                # Graham focused on earning power from continuing operations, excluding discontinued ops
                net_income_value = period_data.get('netIncomeFromContinuingOps')
                if net_income_value is None or net_income_value == 'NA' or net_income_value == '':
                    net_income_value = period_data.get('netIncome')
                    if net_income_value:
                        self._log(f"[DEBUG] Period {period}: Using netIncome (netIncomeFromContinuingOps not available)")
                else:
                    self._log(f"[DEBUG] Period {period}: Using netIncomeFromContinuingOps")
                
                result[period] = {
                    'revenue': self.sanitize_value(period_data.get('totalRevenue')),
                    'net_income': self.sanitize_value(net_income_value),
                    'eps': self.sanitize_value(eps_value),
                }
                
                self._log(f"[DEBUG] Period {period}: Revenue={result[period]['revenue']:,.0f}, "
                         f"Net Income={result[period]['net_income']:,.0f}, "
                         f"EPS={result[period]['eps']:.2f}")
        
        except (KeyError, TypeError, AttributeError) as e:
            self._log(f"[DEBUG] Error parsing quarterly Income Statement: {e}")
        
        return result
    
    def merge_quarterly_data(self, balance_sheet: Dict[str, Dict[str, float]], 
                            income_statement: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        Merge quarterly balance sheet and income statement data.
        
        This method combines the outputs from parse_quarterly_balance_sheet and
        parse_quarterly_income_statement into a single structure for the TTMCalculator.
        
        Args:
            balance_sheet: Quarterly balance sheet data (from parse_quarterly_balance_sheet)
            income_statement: Quarterly income statement data (from parse_quarterly_income_statement)
            
        Returns:
            Dictionary with 'balance_sheet' and 'income_statement' keys.
            Returns empty dicts if data is missing.
            
        Example:
            {
                'balance_sheet': {
                    '2025-09-30': {'total_equity': 363076000000.0, ...},
                    '2025-06-30': {'total_equity': 350000000000.0, ...},
                    ...
                },
                'income_statement': {
                    '2025-09-30': {'revenue': 77673000000.0, ...},
                    '2025-06-30': {'revenue': 75000000000.0, ...},
                    ...
                }
            }
        """
        # Handle missing data gracefully - return empty dicts
        if balance_sheet is None:
            balance_sheet = {}
        if income_statement is None:
            income_statement = {}
        
        self._log(f"[DEBUG] Merging quarterly data: {len(balance_sheet)} balance sheet periods, "
                 f"{len(income_statement)} income statement periods")
        
        return {
            'balance_sheet': balance_sheet,
            'income_statement': income_statement
        }
    
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
    
    def calculate_ttm_dividend(self, dividend_api_data: Optional[List[Dict[str, Any]]], 
                              reference_date: Optional[str] = None) -> tuple[float, List[Dict[str, Any]], str]:
        """
        Calculate trailing twelve months (TTM) dividend from Dividend API payment dates.
        
        This provides the actual dividend income stream for investors buying today,
        based on the sum of all dividend payments in the last 12 months.
        
        Args:
            dividend_api_data: List of dividend records from EODHD Dividend API
            reference_date: Reference date for TTM calculation (YYYY-MM-DD format)
                          Defaults to today if not provided
        
        Returns:
            Tuple of (ttm_total, ttm_payments, currency)
            - ttm_total: Sum of dividends paid in last 12 months
            - ttm_payments: List of payment records included in TTM
            - currency: Currency of dividend payments
        """
        from datetime import datetime, timedelta
        
        if not dividend_api_data or len(dividend_api_data) == 0:
            return 0.0, [], 'USD'
        
        # Determine reference date (default to today)
        if reference_date:
            try:
                ref_date = datetime.strptime(reference_date, '%Y-%m-%d')
            except ValueError:
                ref_date = datetime.now()
        else:
            ref_date = datetime.now()
        
        # Calculate cutoff date (12 months ago)
        cutoff_date = ref_date - timedelta(days=365)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        # Extract currency from first record
        currency = dividend_api_data[0].get('currency', 'USD')
        
        # Filter payments in last 12 months
        ttm_total = 0.0
        ttm_payments = []
        
        for div in dividend_api_data:
            # Use payment date if available, otherwise ex-dividend date
            payment_date_str = div.get('paymentDate') or div.get('date')
            
            if payment_date_str and payment_date_str >= cutoff_str:
                value = self.sanitize_value(div.get('value', 0))
                if value > 0:
                    ttm_total += value
                    ttm_payments.append({
                        'date': payment_date_str,
                        'value': value,
                        'currency': div.get('currency', currency)
                    })
        
        # Sort payments by date (most recent first)
        ttm_payments.sort(key=lambda x: x['date'], reverse=True)
        
        self._log(f"[DEBUG] TTM Dividend: {ttm_total:.4f} {currency} from {len(ttm_payments)} payments in last 12 months")
        
        return ttm_total, ttm_payments, currency
    
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
            
            # Determine final shares with priority:
            # 1. Year-specific shares from outstandingShares.annual (most accurate)
            # 2. Balance sheet shares (if non-zero)
            # 3. Fallback shares
            bs_shares = bs_data.get('shares_outstanding', 0.0)
            if outstanding_shares_by_year and year_only in outstanding_shares_by_year:
                final_shares = outstanding_shares_by_year[year_only]
            elif bs_shares > 0:
                final_shares = bs_shares
            else:
                final_shares = shares_outstanding
            
            # Calculate Working Capital Per Share (WCPS)
            # Formula: (Current Assets - Current Liabilities) / Shares Outstanding
            current_assets = bs_data.get('current_assets', 0.0)
            current_liabilities = bs_data.get('current_liabilities', 0.0)
            
            # Use Decimal for precise calculation
            from decimal import Decimal, ROUND_HALF_UP
            
            if final_shares > 0:
                # Convert to Decimal via string to avoid float artifacts
                ca_dec = Decimal(str(current_assets))
                cl_dec = Decimal(str(current_liabilities))
                shares_dec = Decimal(str(final_shares))
                
                # Calculate working capital
                working_capital = ca_dec - cl_dec
                
                # Calculate WCPS
                wcps_dec = working_capital / shares_dec
                
                # Round to 2 decimal places
                wcps_rounded = wcps_dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                wcps = float(wcps_rounded)
            else:
                # Cannot calculate WCPS without shares outstanding
                wcps = "N/A"
            
            # Calculate Payout Ratio
            # Formula: (Dividend / EPS) × 100
            # Return "N/A" if EPS ≤ 0, "0.0%" if dividend = 0
            if eps <= 0:
                # Cannot calculate meaningful payout ratio with negative/zero earnings
                # Even if dividend is 0, the ratio is undefined against a loss
                payout_ratio = "N/A"
            elif div_amount == 0:
                # No dividend paid, but earnings are positive
                payout_ratio = "0.0%"
            else:
                # Normal case: positive earnings and dividend
                # Convert to Decimal for precise calculation
                div_dec = Decimal(str(div_amount))
                eps_dec = Decimal(str(eps))
                
                # Calculate payout ratio as percentage
                payout_ratio_dec = (div_dec / eps_dec) * Decimal('100')
                
                # Round to 1 decimal place
                payout_ratio_rounded = payout_ratio_dec.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                payout_ratio = f"{float(payout_ratio_rounded):.1f}%"
            
            result[year] = {
                'revenue': is_data.get('revenue', 0.0),
                'net_income': net_income,
                'eps': eps,
                'dividend': div_amount,
                'total_equity': bs_data.get('total_equity', 0.0),
                'intangible_assets': bs_data.get('intangible_assets', 0.0),
                'goodwill': bs_data.get('goodwill', 0.0),
                'shares_outstanding': final_shares,
                'current_assets': current_assets,
                'current_liabilities': current_liabilities,
                'total_liabilities': bs_data.get('total_liabilities', 0.0),
                'long_term_debt': bs_data.get('long_term_debt', 0.0),
                'total_assets': bs_data.get('total_assets', 0.0),
                'total_debt': bs_data.get('total_debt', 0.0),  # NEW: Total debt for Graham analysis
                'wcps': wcps,  # NEW: Working Capital Per Share
                'payout_ratio': payout_ratio,  # NEW: Payout Ratio
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

    @staticmethod
    def calculate_profitability_metrics(
        history: Dict[str, Dict[str, float]], 
        debug: bool = False
    ) -> tuple[float, float, float, Optional[str]]:
        """
        Calculate profitability metrics from most recent annual data.
        
        Uses the same "most recent year" logic as P/E, P/B, and BVPS calculations:
        - Find most recent year with financial data (revenue > 0 OR net_income != 0 OR total_equity > 0)
        - Extract net_income, total_equity, total_assets, revenue from that year
        - Calculate ROE, ROA, Profit Margin
        - Return 0.0 for any metric that cannot be calculated (missing data or zero denominator)
        
        Args:
            history: Financial history dictionary (from merge_financial_data)
            debug: Enable debug logging
            
        Returns:
            Tuple of (roe, roa, profit_margin, calculation_year)
            - roe: Return on Equity (0.0 to 1.0, or 0.0 if cannot calculate)
            - roa: Return on Assets (0.0 to 1.0, or 0.0 if cannot calculate)
            - profit_margin: Profit Margin (0.0 to 1.0, or 0.0 if cannot calculate)
            - calculation_year: Fiscal year used (e.g., "2025-06-30"), or None if no data
        """
        if not history:
            if debug:
                logger.debug("No financial history available for profitability calculations")
            return (0.0, 0.0, 0.0, None)
        
        # Find most recent year with financial data (same logic as P/B calculation)
        sorted_years = sorted(history.keys(), reverse=True)
        most_recent_year = None
        
        for year in sorted_years:
            year_data = history[year]
            revenue = year_data.get('revenue', 0.0)
            net_income = year_data.get('net_income', 0.0)
            total_equity = year_data.get('total_equity', 0.0)
            
            # Check if this year has any financial data
            if revenue > 0 or net_income != 0 or total_equity > 0:
                most_recent_year = year
                break
        
        if not most_recent_year:
            if debug:
                logger.debug("No complete annual financial data available for profitability calculations")
            return (0.0, 0.0, 0.0, None)
        
        # Extract values from most recent year
        year_data = history[most_recent_year]
        net_income = year_data.get('net_income', 0.0)
        total_equity = year_data.get('total_equity', 0.0)
        total_assets = year_data.get('total_assets', 0.0)
        revenue = year_data.get('revenue', 0.0)
        
        # Calculate ROE with zero-division protection
        if total_equity > 0:
            roe = net_income / total_equity
        else:
            roe = 0.0
            if debug:
                logger.debug("ROE cannot be calculated - total_equity is 0")
        
        # Calculate ROA with zero-division protection
        if total_assets > 0:
            roa = net_income / total_assets
        else:
            roa = 0.0
            if debug:
                logger.debug("ROA cannot be calculated - total_assets is 0")
        
        # Calculate Profit Margin with zero-division protection
        if revenue > 0:
            profit_margin = net_income / revenue
        else:
            profit_margin = 0.0
            if debug:
                logger.debug("Profit Margin cannot be calculated - revenue is 0")
        
        if debug:
            logger.debug(f"Calculated profitability metrics from {most_recent_year}:")
            logger.debug(f"  Net Income: ${net_income:,.0f}")
            logger.debug(f"  Total Equity: ${total_equity:,.0f}")
            logger.debug(f"  Total Assets: ${total_assets:,.0f}")
            logger.debug(f"  Revenue: ${revenue:,.0f}")
            logger.debug(f"  ROE: {roe*100:.2f}%")
            logger.debug(f"  ROA: {roa*100:.2f}%")
            logger.debug(f"  Profit Margin: {profit_margin*100:.2f}%")
        
        return (roe, roa, profit_margin, most_recent_year)

    @staticmethod
    def apply_historical_fx_rates(
        history: Dict[str, Dict[str, float]],
        fx_rates_by_date: Dict[str, Optional[float]],
        from_currency: str,
        to_currency: str,
        current_fx_rate: float
    ) -> tuple[Dict[str, Dict[str, float]], List[str]]:
        """
        Apply historical FX rates to financial history data.
        
        Converts all monetary values in history dict using date-matched FX rates.
        Falls back to current_fx_rate for dates without historical rates.
        
        Args:
            history: Financial history dict (year → metrics)
            fx_rates_by_date: Dict mapping fiscal year end dates to FX rates
            from_currency: Source currency
            to_currency: Target currency
            current_fx_rate: Fallback rate for missing historical rates
            
        Returns:
            Tuple of (converted_history, warnings)
            - converted_history: History with all values converted
            - warnings: List of warnings for fallback usage
            
        Example:
            >>> history = {'2024-06-30': {'revenue': 1000, 'net_income': 100}}
            >>> fx_rates = {'2024-06-30': 1.25}
            >>> converted, warnings = apply_historical_fx_rates(
            ...     history, fx_rates, 'GBP', 'USD', 1.30
            ... )
            >>> converted['2024-06-30']['revenue']
            1250.0
        """
        # Define monetary fields that need conversion
        MONETARY_FIELDS = [
            'revenue', 'net_income', 'eps', 'dividend',
            'total_equity', 'intangible_assets', 'goodwill',
            'current_assets', 'current_liabilities', 'total_liabilities',
            'long_term_debt', 'total_assets', 'total_debt',
            'year_end_price'
        ]
        
        converted_history = {}
        warnings = []
        fallback_years = []
        
        for year, data in history.items():
            # Get FX rate for this year (use historical if available, otherwise current)
            fx_rate = fx_rates_by_date.get(year)
            
            if fx_rate is None:
                # No historical rate available, use current rate as fallback
                fx_rate = current_fx_rate
                year_only = year.split('-')[0] if '-' in year else year
                fallback_years.append(year_only)
            
            # Convert all monetary fields
            converted_data = {}
            for field, value in data.items():
                if field in MONETARY_FIELDS and value != 0 and value is not None:
                    # Convert monetary value
                    converted_data[field] = value * fx_rate
                else:
                    # Keep non-monetary fields unchanged
                    converted_data[field] = value
            
            converted_history[year] = converted_data
        
        # Generate warnings for fallback usage
        if fallback_years:
            unique_years = sorted(set(fallback_years))
            warnings.append(
                f"Historical FX rates unavailable for years: {', '.join(unique_years)}. "
                f"Used current rate {current_fx_rate:.4f} as fallback."
            )
        
        return converted_history, warnings
