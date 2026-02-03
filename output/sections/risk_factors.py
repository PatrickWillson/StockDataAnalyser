"""Risk Factors section generator for dossier.

This module generates the risk factors section of the stock analysis dossier,
including market risk, financial strength risk, operational stability risk,
dividend risk, valuation risk, and data quality risk assessments.
"""

from typing import List, Dict, Any
from output.sections.base import DossierSection


def format_price_display(price: float, trading_currency: str, financials_currency: str, 
                        converted_value: float = None) -> str:
    """
    Format price display with trading currency first.
    
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


class RiskFactorsSection(DossierSection):
    """Generates the risk factors section of the dossier.
    
    This section provides a comprehensive risk assessment based on Graham's
    investment criteria:
    - Market & Liquidity Risk
    - Financial Strength Risk
    - Operational Stability Risk
    - Dividend Sustainability Risk
    - Valuation Risk (Margin of Safety)
    - Data Quality Risk
    
    Requirements: 2.3
    """
    
    def __init__(self, financial_data: Dict[str, Any], metrics: Dict[str, Any]):
        """Initialize risk factors section.
        
        Args:
            financial_data: Dictionary containing financial data (FinancialData DTO)
            metrics: Dictionary containing Graham metrics (GrahamMetrics DTO)
        """
        self.financial_data = financial_data
        self.metrics = metrics
    
    def generate(self) -> List[str]:
        """Generate risk factors section content.
        
        Returns:
            List[str]: List of markdown lines for risk factors section
        """
        lines = []
        
        # Generate single comprehensive risk factors section
        lines.extend(self._generate_second_risk_section())
        
        return lines
    
    def _generate_first_risk_section(self) -> List[str]:
        """Generate first risk factors section (quantifiable risks based on financial data).
        
        Returns:
            List[str]: List of markdown lines for first risk section
        """
        lines = []
        
        # Section header
        lines.append("")
        lines.append("## RISK FACTORS")
        lines.append("*Quantifiable risks based on financial data*")
        lines.append("")
        lines.append("**Graham's Principle**: *\"The essence of investment management is the management of risks, not the management of returns.\"*")
        lines.append("")
        
        # Extract currency information
        unified_currency = self.financial_data.get('currency', 'USD')
        
        # Calculate risk metrics from available data
        history = self.financial_data.get('history', {})
        if history:
            sorted_years_risk = sorted(history.keys(), reverse=True)
            
            # Find most recent year with financial data
            latest_year_risk = None
            for year in sorted_years_risk:
                year_data = history[year]
                if year_data.get('revenue', 0.0) > 0 or year_data.get('net_income', 0.0) != 0 or year_data.get('total_equity', 0.0) > 0:
                    latest_year_risk = year
                    break
            
            if latest_year_risk:
                latest_data_risk = history[latest_year_risk]
                
                # 1. Market & Liquidity Risks
                self._add_market_liquidity_risks_first(lines, latest_data_risk)
                
                # 2. Financial Strength Risks
                self._add_financial_strength_risks_first(lines, latest_data_risk, unified_currency)
                
                # 3. Operational Stability Risks
                self._add_operational_stability_risks_first(lines, history, sorted_years_risk)
                
                # 4. Dividend Risk
                self._add_dividend_risk_first(lines, history, sorted_years_risk, unified_currency)
                
                # 5. Valuation Risk
                self._add_valuation_risk_first(lines, unified_currency)
                
                # 6. Data Quality Risks
                self._add_data_quality_risks_first(lines)
                
                lines.append("")
                lines.append("**Risk Assessment Summary**: This analysis identifies quantifiable risks based on financial data. All investments carry risk. Graham emphasized that the margin of safety is the primary defense against adverse outcomes.")
        else:
            lines.append("Insufficient financial data available for risk assessment.")
        
        lines.append("")
        lines.append("---")
        
        return lines

    def _add_market_liquidity_risks_first(self, lines: List[str], latest_data_risk: Dict[str, Any]) -> None:
        """Add market and liquidity risks for first section.
        
        Args:
            lines: List to append lines to
            latest_data_risk: Most recent year's financial data
        """
        lines.append("### Market & Liquidity Risks:")
        
        # Beta risk
        beta = self.financial_data.get('beta', 0)
        if beta is None:
            beta = 0
        if beta > 0:
            if beta < 0.5:
                lines.append(f"- **Volatility (Beta: {beta:.3f})**: Low market correlation")
                lines.append(f"  - Note: Beta varies by calculation period and benchmark. Market sources report 0.33-0.50 range.")
                lines.append(f"  - Low beta may reflect limited liquidity and defensive sector characteristics")
            elif beta < 1.0:
                lines.append(f"- **Volatility (Beta: {beta:.3f})**: Below-market volatility (defensive)")
            elif beta < 1.5:
                lines.append(f"- **Volatility (Beta: {beta:.3f})**: Above-market volatility")
            else:
                lines.append(f"- **Volatility (Beta: {beta:.3f})**: High volatility (2x+ market swings)")
        
        # Liquidity risk (if volume data available)
        avg_volume = self.financial_data.get('average_volume', 0)
        market_cap = self.financial_data.get('price', 0) * latest_data_risk.get('shares_outstanding', 0)
        if avg_volume > 0 and market_cap > 0:
            # Calculate days to liquidate 1% of market cap
            shares_1pct = (market_cap * 0.01) / self.financial_data.get('price', 1)
            days_to_liquidate = shares_1pct / avg_volume if avg_volume > 0 else 999
            
            if days_to_liquidate > 10:
                lines.append(f"- **Liquidity Risk**: Average volume {avg_volume:,.0f} shares/day")
                lines.append(f"  - Would take {days_to_liquidate:.1f} days to liquidate 1% of market cap")
                lines.append(f"  - Limited liquidity may cause wider bid-ask spreads and price impact")
            elif days_to_liquidate > 5:
                lines.append(f"- **Liquidity Risk**: Moderate (avg volume {avg_volume:,.0f} shares/day)")
            else:
                lines.append(f"- **Liquidity**: Adequate (avg volume {avg_volume:,.0f} shares/day)")
        
        lines.append("")
    
    def _add_financial_strength_risks_first(self, lines: List[str], latest_data_risk: Dict[str, Any], 
                                           unified_currency: str) -> None:
        """Add financial strength risks for first section.
        
        Args:
            lines: List to append lines to
            latest_data_risk: Most recent year's financial data
            unified_currency: Currency for display
        """
        lines.append("### Financial Strength Risks:")
        
        # Current ratio risk
        current_assets = latest_data_risk.get('current_assets', 0.0)
        current_liabilities = latest_data_risk.get('current_liabilities', 0.0)
        if current_liabilities > 0:
            current_ratio = current_assets / current_liabilities
            if current_ratio < 1.0:
                lines.append(f"- **Liquidity Crisis Risk**: Current ratio {current_ratio:.2f}x (below 1.0x)")
                lines.append(f"  - Current assets insufficient to cover current liabilities")
                lines.append(f"  - May face difficulty meeting short-term obligations")
            elif current_ratio < 1.5:
                lines.append(f"- **Working Capital Risk**: Current ratio {current_ratio:.2f}x (below Graham's 1.5x minimum)")
                lines.append(f"  - Limited cushion for short-term obligations")
            elif current_ratio < 2.0:
                lines.append(f"- **Working Capital**: Current ratio {current_ratio:.2f}x (adequate for enterprising investors)")
            else:
                lines.append(f"- **Working Capital**: Current ratio {current_ratio:.2f}x (strong - meets defensive standard)")
        
        # Debt risk
        long_term_debt = latest_data_risk.get('long_term_debt', 0.0)
        total_debt = latest_data_risk.get('total_debt', 0.0)
        total_assets = latest_data_risk.get('total_assets', 0.0)
        total_equity = latest_data_risk.get('total_equity', 0.0)
        
        if total_assets > 0:
            debt_to_assets = long_term_debt / total_assets
            if debt_to_assets > 0.50:
                lines.append(f"- **High Debt Risk**: Long-term debt {debt_to_assets*100:.1f}% of assets")
                lines.append(f"  - High leverage increases financial risk during downturns")
            elif debt_to_assets > 0.30:
                lines.append(f"- **Moderate Debt**: Long-term debt {debt_to_assets*100:.1f}% of assets")
            else:
                lines.append(f"- **Low Debt**: Long-term debt only {debt_to_assets*100:.1f}% of assets (conservative)")
            
            # Show total debt if different
            if total_debt > long_term_debt:
                total_debt_to_assets = total_debt / total_assets
                lines.append(f"  - Total debt (including short-term): {total_debt_to_assets*100:.1f}% of assets")
        
        if total_equity > 0 and long_term_debt > 0:
            debt_to_equity = long_term_debt / total_equity
            if debt_to_equity > 1.0:
                lines.append(f"  - Debt-to-Equity: {debt_to_equity:.2f}x (debt exceeds equity)")
            elif debt_to_equity > 0.5:
                lines.append(f"  - Debt-to-Equity: {debt_to_equity:.2f}x")
        
        lines.append("")
    
    def _add_operational_stability_risks_first(self, lines: List[str], history: Dict[str, Any], 
                                              sorted_years_risk: List[str]) -> None:
        """Add operational stability risks for first section.
        
        Args:
            lines: List to append lines to
            history: Historical financial data
            sorted_years_risk: Sorted list of years
        """
        lines.append("### Operational Stability Risks:")
        
        # Earnings volatility (calculate from recent 5 years)
        recent_5_years = sorted_years_risk[:5] if len(sorted_years_risk) >= 5 else sorted_years_risk
        profit_margins = []
        net_incomes = []
        
        for year in recent_5_years:
            year_data = history[year]
            revenue = year_data.get('revenue', 0.0)
            net_income = year_data.get('net_income', 0.0)
            
            if revenue > 0:
                margin = (net_income / revenue) * 100
                # Cap margin at reasonable bounds to prevent overflow in variance calculation
                margin = max(-1000, min(1000, margin))
                profit_margins.append(margin)
                net_incomes.append(net_income)
        
        if len(profit_margins) >= 3:
            # Calculate standard deviation of profit margins
            avg_margin = sum(profit_margins) / len(profit_margins)
            try:
                variance = sum((m - avg_margin) ** 2 for m in profit_margins) / len(profit_margins)
                std_dev = variance ** 0.5
            except (OverflowError, ValueError):
                # Handle extreme values gracefully
                std_dev = float('inf')
            
            # Count loss years
            loss_years = sum(1 for ni in net_incomes if ni < 0)
            
            # Format std_dev for display
            if std_dev == float('inf') or std_dev > 999:
                std_dev_str = ">999"
            else:
                std_dev_str = f"{std_dev:.1f}"
            
            if loss_years > 0:
                lines.append(f"- **Earnings Volatility**: {loss_years} loss year{'s' if loss_years > 1 else ''} in last {len(recent_5_years)} years")
                lines.append(f"  - Profit margin volatility: ±{std_dev_str}% (std dev)")
                lines.append(f"  - Cyclical or turnaround situation - higher risk")
            elif std_dev > 10:
                lines.append(f"- **Earnings Volatility**: High profit margin swings (±{std_dev_str}% std dev)")
                lines.append(f"  - Indicates cyclical business or operational instability")
            elif std_dev > 5:
                lines.append(f"- **Earnings Volatility**: Moderate (±{std_dev:.1f}% std dev)")
            else:
                lines.append(f"- **Earnings Stability**: Low volatility (±{std_dev:.1f}% std dev)")
                lines.append(f"  - Consistent profit margins indicate stable operations")
        
        # ROE consistency
        roe = self.financial_data.get('roe', 0)
        if roe > 0:
            if roe < 0.05:
                lines.append(f"- **Return on Equity**: {roe*100:.1f}% (weak - below 5%)")
                lines.append(f"  - Low returns may indicate competitive pressures or inefficiency")
            elif roe < 0.10:
                lines.append(f"- **Return on Equity**: {roe*100:.1f}% (below Graham's 10% preference)")
            elif roe > 0.20:
                lines.append(f"- **Return on Equity**: {roe*100:.1f}% (strong)")
        
        lines.append("")

    def _add_dividend_risk_first(self, lines: List[str], history: Dict[str, Any], 
                                sorted_years_risk: List[str], unified_currency: str) -> None:
        """Add dividend risk for first section.
        
        Args:
            lines: List to append lines to
            history: Historical financial data
            sorted_years_risk: Sorted list of years
            unified_currency: Currency for display
        """
        forward_div = self.financial_data.get('forward_dividend_rate', 0)
        if forward_div and forward_div > 0:
            lines.append("### Dividend Risk:")
            
            # Calculate payout ratio
            most_recent_eps = 0
            for year in sorted_years_risk:
                year_data = history[year]
                if year_data.get('revenue', 0.0) > 0 or year_data.get('net_income', 0.0) != 0:
                    most_recent_eps = year_data.get('eps', 0)
                    break
            
            if most_recent_eps and most_recent_eps > 0:
                payout_ratio = (forward_div / most_recent_eps) * 100
                
                if payout_ratio > 100:
                    lines.append(f"- **Dividend Sustainability Risk**: Payout ratio {payout_ratio:.1f}%")
                    lines.append(f"  - Paying more than earnings (unsustainable)")
                    lines.append(f"  - Dividend cut likely unless earnings improve")
                elif payout_ratio > 80:
                    lines.append(f"- **High Payout Ratio**: {payout_ratio:.1f}% of earnings")
                    lines.append(f"  - Limited room for dividend growth or earnings decline")
                elif payout_ratio > 60:
                    lines.append(f"- **Moderate Payout Ratio**: {payout_ratio:.1f}% of earnings")
                else:
                    lines.append(f"- **Conservative Payout**: {payout_ratio:.1f}% of earnings")
                    lines.append(f"  - Sustainable with room for growth")
            
            # Dividend coverage from cash flow
            most_recent_net_income = 0
            most_recent_dividends_paid = 0
            for year in sorted_years_risk:
                year_data = history[year]
                if year_data.get('revenue', 0.0) > 0 or year_data.get('net_income', 0.0) != 0:
                    most_recent_net_income = year_data.get('net_income', 0)
                    most_recent_dividends_paid = year_data.get('dividend', 0) * year_data.get('shares_outstanding', 0)
                    break
            
            if most_recent_dividends_paid > 0 and most_recent_net_income > 0:
                coverage = most_recent_net_income / most_recent_dividends_paid
                if coverage < 1.0:
                    lines.append(f"  - Dividend coverage: {coverage:.2f}x (earnings insufficient)")
                elif coverage < 1.5:
                    lines.append(f"  - Dividend coverage: {coverage:.2f}x (tight)")
                else:
                    lines.append(f"  - Dividend coverage: {coverage:.2f}x (adequate)")
            
            lines.append("")
    
    def _add_valuation_risk_first(self, lines: List[str], unified_currency: str) -> None:
        """Add valuation risk for first section.
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for display
        """
        lines.append("### Valuation Risk:")
        
        margin_of_safety = self.metrics.get('margin_of_safety', 0)
        graham_number = self.metrics.get('graham_number', 0)
        
        if isinstance(margin_of_safety, float):
            if margin_of_safety < 0:
                lines.append(f"- **Overvaluation Risk**: Margin of Safety {margin_of_safety:.1f}%")
                lines.append(f"  - Trading above Graham intrinsic value")
                lines.append(f"  - No margin for error if business deteriorates")
            elif margin_of_safety < 20:
                lines.append(f"- **Limited Margin of Safety**: {margin_of_safety:.1f}%")
                lines.append(f"  - Below Graham's 20-30% minimum for defensive investors")
                lines.append(f"  - Stock appears fairly valued but lacks substantial discount")
                lines.append(f"  - More suitable for enterprising investors willing to accept higher risk")
            elif margin_of_safety < 30:
                lines.append(f"- **Adequate Margin of Safety**: {margin_of_safety:.1f}%")
                lines.append(f"  - Meets Graham's minimum standard for defensive investors")
            else:
                lines.append(f"- **Strong Margin of Safety**: {margin_of_safety:.1f}%")
                lines.append(f"  - Substantial discount to intrinsic value")
                lines.append(f"  - Provides cushion against adverse developments")
        elif graham_number == "N/A":
            lines.append(f"- **Valuation Risk**: Cannot calculate margin of safety")
            lines.append(f"  - Negative equity or negative earnings")
            lines.append(f"  - Rely on EPV and qualitative analysis")
        
        # P/E ratio risk
        pe_ratio = self.financial_data.get('pe_ratio', 0)
        if pe_ratio > 0:
            if pe_ratio > 25:
                lines.append(f"  - P/E Ratio {pe_ratio:.1f}x: High expectations priced in")
                lines.append(f"  - Vulnerable to earnings disappointments")
            elif pe_ratio > 15:
                lines.append(f"  - P/E Ratio {pe_ratio:.1f}x: Above Graham's 15x defensive limit")
        
        lines.append("")
    
    def _add_data_quality_risks_first(self, lines: List[str]) -> None:
        """Add data quality risks for first section.
        
        Args:
            lines: List to append lines to
        """
        lines.append("### Data Quality Risks:")
        
        # Price source risk
        price_source = self.financial_data.get('price_source', 'EODHD')
        if price_source != 'EODHD':
            lines.append(f"- **Price Data**: Using {price_source} (primary source unavailable)")
            lines.append(f"  - May have timing differences or slight inaccuracies")
        
        # Institutional ownership verification
        institutional = self.financial_data.get('institutional_ownership', 0)
        if institutional > 20:
            lines.append(f"- **Institutional Ownership**: {institutional:.1f}% (verify with regulatory filings)")
        
        # 52-week range staleness
        lines.append(f"- **52-Week Range**: Verify with live sources before trading")
        lines.append(f"  - API data may be stale or use different calculation periods")
        
        lines.append("")

    def _generate_second_risk_section(self) -> List[str]:
        """Generate second risk factors section (based on Graham's investment criteria).
        
        Returns:
            List[str]: List of markdown lines for second risk section
        """
        lines = []
        
        # Section header
        lines.append("")
        lines.append("## RISK FACTORS")
        lines.append("*Quantifiable risks based on Graham's investment criteria*")
        lines.append("")
        
        # Extract currency information
        unified_currency = self.financial_data.get('currency', 'USD')
        
        # Calculate risk metrics from available data
        history = self.financial_data.get('history', {})
        if history:
            sorted_years = sorted(history.keys(), reverse=True)
            
            # Find most recent year with financial data
            latest_year = None
            for year in sorted_years:
                year_data = history[year]
                if year_data.get('revenue', 0.0) > 0 or year_data.get('net_income', 0.0) != 0 or year_data.get('total_equity', 0.0) > 0:
                    latest_year = year
                    break
            
            if latest_year:
                latest_data = history[latest_year]
                
                # 1. Market & Liquidity Risk
                self._add_market_liquidity_risk_second(lines, latest_data)
                
                # 2. Financial Strength Risk
                self._add_financial_strength_risk_second(lines, latest_data, unified_currency)
                
                # 3. Operational Stability Risk
                self._add_operational_stability_risk_second(lines, history, sorted_years)
                
                # 4. Dividend Risk
                self._add_dividend_risk_second(lines, history, sorted_years, latest_data)
                
                # 5. Valuation Risk
                self._add_valuation_risk_second(lines, unified_currency)
                
                # 6. Data Quality Risk
                self._add_data_quality_risk_second(lines, sorted_years)
                
                # Graham's principle on risk
                lines.append("**Graham's Principle on Risk**: *\"The essence of investment management is the management of risks, not the management of returns. Returns are the reward for taking risk, but the risk must be measured and managed.\"*")
        else:
            lines.append("Insufficient data available for risk assessment.")
        
        lines.append("")
        lines.append("---")
        
        return lines
    
    def _add_market_liquidity_risk_second(self, lines: List[str], latest_data: Dict[str, Any]) -> None:
        """Add market and liquidity risk for second section.
        
        Args:
            lines: List to append lines to
            latest_data: Most recent year's financial data
        """
        lines.append("### Market & Liquidity Risk:")
        beta = self.financial_data.get('beta', 0)
        if beta is None:
            beta = 0
        if beta > 0:
            if beta < 0.5:
                lines.append(f"- **Beta: {beta:.3f}** - Low volatility relative to market")
                lines.append(f"  - Note: Beta varies by calculation period and benchmark. Market sources report 0.33-0.50 range.")
                lines.append(f"  - Low beta may reflect limited liquidity and defensive sector characteristics")
            elif beta < 1.0:
                lines.append(f"- **Beta: {beta:.3f}** - Below-market volatility")
            elif beta < 1.5:
                lines.append(f"- **Beta: {beta:.3f}** - Above-market volatility")
            else:
                lines.append(f"- **Beta: {beta:.3f}** - High volatility (⚠️ Risk)")
        
        # Average volume and market cap for liquidity assessment
        avg_volume = self.financial_data.get('average_volume', 0)
        shares = latest_data.get('shares_outstanding', 0)
        price = self.financial_data.get('price', 0)
        if avg_volume > 0 and shares > 0:
            liquidity_pct = (avg_volume / shares) * 100
            if liquidity_pct < 0.1:
                lines.append(f"- **Daily Liquidity: {liquidity_pct:.3f}%** of shares outstanding (⚠️ Low liquidity - may be difficult to exit large positions)")
            elif liquidity_pct < 0.5:
                lines.append(f"- **Daily Liquidity: {liquidity_pct:.3f}%** of shares outstanding (Moderate)")
            else:
                lines.append(f"- **Daily Liquidity: {liquidity_pct:.3f}%** of shares outstanding (Good)")
        
        lines.append("")
    
    def _add_financial_strength_risk_second(self, lines: List[str], latest_data: Dict[str, Any], 
                                           unified_currency: str) -> None:
        """Add financial strength risk for second section.
        
        Args:
            lines: List to append lines to
            latest_data: Most recent year's financial data
            unified_currency: Currency for display
        """
        lines.append("### Financial Strength Risk:")
        
        # Current ratio
        current_assets = latest_data.get('current_assets', 0.0)
        current_liabilities = latest_data.get('current_liabilities', 0.0)
        if current_liabilities > 0:
            current_ratio = current_assets / current_liabilities
            if current_ratio >= 2.0:
                lines.append(f"- **Current Ratio: {current_ratio:.2f}x** - Strong liquidity (meets Graham's 2.0x defensive standard)")
            elif current_ratio >= 1.5:
                lines.append(f"- **Current Ratio: {current_ratio:.2f}x** - Adequate liquidity (meets enterprising 1.5x minimum)")
            elif current_ratio >= 1.0:
                lines.append(f"- **Current Ratio: {current_ratio:.2f}x** - ⚠️ Below Graham's standards (defensive requires 2.0x)")
            else:
                lines.append(f"- **Current Ratio: {current_ratio:.2f}x** - ⚠️ Critical liquidity risk")
        
        # Debt levels
        long_term_debt = latest_data.get('long_term_debt', 0.0)
        total_debt = latest_data.get('total_debt', 0.0)
        short_term_debt = total_debt - long_term_debt if total_debt > long_term_debt else 0.0
        total_assets = latest_data.get('total_assets', 0.0)
        net_current_assets = current_assets - current_liabilities
        
        if total_assets > 0 and long_term_debt > 0:
            lt_debt_to_assets = (long_term_debt / total_assets) * 100
            total_debt_to_assets = (total_debt / total_assets) * 100
            
            # Determine assessment based on long-term debt
            if lt_debt_to_assets < 10:
                assessment = "Conservative"
            elif lt_debt_to_assets < 30:
                assessment = "Moderate"
            else:
                assessment = "⚠️ High leverage"
            
            # Show long-term debt with breakdown
            lines.append(f"- **Long-Term Debt: ${long_term_debt:,.0f} {unified_currency}** ({lt_debt_to_assets:.1f}% of assets) - {assessment}")
            if short_term_debt > 0:
                lines.append(f"  - Short-term debt: ${short_term_debt:,.0f} {unified_currency}")
                lines.append(f"  - Total debt: ${total_debt:,.0f} {unified_currency} ({total_debt_to_assets:.1f}% of assets)")
        elif total_assets > 0 and long_term_debt == 0:
            lines.append(f"- **Long-Term Debt: ${long_term_debt:,.0f} {unified_currency}** - Debt-free (excellent)")
            if short_term_debt > 0:
                total_debt_to_assets = (total_debt / total_assets) * 100
                lines.append(f"  - Short-term debt: ${short_term_debt:,.0f} {unified_currency} ({total_debt_to_assets:.1f}% of assets)")
        
        # Graham's defensive test: Long-term debt < Net Current Assets
        if net_current_assets > 0 and long_term_debt > 0:
            if long_term_debt < net_current_assets:
                lines.append(f"- **Debt Coverage: ✓** Long-term debt < Net Current Assets (passes Graham's defensive test)")
            else:
                debt_ratio = (long_term_debt / net_current_assets) * 100
                lines.append(f"- **Debt Coverage: ⚠️** Long-term debt is {debt_ratio:.0f}% of Net Current Assets (fails Graham's defensive test)")
        
        lines.append("")

    def _add_operational_stability_risk_second(self, lines: List[str], history: Dict[str, Any], 
                                              sorted_years: List[str]) -> None:
        """Add operational stability risk for second section.
        
        Args:
            lines: List to append lines to
            history: Historical financial data
            sorted_years: Sorted list of years
        """
        lines.append("### Operational Stability Risk:")
        
        # Earnings volatility (last 10 years)
        profit_margins = []
        loss_years = 0
        years_to_check = sorted_years[:10] if len(sorted_years) >= 10 else sorted_years
        
        for year in years_to_check:
            year_data = history[year]
            revenue = year_data.get('revenue', 0.0)
            net_income = year_data.get('net_income', 0.0)
            
            if revenue > 0:
                margin = (net_income / revenue) * 100
                # Validate margin is finite (avoid infinity from near-zero revenue)
                if abs(margin) < 1e6:  # Reasonable profit margin range
                    profit_margins.append(margin)
                if net_income < 0:
                    loss_years += 1
        
        if profit_margins:
            import statistics
            avg_margin = statistics.mean(profit_margins)
            if len(profit_margins) > 1:
                margin_volatility = statistics.stdev(profit_margins)
                lines.append(f"- **Profit Margin Stability: {avg_margin:.1f}% average, {margin_volatility:.1f}% std dev** over {len(profit_margins)} years")
                if margin_volatility < 5:
                    lines.append(f"  - Low volatility indicates stable operations")
                elif margin_volatility < 10:
                    lines.append(f"  - Moderate volatility")
                else:
                    lines.append(f"  - ⚠️ High volatility indicates cyclical or unstable business")
            else:
                lines.append(f"- **Profit Margin: {avg_margin:.1f}%** (insufficient history for volatility analysis)")
        
        # Loss years
        if loss_years > 0:
            lines.append(f"- **Loss Years: {loss_years} of {len(years_to_check)}** - ⚠️ Earnings not consistently positive")
        else:
            lines.append(f"- **Loss Years: 0 of {len(years_to_check)}** - Consistent profitability (excellent)")
        
        # ROE consistency
        roe = self.financial_data.get('roe', 0)
        if roe > 0:
            if roe > 0.15:
                lines.append(f"- **Return on Equity: {roe*100:.1f}%** - Strong capital efficiency")
            elif roe > 0.10:
                lines.append(f"- **Return on Equity: {roe*100:.1f}%** - Adequate returns")
            else:
                lines.append(f"- **Return on Equity: {roe*100:.1f}%** - ⚠️ Below 10% threshold")
        
        lines.append("")
    
    def _add_dividend_risk_second(self, lines: List[str], history: Dict[str, Any], 
                                  sorted_years: List[str], latest_data: Dict[str, Any]) -> None:
        """Add dividend sustainability risk for second section.
        
        Args:
            lines: List to append lines to
            history: Historical financial data
            sorted_years: Sorted list of years
            latest_data: Most recent year's financial data
        """
        forward_div = self.financial_data.get('forward_dividend_rate', 0)
        if forward_div and forward_div > 0:
            lines.append("### Dividend Sustainability Risk:")
            
            # Payout ratio
            eps = latest_data.get('eps', 0.0)
            if eps > 0:
                payout_ratio = (forward_div / eps) * 100
                if payout_ratio < 50:
                    lines.append(f"- **Payout Ratio: {payout_ratio:.1f}%** - Conservative (sustainable)")
                elif payout_ratio < 75:
                    lines.append(f"- **Payout Ratio: {payout_ratio:.1f}%** - Moderate")
                elif payout_ratio < 100:
                    lines.append(f"- **Payout Ratio: {payout_ratio:.1f}%** - ⚠️ High (limited room for growth)")
                else:
                    lines.append(f"- **Payout Ratio: {payout_ratio:.1f}%** - ⚠️ Unsustainable (paying more than earnings)")
            
            # Dividend coverage from cash flow
            operating_cash_flow = latest_data.get('operating_cash_flow', 0.0)
            shares = latest_data.get('shares_outstanding', 0)
            if operating_cash_flow > 0 and shares > 0:
                cash_per_share = operating_cash_flow / shares
                dividend_coverage = cash_per_share / forward_div if forward_div > 0 else 0
                if dividend_coverage >= 2.0:
                    lines.append(f"- **Dividend Coverage: {dividend_coverage:.1f}x** from operating cash flow - Well covered")
                elif dividend_coverage >= 1.5:
                    lines.append(f"- **Dividend Coverage: {dividend_coverage:.1f}x** from operating cash flow - Adequate")
                elif dividend_coverage >= 1.0:
                    lines.append(f"- **Dividend Coverage: {dividend_coverage:.1f}x** from operating cash flow - ⚠️ Tight coverage")
                else:
                    lines.append(f"- **Dividend Coverage: {dividend_coverage:.1f}x** from operating cash flow - ⚠️ Not covered by cash flow")
            
            # Dividend history consistency
            years_to_check = sorted_years[:10] if len(sorted_years) >= 10 else sorted_years
            dividend_years = 0
            for year in years_to_check:
                if history[year].get('dividend', 0.0) > 0:
                    dividend_years += 1
            
            if dividend_years == len(years_to_check):
                lines.append(f"- **Dividend History: {dividend_years} consecutive years** - Uninterrupted record (excellent)")
            elif dividend_years >= len(years_to_check) * 0.8:
                lines.append(f"- **Dividend History: {dividend_years} of {len(years_to_check)} years** - Mostly consistent")
            else:
                lines.append(f"- **Dividend History: {dividend_years} of {len(years_to_check)} years** - ⚠️ Inconsistent payment history")
            
            lines.append("")
    
    def _add_valuation_risk_second(self, lines: List[str], unified_currency: str) -> None:
        """Add valuation risk (margin of safety) for second section.
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for display
        """
        lines.append("### Valuation Risk (Margin of Safety):")
        
        margin_of_safety = self.metrics.get('margin_of_safety', 'N/A')
        graham_number = self.metrics.get('graham_number', 'N/A')
        price = self.financial_data.get('price', 0)
        
        if isinstance(margin_of_safety, (int, float)):
            if margin_of_safety >= 30:
                lines.append(f"- **Margin of Safety: {margin_of_safety:.1f}%** - Excellent discount to intrinsic value")
                lines.append(f"  - Graham's Standard: 20-30% minimum for defensive investors")
                lines.append(f"  - Assessment: **Low valuation risk** - substantial cushion against estimation errors")
            elif margin_of_safety >= 20:
                lines.append(f"- **Margin of Safety: {margin_of_safety:.1f}%** - Meets Graham's minimum standard")
                lines.append(f"  - Graham's Standard: 20-30% minimum for defensive investors")
                lines.append(f"  - Assessment: **Acceptable valuation risk** for defensive investors")
            elif margin_of_safety > 0:
                lines.append(f"- **Margin of Safety: {margin_of_safety:.1f}%** - Below Graham's recommended minimum")
                lines.append(f"  - Graham's Standard: 20-30% minimum for defensive investors")
                lines.append(f"  - Assessment: **Moderate valuation risk** - limited cushion against errors or deterioration")
                lines.append(f"  - More suitable for enterprising investors willing to accept higher risk")
            else:
                lines.append(f"- **Margin of Safety: {margin_of_safety:.1f}%** - Trading above intrinsic value")
                lines.append(f"  - Graham's Standard: 20-30% minimum for defensive investors")
                lines.append(f"  - Assessment: **High valuation risk** - no margin for error")
        else:
            lines.append(f"- **Margin of Safety: {margin_of_safety}** - Cannot assess valuation risk")
        
        # Show intrinsic value for context
        if isinstance(graham_number, (int, float)) and graham_number > 0:
            graham_display = format_price_display(graham_number, unified_currency, unified_currency)
            current_price_display = format_price_display(price, unified_currency, unified_currency)
            lines.append(f"  - Intrinsic Value (Graham): {graham_display}")
            lines.append(f"  - Current Price: {current_price_display}")
        
        lines.append("")
    
    def _add_data_quality_risk_second(self, lines: List[str], sorted_years: List[str]) -> None:
        """Add data quality risk for second section.
        
        Args:
            lines: List to append lines to
            sorted_years: Sorted list of years
        """
        lines.append("### Data Quality Risk:")
        
        # Institutional ownership verification
        institutional = self.financial_data.get('institutional_ownership', 0)
        if institutional > 0:
            if institutional > 20:
                lines.append(f"- **Institutional Ownership: {institutional:.2f}%** - Verify with regulatory filings")
            else:
                lines.append(f"- **Institutional Ownership: {institutional:.2f}%** - Verify with regulatory filings")
        
        # Price source
        price_source = self.financial_data.get('price_source', 'EODHD')
        if price_source != 'EODHD':
            lines.append(f"- **Price Source: {price_source}** - ⚠️ Using fallback source (EODHD unavailable)")
        
        # Years of history
        years_available = len(sorted_years)
        if years_available < 10:
            lines.append(f"- **Financial History: {years_available} years** - ⚠️ Limited track record (Graham preferred 10+ years)")
        
        lines.append("")
