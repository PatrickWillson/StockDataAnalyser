"""TTM Analysis section generator for dossier.

This module generates the TTM (Trailing Twelve Months) analysis section of the stock
analysis dossier, including TTM Graham calculations and comparisons with annual metrics.
"""

from typing import List, Dict, Any, Union, Optional
from output.sections.base import DossierSection
from core.report_context import ReportContext, build_report_context


class TTMAnalysisSection(DossierSection):
    """Generates TTM (Trailing Twelve Months) analysis section for dossier.
    
    This section includes:
    - Reporting frequency detected (quarterly or semi-annual)
    - Date range covered by TTM calculations
    - TTM Graham calculations (Graham Number, TBVPS, Net-Net, MOS, P/E, P/B)
    - Percentage differences from annual calculations
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7
    """
    
    def __init__(self, ttm_metrics: Dict[str, Any], annual_metrics: Dict[str, Any], financial_data: Dict[str, Any], context: Optional[ReportContext] = None):
        """Initialize TTM section generator.
        
        Args:
            ttm_metrics: TTM calculations from TTMCalculator
            annual_metrics: Annual calculations for comparison
            financial_data: Full financial data dict (for TTM dividend)
        """
        self.ttm_metrics = ttm_metrics
        self.annual_metrics = annual_metrics
        self.financial_data = financial_data
        self.context = context or build_report_context(financial_data, annual_metrics)
    
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
        
        # TTM Dividend (if available)
        self._add_ttm_dividend(lines)
        
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
        
        # TTM Margin of Safety: measured against the TTM Graham Number, a different basis from the
        # annual margin of safety (lower of normalized Graham Number and EPV), so no diff is shown
        ttm_mos = self.ttm_metrics.get('ttm_margin_of_safety')
        if isinstance(ttm_mos, (int, float)):
            lines.append(f"- TTM Margin of Safety: {float(ttm_mos):.1f}% (vs the TTM Graham Number; the annual "
                         f"margin of safety uses the lower of the normalized Graham Number and EPV)")
        else:
            lines.append("- TTM Margin of Safety: N/A")
        
        # TTM P/E and P/B against the latest annual P/E and P/B (price / latest annual EPS and BVPS)
        self._add_metric_with_comparison(
            lines,
            "TTM P/E Ratio",
            self.ttm_metrics.get('ttm_pe_ratio'),
            self._annual_ratio('pe_ratio'),
            currency,
            is_currency=False
        )
        
        self._add_metric_with_comparison(
            lines,
            "TTM P/B Ratio",
            self.ttm_metrics.get('ttm_pb_ratio'),
            self._annual_ratio('price_to_book'),
            currency,
            is_currency=False
        )
    
    def _annual_ratio(self, key: str) -> Union[float, str]:
        """Latest annual P/E or P/B from financial_data, "N/A" when not positive."""
        value = self.financial_data.get(key)
        return value if isinstance(value, (int, float)) and value > 0 else "N/A"
    
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
            # Avoid division by zero
            if abs(annual_float) == 0:
                return ""
            
            pct_diff = round(((ttm_float - annual_float) / abs(annual_float)) * 100, 1)
            
            # Format with sign (rounded first, so a tiny negative shows as 0.0%, not -0.0%)
            if pct_diff == 0:
                return "0.0%"
            if pct_diff > 0:
                return f"+{pct_diff:.1f}%"
            else:
                return f"{pct_diff:.1f}%"
        except (ValueError, TypeError):
            return ""
    
    def _add_ttm_dividend(self, lines: List[str]) -> None:
        """Add TTM dividend information if available.
        
        Args:
            lines: List to append lines to
        """
        ttm_dividend = self.financial_data.get('ttm_dividend', 0.0)
        ttm_payments = self.financial_data.get('ttm_dividend_payments', [])
        currency = self.financial_data.get('currency', 'USD')
        price = self.financial_data.get('price', 0.0)
        
        if not ttm_dividend or ttm_dividend <= 0:
            return
        
        # Calculate TTM yield
        ttm_yield = 0.0
        if price > 0:
            ttm_yield = (ttm_dividend / price) * 100
        
        # Get fiscal year dividend for comparison (from history)
        history = self.financial_data.get('history', {})
        fiscal_year_dividend = 0.0
        fiscal_year = None
        
        if history and self.context.latest_year:
            # Most recent complete fiscal year
            fiscal_year = self.context.latest_year_label
            if self.financial_data.get('is_dividend_amounts', False):
                fiscal_year_dividend = self.context.latest_row.get('dividend', 0.0)
        
        lines.append("")
        lines.append(f"- TTM Dividend (Last 12 Months): {ttm_dividend:.2f} {currency} (Yield: {ttm_yield:.2f}%)")
        
        # Show payment breakdown if available
        if ttm_payments and len(ttm_payments) > 0:
            lines.append(f"  - Based on {len(ttm_payments)} payment(s):")
            for payment in ttm_payments:
                payment_date = payment.get('date', 'N/A')
                payment_value = payment.get('value', 0.0)
                lines.append(f"    - {payment_date}: {payment_value:.4f} {currency}")
        
        # Compare with fiscal year dividend if available
        if fiscal_year_dividend > 0 and fiscal_year:
            fiscal_yield = (fiscal_year_dividend / price) * 100 if price > 0 else 0.0
            # Avoid division by zero
            if fiscal_year_dividend > 0:
                pct_diff = ((ttm_dividend - fiscal_year_dividend) / fiscal_year_dividend) * 100
                diff_sign = "+" if pct_diff > 0 else ""
                lines.append(f"  - FY{fiscal_year} Dividend: {fiscal_year_dividend:.2f} {currency} (Yield: {fiscal_yield:.2f}%, Diff: {diff_sign}{pct_diff:.1f}%)")
