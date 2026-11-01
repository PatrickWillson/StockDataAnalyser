"""Executive Summary section generator for dossier.

This module generates the executive summary section of the stock analysis dossier,
including verdict, intrinsic values, margin of safety, current price, and dividend information.
"""

from typing import List, Dict, Any, Optional, Union
from output.sections.base import DossierSection
from core.report_context import ReportContext, build_report_context, fiscal_year
from core.models import FinancialData, EPVDetails, GrahamResult, MarginOfSafetyDetails, ThreeYearAvgPE, or_default
from output.formatting import format_price_display


class ExecutiveSummarySection(DossierSection):
    """Generates the executive summary section of the dossier.
    
    This section includes:
    - Verdict (core.verdict, design D8) and the rule that produced it
    - Intrinsic values (Graham Number, EPV, Net-Net)
    - Margin of Safety
    - Current price and 52-week range
    - Dividend information with source transparency
    - Valuation ratios (P/E, Price/Book)
    
    Requirements: 1.4, 2.1
    """
    
    def __init__(self, financial_data: Dict[str, Any], metrics: Union[GrahamResult, Dict[str, Any]],
                 context: Optional[ReportContext] = None):
        """Initialize executive summary section.
        
        Args:
            financial_data: Dictionary containing financial data (FinancialData DTO)
            metrics: Graham metrics (GrahamResult, or its dict form)
        """
        self.financial_data = FinancialData.from_dict(financial_data)
        self.metrics = GrahamResult.from_dict(metrics)
        self.context = context or build_report_context(financial_data, metrics)
    
    def generate(self) -> List[str]:
        """Generate executive summary section content.
        
        Returns:
            List[str]: List of markdown lines for executive summary section
        """
        lines = []
        
        # Section header
        lines.append("")
        lines.append("## SECTION 1: EXECUTIVE SUMMARY")
        lines.append("*Current metrics (P/E, Price) reflect most recent available data*")
        lines.append("")
        
        # Extract currency information
        unified_currency = or_default(self.financial_data.currency, 'USD')
        original_stock_currency = or_default(self.financial_data.original_stock_currency, unified_currency)
        
        # Verdict
        lines.append(f"- Verdict: **{self.metrics.verdict}**")
        if self.metrics.verdict_reason:
            lines.append(f"  - {self.metrics.verdict_reason}")
        
        # Intrinsic values
        self._add_intrinsic_values(lines, unified_currency)
        
        # Margin of Safety - Requirement 10.1
        # Display normalized MoS as primary value with limiting factor
        mos_details = self.metrics.margin_of_safety_details or MarginOfSafetyDetails()
        mos_percentage = or_default(mos_details.mos_percentage, or_default(self.metrics.margin_of_safety, 'N/A'))
        limiting_factor = or_default(mos_details.limiting_factor, 'N/A')
        intrinsic_value_used = or_default(mos_details.intrinsic_value_used, 'N/A')
        mos_note = or_default(mos_details.note, None)
        
        if mos_percentage != 'N/A':
            # Format the MoS display with limiting factor
            if mos_note:
                lines.append(f"- Margin of Safety: {mos_percentage:.1f}% ({limiting_factor} only; {mos_note})")
                if intrinsic_value_used != 'N/A':
                    iv_display = format_price_display(float(intrinsic_value_used), unified_currency, unified_currency)
                    lines.append(f"  - Conservative Intrinsic Value: {iv_display}")
            elif limiting_factor != 'N/A':
                lines.append(f"- Margin of Safety: {mos_percentage:.1f}% (Capped by {limiting_factor})")
                
                # Add explanatory note about which intrinsic value was used
                if intrinsic_value_used != 'N/A':
                    iv_display = format_price_display(float(intrinsic_value_used), unified_currency, unified_currency)
                    lines.append(f"  - Conservative Intrinsic Value: {iv_display}")
            else:
                lines.append(f"- Margin of Safety: {mos_percentage:.1f}%")
        elif mos_note:
            lines.append(f"- Margin of Safety: {mos_percentage} ({mos_note})")
        else:
            lines.append(f"- Margin of Safety: {mos_percentage}")
        
        # Current price
        self._add_current_price(lines, unified_currency, original_stock_currency)
        
        # 52-week range
        self._add_52_week_range(lines, unified_currency, original_stock_currency)
        
        # Dividend information
        self._add_dividend_info(lines, unified_currency)
        
        # Valuation ratios
        self._add_valuation_ratios(lines)
        
        lines.append("")
        lines.append("---")
        
        return lines
    
    def _add_intrinsic_values(self, lines: List[str], unified_currency: str) -> None:
        """Add intrinsic value lines (Graham, EPV, Net-Net).
        
        Requirements 3.3, 3.4, 3.5:
        - Display both single-year and normalized Graham Numbers with clear labels
        - Label legacy as "Graham Number (Single-Year EPS)"
        - Label normalized as "Graham Number (3-Year Avg EPS)"
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for display
        """
        graham_str = self.metrics.graham_number
        normalized_graham_str = or_default(self.metrics.normalized_graham_number, 'N/A')
        epv_details = self.metrics.epv_details or EPVDetails()
        net_net_str = or_default(self.metrics.net_net_value, 'N/A')
        
        # Legacy Graham Number (Single-Year EPS) - Requirement 3.4
        if graham_str != 'N/A':
            graham_display = format_price_display(float(graham_str), unified_currency, unified_currency)
            lines.append(f"- Graham Number (Single-Year EPS): {graham_display}")
        else:
            lines.append(f"- Graham Number (Single-Year EPS): {graham_str}")
        
        # Normalized Graham Number (3-Year Avg EPS) - Requirement 3.5
        if normalized_graham_str != 'N/A':
            normalized_display = format_price_display(float(normalized_graham_str), unified_currency, unified_currency)
            lines.append(f"- Graham Number (3-Year Avg EPS): {normalized_display}")
        else:
            lines.append(f"- Graham Number (3-Year Avg EPS): {normalized_graham_str}")
        
        # Add note if values diverge significantly (>20% difference)
        if graham_str != 'N/A' and normalized_graham_str != 'N/A':
            single_year = float(graham_str)
            normalized = float(normalized_graham_str)
            
            # Only calculate percentage difference if single_year is not zero
            if single_year > 0:
                pct_diff = abs(normalized - single_year) / single_year * 100
                
                if pct_diff > 20:
                    if normalized > single_year:
                        lines.append(f"  - ⚠️ Note: 3-year average ({pct_diff:.0f}% higher) smooths recent earnings decline")
                    else:
                        lines.append(f"  - ⚠️ Note: 3-year average ({pct_diff:.0f}% lower) reveals earnings peaked in recent year")
        
        # EPV per share (metrics['epv'] is the whole-company value)
        # Core reports an unavailable EPV as years_used == 0 (too little history or negative average earnings)
        epv_per_share = or_default(epv_details.epv_per_share, None)
        epv_years = or_default(epv_details.years_used, 0)
        if isinstance(epv_per_share, (int, float)) and epv_per_share > 0 and epv_years:
            epv_display = format_price_display(float(epv_per_share), unified_currency, unified_currency)
            lines.append(f"- Intrinsic Value (EPV per share): {epv_display} ({epv_years}-year average earnings)")
        elif epv_years and isinstance(or_default(self.metrics.epv, None), (int, float)) and self.metrics.epv > 0:
            lines.append("- Intrinsic Value (EPV per share): N/A (no share count for the latest year)")
        else:
            lines.append("- Intrinsic Value (EPV per share): N/A (requires 7+ years of annual earnings with a positive average)")
        
        # Net-Net Value
        if net_net_str != 'N/A':
            net_net_display = format_price_display(float(net_net_str), unified_currency, unified_currency)
            lines.append(f"- Net-Net Value: {net_net_display}")
        else:
            lines.append(f"- Net-Net Value: {net_net_str}")
    
    def _add_current_price(self, lines: List[str], unified_currency: str, 
                          original_stock_currency: str) -> None:
        """Add current price line with appropriate currency display.
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for financials
            original_stock_currency: Currency stock trades in
        """
        exchange = or_default(self.financial_data.exchange, '')
        price = self.financial_data.price
        
        # Special handling for LSE stocks
        if exchange == "LSE" and unified_currency == "GBP":
            # Show as "16.50 GBP (1,650 pence)"
            price_in_pence = price * 100
            current_price_display = f"{price:.2f} GBP ({price_in_pence:,.0f} pence)"
        else:
            # Standard display
            current_price_display = format_price_display(
                price, 
                unified_currency,
                unified_currency
            )
        
        lines.append(f"- Current Price: {current_price_display}")
    
    def _add_52_week_range(self, lines: List[str], unified_currency: str, 
                          original_stock_currency: str) -> None:
        """Add 52-week range line with currency conversion if needed.
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for financials
            original_stock_currency: Currency stock trades in
        """
        week_52_high = or_default(self.financial_data.week_52_high, 0)
        week_52_low = or_default(self.financial_data.week_52_low, 0)
        
        if week_52_high > 0 and week_52_low > 0:
            # Core already expressed the 52-week values in the quote's major currency
            # (e.g. pence -> GBP), the same currency as the price before FX
            trading_currency = or_default(self.financial_data.price_currency_before_fx, None) or original_stock_currency
            
            # Convert to unified currency if needed, with the rate core already used for the price
            # (fx_rate_used: price currency -> financials currency; same pair as trading_currency here)
            if trading_currency != unified_currency:
                fx_rate = or_default(self.financial_data.fx_rate_used, None)
                
                if fx_rate:
                    high_display = format_price_display(week_52_high, trading_currency, 
                                                       unified_currency, week_52_high * fx_rate)
                    low_display = format_price_display(week_52_low, trading_currency, 
                                                      unified_currency, week_52_low * fx_rate)
                else:
                    # Fallback if conversion unavailable
                    high_display = format_price_display(week_52_high, trading_currency, 
                                                       unified_currency)
                    low_display = format_price_display(week_52_low, trading_currency, 
                                                      unified_currency)
            else:
                high_display = format_price_display(week_52_high, trading_currency, 
                                                   unified_currency)
                low_display = format_price_display(week_52_low, trading_currency, 
                                                  unified_currency)
            
            lines.append(f"- 52-Week Range: {low_display} - {high_display}")
    
    def _add_dividend_info(self, lines: List[str], unified_currency: str) -> None:
        """Add dividend information with source transparency.
        
        Requirements 2.5, 2.6, 2.7, 2.8
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for display
        """
        forward_div = or_default(self.financial_data.forward_dividend_rate, None)
        or_default(self.financial_data.dividend_source, 'Unknown')
        source_indicators = or_default(self.financial_data.dividend_sources, {})
        
        # Get most recent COMPLETE year dividend information
        # Trailing dividend should be from the last complete fiscal year, not an incomplete year
        history = or_default(self.financial_data.history, {})
        most_recent_complete_year = None
        most_recent_div_source = None
        most_recent_div_amount = None
        
        if history and self.context.latest_year:
            # The most recent complete (reported) year gives the trailing dividend
            most_recent_complete_year = self.context.latest_year_label
            most_recent_div_source = source_indicators.get(most_recent_complete_year, 'unknown')
            most_recent_div_amount = or_default(self.context.latest_row.dividend, 0.0)
        
        # Payment counts are not amounts (F21): report the count, never a per-share figure or yield
        if not or_default(self.financial_data.is_dividend_amounts, False):
            if most_recent_div_amount:
                lines.append(f"- Dividend: amount not available ({most_recent_div_amount:.0f} payments "
                             f"in {most_recent_complete_year}; payment counts only)")
            most_recent_div_amount = 0.0
        
        # Requirement 2.7: Show both trailing (complete year) and forward rate when both available
        if most_recent_div_source in ['cash_flow', 'dividend_api'] and forward_div and forward_div > 0 and most_recent_div_amount > 0:
            # Both actual dividend (from complete year) and forward rate available - show both
            actual_yield_trailing = self.context.trailing_yield_pct
            actual_yield_fwd = self.context.forward_yield_pct
            
            trailing_display = format_price_display(most_recent_div_amount, unified_currency, unified_currency)
            fwd_display = format_price_display(forward_div, unified_currency, unified_currency)
            
            # Determine label based on actual source
            if most_recent_div_source == 'dividend_api':
                lines.append(f"- Trailing Dividend: {trailing_display} (Yield: {actual_yield_trailing:.2f}%) - Declared (Dividend API) [{most_recent_complete_year}]")
            else:
                lines.append(f"- Trailing Dividend: {trailing_display} (Yield: {actual_yield_trailing:.2f}%) - Paid (Cash Flow) [{most_recent_complete_year}]")
            lines.append(f"  - Forward Rate: {fwd_display} (Yield: {actual_yield_fwd:.2f}%)")
        elif most_recent_div_amount and most_recent_div_amount > 0:
            # Have trailing dividend from complete year, but no forward rate
            actual_yield = self.context.trailing_yield_pct
            div_display = format_price_display(most_recent_div_amount, unified_currency, unified_currency)
            
            # Determine label based on source (Requirements 2.6)
            if most_recent_div_source == 'dividend_api':
                lines.append(f"- Trailing Dividend: {div_display} (Yield: {actual_yield:.2f}%) - Declared (Dividend API) [{most_recent_complete_year}]")
            elif most_recent_div_source == 'cash_flow':
                lines.append(f"- Trailing Dividend: {div_display} (Yield: {actual_yield:.2f}%) - Paid (Cash Flow) [{most_recent_complete_year}]")
            elif most_recent_div_source == 'dividends_array':
                lines.append(f"- Trailing Dividend: {div_display} (Yield: {actual_yield:.2f}%) - Paid (Dividend history) [{most_recent_complete_year}]")
            else:
                lines.append(f"- Trailing Dividend: {div_display} (Yield: {actual_yield:.2f}%) [{most_recent_complete_year}]")
        elif forward_div and forward_div > 0:
            # No trailing dividend from complete year, only forward rate available
            actual_yield = self.context.forward_yield_pct
            div_display = format_price_display(forward_div, unified_currency, unified_currency)
            lines.append(f"- Forward Annual Dividend: {div_display} (Yield: {actual_yield:.2f}%)")
            lines.append("  - ⚠️ No historical dividend data available - using forward declared rate")
    
    def _add_valuation_ratios(self, lines: List[str]) -> None:
        """Add valuation ratios (P/E, Price/Book).
        
        Args:
            lines: List to append lines to
        """
        pe_ratio = or_default(self.financial_data.pe_ratio, 0)
        price_to_book = or_default(self.financial_data.price_to_book, 0)
        
        if pe_ratio > 0:
            lines.append(f"- P/E Ratio (Current Year): {pe_ratio:.2f}")
        
        # Add three-year average P/E if available
        three_year_pe = or_default(self.metrics.three_year_avg_pe, ThreeYearAvgPE())
        if isinstance(three_year_pe, ThreeYearAvgPE):
            pe_on_avg = or_default(three_year_pe.pe_on_avg, None)
            avg_eps = or_default(three_year_pe.three_year_avg_eps, None)
            years_used = or_default(three_year_pe.years_used, ())
            
            if pe_on_avg != 'N/A' and avg_eps != 'N/A' and years_used:
                # Format years range
                if len(years_used) >= 2:
                    first_year = fiscal_year(years_used[-1])  # Oldest year
                    last_year = fiscal_year(years_used[0])    # Most recent year
                    years_str = f"{first_year}-{last_year}"
                else:
                    years_str = "recent years"
                
                lines.append(f"- P/E Ratio (3-Year Avg): {pe_on_avg:.2f} (based on avg EPS of {avg_eps:.2f} from {years_str})")
        
        if price_to_book > 0:
            lines.append(f"- Price/Book: {price_to_book:.2f}")
