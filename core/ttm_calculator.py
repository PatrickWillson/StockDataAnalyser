"""
TTM Calculator - Trailing Twelve Months calculations for Graham methodology.

This module calculates TTM financial metrics and Graham valuations using
the most recent 12 months of periodic data (quarterly or semi-annual).

Key Features:
- Automatic detection of reporting frequency (quarterly vs semi-annual)
- Income statement items summed over periods
- Balance sheet items use most recent period
- Graceful degradation when data is unavailable
"""

import logging
from datetime import datetime
from typing import Dict, Union, List, Any, Optional

# Configure module-level logger
logger = logging.getLogger(__name__)


class TTMCalculator:
    """
    Calculates Trailing Twelve Months (TTM) financial metrics and Graham valuations.
    
    Supports both quarterly and semi-annual reporting frequencies.
    Handles edge cases gracefully with warnings.
    """
    
    def __init__(self, quarterly_data: Dict[str, Any], price: float, currency: str,
                 original_currency: Optional[str] = None, fx_rate: Optional[float] = None):
        """
        Initialize TTM calculator.
        
        Args:
            quarterly_data: Dict with 'balance_sheet' and 'income_statement' keys
                           Each contains date-keyed financial data
            price: Current stock price, already normalised to the unified currency by the client
                   (London Fix / GBX handling happens once, upstream)
            currency: Unified currency for all calculations
            original_currency: Original currency of quarterly data (before conversion)
            fx_rate: FX rate used for conversion (original → unified)
        """
        self.quarterly_data = quarterly_data
        self.currency = currency
        self.original_currency = original_currency
        self.fx_rate = fx_rate
        self.warnings: List[str] = []
        
        self.price = price
        
        # Apply currency conversion if needed
        if original_currency and currency and original_currency != currency:
            if fx_rate and fx_rate > 0:
                self._apply_currency_conversion(fx_rate)
                self.warnings.append(
                    f"TTM Currency Conversion: {original_currency} → {currency} at rate {fx_rate:.4f}"
                )
            else:
                self.warnings.append(
                    f"TTM Currency Conversion: Unable to convert {original_currency} → {currency} (rate unavailable)"
                )
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string to datetime object.
        
        Args:
            date_str: Date string in format 'YYYY-MM-DD'
            
        Returns:
            datetime object or None if parsing fails
        """
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            return None
    
    def _apply_currency_conversion(self, fx_rate: float) -> None:
        """
        Apply currency conversion to all monetary values in quarterly data.
        
        Converts all monetary fields (revenue, net income, equity, assets, liabilities)
        by multiplying by the FX rate.
        
        Args:
            fx_rate: Exchange rate to apply (original_currency → unified_currency)
        """
        # Monetary fields in income statement
        income_monetary_fields = ['revenue', 'net_income']
        
        # Monetary fields in balance sheet
        balance_monetary_fields = [
            'total_equity', 'intangible_assets', 'goodwill',
            'current_assets', 'total_liabilities'
        ]
        
        # Convert income statement data
        income_statement = self.quarterly_data.get('income_statement', {})
        for period_date, period_data in income_statement.items():
            for field in income_monetary_fields:
                if field in period_data:
                    period_data[field] = period_data[field] * fx_rate
        
        # Convert balance sheet data
        balance_sheet = self.quarterly_data.get('balance_sheet', {})
        for period_date, period_data in balance_sheet.items():
            for field in balance_monetary_fields:
                if field in period_data:
                    period_data[field] = period_data[field] * fx_rate
    
    def _calculate_interval_days(self, date1_str: str, date2_str: str) -> Optional[int]:
        """
        Calculate number of days between two dates.
        
        Args:
            date1_str: First date string (more recent)
            date2_str: Second date string (older)
            
        Returns:
            Number of days between dates, or None if parsing fails
        """
        date1 = self._parse_date(date1_str)
        date2 = self._parse_date(date2_str)
        
        if date1 is None or date2 is None:
            return None
        
        delta = date1 - date2
        return abs(delta.days)
    
    def detect_reporting_frequency(self) -> str:
        """
        Detect reporting frequency by analyzing period intervals.
        
        Algorithm:
        - Calculate average interval between consecutive periods
        - Uses only the most recent periods to detect current reporting pattern
        - ~90 days (±15 days) → Quarterly
        - ~180 days (±30 days) → Semi-annual
        - Otherwise → Irregular
        
        Returns:
            'quarterly', 'semi-annual', or 'irregular'
        """
        logger.debug("Frequency detection starting")
        
        # Get income statement periods (should match balance sheet)
        income_statement = self.quarterly_data.get('income_statement', {})
        
        if not income_statement:
            logger.debug("Frequency detection: No periodic data available")
            self.warnings.append("TTM Analysis: No periodic data available")
            return 'irregular'
        
        # Get sorted dates (most recent first)
        dates = sorted(income_statement.keys(), reverse=True)
        logger.debug(f"Frequency detection: {len(dates)} total periods available")
        
        if len(dates) < 2:
            logger.debug("Frequency detection: Insufficient periods (< 2)")
            self.warnings.append("TTM Analysis: Insufficient periods to determine frequency")
            return 'irregular'
        
        # Use only the most recent periods to detect current reporting pattern
        # This handles companies that switched from quarterly to semi-annual (or vice versa)
        # Use up to 5 most recent periods (4 intervals) for detection
        recent_dates = dates[:min(5, len(dates))]
        logger.debug(f"Frequency detection: Using {len(recent_dates)} most recent periods: {recent_dates}")
        
        # Calculate intervals between consecutive periods
        intervals = []
        for i in range(len(recent_dates) - 1):
            interval = self._calculate_interval_days(recent_dates[i], recent_dates[i + 1])
            if interval is not None:
                intervals.append(interval)
                logger.debug(f"Frequency detection: Interval {i+1}: {recent_dates[i]} to {recent_dates[i+1]} = {interval} days")
        
        if not intervals:
            logger.debug("Frequency detection: Unable to calculate any intervals")
            self.warnings.append("TTM Analysis: Unable to calculate period intervals")
            return 'irregular'
        
        # Calculate average interval
        avg_interval = sum(intervals) / len(intervals)
        logger.debug(f"Frequency detection: Average interval = {avg_interval:.1f} days (from {len(intervals)} intervals)")
        
        # Classify based on average interval
        # Quarterly: ~90 days (±15 days) → 75-105 days
        if 75 <= avg_interval <= 105:
            logger.debug("Frequency detection: Classified as QUARTERLY (75-105 days)")
            return 'quarterly'
        
        # Semi-annual: ~180 days (±30 days) → 150-210 days
        if 150 <= avg_interval <= 210:
            logger.debug("Frequency detection: Classified as SEMI-ANNUAL (150-210 days)")
            return 'semi-annual'
        
        # Irregular pattern
        logger.debug(f"Frequency detection: Classified as IRREGULAR (avg {avg_interval:.1f} days outside valid ranges)")
        self.warnings.append(
            f"TTM Analysis: Irregular reporting pattern detected (avg interval: {avg_interval:.0f} days)"
        )
        return 'irregular'
    
    def _detect_data_gaps(self, periods: List[str], frequency: str) -> bool:
        """
        Detect if there are gaps in the period sequence.
        
        A gap is detected when the interval between consecutive periods
        significantly deviates from the expected interval for the frequency.
        
        Args:
            periods: List of period dates in descending order
            frequency: Reporting frequency ('quarterly' or 'semi-annual')
            
        Returns:
            True if gaps detected, False otherwise
        """
        # Log method entry with parameters
        logger.debug(f"Gap detection starting: frequency={frequency}, periods={periods}")
        
        if len(periods) < 2:
            logger.debug("Gap detection skipped: fewer than 2 periods")
            return False
        
        # Expected interval and tolerance based on frequency
        if frequency == 'quarterly':
            expected_interval = 90
            tolerance = 30  # Allow ±30 days for quarterly (more lenient than detection)
        else:  # semi-annual
            expected_interval = 180
            tolerance = 45  # Allow ±45 days for semi-annual
        
        # Calculate and log threshold
        threshold = expected_interval + tolerance
        logger.debug(f"Gap detection thresholds: expected_interval={expected_interval}, tolerance={tolerance}, threshold={threshold}")
        
        # Check each interval between consecutive periods
        missing_periods = []
        for i in range(len(periods) - 1):
            interval = self._calculate_interval_days(periods[i], periods[i + 1])
            if interval is None:
                logger.warning(f"Gap detection: Unable to calculate interval between {periods[i]} and {periods[i+1]}")
                continue
            
            # Log interval calculation with dates and days
            logger.debug(f"Gap detection: Interval between {periods[i+1]} and {periods[i]} = {interval} days (threshold: {threshold})")
            
            # Check if interval is significantly larger than expected (indicating missing period)
            # If interval is ~2x expected, there's likely a missing period
            if interval > threshold:
                # Calculate how many periods might be missing
                missing_count = round(interval / expected_interval) - 1
                logger.debug(f"Gap detected: interval {interval} days > threshold {threshold} days, missing_count={missing_count}")
                if missing_count > 0:
                    missing_periods.append(f"between {periods[i + 1]} and {periods[i]}")
            else:
                logger.debug(f"No gap: interval {interval} days <= threshold {threshold} days")
        
        if missing_periods:
            warning_msg = f"TTM Analysis: Periodic data has gaps - missing periods {', '.join(missing_periods)}"
            logger.warning(warning_msg)
            self.warnings.append(warning_msg)
            logger.debug(f"Gap detection complete: Gaps found - {missing_periods}")
            return True
        
        logger.debug("Gap detection complete: No gaps found")
        return False
    
    def _select_periods_for_ttm(self, frequency: str) -> List[str]:
        """
        Select appropriate periods for TTM calculation based on reporting frequency.
        
        Args:
            frequency: Reporting frequency ('quarterly', 'semi-annual', or 'irregular')
            
        Returns:
            List of selected period dates in descending order (most recent first)
            Returns empty list if insufficient periods or coverage gap
        """
        # Log method entry with frequency parameter
        logger.debug(f"Period selection starting: frequency={frequency}")
        
        # Determine number of periods needed
        periods_needed = 4 if frequency == 'quarterly' else 2
        logger.debug(f"Periods needed for {frequency} reporting: {periods_needed}")
        
        # Get sorted periods
        income_statement = self.quarterly_data.get('income_statement', {})
        balance_sheet = self.quarterly_data.get('balance_sheet', {})
        
        income_dates = sorted(income_statement.keys(), reverse=True)
        balance_dates = sorted(balance_sheet.keys(), reverse=True)
        
        # Log number of available periods
        logger.debug(f"Available periods: {len(income_dates)} income statement periods, {len(balance_dates)} balance sheet periods")
        
        # Check if we have enough periods
        if len(income_dates) < periods_needed:
            self.warnings.append(
                f"TTM Analysis: Insufficient periodic data ({len(income_dates)} periods available, "
                f"{periods_needed} required for {frequency} reporting)"
            )
            return []
        
        if len(balance_dates) < 1:
            self.warnings.append("TTM Analysis: No balance sheet data available")
            return []
        
        # Select periods to use
        selected_periods = income_dates[:periods_needed]
        
        # Detect data gaps - check if intervals between consecutive periods are consistent
        if len(selected_periods) >= 2:
            gaps_detected = self._detect_data_gaps(selected_periods, frequency)
            if gaps_detected:
                return []
        
        # Verify periods cover approximately 12 months (within 15 days tolerance)
        # Note: The span is measured from first to last period, which is (n-1) intervals
        # For TTM, we want consecutive periods that together represent 12 months of data:
        # - Quarterly: 4 consecutive quarters = 3 intervals of ~90 days = ~270 days span
        # - Semi-annual: 2 consecutive half-years = 1 interval of ~180 days = ~180 days span
        if len(selected_periods) >= 2:
            total_span = self._calculate_interval_days(selected_periods[0], selected_periods[-1])
            logger.debug(f"Span validation: total_span={total_span} days (from {selected_periods[-1]} to {selected_periods[0]})")
            
            if total_span is not None:
                # Expected span depends on frequency:
                # - Quarterly: 4 periods = 3 intervals of ~90 days = ~270 days
                # - Semi-annual: 2 periods = 1 interval of ~180 days = ~180 days
                if frequency == 'quarterly':
                    # 3 intervals × 90 days ± 15 days per interval = 270 ± 45 days
                    expected_min, expected_max = 225, 315
                    expected_desc = "~270 days (3 quarterly intervals)"
                else:  # semi-annual
                    # 1 interval of ~180 days ± 30 days = 180 ± 30 days
                    # (Using ±30 days tolerance for semi-annual as per frequency detection)
                    expected_min, expected_max = 150, 210
                    expected_desc = "~180 days (1 semi-annual interval)"
                
                logger.debug(f"Span validation: expected range {expected_min}-{expected_max} days ({expected_desc})")
                
                if not (expected_min <= total_span <= expected_max):
                    logger.warning(f"Span validation FAILED: {total_span} days not in range {expected_min}-{expected_max}")
                    self.warnings.append(
                        f"TTM Analysis: Selected periods cover {total_span} days (expected {expected_desc})"
                    )
                    return []
                else:
                    logger.debug(f"Span validation PASSED: {total_span} days is within range {expected_min}-{expected_max}")
        
        # Log exit with selected periods
        logger.debug(f"Period selection complete: {len(selected_periods)} periods selected - {selected_periods}")
        return selected_periods
    
    def calculate_ttm_metrics(self) -> Dict[str, Any]:
        """
        Calculate TTM financial metrics.
        
        Returns:
            Dict with keys: ttm_revenue, ttm_net_income, ttm_eps,
                           total_equity, current_assets, total_liabilities, etc.
                           Returns empty dict if insufficient data
        """
        # Get income statement and balance sheet data
        income_statement = self.quarterly_data.get('income_statement', {})
        balance_sheet = self.quarterly_data.get('balance_sheet', {})
        
        if not income_statement:
            self.warnings.append("TTM Analysis: No periodic data available")
            return {}
        
        # Get all period dates
        income_dates = sorted(income_statement.keys(), reverse=True)
        
        # Run data quality validations FIRST (before any other processing)
        self._validate_period_order(income_dates)
        self._validate_no_duplicates(income_dates)
        self._validate_date_ranges(income_dates)
        
        # Detect reporting frequency
        frequency = self.detect_reporting_frequency()
        
        if frequency == 'irregular':
            # Before giving up, check if there are gaps that caused the irregular pattern
            income_statement = self.quarterly_data.get('income_statement', {})
            income_dates = sorted(income_statement.keys(), reverse=True)
            
            if len(income_dates) >= 4:
                # Try to detect gaps assuming quarterly reporting
                test_periods = income_dates[:4]
                if self._detect_data_gaps(test_periods, 'quarterly'):
                    # Gap was detected, warning already added
                    pass
            elif len(income_dates) >= 2:
                # Try to detect gaps assuming semi-annual reporting
                test_periods = income_dates[:2]
                if self._detect_data_gaps(test_periods, 'semi-annual'):
                    # Gap was detected, warning already added
                    pass
            
            self.warnings.append("TTM Analysis: Cannot calculate metrics with irregular reporting")
            return {}
        
        # Select periods for TTM calculation
        selected_periods = self._select_periods_for_ttm(frequency)
        
        if not selected_periods:
            # Warnings already added by _select_periods_for_ttm
            return {}
        
        # Get data structures
        income_statement = self.quarterly_data.get('income_statement', {})
        balance_sheet = self.quarterly_data.get('balance_sheet', {})
        balance_dates = sorted(balance_sheet.keys(), reverse=True)
        
        # Sum income statement items over periods
        ttm_revenue = 0.0
        ttm_net_income = 0.0
        
        for period in selected_periods:
            period_data = income_statement[period]
            ttm_revenue += period_data.get('revenue', 0.0)
            ttm_net_income += period_data.get('net_income', 0.0)
        
        # Get most recent balance sheet values
        most_recent_balance = balance_sheet[balance_dates[0]]
        
        total_equity = most_recent_balance.get('total_equity', 0.0)
        intangible_assets = most_recent_balance.get('intangible_assets', 0.0)
        goodwill = most_recent_balance.get('goodwill', 0.0)
        current_assets = most_recent_balance.get('current_assets', 0.0)
        total_liabilities = most_recent_balance.get('total_liabilities', 0.0)
        shares_outstanding = most_recent_balance.get('shares_outstanding', 0.0)
        
        # Calculate TTM EPS: Sum(Net Income) / Most Recent Shares Outstanding
        # NOT sum of EPS values (incorrect when share count changes)
        ttm_eps = ttm_net_income / shares_outstanding if shares_outstanding > 0 else 0.0
        
        # Format date range for display
        date_range = self._format_date_range(selected_periods, frequency)
        
        return {
            'ttm_revenue': ttm_revenue,
            'ttm_net_income': ttm_net_income,
            'ttm_eps': ttm_eps,
            'total_equity': total_equity,
            'intangible_assets': intangible_assets,
            'goodwill': goodwill,
            'current_assets': current_assets,
            'total_liabilities': total_liabilities,
            'shares_outstanding': shares_outstanding,
            'reporting_frequency': frequency,
            'periods_used': selected_periods,
            'date_range': date_range
        }
    
    def _format_date_range(self, periods: List[str], frequency: str) -> str:
        """
        Format date range for display.
        
        Args:
            periods: List of period dates (e.g., ['2025-09-30', '2025-06-30', ...])
            frequency: Reporting frequency ('quarterly' or 'semi-annual')
            
        Returns:
            Formatted string like "Q4 2024 through Q3 2025" for quarterly
            or "H2 2024 through H1 2025" for semi-annual
        """
        if not periods:
            return "N/A"
        
        # Get oldest and newest dates
        oldest = periods[-1]  # Last in list (oldest)
        newest = periods[0]   # First in list (newest)
        
        # Parse dates
        oldest_date = self._parse_date(oldest)
        newest_date = self._parse_date(newest)
        
        if oldest_date is None or newest_date is None:
            return f"{oldest} through {newest}"
        
        # Format based on frequency
        if frequency == 'semi-annual':
            # Use H1/H2 labels for semi-annual
            oldest_label = self._get_half_label(oldest_date)
            newest_label = self._get_half_label(newest_date)
        else:
            # Use Q1/Q2/Q3/Q4 labels for quarterly
            oldest_label = self._get_quarter_label(oldest_date)
            newest_label = self._get_quarter_label(newest_date)
        
        return f"{oldest_label} through {newest_label}"
    
    def _get_half_label(self, date: datetime) -> str:
        """
        Get half-year label for a date.
        
        Args:
            date: datetime object
            
        Returns:
            String like "H1 2025" or "H2 2025"
        """
        month = date.month
        year = date.year
        
        # Determine half based on month
        if month <= 6:
            return f"H1 {year}"
        else:
            return f"H2 {year}"
    
    def _get_quarter_label(self, date: datetime) -> str:
        """
        Get quarter label for a date.
        
        Args:
            date: datetime object
            
        Returns:
            String like "Q1 2025" or "H1 2025"
        """
        month = date.month
        year = date.year
        
        # Determine quarter based on month
        if month <= 3:
            return f"Q1 {year}"
        elif month <= 6:
            return f"Q2 {year}"
        elif month <= 9:
            return f"Q3 {year}"
        else:
            return f"Q4 {year}"
    
    def compute_ttm_tbvps(self, ttm_metrics: Dict[str, Any]) -> Union[float, str]:
        """
        Calculate TTM Tangible Book Value Per Share.
        
        Formula: (Total Equity - Intangible Assets - Goodwill) / Shares Outstanding
        
        Args:
            ttm_metrics: Dict containing TTM financial metrics
            
        Returns:
            float rounded to 2 decimals, or "N/A" if invalid inputs
        """
        total_equity = ttm_metrics.get('total_equity', 0.0)
        intangible_assets = ttm_metrics.get('intangible_assets', 0.0)
        goodwill = ttm_metrics.get('goodwill', 0.0)
        shares_outstanding = ttm_metrics.get('shares_outstanding', 0.0)
        
        # Check for invalid inputs
        if shares_outstanding <= 0:
            self.warnings.append("TTM TBVPS: Shares outstanding is zero or negative")
            return "N/A"
        
        # Calculate tangible book value
        tangible_book_value = total_equity - intangible_assets - goodwill
        tbvps = tangible_book_value / shares_outstanding
        
        # Check for negative TBVPS
        if tbvps < 0:
            self.warnings.append("TTM TBVPS: Negative tangible book value - company has negative equity after removing intangibles")
            return "N/A"
        
        return round(tbvps, 2)
    
    def compute_ttm_graham_number(self, ttm_metrics: Dict[str, Any]) -> Union[float, str]:
        """
        Calculate TTM Graham Number.
        
        Formula: sqrt(22.5 × TTM_EPS × TTM_TBVPS)
        
        Args:
            ttm_metrics: Dict containing TTM financial metrics
            
        Returns:
            float rounded to 2 decimals, or "N/A" if invalid inputs
        """
        import math
        
        ttm_eps = ttm_metrics.get('ttm_eps', 0.0)
        ttm_tbvps = self.compute_ttm_tbvps(ttm_metrics)
        
        # Check if TBVPS calculation failed
        if ttm_tbvps == "N/A":
            self.warnings.append("TTM Graham Number: Cannot calculate - TBVPS is N/A")
            return "N/A"
        
        # Check for non-positive EPS
        if ttm_eps <= 0:
            self.warnings.append("TTM Graham Number: EPS is zero or negative")
            return "N/A"
        
        # Check for negative TBVPS (should already be caught, but double-check)
        if ttm_tbvps < 0:
            self.warnings.append("TTM Graham Number: TBVPS is negative")
            return "N/A"
        
        # Calculate Graham Number
        graham_number = math.sqrt(22.5 * ttm_eps * ttm_tbvps)
        
        return round(graham_number, 2)
    
    def compute_ttm_net_net(self, ttm_metrics: Dict[str, Any]) -> Union[float, str]:
        """
        Calculate TTM Net-Net Working Capital Value.
        
        Formula: (Current Assets - Total Liabilities) / Shares Outstanding
        
        Args:
            ttm_metrics: Dict containing TTM financial metrics
            
        Returns:
            float rounded to 2 decimals, or "N/A" if data unavailable
        """
        current_assets = ttm_metrics.get('current_assets', 0.0)
        total_liabilities = ttm_metrics.get('total_liabilities', 0.0)
        shares_outstanding = ttm_metrics.get('shares_outstanding', 0.0)
        
        # Check for invalid inputs
        if shares_outstanding <= 0:
            self.warnings.append("TTM Net-Net: Shares outstanding is zero or negative")
            return "N/A"
        
        # Check if data is available
        if current_assets == 0.0 and total_liabilities == 0.0:
            self.warnings.append("TTM Net-Net: Current assets and liabilities data unavailable")
            return "N/A"
        
        # Calculate net-net value
        net_net_value = (current_assets - total_liabilities) / shares_outstanding
        
        return round(net_net_value, 2)
    
    def compute_ttm_margin_of_safety(self, graham_number: Union[float, str]) -> Union[float, str]:
        """
        Calculate TTM Margin of Safety.
        
        Formula: ((TTM_Graham_Number - Price) / TTM_Graham_Number) × 100
        
        Args:
            graham_number: TTM Graham Number (can be "N/A")
            
        Returns:
            float rounded to 1 decimal, or "N/A" if Graham Number is N/A
        """
        # Check if Graham Number is available
        if graham_number == "N/A":
            self.warnings.append("TTM Margin of Safety: Cannot calculate - Graham Number is N/A")
            return "N/A"
        
        # Check for zero Graham Number (shouldn't happen, but be safe)
        if graham_number == 0:
            self.warnings.append("TTM Margin of Safety: Graham Number is zero")
            return "N/A"
        
        # Calculate margin of safety
        margin_of_safety = ((graham_number - self.price) / graham_number) * 100
        
        return round(margin_of_safety, 1)
    
    def compute_ttm_pe_pb_ratios(self, ttm_metrics: Dict[str, Any]) -> Dict[str, Union[float, str]]:
        """
        Calculate TTM P/E and P/B ratios.
        
        Formulas:
        - TTM P/E = Price / TTM_EPS
        - TTM P/B = Price / TTM_Book_Value_Per_Share
        
        Args:
            ttm_metrics: Dict containing TTM financial metrics
            
        Returns:
            Dict with 'ttm_pe_ratio' and 'ttm_pb_ratio' keys
        """
        ttm_eps = ttm_metrics.get('ttm_eps', 0.0)
        total_equity = ttm_metrics.get('total_equity', 0.0)
        shares_outstanding = ttm_metrics.get('shares_outstanding', 0.0)
        
        # Calculate P/E ratio
        if ttm_eps <= 0:
            self.warnings.append("TTM P/E: EPS is zero or negative")
            ttm_pe_ratio = "N/A"
        else:
            ttm_pe_ratio = round(self.price / ttm_eps, 2)
        
        # Calculate Book Value Per Share
        if shares_outstanding <= 0:
            self.warnings.append("TTM P/B: Shares outstanding is zero or negative")
            ttm_pb_ratio = "N/A"
        else:
            book_value_per_share = total_equity / shares_outstanding
            
            if book_value_per_share <= 0:
                self.warnings.append("TTM P/B: Book value per share is zero or negative")
                ttm_pb_ratio = "N/A"
            else:
                ttm_pb_ratio = round(self.price / book_value_per_share, 2)
        
        return {
            'ttm_pe_ratio': ttm_pe_ratio,
            'ttm_pb_ratio': ttm_pb_ratio
        }
    
    def _validate_period_order(self, periods: List[str]) -> bool:
        """
        Verify periods are in chronological order (most recent first).
        
        Note: This validation is called AFTER sorting, so it checks if the
        original data was already in the correct order by comparing with sorted.
        
        Args:
            periods: List of period dates (already sorted descending)
            
        Returns:
            True if periods are in correct order, False otherwise
        """
        if len(periods) < 2:
            return True
        
        # Since we receive already-sorted periods, we can't detect if they were
        # originally out of order. This validation is informational only.
        # In practice, dict keys maintain insertion order, so if the API returns
        # them out of order, we would need to check before sorting.
        
        # Parse all dates to ensure they're valid
        parsed_dates = []
        for period in periods:
            date = self._parse_date(period)
            if date is None:
                self.warnings.append(f"TTM Data Quality: Unable to parse date '{period}'")
                return False
            parsed_dates.append(date)
        
        # Verify dates are in descending order (most recent first)
        for i in range(len(parsed_dates) - 1):
            if parsed_dates[i] < parsed_dates[i + 1]:
                self.warnings.append(
                    f"TTM Data Quality: Periods are not in chronological order "
                    f"({periods[i]} comes before {periods[i + 1]})"
                )
                return False
        
        return True
    
    def _validate_no_duplicates(self, periods: List[str]) -> bool:
        """
        Verify no duplicate period dates.
        
        Note: Since periods come from dict keys, Python automatically deduplicates them.
        This validation checks if the list has duplicates (which shouldn't happen with dict keys).
        
        Args:
            periods: List of period dates
            
        Returns:
            True if no duplicates found, False otherwise
        """
        if len(periods) != len(set(periods)):
            # Find duplicates
            seen = set()
            duplicates = []
            for period in periods:
                if period in seen:
                    duplicates.append(period)
                seen.add(period)
            
            self.warnings.append(
                f"TTM Data Quality: Duplicate periods found: {', '.join(duplicates)}"
            )
            return False
        
        return True
    
    def _validate_date_ranges(self, periods: List[str]) -> bool:
        """
        Verify period dates are within expected ranges.
        
        Checks that dates are:
        - Not in the future (beyond current date + 1 year)
        - Not too old (before 1950)
        
        Args:
            periods: List of period dates
            
        Returns:
            True if all dates are valid, False otherwise
        """
        current_date = datetime.now()
        future_limit = datetime(current_date.year + 1, 12, 31)
        past_limit = datetime(1950, 1, 1)
        
        invalid_dates = []
        
        for period in periods:
            date = self._parse_date(period)
            if date is None:
                continue
            
            if date > future_limit:
                invalid_dates.append(f"{period} (future date)")
            elif date < past_limit:
                invalid_dates.append(f"{period} (too old)")
        
        if invalid_dates:
            self.warnings.append(
                f"TTM Data Quality: Invalid period dates: {', '.join(invalid_dates)}"
            )
            return False
        
        return True
    
    def _validate_ttm_vs_annual(self, ttm_metrics: Dict[str, Any], 
                                annual_metrics: Optional[Dict[str, Any]] = None) -> None:
        """
        Compare TTM values to annual values and add warnings if differences are significant.
        
        Args:
            ttm_metrics: TTM financial metrics
            annual_metrics: Annual financial metrics (optional)
        """
        if not annual_metrics:
            # No annual metrics to compare against
            return
        
        # Compare TTM EPS to annual EPS
        ttm_eps = ttm_metrics.get('ttm_eps', 0.0)
        annual_eps = annual_metrics.get('eps', 0.0)
        
        if ttm_eps > 0 and annual_eps > 0:
            eps_diff_pct = abs(ttm_eps - annual_eps) / annual_eps * 100
            
            if eps_diff_pct > 20:
                warning_msg = (
                    f"TTM Validation: TTM EPS differs from annual EPS by {eps_diff_pct:.1f}% "
                    f"(TTM: {ttm_eps:.2f}, Annual: {annual_eps:.2f})"
                )
                self.warnings.append(warning_msg)
        
        # Compare TTM revenue to annual revenue
        ttm_revenue = ttm_metrics.get('ttm_revenue', 0.0)
        annual_revenue = annual_metrics.get('revenue', 0.0)
        
        if ttm_revenue > 0 and annual_revenue > 0:
            revenue_diff_pct = abs(ttm_revenue - annual_revenue) / annual_revenue * 100
            
            if revenue_diff_pct > 50:
                warning_msg = (
                    f"TTM Validation: TTM revenue differs from annual revenue by {revenue_diff_pct:.1f}% "
                    f"(TTM: {ttm_revenue:.0f}, Annual: {annual_revenue:.0f})"
                )
                self.warnings.append(warning_msg)
        
        # Compare TTM net income to annual net income
        ttm_net_income = ttm_metrics.get('ttm_net_income', 0.0)
        annual_net_income = annual_metrics.get('net_income', 0.0)
        
        if ttm_net_income != 0 and annual_net_income != 0:
            net_income_diff_pct = abs(ttm_net_income - annual_net_income) / abs(annual_net_income) * 100
            
            if net_income_diff_pct > 50:
                warning_msg = (
                    f"TTM Validation: TTM net income differs from annual net income by {net_income_diff_pct:.1f}% "
                    f"(TTM: {ttm_net_income:.0f}, Annual: {annual_net_income:.0f})"
                )
                self.warnings.append(warning_msg)
    
    def compute_all(self, annual_metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Compute all TTM metrics and Graham calculations.
        
        Each calculation is isolated with try/except to ensure one failure
        doesn't stop other calculations from completing.
        
        Args:
            annual_metrics: Optional annual financial metrics for validation comparison
        
        Returns:
            Dict with all TTM calculations, warnings, and metadata
        """
        # Calculate TTM metrics
        try:
            ttm_metrics = self.calculate_ttm_metrics()
        except Exception as e:
            self.warnings.append(f"TTM Analysis: Failed to calculate metrics - {str(e)}")
            ttm_metrics = {}
        
        # If no metrics available, return minimal result
        if not ttm_metrics:
            return {
                'ttm_graham_number': "N/A",
                'ttm_tbvps': "N/A",
                'ttm_net_net': "N/A",
                'ttm_margin_of_safety': "N/A",
                'ttm_pe_ratio': "N/A",
                'ttm_pb_ratio': "N/A",
                'reporting_frequency': 'irregular',
                'date_range': 'N/A',
                'currency': self.currency,
                'original_currency': self.original_currency,
                'fx_rate_used': self.fx_rate,
                'warnings': self.warnings.copy()
            }
        
        # Validate TTM vs annual metrics if annual metrics provided
        if annual_metrics:
            try:
                self._validate_ttm_vs_annual(ttm_metrics, annual_metrics)
            except Exception as e:
                self.warnings.append(f"TTM Validation: Failed to compare with annual metrics - {str(e)}")
        
        # Compute Graham calculations with error isolation
        # Each calculation is wrapped in try/except to ensure failures are isolated
        
        # TBVPS calculation
        try:
            ttm_tbvps = self.compute_ttm_tbvps(ttm_metrics)
        except Exception as e:
            self.warnings.append(f"TTM TBVPS: Calculation failed - {str(e)}")
            ttm_tbvps = "N/A"
        
        # Graham Number calculation
        try:
            ttm_graham_number = self.compute_ttm_graham_number(ttm_metrics)
        except Exception as e:
            self.warnings.append(f"TTM Graham Number: Calculation failed - {str(e)}")
            ttm_graham_number = "N/A"
        
        # Net-Net calculation
        try:
            ttm_net_net = self.compute_ttm_net_net(ttm_metrics)
        except Exception as e:
            self.warnings.append(f"TTM Net-Net: Calculation failed - {str(e)}")
            ttm_net_net = "N/A"
        
        # Margin of Safety calculation
        try:
            ttm_margin_of_safety = self.compute_ttm_margin_of_safety(ttm_graham_number)
        except Exception as e:
            self.warnings.append(f"TTM Margin of Safety: Calculation failed - {str(e)}")
            ttm_margin_of_safety = "N/A"
        
        # P/E and P/B ratios calculation
        try:
            pe_pb_ratios = self.compute_ttm_pe_pb_ratios(ttm_metrics)
        except Exception as e:
            self.warnings.append(f"TTM P/E and P/B: Calculation failed - {str(e)}")
            pe_pb_ratios = {'ttm_pe_ratio': "N/A", 'ttm_pb_ratio': "N/A"}
        
        result = {
            'ttm_revenue': ttm_metrics.get('ttm_revenue', 0.0),
            'ttm_net_income': ttm_metrics.get('ttm_net_income', 0.0),
            'ttm_eps': ttm_metrics.get('ttm_eps', 0.0),
            'ttm_graham_number': ttm_graham_number,
            'ttm_tbvps': ttm_tbvps,
            'ttm_net_net': ttm_net_net,
            'ttm_margin_of_safety': ttm_margin_of_safety,
            'ttm_pe_ratio': pe_pb_ratios.get('ttm_pe_ratio', "N/A"),
            'ttm_pb_ratio': pe_pb_ratios.get('ttm_pb_ratio', "N/A"),
            'reporting_frequency': ttm_metrics.get('reporting_frequency', 'irregular'),
            'date_range': ttm_metrics.get('date_range', 'N/A'),
            'periods_used': ttm_metrics.get('periods_used', []),
            'currency': self.currency,
            'original_currency': self.original_currency,
            'fx_rate_used': self.fx_rate,
            'warnings': self.warnings.copy()
        }
        
        return result
