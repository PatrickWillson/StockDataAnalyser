"""
Financial Data Processor

Normalisation and validation of provider-neutral fundamentals (core/fundamentals.py): history
rows, dividend history by source priority, TTM dividends, data-quality checks. Reads no vendor
format; data-source adapters (e.g. clients/eodhd_mapper.py) fill CompanyFundamentals.
"""

import logging
from typing import Dict, Any, List, Optional, Sequence
from core.currency_converter import CurrencyConverter
from core.fundamentals import CompanyFundamentals, DividendPayment, number_or_zero
from core.history import fiscal_year, fiscal_year_of_date, has_statement_data, is_dividend_only_year
from core.models import HistoryRow, or_default
from core.price_quote import PriceQuote, same_currency
from config.valuation_config import NORMALIZED_EPS_YEARS
from config.data_quality_config import (ANNUAL_REPORT_MAX_AGE_MONTHS, DAYS_PER_MONTH, MAX_MISSING_HISTORY_YEARS,
                                         MIN_HISTORY_YEARS_RECOMMENDED)

logger = logging.getLogger(__name__)


class FinancialDataProcessor:
    """Processes and normalizes provider-neutral company fundamentals."""
    
    def __init__(self, currency_converter: Optional[CurrencyConverter] = None, debug: bool = False):
        """
        Initialize processor with optional currency converter.
        
        Args:
            currency_converter: Optional currency converter for currency conversions
            debug: Enable debug logging (default: False)
        """
        self.currency_converter = currency_converter
        self.debug = debug
    
    def _log(self, message: str):
        """Print debug message if debug mode is enabled."""
        if self.debug:
            logger.debug(message)
    
    @staticmethod
    def sanitize_value(value: Any) -> float:
        """Convert "NA" strings and null values to 0.0 (core.fundamentals.number_or_zero)."""
        return number_or_zero(value)
    
    @staticmethod
    def get_current_price(quote: Optional[PriceQuote], trading_currency: Optional[str],
                          warnings: Optional[List[str]] = None,
                          source: str = "the fundamentals source") -> tuple[float, Optional[str]]:
        """
        Current price from the yfinance quote, the only price source.
        
        Vendor price fields and market-cap-derived prices are not used: their date, basis and
        unit (pence or pounds) are opaque (GRAHAM_METHODOLOGY §8.1). The quote is only accepted
        when its currency matches the fundamentals source's trading currency (in any unit, e.g.
        GBp for GBX), so a lookup that found another listing is rejected (F7). Without a usable
        price there is no valuation, so the caller stops (no price, no dossier).
        
        Args:
            quote: Current price and its quote currency from yfinance, or None
            trading_currency: The fundamentals source's trading currency
            warnings: List to append the price-source note to
            source: Name of the fundamentals source, for the message
            
        Returns:
            (price, None) when usable, else (0.0, reason)
        """
        if warnings is None:
            warnings = []
        if quote is None or not quote.price or quote.price <= 0:
            return 0.0, "no price from yfinance"
        if not quote.currency:
            return 0.0, "yfinance did not report the quote currency, so the listing cannot be confirmed"
        if not same_currency(quote.currency, trading_currency):
            return 0.0, (f"yfinance quotes {quote.currency} but {source} trades this ticker in "
                         f"{trading_currency}: probably a different listing")
        warnings.append("Price Source: yfinance (primary source)")
        return quote.price, None
    
    def parse_balance_sheet(self, fundamentals: CompanyFundamentals) -> Dict[str, Dict[str, float]]:
        """Annual balance sheet history fields by period end, newest first."""
        rows = fundamentals.annual_balance_sheets
        self._log(f"[DEBUG] Found {len(rows)} periods of Balance Sheet data")
        return {row.period_end: row.as_history_fields() for row in rows}
    
    def parse_income_statement(self, fundamentals: CompanyFundamentals) -> Dict[str, Dict[str, float]]:
        """Annual income statement history fields by period end, newest first."""
        rows = fundamentals.annual_income_statements
        self._log(f"[DEBUG] Found {len(rows)} periods of Income Statement data")
        return {row.period_end: row.as_history_fields() for row in rows}
    
    def parse_quarterly_balance_sheet(self, fundamentals: CompanyFundamentals) -> Dict[str, Dict[str, float]]:
        """
        Periodic (quarterly or semi-annual) balance sheet fields by period end, newest first;
        empty when the source has no periodic data. E.g. {'2025-09-30': {'total_equity': ..., ...}}
        """
        rows = fundamentals.quarterly_balance_sheets
        self._log(f"[DEBUG] Found {len(rows)} periods of quarterly Balance Sheet data")
        return {row.period_end: row.as_history_fields() for row in rows}
    
    def parse_quarterly_income_statement(self, fundamentals: CompanyFundamentals) -> Dict[str, Dict[str, float]]:
        """
        Periodic income statement fields by period end, newest first; empty when the source
        has no periodic data. E.g. {'2025-09-30': {'revenue': ..., 'net_income': ..., 'eps': ...}}
        """
        rows = fundamentals.quarterly_income_statements
        self._log(f"[DEBUG] Found {len(rows)} periods of quarterly Income Statement data")
        return {row.period_end: row.as_history_fields() for row in rows}
    
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
    
    def parse_dividend_history(self, fundamentals: CompanyFundamentals) -> tuple[Dict[str, float], Optional[float], bool, str, Dict[str, str]]:
        """
        Dividend per share for each year, from the best source the fundamentals carry.
        
        Priority Order:
        1. Dividend payments (declared dividends with exact dates)
        2. Annual dividends paid from the cash flow statement / that year's shares
        3. Dividend amounts without currency, then payment counts per year (flagged by is_amount_data=False)
        
        The forward dividend rate is a vendor estimate: it is returned for labelled display only and
        never written into the history (GRAHAM_METHODOLOGY §8.1, F21).
        
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
        is_amount_data = False
        dividend_currency = fundamentals.trading_currency  # Default to stock currency
        forward_rate = fundamentals.forward_dividend_rate
        if forward_rate:
            self._log(f"[DEBUG] Forward Annual Dividend Rate: {forward_rate}")
        
        try:
            # PRIORITY 1: Dividend payments (declared dividends)
            # Dividends belong to the fiscal year they fall in, like the statements beside them
            period_ends = sorted({row.period_end for row in (*fundamentals.annual_income_statements,
                                                             *fundamentals.annual_balance_sheets)})
            payments = fundamentals.dividend_payments
            if payments:
                self._log(f"[DEBUG] Processing {len(payments)} dividend payment records")
                
                # Aggregate dividends by year (sum all payments in each year)
                year_totals = {}
                dividend_currency = payments[0].currency
                for payment in payments:
                    # Payment date if available, otherwise ex-dividend date
                    if payment.date:
                        year = fiscal_year_of_date(payment.date, period_ends)
                        if payment.amount > 0:
                            year_totals[year] = year_totals.get(year, 0.0) + payment.amount
                            self._log(f"[DEBUG] Year {year}: Added dividend {payment.amount:.4f} (from dividend payments)")
                
                if year_totals:
                    result = year_totals
                    is_amount_data = True
                    for year in year_totals.keys():
                        source_indicators[year] = 'dividend_api'
                    self._log(f"[DEBUG] Aggregated dividends for {len(result)} years from dividend payments (in {dividend_currency})")
                    return result, forward_rate, is_amount_data, dividend_currency, source_indicators
            
            # PRIORITY 2: Cash flow dividends paid / that year's shares
            dividends_paid = fundamentals.annual_dividends_paid
            if dividends_paid:
                self._log(f"[DEBUG] Found cash flow dividends paid for {len(dividends_paid)} years")
                self._log(f"[DEBUG] Cash Flow currency: {fundamentals.cash_flow_currency}")
                shares_by_year = fundamentals.shares_by_year
                for period_end, div_amount in dividends_paid.items():
                    year_only = fiscal_year(period_end)
                    shares = shares_by_year.get(year_only, 0)
                    if shares > 0 and div_amount > 0:
                        div_per_share = div_amount / shares
                        result[year_only] = div_per_share
                        source_indicators[year_only] = 'cash_flow'
                        self._log(f"[DEBUG] Year {year_only}: Dividend per share = {div_per_share:.4f} (from {div_amount:,.0f} / {shares:,.0f} shares) [cash_flow]")
                
                if result:
                    is_amount_data = True
                    dividend_currency = fundamentals.cash_flow_currency  # Dividends are in Cash Flow currency
                    self._log(f"[DEBUG] Calculated dividend per share for {len(result)} years from Cash Flow (in {dividend_currency})")
                    return result, forward_rate, is_amount_data, dividend_currency, source_indicators
            
            # Fallback 1: dividend amounts without a stated currency (the trading currency)
            if fundamentals.dividend_amounts:
                self._log(f"[DEBUG] Found {len(fundamentals.dividend_amounts)} dividend amount records")
                year_totals = {}
                for dividend in fundamentals.dividend_amounts:
                    year = fiscal_year_of_date(dividend.date, period_ends)
                    if dividend.amount > 0:
                        year_totals[year] = year_totals.get(year, 0.0) + dividend.amount
                        source_indicators[year] = 'dividends_array'
                
                if year_totals:
                    result = year_totals
                    is_amount_data = True
                    self._log(f"[DEBUG] Aggregated dividend amounts for {len(result)} years from dividend amount records")
                    return result, forward_rate, is_amount_data, dividend_currency, source_indicators
            
            # Fallback 2: payment counts per year (no amounts)
            if fundamentals.dividend_counts_by_year:
                logger.warning("Using dividend payment counts (actual amounts not available from API)")
                for year, count in fundamentals.dividend_counts_by_year.items():
                    result[year] = count
                    source_indicators[year] = 'count'
                self._log(f"[DEBUG] Parsed {len(result)} years of dividend counts")
                return result, forward_rate, is_amount_data, dividend_currency, source_indicators
            
            if not result:
                self._log("[DEBUG] No dividend history could be parsed")
                
        except (KeyError, TypeError, AttributeError) as e:
            self._log(f"[DEBUG] Error parsing dividend history: {e}")
        
        return result, forward_rate, is_amount_data, dividend_currency, source_indicators
    
    def calculate_ttm_dividend(self, dividend_payments: Optional[Sequence[DividendPayment]],
                              reference_date: Optional[str] = None) -> tuple[float, List[Dict[str, Any]], str]:
        """
        Calculate trailing twelve months (TTM) dividend from dividend payment dates.
        
        This provides the actual dividend income stream for investors buying today,
        based on the sum of all dividend payments in the last 12 months.
        
        Args:
            dividend_payments: Declared dividend payments (CompanyFundamentals.dividend_payments)
            reference_date: Reference date for TTM calculation (YYYY-MM-DD format)
                          Defaults to today if not provided
        
        Returns:
            Tuple of (ttm_total, ttm_payments, currency)
            - ttm_total: Sum of dividends paid in last 12 months
            - ttm_payments: List of payment records included in TTM
            - currency: Currency of dividend payments
        """
        from datetime import datetime, timedelta
        
        if not dividend_payments:
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
        ref_str = ref_date.strftime('%Y-%m-%d')
        
        # Currency of the first payment
        currency = dividend_payments[0].currency
        
        # Filter payments in the last 12 months up to the reference date (declared future
        # payments are not trailing dividends)
        ttm_total = 0.0
        ttm_payments = []
        
        for payment in dividend_payments:
            if payment.date and cutoff_str <= payment.date <= ref_str:
                if payment.amount > 0:
                    ttm_total += payment.amount
                    ttm_payments.append({
                        'date': payment.date,
                        'value': payment.amount,
                        'currency': payment.currency
                    })
        
        # Sort payments by date (most recent first)
        ttm_payments.sort(key=lambda x: x['date'], reverse=True)
        
        self._log(f"[DEBUG] TTM Dividend: {ttm_total:.4f} {currency} from {len(ttm_payments)} payments in last 12 months")
        
        return ttm_total, ttm_payments, currency
    
    @staticmethod
    def merge_financial_data(balance_sheet: Dict, income_statement: Dict, 
                            dividend_history: Dict, shares_outstanding: float,
                            outstanding_shares_by_year: Optional[Dict[str, float]] = None,
                            dividends_are_amounts: bool = True) -> Dict[str, Dict[str, float]]:
        """
        Merge balance sheet, income statement, and dividend data by year.
        Calculates EPS from net income if not available.
        
        Args:
            balance_sheet: Balance sheet data by year
            income_statement: Income statement data by year
            dividend_history: Dividend data by year
            shares_outstanding: Default shares outstanding (fallback)
            outstanding_shares_by_year: Optional dict of year-specific shares outstanding
            dividends_are_amounts: False when dividend_history holds payment counts; the payout
                                   ratio is then "N/A" (counts are never used as amounts, F21)
        
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
        
        # Add years from dividend history that have no financial statements yet. A year that has a
        # statement row already gets its dividend there: companies with 52/53-week years end on a
        # different date each year (Apple 2024-09-28, 2023-09-30), so the detected month-day must
        # not create a second, dividend-only row for it
        statement_years = {fiscal_year(year) for year in all_years}
        for div_year in dividend_history.keys():
            # Convert year-only format to date format using detected fiscal year end
            if '-' not in div_year and div_year not in statement_years:
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
            year_only = fiscal_year(year)
            div_amount = dividend_history.get(year_only, 0.0)
            
            if div_amount == 0.0 and year_only not in dividend_history:
                missing_div_count += 1
            
            # Determine this year's shares with priority:
            # 1. Year-specific shares from outstandingShares.annual (most accurate)
            # 2. Balance sheet shares for that year (if non-zero)
            # 3. Fallback: current shares outstanding
            bs_shares = bs_data.get('shares_outstanding', 0.0)
            if outstanding_shares_by_year and year_only in outstanding_shares_by_year:
                final_shares = outstanding_shares_by_year[year_only]
            elif bs_shares > 0:
                final_shares = bs_shares
            else:
                final_shares = shares_outstanding
            
            # Get EPS, or calculate from net income if missing, using the same year's shares
            eps = is_data.get('eps', 0.0)
            net_income = is_data.get('net_income', 0.0)
            
            if eps == 0.0 and net_income != 0.0 and final_shares > 0:
                eps = net_income / final_shares
                calculated_eps_count += 1
            
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
            if eps <= 0 or not dividends_are_amounts:
                # Cannot calculate meaningful payout ratio with negative/zero earnings
                # (even if dividend is 0, the ratio is undefined against a loss), or from counts
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
                'inventory': bs_data.get('inventory'),  # None = not reported (quick ratio N/A)
                'claims_outside_equity': bs_data.get('claims_outside_equity', 0.0),  # minority / redeemable equity (NCAV)
                'preferred_stock': bs_data.get('preferred_stock', 0.0),  # inside equity, ahead of the common (§3.5)
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
        if len(history) < MIN_HISTORY_YEARS_RECOMMENDED:
            warnings.append(f"Insufficient History Warning: Only {len(history)} years of data available "
                            f"(minimum {MIN_HISTORY_YEARS_RECOMMENDED} recommended)")
        
        # Check for missing required fields
        required_fields = ['revenue', 'net_income', 'eps', 'total_equity']
        sorted_years = sorted(history.keys(), reverse=True)
        
        for year in sorted_years:
            year_data = history[year]
            missing_fields = [field for field in required_fields if year_data.get(field, 0.0) == 0.0]
            if missing_fields:
                warnings.append(f"Year {year}: Incomplete data (missing: {', '.join(missing_fields)})")
        
        # Check for data gaps: fiscal years with no annual report inside the reported range
        # (dividend-only placeholder years don't count as reports, so they can't hide a gap)
        report_years = sorted({int(fiscal_year(y)) for y in sorted_years
                               if fiscal_year(y).isdigit() and not is_dividend_only_year(history[y])})
        if len(report_years) >= 2:
            missing_years = sorted(set(range(report_years[0], report_years[-1] + 1)) - set(report_years),
                                   reverse=True)
            if len(missing_years) >= MAX_MISSING_HISTORY_YEARS:
                warnings.append(
                    f"Data Gap Warning: {len(missing_years)} fiscal years missing between "
                    f"{report_years[0]} and {report_years[-1]} ({', '.join(str(y) for y in missing_years)})"
                )

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
            if has_statement_data(year_data):
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
    def extract_3year_eps_data(history: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Extract 3 most recent consecutive fiscal years of EPS data with validation.
        
        This function is used for normalized Graham Number calculations that require
        3-year average EPS to smooth cyclical volatility and prevent bull traps.
        
        Args:
            history: Financial history dictionary (from merge_financial_data)
                    Keys are fiscal year end dates (e.g., '2024-12-31')
                    Values are dicts containing 'eps' and other financial metrics
        
        Returns:
            Dictionary with the following structure:
            {
                'eps_values': [float, float, float],  # Most recent to oldest
                'years': [str, str, str],             # ISO dates (e.g., '2024-12-31')
                'valid': bool,                         # True if all 3 years present and non-null
                'warning': str or None                 # Explanation if invalid
            }
        
        Edge Cases:
            - Fewer than 3 years: valid=False, warning explains insufficient data
            - Null EPS values: valid=False, warning specifies which years
            - "NA" strings: valid=False, warning specifies which years
            - Non-numeric EPS: valid=False, warning specifies which years
        
        Example:
            >>> history = {
            ...     '2024-12-31': {'eps': 4.85},
            ...     '2023-12-31': {'eps': 25.51},
            ...     '2022-12-31': {'eps': 14.40}
            ... }
            >>> result = extract_3year_eps_data(history)
            >>> result['valid']
            True
            >>> result['eps_values']
            [4.85, 25.51, 14.40]
        """
        # Initialize result structure
        result = {
            'eps_values': [],
            'years': [],
            'valid': False,
            'warning': None
        }
        
        # Check if history exists
        if not history:
            result['warning'] = "No financial history available"
            return result
        
        # Sort years in descending order (most recent first), skipping years with no
        # statement data: dividend-only years added by merge_financial_data have revenue,
        # net income and equity all present and 0.0, and EPS 0.0. A break-even year still
        # has revenue or equity, so it is kept.
        sorted_years = [year for year in sorted(history.keys(), reverse=True)
                        if not is_dividend_only_year(history[year])]

        # Check if we have at least 3 years
        if len(sorted_years) < NORMALIZED_EPS_YEARS:
            result['warning'] = f"Insufficient data: Only {len(sorted_years)} years available, need {NORMALIZED_EPS_YEARS} for normalized calculation"
            return result
        
        # Extract first 3 years
        three_years = sorted_years[:NORMALIZED_EPS_YEARS]
        eps_values = []
        missing_years = []
        
        # Validate each year has valid EPS
        for year in three_years:
            eps = or_default(HistoryRow.from_dict(history[year]).eps, None)
            
            # Check for null, "NA" strings, or non-numeric values
            if eps is None or eps == "" or eps == "NA" or eps == "N/A":
                missing_years.append(year)
                eps_values.append(None)
            else:
                # Try to convert to float
                try:
                    eps_float = float(eps)
                    eps_values.append(eps_float)
                except (ValueError, TypeError):
                    missing_years.append(year)
                    eps_values.append(None)
        
        # Check if all 3 years have valid EPS
        if missing_years:
            result['warning'] = f"Missing EPS data for years: {', '.join(missing_years)}"
            result['eps_values'] = eps_values
            result['years'] = three_years
            return result
        
        # All validations passed
        result['eps_values'] = eps_values
        result['years'] = three_years
        result['valid'] = True
        
        return result

    @staticmethod
    def annual_report_age_months(history: Dict[str, Dict], current_date: Optional[Any] = None) -> Optional[float]:
        """Months since the most recent annual report's period end, or None without a dated report."""
        from datetime import datetime
        years = [year for year in sorted(history, reverse=True) if not is_dividend_only_year(history[year])]
        try:
            report_date = datetime.strptime(years[0], '%Y-%m-%d')
        except (IndexError, ValueError):
            return None
        return ((current_date or datetime.now()) - report_date).days / DAYS_PER_MONTH

    @staticmethod
    def check_data_staleness(history: Dict[str, Dict], current_date: Optional[Any] = None) -> Optional[str]:
        """
        Check if most recent annual report is stale (>9 months old).
        
        This function detects if financial data is outdated by comparing the most recent
        fiscal year end date to the current date. Graham methodology emphasizes using
        audited annual data, but data older than 9 months may be too stale for reliable
        valuation decisions.
        
        Args:
            history: Financial history dictionary (from merge_financial_data)
                    Keys are fiscal year end dates (e.g., '2024-12-31')
            current_date: Reference date for staleness check (datetime object)
                         Defaults to datetime.now() if not provided
        
        Returns:
            str: Warning message if data is stale (>9 months old), None otherwise
            
        Edge Cases:
            - Empty history: Returns warning "No financial history available"
            - Invalid date format: Logs error, returns None (graceful degradation)
            - Future date (clock skew): Returns warning "Data date is in the future"
        
        Example:
            >>> from datetime import datetime
            >>> history = {'2024-12-31': {'eps': 4.85}}
            >>> current = datetime(2025, 10, 1)  # 9+ months later
            >>> warning = check_data_staleness(history, current)
            >>> "Potentially Stale Data" in warning
            True
        """
        from datetime import datetime
        
        # Handle empty history
        if not history:
            return "No financial history available"
        
        # Get current date if not provided
        if current_date is None:
            current_date = datetime.now()
        
        # Most recent year with an annual report (dividend-only placeholder years are skipped;
        # they are often in the future and would trigger a false "future date" warning)
        report_years = [year for year in sorted(history.keys(), reverse=True)
                        if not is_dividend_only_year(history[year])]
        if not report_years:
            return "No financial history available"
        most_recent_year = report_years[0]
        
        # Parse year as ISO date (YYYY-MM-DD format)
        try:
            report_date = datetime.strptime(most_recent_year, '%Y-%m-%d')
        except ValueError:
            # Invalid date format - log error and return None (graceful degradation)
            logger.error(f"Invalid date format in financial history: {most_recent_year}")
            return None
        
        # Check for future date (clock skew)
        if report_date > current_date:
            return f"Data date is in the future: Most recent annual report is dated {most_recent_year}"
        
        # Calculate months difference
        # Using 30.44 days per month (365.25 / 12) for accurate calculation
        days_diff = (current_date - report_date).days
        months_diff = days_diff / DAYS_PER_MONTH
        
        # Check if data is stale (>9 months old)
        if months_diff > ANNUAL_REPORT_MAX_AGE_MONTHS:
            return (
                f"Potentially Stale Data: Most recent annual report is from {most_recent_year} "
                f"({int(months_diff)} months old)"
            )
        
        # Data is fresh
        return None

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
            'long_term_debt', 'total_assets', 'total_debt', 'inventory', 'claims_outside_equity',
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
                year_only = fiscal_year(year)
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
