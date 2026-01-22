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
        
        # Margin of Safety
        lines.append(f"- Margin of Safety: {self.metrics['margin_of_safety']}")
        
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
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for display
        """
        graham_str = self.metrics['graham_number']
        epv_str = self.metrics['epv']
        net_net_str = self.metrics.get('net_net_value', 'N/A')
        
        # Graham Number
        if graham_str != 'N/A':
            graham_display = format_price_display(float(graham_str), unified_currency, unified_currency)
            lines.append(f"- Intrinsic Value (Graham): {graham_display}")
        else:
            lines.append(f"- Intrinsic Value (Graham): {graham_str}")
        
        # EPV
        if epv_str != 'N/A':
            epv_display = format_price_display(float(epv_str), unified_currency, unified_currency)
            lines.append(f"- Intrinsic Value (EPV): {epv_display}")
        else:
            lines.append(f"- Intrinsic Value (EPV): {epv_str}")
        
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
        
        if week_52_high > 0 and week_52_low > 0:
            # Convert to unified currency if needed
            if original_stock_currency != unified_currency:
                # Use CurrencyConverter for proper GBX/GBP handling
                from core.currency_converter import CurrencyConverter
                converter = CurrencyConverter()
                
                high_converted, high_success = converter.convert(week_52_high, original_stock_currency, unified_currency)
                low_converted, low_success = converter.convert(week_52_low, original_stock_currency, unified_currency)
                
                if high_success and low_success:
                    high_display = format_price_display(week_52_high, original_stock_currency, 
                                                       unified_currency, high_converted)
                    low_display = format_price_display(week_52_low, original_stock_currency, 
                                                      unified_currency, low_converted)
                else:
                    # Fallback if conversion unavailable
                    high_display = format_price_display(week_52_high, original_stock_currency, 
                                                       unified_currency)
                    low_display = format_price_display(week_52_low, original_stock_currency, 
                                                      unified_currency)
            else:
                high_display = format_price_display(week_52_high, original_stock_currency, 
                                                   unified_currency)
                low_display = format_price_display(week_52_low, original_stock_currency, 
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
        
        # Get most recent year dividend information
        history = self.financial_data.get('history', {})
        most_recent_year = None
        most_recent_div_source = None
        most_recent_div_amount = None
        most_recent_year_incomplete = False
        
        if history:
            sorted_years = sorted(history.keys(), reverse=True)
            if sorted_years:
                most_recent_year = sorted_years[0].split('-')[0]
                most_recent_div_source = source_indicators.get(most_recent_year, 'unknown')
                most_recent_div_amount = history[sorted_years[0]].get('dividend', 0.0)
                
                # Check if most recent year has complete financial data
                year_data = history[sorted_years[0]]
                has_financial_data = (
                    year_data.get('revenue', 0.0) > 0 or 
                    year_data.get('net_income', 0.0) != 0 or 
                    year_data.get('total_equity', 0.0) > 0
                )
                most_recent_year_incomplete = not has_financial_data and most_recent_div_amount > 0
        
        # Requirement 2.7: Show both values when both are available for most recent year
        if most_recent_div_source in ['cash_flow', 'dividend_api'] and forward_div and forward_div > 0 and most_recent_div_amount > 0:
            # Both actual dividend and forward rate available - show both
            actual_yield_cf = (most_recent_div_amount / self.financial_data['price']) * 100
            actual_yield_fwd = (forward_div / self.financial_data['price']) * 100
            
            cf_display = format_price_display(most_recent_div_amount, unified_currency, unified_currency)
            fwd_display = format_price_display(forward_div, unified_currency, unified_currency)
            
            # Determine label based on actual source
            if most_recent_div_source == 'dividend_api':
                dividend_label = f"- Trailing Dividend: {cf_display} (Yield: {actual_yield_cf:.2f}%) - Declared (Dividend API)"
                if most_recent_year_incomplete:
                    dividend_label += f" [{most_recent_year} - Incomplete Year]"
                lines.append(dividend_label)
            else:
                lines.append(f"- Trailing Dividend: {cf_display} (Yield: {actual_yield_cf:.2f}%) - Paid (Cash Flow)")
            lines.append(f"  - Forward Rate: {fwd_display} (Yield: {actual_yield_fwd:.2f}%)")
        elif forward_div and forward_div > 0:
            actual_yield = (forward_div / self.financial_data['price']) * 100
            # Dividend is already in unified currency
            div_display = format_price_display(forward_div, unified_currency, unified_currency)
            
            # Determine label based on source (Requirements 2.6)
            if most_recent_div_source == 'dividend_api':
                # Using Dividend API (declared dividends with exact dates)
                dividend_label = f"- Trailing Dividend: {div_display} (Yield: {actual_yield:.2f}%) - Declared (Dividend API)"
                if most_recent_year_incomplete:
                    dividend_label += f" [{most_recent_year} - Incomplete Year]"
                lines.append(dividend_label)
            elif most_recent_div_source == 'cash_flow':
                # Using actual cash flow data
                lines.append(f"- Trailing Dividend: {div_display} (Yield: {actual_yield:.2f}%) - Paid (Cash Flow)")
            elif most_recent_div_source == 'forward_rate':
                # Using forward rate - add warning (Requirement 2.5)
                lines.append(f"- Trailing Dividend: {div_display} (Yield: {actual_yield:.2f}%) - Declared (Forward Rate)")
                lines.append(f"  - ⚠️ {most_recent_year} dividend uses forward declared rate (cash flow data unavailable) - this is an estimate, not historical fact")
            else:
                # Unknown source or mixed
                lines.append(f"- Trailing Dividend: {div_display} (Yield: {actual_yield:.2f}%)")
    
    def _add_valuation_ratios(self, lines: List[str]) -> None:
        """Add valuation ratios (P/E, Price/Book).
        
        Args:
            lines: List to append lines to
        """
        pe_ratio = self.financial_data.get('pe_ratio', 0)
        price_to_book = self.financial_data.get('price_to_book', 0)
        
        if pe_ratio > 0:
            lines.append(f"- P/E Ratio: {pe_ratio:.2f}")
        if price_to_book > 0:
            lines.append(f"- Price/Book: {price_to_book:.2f}")
