"""TTM Analysis section generator for dossier.

This module generates the TTM (Trailing Twelve Months) analysis section of the stock
analysis dossier, including TTM Graham calculations and comparisons with annual metrics.
"""

from typing import List, Dict, Any, Union
from output.sections.base import DossierSection


class TTMAnalysisSection(DossierSection):
    """Generates TTM (Trailing Twelve Months) analysis section for dossier.
    
    This section includes:
    - Reporting frequency detected (quarterly or semi-annual)
    - Date range covered by TTM calculations
    - TTM Graham calculations (Graham Number, TBVPS, Net-Net, MOS, P/E, P/B)
    - Percentage differences from annual calculations
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
    """
    
    def __init__(self, ttm_metrics: Dict[str, Any], annual_metrics: Dict[str, Any]):
        """Initialize TTM section generator.
        
        Args:
            ttm_metrics: TTM calculations from TTMCalculator
            annual_metrics: Annual calculations for comparison
        """
        self.ttm_metrics = ttm_metrics
        self.annual_metrics = annual_metrics
    
    def generate(self) -> List[str]:
        """Generate TTM section markdown lines.
        
        Returns:
            List[str]: List of markdown lines for the TTM section
        """
        lines = []
        
        # Section header
        lines.append("")
        lines.append("## SECTION 1.5: TTM (TRAILING TWELVE MONTHS) ANALYSIS")
        lines.append("*TTM calculations provide more current metrics using the most recent 12 months of periodic data*")
        lines.append("")
        
        # Reporting frequency and date range
        reporting_frequency = self.ttm_metrics.get('reporting_frequency', 'unknown')
        date_range = self.ttm_metrics.get('date_range', 'N/A')
        
        if reporting_frequency != 'unknown':
            frequency_display = reporting_frequency.replace('_', '-').title()
            lines.append(f"- Reporting Frequency: {frequency_display}")
        
        if date_range != 'N/A':
            lines.append(f"- Period Covered: {date_range}")
        
        lines.append("")
        
        # TTM Graham calculations with comparisons
        self._add_ttm_calculations(lines)
        
        lines.append("")
        lines.append("---")
        
        return lines
    
    def _add_ttm_calculations(self, lines: List[str]) -> None:
        """Add TTM Graham calculations with percentage differences from annual.
        
        Args:
            lines: List to append lines to
        """
        # Get currency for display
        currency = self.ttm_metrics.get('currency', 'USD')
        
        # TTM Graham Number
        self._add_metric_with_comparison(
            lines,
            "TTM Graham Number",
            self.ttm_metrics.get('ttm_graham_number'),
            self.annual_metrics.get('graham_number'),
            currency,
            is_currency=True
        )
        
        # TTM TBVPS
        self._add_metric_with_comparison(
            lines,
            "TTM Tangible Book Value Per Share",
            self.ttm_metrics.get('ttm_tbvps'),
            self.annual_metrics.get('tbvps'),
            currency,
            is_currency=True
        )
        
        # TTM Net-Net Value
        self._add_metric_with_comparison(
            lines,
            "TTM Net-Net Value",
            self.ttm_metrics.get('ttm_net_net'),
            self.annual_metrics.get('net_net_value'),
            currency,
            is_currency=True
        )
        
        # TTM Margin of Safety
        self._add_metric_with_comparison(
            lines,
            "TTM Margin of Safety",
            self.ttm_metrics.get('ttm_margin_of_safety'),
            self.annual_metrics.get('margin_of_safety'),
            currency,
            is_currency=False,
            is_percentage=True
        )
        
        # TTM P/E Ratio
        self._add_metric_with_comparison(
            lines,
            "TTM P/E Ratio",
            self.ttm_metrics.get('ttm_pe_ratio'),
            self.annual_metrics.get('pe_ratio'),
            currency,
            is_currency=False
        )
        
        # TTM P/B Ratio
        self._add_metric_with_comparison(
            lines,
            "TTM P/B Ratio",
            self.ttm_metrics.get('ttm_pb_ratio'),
            self.annual_metrics.get('pb_ratio'),
            currency,
            is_currency=False
        )
    
    def _add_metric_with_comparison(self, lines: List[str], label: str, 
                                   ttm_value: Union[float, str], 
                                   annual_value: Union[float, str],
                                   currency: str,
                                   is_currency: bool = False,
                                   is_percentage: bool = False) -> None:
        """Add a metric line with TTM value and comparison to annual.
        
        Args:
            lines: List to append lines to
            label: Metric label
            ttm_value: TTM metric value
            annual_value: Annual metric value for comparison
            currency: Currency for display
            is_currency: Whether value is a currency amount
            is_percentage: Whether value is already a percentage
        """
        # Format TTM value
        if ttm_value == "N/A" or ttm_value is None:
            ttm_display = "N/A"
        elif is_currency:
            ttm_display = f"{float(ttm_value):,.2f} {currency}"
        elif is_percentage:
            ttm_display = f"{float(ttm_value):.1f}%"
        else:
            ttm_display = f"{float(ttm_value):.2f}"
        
        # Calculate percentage difference if both values available
        pct_diff = self._calculate_percentage_difference(ttm_value, annual_value)
        
        if pct_diff:
            lines.append(f"- {label}: {ttm_display} (Annual: {self._format_annual_value(annual_value, currency, is_currency, is_percentage)}, Diff: {pct_diff})")
        else:
            lines.append(f"- {label}: {ttm_display}")
    
    def _format_annual_value(self, annual_value: Union[float, str], currency: str,
                            is_currency: bool, is_percentage: bool) -> str:
        """Format annual value for display.
        
        Args:
            annual_value: Annual metric value
            currency: Currency for display
            is_currency: Whether value is a currency amount
            is_percentage: Whether value is already a percentage
            
        Returns:
            Formatted string
        """
        if annual_value == "N/A" or annual_value is None:
            return "N/A"
        elif is_currency:
            return f"{float(annual_value):,.2f} {currency}"
        elif is_percentage:
            return f"{float(annual_value):.1f}%"
        else:
            return f"{float(annual_value):.2f}"
    
    def _calculate_percentage_difference(self, ttm_value: Union[float, str], 
                                        annual_value: Union[float, str]) -> str:
        """Calculate percentage difference between TTM and annual values.
        
        Formula: (TTM - Annual) / Annual × 100
        
        Args:
            ttm_value: TTM metric value
            annual_value: Annual metric value
            
        Returns:
            Formatted string like "+15.3%" or "-8.2%", or empty string if N/A
        """
        # Handle N/A cases
        if ttm_value == "N/A" or ttm_value is None:
            return ""
        if annual_value == "N/A" or annual_value is None:
            return ""
        
        try:
            ttm_float = float(ttm_value)
            annual_float = float(annual_value)
            
            # Avoid division by zero
            if annual_float == 0:
                return ""
            
            # Calculate percentage difference
            pct_diff = ((ttm_float - annual_float) / abs(annual_float)) * 100
            
            # Format with sign
            if pct_diff > 0:
                return f"+{pct_diff:.1f}%"
            else:
                return f"{pct_diff:.1f}%"
        except (ValueError, TypeError):
            return ""
    
    def _format_date_range(self, periods: List[str]) -> str:
        """Format date range for display.
        
        Converts period dates to readable format like "Q4 2024 through Q3 2025"
        or "H2 2024 through H1 2025" for semi-annual reporters.
        
        Args:
            periods: List of period dates (e.g., ['2025-09-30', '2025-06-30', ...])
            
        Returns:
            Formatted string like "Q4 2024 through Q3 2025"
        """
        if not periods or len(periods) == 0:
            return "N/A"
        
        # Periods are in descending order (most recent first)
        most_recent = periods[0]
        oldest = periods[-1]
        
        # Determine if quarterly or semi-annual based on number of periods
        is_quarterly = len(periods) == 4
        
        # Parse dates
        try:
            from datetime import datetime
            
            most_recent_date = datetime.strptime(most_recent, '%Y-%m-%d')
            oldest_date = datetime.strptime(oldest, '%Y-%m-%d')
            
            if is_quarterly:
                # Quarterly format: Q1, Q2, Q3, Q4
                most_recent_quarter = self._get_quarter(most_recent_date.month)
                oldest_quarter = self._get_quarter(oldest_date.month)
                
                return f"{oldest_quarter} {oldest_date.year} through {most_recent_quarter} {most_recent_date.year}"
            else:
                # Semi-annual format: H1, H2
                most_recent_half = self._get_half(most_recent_date.month)
                oldest_half = self._get_half(oldest_date.month)
                
                return f"{oldest_half} {oldest_date.year} through {most_recent_half} {most_recent_date.year}"
        except (ValueError, AttributeError):
            # Fallback to simple date display
            return f"{oldest} through {most_recent}"
    
    def _get_quarter(self, month: int) -> str:
        """Get quarter label from month.
        
        Args:
            month: Month number (1-12)
            
        Returns:
            Quarter label (Q1, Q2, Q3, Q4)
        """
        if month <= 3:
            return "Q1"
        elif month <= 6:
            return "Q2"
        elif month <= 9:
            return "Q3"
        else:
            return "Q4"
    
    def _get_half(self, month: int) -> str:
        """Get half-year label from month.
        
        Args:
            month: Month number (1-12)
            
        Returns:
            Half-year label (H1, H2)
        """
        if month <= 6:
            return "H1"
        else:
            return "H2"
