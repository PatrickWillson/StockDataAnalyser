"""Methodology Notes section generator for dossier.

This module generates the methodology notes section of the stock analysis dossier,
explaining how key valuation metrics are calculated including P/E ratio, Graham Number,
EPV (Earnings Power Value), Net-Net Value, and Margin of Safety.
"""

from typing import List, Dict, Any, Optional


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


class MethodologySection:
    """Generates the methodology notes section of the dossier.
    
    This section explains how key valuation metrics are calculated:
    - P/E Ratio calculation methodology
    - Graham Number formula and explanation
    - EPV (Earnings Power Value) with Graham's full-cycle method
    - Net-Net Value calculation
    - Margin of Safety explanation
    
    Requirements: 2.4
    """
    
    def __init__(self, financial_data: Dict[str, Any], metrics: Dict[str, Any]):
        """Initialize methodology section.
        
        Args:
            financial_data: Dictionary containing financial data (FinancialData DTO)
            metrics: Dictionary containing Graham metrics (GrahamMetrics DTO)
        """
        self.financial_data = financial_data
        self.metrics = metrics
    
    def generate(self) -> List[str]:
        """Generate methodology notes section content.
        
        Returns:
            List[str]: List of markdown lines for methodology notes section
        """
        lines = []
        
        # Section header
        lines.append("")
        lines.append("## METHODOLOGY NOTES")
        lines.append("*How key metrics are calculated*")
        lines.append("")
        
        # Extract currency and history
        unified_currency = self.financial_data.get('currency', 'USD')
        history = self.financial_data.get('history', {})
        
        # Get EPV details
        epv_details = self.metrics.get('epv_details', {})
        
        # Get most recent EPS for P/E explanation
        most_recent_eps = self._get_most_recent_eps(history)
        
        lines.append("### Valuation Metrics:")
        
        # P/E Ratio explanation
        self._add_pe_ratio_explanation(lines, unified_currency, most_recent_eps)
        
        # Profitability Metrics explanation
        self._add_profitability_metrics_explanation(lines)
        
        # Graham Number explanation
        self._add_graham_number_explanation(lines, unified_currency)
        
        # EPV explanation
        self._add_epv_explanation(lines, unified_currency, epv_details)
        
        # Net-Net Value explanation
        self._add_net_net_explanation(lines, unified_currency)
        
        # Margin of Safety explanation
        self._add_margin_of_safety_explanation(lines)
        
        # TTM methodology explanation
        self._add_ttm_methodology_explanation(lines)
        
        lines.append("")
        lines.append("---")
        
        return lines
    
    def _get_most_recent_eps(self, history: Dict[str, Any]) -> float:
        """Get most recent EPS from history with financial data.
        
        Args:
            history: Financial history dictionary
            
        Returns:
            float: Most recent EPS value, or 0 if not found
        """
        if not history:
            return 0
        
        sorted_years = sorted(history.keys(), reverse=True)
        for year in sorted_years:
            year_data = history[year]
            if year_data.get('revenue', 0.0) > 0 or year_data.get('net_income', 0.0) != 0 or year_data.get('total_equity', 0.0) > 0:
                return year_data.get('eps', 0)
        
        return 0
    
    def _add_pe_ratio_explanation(self, lines: List[str], unified_currency: str, 
                                  most_recent_eps: float) -> None:
        """Add P/E ratio calculation explanation.
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for display
            most_recent_eps: Most recent EPS value
        """
        pe_ratio = self.financial_data.get('pe_ratio', 0)
        
        if pe_ratio > 0 and most_recent_eps and most_recent_eps > 0:
            eps_display = format_price_display(most_recent_eps, unified_currency, unified_currency)
            lines.append(f"- **P/E Ratio ({pe_ratio:.2f})**: Current Price / Most Recent Annual EPS")
            lines.append(f"  - Calculated from audited financials, not API pre-calculated ratios")
            lines.append(f"  - EPS: {eps_display} (Net Income / Shares Outstanding)")
    
    def _add_profitability_metrics_explanation(self, lines: List[str]) -> None:
        """Add profitability metrics calculation explanation.
        
        Args:
            lines: List to append lines to
        """
        lines.append("- **Profitability Metrics (ROE, ROA, Profit Margin)**:")
        lines.append("  - **ROE (Return on Equity)**: Net Income / Total Stockholder Equity")
        lines.append("    - Calculated from most recent annual audited data")
        lines.append("    - Measures how efficiently company uses shareholder equity to generate profit")
        lines.append("  - **ROA (Return on Assets)**: Net Income / Total Assets")
        lines.append("    - Calculated from most recent annual audited data")
        lines.append("    - Measures how efficiently company uses all assets to generate profit")
        lines.append("  - **Profit Margin**: Net Income / Revenue")
        lines.append("    - Calculated from most recent annual audited data")
        lines.append("    - Measures what percentage of revenue becomes profit")
        lines.append("  - **Why Annual Data vs TTM:**")
        lines.append("    - Annual data comes from audited financial statements (verified)")
        lines.append("    - TTM data may include estimates and unaudited quarters")
        lines.append("    - Consistency: All Graham metrics (P/E, P/B, BVPS, ROE, ROA, Margin) use same fiscal year")
        lines.append("    - Comparability: Annual data allows year-over-year comparison of audited results")
    
    def _add_graham_number_explanation(self, lines: List[str], unified_currency: str) -> None:
        """Add Graham Number formula explanation.
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for display
        """
        graham_number = self.metrics.get('graham_number', 0)
        
        if isinstance(graham_number, (int, float)) and graham_number > 0:
            graham_display = format_price_display(graham_number, unified_currency, unified_currency)
            lines.append(f"- **Graham Number ({graham_display})**: √(22.5 × EPS × BVPS)")
            lines.append(f"  - Conservative intrinsic value estimate")
            lines.append(f"  - Based on Benjamin Graham's formula from 'The Intelligent Investor'")
    
    def _add_epv_explanation(self, lines: List[str], unified_currency: str, 
                            epv_details: Dict[str, Any]) -> None:
        """Add EPV (Earnings Power Value) methodology explanation.
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for display
            epv_details: EPV calculation details dictionary
        """
        epv_value = self.metrics.get('epv', 0)
        
        if epv_value > 0:
            ticker = self.financial_data.get('ticker', 'UNKNOWN')
            epv_per_share = epv_details.get('epv_per_share', 0)
            normalized_earnings = epv_details.get('normalized_earnings', 0)
            years_used = epv_details.get('years_used', 0)
            cost_of_capital = epv_details.get('cost_of_capital', 0.10)
            years_included = epv_details.get('years_included', [])
            net_incomes = epv_details.get('net_incomes', [])
            
            lines.append(f"- **EPV - Earnings Power Value**")
            lines.append(f"")
            lines.append(f"  **Graham's Full-Cycle Method:**")
            lines.append(f"  - Uses 7-10 year average of net income")
            lines.append(f"  - **Includes ALL years** (profitable and unprofitable)")
            lines.append(f"  - Loss years reduce the average (real value destruction)")
            lines.append(f"  - Only extraordinary one-time events should be adjusted")
            lines.append(f"")
            lines.append(f"  **Calculation for {ticker}:**")
            lines.append(f"  - Years Used: {years_used}")
            
            # Show years range and net incomes
            if years_included and net_incomes:
                # Format net incomes with currency
                net_income_strs = []
                for ni in net_incomes:
                    if ni >= 0:
                        net_income_strs.append(f"{unified_currency}{ni:,.0f}")
                    else:
                        net_income_strs.append(f"-{unified_currency}{abs(ni):,.0f}")
                
                # Show years range
                if len(years_included) > 0:
                    first_year = years_included[-1].split('-')[0]  # Oldest year
                    last_year = years_included[0].split('-')[0]    # Most recent year
                    lines.append(f"  - Years: {first_year}-{last_year}")
                
                # Show net incomes
                lines.append(f"  - Net Incomes: {', '.join(net_income_strs)}")
            
            if normalized_earnings > 0:
                lines.append(f"  - Normalized Earnings: {unified_currency}{normalized_earnings:,.0f} (average including losses)")
            
            lines.append(f"  - EPV: {unified_currency}{epv_value:,.0f} ({unified_currency}{normalized_earnings:,.0f} / {cost_of_capital:.0%})")
            
            if epv_per_share > 0:
                epv_per_share_display = format_price_display(epv_per_share, unified_currency, unified_currency)
                lines.append(f"  - EPV Per Share: {epv_per_share_display}")
            
            lines.append(f"")
            
            # Add note about loss years or consistent profitability
            loss_years = [ni for ni in net_incomes if ni < 0]
            if loss_years:
                loss_count = len(loss_years)
                # Identify which years were losses
                loss_year_labels = []
                for i, ni in enumerate(net_incomes):
                    if ni < 0 and i < len(years_included):
                        loss_year_labels.append(years_included[i].split('-')[0])
                
                if loss_year_labels:
                    loss_years_str = ', '.join(loss_year_labels)
                    lines.append(f"  **Note**: The {years_used}-year average includes {loss_count} loss year{'s' if loss_count > 1 else ''} ({loss_years_str}), reflecting the company's full business cycle performance per Graham's methodology.")
                else:
                    lines.append(f"  **Note**: The {years_used}-year average includes {loss_count} loss year{'s' if loss_count > 1 else ''}, reflecting the company's full business cycle performance per Graham's methodology.")
            else:
                lines.append(f"  **Note**: All {years_used} years were profitable, demonstrating consistent earnings power.")
            
            lines.append(f"")
            lines.append(f"  **Graham's Principle**: *\"The concept of 'earning power' implies a fairly confident expectation of certain future results, based on past performance under varying conditions. The record must cover a number of years, first because a continued or repeated performance is always more impressive than a single occurrence and secondly because the average of a fairly long period will tend to absorb and equalize the distorting influences of the business cycle.\"*")
    
    def _add_net_net_explanation(self, lines: List[str], unified_currency: str) -> None:
        """Add Net-Net Value calculation explanation.
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for display
        """
        net_net = self.metrics.get('net_net_value', 0)
        
        if isinstance(net_net, (int, float)) and net_net > 0:
            net_net_display = format_price_display(net_net, unified_currency, unified_currency)
            lines.append(f"- **Net-Net Value ({net_net_display})**: (Current Assets - Total Liabilities) / Shares")
            lines.append(f"  - Conservative liquidation value estimate")
            lines.append(f"  - Graham's 'cigar butt' valuation for distressed situations")
    
    def _add_margin_of_safety_explanation(self, lines: List[str]) -> None:
        """Add Margin of Safety calculation explanation.
        
        Args:
            lines: List to append lines to
        """
        mos = self.metrics.get('margin_of_safety', 0)
        
        if isinstance(mos, (int, float)):
            lines.append(f"- **Margin of Safety ({mos:.1f}%)**: (Graham Number - Price) / Graham Number × 100")
            lines.append(f"  - Percentage discount to intrinsic value")
            lines.append(f"  - Graham recommended minimum 20-30% for defensive investors")
    
    def _add_ttm_methodology_explanation(self, lines: List[str]) -> None:
        """Add TTM (Trailing Twelve Months) methodology explanation.
        
        Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7
        
        Args:
            lines: List to append lines to
        """
        lines.append("")
        lines.append("### TTM (Trailing Twelve Months) Calculations:")
        lines.append("")
        lines.append("TTM calculations provide more current financial metrics by using the most recent 12 months of periodic data:")
        lines.append("")
        
        lines.append("**Income Statement Items** (Revenue, Net Income, EPS):")
        lines.append("- **Quarterly reporters**: Sum of last 4 quarters")
        lines.append("- **Semi-annual reporters**: Sum of last 2 periods (H1 + H2)")
        lines.append("- **EPS Calculation**: TTM EPS = Sum(Net Income) / Most Recent Shares Outstanding")
        lines.append("  - **Important**: Do NOT sum EPS values directly (incorrect when share count changes)")
        lines.append("  - Example: If shares increase from 50M to 55M during the year, summing EPS overstates earnings power")
        lines.append("")
        
        lines.append("**Balance Sheet Items** (Assets, Liabilities, Equity):")
        lines.append("- Use most recent period value (not summed)")
        lines.append("- Balance sheet represents point-in-time snapshot, not cumulative")
        lines.append("")
        
        lines.append("**Reporting Frequency Detection**:")
        lines.append("- Average interval ~90 days (±15 days) → Quarterly")
        lines.append("- Average interval ~180 days (±30 days) → Semi-annual")
        lines.append("- Irregular intervals → Warning + attempt to use most recent continuous 12-month period")
        lines.append("")
        
        lines.append("**TTM vs Annual**:")
        lines.append("- **TTM**: More current (includes most recent quarter)")
        lines.append("  - Reflects recent business performance")
        lines.append("  - May include unaudited quarterly data")
        lines.append("  - Better for fast-changing businesses")
        lines.append("- **Annual**: More stable (full fiscal year, audited)")
        lines.append("  - Verified by external auditors")
        lines.append("  - Smooths out seasonal variations")
        lines.append("  - Graham's preferred methodology")
        lines.append("- Both are valuable for different reasons")
        lines.append("")
        
        lines.append("**Limitations**:")
        lines.append("- TTM data may be unaudited (quarterly reports)")
        lines.append("- Seasonal businesses may show distortions")
        lines.append("- Currency conversion uses current rate (not historical)")
        lines.append("- Requires sufficient periodic data (4 quarters or 2 semi-annual periods)")
        lines.append("- Data gaps or irregular reporting may prevent TTM calculation")
