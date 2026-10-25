"""Executive Summary section generator for dossier.

This module generates the executive summary section of the stock analysis dossier,
including verdict, intrinsic values, margin of safety, current price, and dividend information.
"""

from typing import List, Dict, Any, Optional
from output.sections.base import DossierSection


def format_price_display(price: float, trading_currency: str, financials_currency: str, 
                        converted_value: Optional[float] = None) -> str:
    """
    Format price display with trading currency first.
    
    Requirements 4.1, 4.2, 4.3, 4.4:
    - Shows trading currency first (e.g., "1,650 GBX")
    - Shows conversion when currencies differ (e.g., "1,650 GBX (16.50 GBP)")
    - Consistent format across all price displays
    
    Args:
        price: Price value in trading currency
        trading_currency: Currency the stock trades in
        financials_currency: Currency of financial statements
        converted_value: Optional converted value in financials currency
        
    Returns:
        Formatted price string
    """
    # Format price with commas and 2 decimal places
    formatted_price = f"{price:,.2f}"
    
    # Single currency case
    if trading_currency == financials_currency:
        return f"{formatted_price} {trading_currency}"
    
    # Dual currency case - show trading currency first, then conversion
    if converted_value is not None:
        formatted_converted = f"{converted_value:,.2f}"
        return f"{formatted_price} {trading_currency} ({formatted_converted} {financials_currency})"
    
    # Fallback if no converted value provided but currencies differ
    return f"{formatted_price} {trading_currency}"


class ExecutiveSummarySection(DossierSection):
    """Generates the executive summary section of the dossier.
    
    This section includes:
    - Verdict (UNDERVALUED/FAIRLY VALUED/OVERVALUED)
    - Intrinsic values (Graham Number, EPV, Net-Net)
    - Margin of Safety
    - Current price and 52-week range
    - Dividend information with source transparency
    - Valuation ratios (P/E, Price/Book)
    
    Requirements: 1.4, 2.1
    """
    
    def __init__(self, financial_data: Dict[str, Any], metrics: Dict[str, Any]):
        """Initialize executive summary section.
        
        Args:
            financial_data: Dictionary containing financial data (FinancialData DTO)
            metrics: Dictionary containing Graham metrics (GrahamMetrics DTO)
        """
        self.financial_data = financial_data
        self.metrics = metrics
    
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
        unified_currency = self.financial_data.get('currency', 'USD')
        original_stock_currency = self.financial_data.get('original_stock_currency', unified_currency)
        
        # Verdict
        lines.append(f"- Verdict: **{self.metrics['verdict']}**")
        
        # Intrinsic values
        self._add_intrinsic_values(lines, unified_currency)
        
        # Margin of Safety - Requirement 10.1
        # Display normalized MoS as primary value with limiting factor
        mos_details = self.metrics.get('margin_of_safety_details', {})
        mos_percentage = mos_details.get('mos_percentage', self.metrics.get('margin_of_safety', 'N/A'))
        limiting_factor = mos_details.get('limiting_factor', 'N/A')
        intrinsic_value_used = mos_details.get('intrinsic_value_used', 'N/A')
        
        if mos_percentage != 'N/A':
            # Format the MoS display with limiting factor
            if limiting_factor != 'N/A':
                lines.append(f"- Margin of Safety: {mos_percentage:.1f}% (Capped by {limiting_factor})")
                
                # Add explanatory note about which intrinsic value was used
                if intrinsic_value_used != 'N/A':
                    iv_display = format_price_display(float(intrinsic_value_used), unified_currency, unified_currency)
                    lines.append(f"  - Conservative Intrinsic Value: {iv_display}")
            else:
                lines.append(f"- Margin of Safety: {mos_percentage:.1f}%")
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
        graham_str = self.metrics['graham_number']
        normalized_graham_str = self.metrics.get('normalized_graham_number', 'N/A')
        epv_details = self.metrics.get('epv_details') or {}
        net_net_str = self.metrics.get('net_net_value', 'N/A')
        
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
        epv_per_share = epv_details.get('epv_per_share')
        epv_years = epv_details.get('years_used', 0)
        if isinstance(epv_per_share, (int, float)) and epv_per_share > 0 and epv_years:
            epv_display = format_price_display(float(epv_per_share), unified_currency, unified_currency)
            lines.append(f"- Intrinsic Value (EPV per share): {epv_display} ({epv_years}-year average earnings)")
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
        exchange = self.financial_data.get('exchange', '')
        price = self.financial_data['price']
        
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
        week_52_high = self.financial_data.get('week_52_high', 0)
        week_52_low = self.financial_data.get('week_52_low', 0)
        exchange = self.financial_data.get('exchange', '')
        
        if week_52_high > 0 and week_52_low > 0:
            # For LSE stocks, the 52-week values have already been converted from GBX to GBP
            # in the EODHD client (London Fix), so we need to use GBP as the trading currency
            trading_currency = original_stock_currency
            if exchange == "LSE" and original_stock_currency == "GBX":
                trading_currency = "GBP"  # Values are already in GBP after London Fix
            
            # Convert to unified currency if needed
            if trading_currency != unified_currency:
                # Use CurrencyConverter for proper GBX/GBP handling
                from core.currency_converter import CurrencyConverter
                converter = CurrencyConverter()
                
                high_converted, high_success = converter.convert(week_52_high, trading_currency, unified_currency)
                low_converted, low_success = converter.convert(week_52_low, trading_currency, unified_currency)
                
                if high_success and low_success:
                    high_display = format_price_display(week_52_high, trading_currency, 
                                                       unified_currency, high_converted)
                    low_display = format_price_display(week_52_low, trading_currency, 
                                                      unified_currency, low_converted)
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
        forward_div = self.financial_data.get('forward_dividend_rate')
        dividend_source = self.financial_data.get('dividend_source', 'Unknown')
        source_indicators = self.financial_data.get('dividend_sources', {})
        
        # Get most recent COMPLETE year dividend information
        # Trailing dividend should be from the last complete fiscal year, not an incomplete year
        history = self.financial_data.get('history', {})
        most_recent_complete_year = None
        most_recent_div_source = None
        most_recent_div_amount = None
        
        if history:
            sorted_years = sorted(history.keys(), reverse=True)
            
            # Find the most recent year with complete financial data
            for year_key in sorted_years:
                year_data = history[year_key]
                has_financial_data = (
                    year_data.get('revenue', 0.0) > 0 or 
                    year_data.get('net_income', 0.0) != 0 or 
                    year_data.get('total_equity', 0.0) > 0
                )
                
                if has_financial_data:
                    # This is a complete year - use it for trailing dividend
                    most_recent_complete_year = year_key.split('-')[0]
                    most_recent_div_source = source_indicators.get(most_recent_complete_year, 'unknown')
                    most_recent_div_amount = year_data.get('dividend', 0.0)
                    break
        
        # Requirement 2.7: Show both trailing (complete year) and forward rate when both available
        if most_recent_div_source in ['cash_flow', 'dividend_api'] and forward_div and forward_div > 0 and most_recent_div_amount > 0:
            # Both actual dividend (from complete year) and forward rate available - show both
            actual_yield_trailing = (most_recent_div_amount / self.financial_data['price']) * 100
            actual_yield_fwd = (forward_div / self.financial_data['price']) * 100
            
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
            actual_yield = (most_recent_div_amount / self.financial_data['price']) * 100
            div_display = format_price_display(most_recent_div_amount, unified_currency, unified_currency)
            
            # Determine label based on source (Requirements 2.6)
            if most_recent_div_source == 'dividend_api':
                lines.append(f"- Trailing Dividend: {div_display} (Yield: {actual_yield:.2f}%) - Declared (Dividend API) [{most_recent_complete_year}]")
            elif most_recent_div_source == 'cash_flow':
                lines.append(f"- Trailing Dividend: {div_display} (Yield: {actual_yield:.2f}%) - Paid (Cash Flow) [{most_recent_complete_year}]")
            else:
                lines.append(f"- Trailing Dividend: {div_display} (Yield: {actual_yield:.2f}%) [{most_recent_complete_year}]")
        elif forward_div and forward_div > 0:
            # No trailing dividend from complete year, only forward rate available
            actual_yield = (forward_div / self.financial_data['price']) * 100
            div_display = format_price_display(forward_div, unified_currency, unified_currency)
            lines.append(f"- Forward Annual Dividend: {div_display} (Yield: {actual_yield:.2f}%)")
            lines.append(f"  - ⚠️ No historical dividend data available - using forward declared rate")
    
    def _add_valuation_ratios(self, lines: List[str]) -> None:
        """Add valuation ratios (P/E, Price/Book).
        
        Args:
            lines: List to append lines to
        """
        pe_ratio = self.financial_data.get('pe_ratio', 0)
        price_to_book = self.financial_data.get('price_to_book', 0)
        
        if pe_ratio > 0:
            lines.append(f"- P/E Ratio (Current Year): {pe_ratio:.2f}")
        
        # Add three-year average P/E if available
        three_year_pe = self.metrics.get('three_year_avg_pe', {})
        if isinstance(three_year_pe, dict):
            pe_on_avg = three_year_pe.get('pe_on_avg')
            avg_eps = three_year_pe.get('three_year_avg_eps')
            years_used = three_year_pe.get('years_used', [])
            
            if pe_on_avg != 'N/A' and avg_eps != 'N/A' and years_used:
                # Format years range
                if len(years_used) >= 2:
                    first_year = years_used[-1].split('-')[0]  # Oldest year
                    last_year = years_used[0].split('-')[0]    # Most recent year
                    years_str = f"{first_year}-{last_year}"
                else:
                    years_str = "recent years"
                
                lines.append(f"- P/E Ratio (3-Year Avg): {pe_on_avg:.2f} (based on avg EPS of {avg_eps:.2f} from {years_str})")
        
        if price_to_book > 0:
            lines.append(f"- Price/Book: {price_to_book:.2f}")
