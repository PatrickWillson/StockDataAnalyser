"""Risk Factors section generator for dossier.

This module generates the risk factors section of the stock analysis dossier,
including market risk, financial strength risk, operational stability risk,
dividend risk, valuation risk, and data quality risk assessments.
"""

from typing import List, Dict, Any
from output.sections.base import DossierSection
from output.formatting import format_price_display
from core.history import has_statement_data
from config.data_quality_config import MIN_HISTORY_YEARS_RECOMMENDED
from config.investor_thresholds import DEFENSIVE, ENTERPRISING
from config.risk_thresholds import (
    BETA_HIGH,
    BETA_LOW,
    BETA_MARKET,
    CURRENT_RATIO_CRITICAL,
    DIVIDEND_COVERAGE_ADEQUATE,
    DIVIDEND_COVERAGE_MIN,
    DIVIDEND_COVERAGE_STRONG,
    DIVIDEND_MOSTLY_CONSISTENT_FRACTION,
    INSTITUTIONAL_HIGH_PCT,
    LIQUIDITY_LOW_PCT,
    LIQUIDITY_MODERATE_PCT,
    LT_DEBT_TO_ASSETS_LOW_PCT,
    LT_DEBT_TO_ASSETS_MODERATE_PCT,
    MARGIN_VOLATILITY_LOW_PCT,
    MARGIN_VOLATILITY_MODERATE_PCT,
    MOS_GRAHAM_BARGAIN_PCT,
    PAYOUT_CONSERVATIVE_PCT,
    PAYOUT_MAX_PCT,
    PAYOUT_MODERATE_PCT,
    PROFIT_MARGIN_SANITY_LIMIT_PCT,
    RISK_HISTORY_WINDOW_YEARS,
    ROE_ADEQUATE,
    ROE_STRONG,
)


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
                if has_statement_data(year_data):
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
            if beta < BETA_LOW:
                lines.append(f"- **Beta: {beta:.3f}** - Low volatility relative to market")
                lines.append("  - Note: Beta varies by calculation period and benchmark. Market sources report 0.33-0.50 range.")
                lines.append("  - Low beta may reflect limited liquidity and defensive sector characteristics")
            elif beta < BETA_MARKET:
                lines.append(f"- **Beta: {beta:.3f}** - Below-market volatility")
            elif beta < BETA_HIGH:
                lines.append(f"- **Beta: {beta:.3f}** - Above-market volatility")
            else:
                lines.append(f"- **Beta: {beta:.3f}** - High volatility (⚠️ Risk)")
        
        # Average volume and market cap for liquidity assessment
        avg_volume = self.financial_data.get('average_volume', 0)
        shares = latest_data.get('shares_outstanding', 0)
        self.financial_data.get('price', 0)
        if avg_volume > 0 and shares > 0:
            liquidity_pct = (avg_volume / shares) * 100
            if liquidity_pct < LIQUIDITY_LOW_PCT:
                lines.append(f"- **Daily Liquidity: {liquidity_pct:.3f}%** of shares outstanding (⚠️ Low liquidity - may be difficult to exit large positions)")
            elif liquidity_pct < LIQUIDITY_MODERATE_PCT:
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
            if current_ratio >= DEFENSIVE.MIN_CURRENT_RATIO:
                lines.append(f"- **Current Ratio: {current_ratio:.2f}x** - Strong liquidity (meets Graham's {DEFENSIVE.MIN_CURRENT_RATIO:.1f}x defensive standard)")
            elif current_ratio >= ENTERPRISING.MIN_CURRENT_RATIO:
                lines.append(f"- **Current Ratio: {current_ratio:.2f}x** - Adequate liquidity (meets enterprising {ENTERPRISING.MIN_CURRENT_RATIO:.1f}x minimum)")
            elif current_ratio >= CURRENT_RATIO_CRITICAL:
                lines.append(f"- **Current Ratio: {current_ratio:.2f}x** - ⚠️ Below Graham's standards (defensive requires {DEFENSIVE.MIN_CURRENT_RATIO:.1f}x)")
            else:
                lines.append(f"- **Current Ratio: {current_ratio:.2f}x** - ⚠️ Critical liquidity risk")
        
        # Debt levels
        long_term_debt = latest_data.get('long_term_debt', 0.0)
        total_debt = latest_data.get('total_debt', 0.0)
        # Total debt is the reported total (incl. leases), so the remainder is short-term debt and leases
        other_debt = total_debt - long_term_debt if total_debt > long_term_debt else 0.0
        total_assets = latest_data.get('total_assets', 0.0)
        net_current_assets = current_assets - current_liabilities
        
        if total_assets > 0 and long_term_debt > 0:
            lt_debt_to_assets = (long_term_debt / total_assets) * 100
            total_debt_to_assets = (total_debt / total_assets) * 100
            
            # Determine assessment based on long-term debt
            if lt_debt_to_assets < LT_DEBT_TO_ASSETS_LOW_PCT:
                assessment = "Conservative"
            elif lt_debt_to_assets < LT_DEBT_TO_ASSETS_MODERATE_PCT:
                assessment = "Moderate"
            else:
                assessment = "⚠️ High leverage"
            
            # Show long-term debt with breakdown
            lines.append(f"- **Long-Term Debt: ${long_term_debt:,.0f} {unified_currency}** ({lt_debt_to_assets:.1f}% of assets) - {assessment}")
            if other_debt > 0:
                lines.append(f"  - Short-term debt and leases: ${other_debt:,.0f} {unified_currency}")
                lines.append(f"  - Total debt: ${total_debt:,.0f} {unified_currency} ({total_debt_to_assets:.1f}% of assets)")
        elif total_assets > 0 and long_term_debt == 0:
            lines.append(f"- **Long-Term Debt: ${long_term_debt:,.0f} {unified_currency}** - Debt-free (excellent)")
            if other_debt > 0:
                total_debt_to_assets = (total_debt / total_assets) * 100
                lines.append(f"  - Short-term debt and leases: ${other_debt:,.0f} {unified_currency} ({total_debt_to_assets:.1f}% of assets)")
        
        # Graham's defensive test: long-term debt not more than net current assets (working capital)
        if net_current_assets > 0 and long_term_debt > 0:
            if long_term_debt <= net_current_assets:
                lines.append("- **Debt Coverage: ✓** Long-term debt ≤ net current assets (passes Graham's defensive test)")
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
        years_to_check = sorted_years[:RISK_HISTORY_WINDOW_YEARS] if len(sorted_years) >= RISK_HISTORY_WINDOW_YEARS else sorted_years
        
        for year in years_to_check:
            year_data = history[year]
            revenue = year_data.get('revenue', 0.0)
            net_income = year_data.get('net_income', 0.0)
            
            if revenue > 0:
                margin = (net_income / revenue) * 100
                # Validate margin is finite (avoid infinity from near-zero revenue)
                if abs(margin) < PROFIT_MARGIN_SANITY_LIMIT_PCT:  # Reasonable profit margin range
                    profit_margins.append(margin)
                if net_income < 0:
                    loss_years += 1
        
        if profit_margins:
            import statistics
            avg_margin = statistics.mean(profit_margins)
            if len(profit_margins) > 1:
                margin_volatility = statistics.stdev(profit_margins)
                lines.append(f"- **Profit Margin Stability: {avg_margin:.1f}% average, {margin_volatility:.1f}% std dev** over {len(profit_margins)} years")
                if margin_volatility < MARGIN_VOLATILITY_LOW_PCT:
                    lines.append("  - Low volatility indicates stable operations")
                elif margin_volatility < MARGIN_VOLATILITY_MODERATE_PCT:
                    lines.append("  - Moderate volatility")
                else:
                    lines.append("  - ⚠️ High volatility indicates cyclical or unstable business")
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
            if roe > ROE_STRONG:
                lines.append(f"- **Return on Equity: {roe*100:.1f}%** - Strong capital efficiency")
            elif roe > ROE_ADEQUATE:
                lines.append(f"- **Return on Equity: {roe*100:.1f}%** - Adequate returns")
            else:
                lines.append(f"- **Return on Equity: {roe*100:.1f}%** - ⚠️ Below {ROE_ADEQUATE:.0%} threshold")
        
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
        # The latest fiscal year's audited dividend per share, never EODHD's forward estimate (F21);
        # history 'dividend' values are payment counts when is_dividend_amounts is False
        is_amounts = self.financial_data.get('is_dividend_amounts', False)
        latest_div = latest_data.get('dividend', 0.0) if is_amounts else 0.0
        paid_any = any(history[year].get('dividend', 0.0) > 0 for year in sorted_years)
        if latest_div > 0 or paid_any:
            lines.append("### Dividend Sustainability Risk:")
            
            # Payout ratio (latest fiscal year: dividend per share / EPS)
            eps = latest_data.get('eps', 0.0)
            if latest_div > 0 and eps > 0:
                payout_ratio = (latest_div / eps) * 100
                if payout_ratio < PAYOUT_CONSERVATIVE_PCT:
                    lines.append(f"- **Payout Ratio: {payout_ratio:.1f}%** - Conservative (sustainable)")
                elif payout_ratio < PAYOUT_MODERATE_PCT:
                    lines.append(f"- **Payout Ratio: {payout_ratio:.1f}%** - Moderate")
                elif payout_ratio < PAYOUT_MAX_PCT:
                    lines.append(f"- **Payout Ratio: {payout_ratio:.1f}%** - ⚠️ High (limited room for growth)")
                else:
                    lines.append(f"- **Payout Ratio: {payout_ratio:.1f}%** - ⚠️ Unsustainable (paying more than earnings)")
            
            # Dividend coverage from cash flow
            operating_cash_flow = latest_data.get('operating_cash_flow', 0.0)
            shares = latest_data.get('shares_outstanding', 0)
            if latest_div > 0 and operating_cash_flow > 0 and shares > 0:
                cash_per_share = operating_cash_flow / shares
                dividend_coverage = cash_per_share / latest_div
                if dividend_coverage >= DIVIDEND_COVERAGE_STRONG:
                    lines.append(f"- **Dividend Coverage: {dividend_coverage:.1f}x** from operating cash flow - Well covered")
                elif dividend_coverage >= DIVIDEND_COVERAGE_ADEQUATE:
                    lines.append(f"- **Dividend Coverage: {dividend_coverage:.1f}x** from operating cash flow - Adequate")
                elif dividend_coverage >= DIVIDEND_COVERAGE_MIN:
                    lines.append(f"- **Dividend Coverage: {dividend_coverage:.1f}x** from operating cash flow - ⚠️ Tight coverage")
                else:
                    lines.append(f"- **Dividend Coverage: {dividend_coverage:.1f}x** from operating cash flow - ⚠️ Not covered by cash flow")
            
            # Dividend history consistency
            years_to_check = sorted_years[:RISK_HISTORY_WINDOW_YEARS] if len(sorted_years) >= RISK_HISTORY_WINDOW_YEARS else sorted_years
            dividend_years = 0
            for year in years_to_check:
                if history[year].get('dividend', 0.0) > 0:
                    dividend_years += 1
            
            if dividend_years == len(years_to_check):
                lines.append(f"- **Dividend History: {dividend_years} consecutive years** - Uninterrupted record (excellent)")
            elif dividend_years >= len(years_to_check) * DIVIDEND_MOSTLY_CONSISTENT_FRACTION:
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
        intrinsic_value = (self.metrics.get('margin_of_safety_details') or {}).get('intrinsic_value_used', 'N/A')
        price = self.financial_data.get('price', 0)
        
        # Graham: a bargain needs indicated value at least 50% above price, i.e. a margin of at
        # least one-third of value (GRAHAM_METHODOLOGY §1.2, §3.3)
        if isinstance(margin_of_safety, (int, float)):
            if margin_of_safety >= MOS_GRAHAM_BARGAIN_PCT:
                lines.append(f"- **Margin of Safety: {margin_of_safety:.1f}%** - Bargain by Graham's standard")
                lines.append("  - Graham: a bargain's indicated value is at least 50% above the price (margin ≥ 33.3%)")
            elif margin_of_safety > 0:
                lines.append(f"- **Margin of Safety: {margin_of_safety:.1f}%** - Below conservative value, short of Graham's bargain margin")
                lines.append("  - Graham: a bargain's indicated value is at least 50% above the price (margin ≥ 33.3%)")
            else:
                lines.append(f"- **Margin of Safety: {margin_of_safety:.1f}%** - Trading above conservative intrinsic value")
                lines.append("  - Assessment: **High valuation risk** - no margin of safety")
        else:
            lines.append(f"- **Margin of Safety: {margin_of_safety}** - Cannot assess valuation risk")
        
        # Show the intrinsic value the margin is measured against
        if isinstance(intrinsic_value, (int, float)) and intrinsic_value > 0:
            value_display = format_price_display(intrinsic_value, unified_currency, unified_currency)
            current_price_display = format_price_display(price, unified_currency, unified_currency)
            lines.append(f"  - Conservative Intrinsic Value: {value_display}")
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
            if institutional > INSTITUTIONAL_HIGH_PCT:
                lines.append(f"- **Institutional Ownership: {institutional:.2f}%** - Verify with regulatory filings")
            else:
                lines.append(f"- **Institutional Ownership: {institutional:.2f}%** - Verify with regulatory filings")
        
        # Price source
        price_source = self.financial_data.get('price_source', 'yfinance')
        lines.append(f"- **Price Source: {price_source}** (current quote; the only price source)")
        
        # Years of history
        years_available = len(sorted_years)
        if years_available < MIN_HISTORY_YEARS_RECOMMENDED:
            lines.append(f"- **Financial History: {years_available} years** - ⚠️ Limited track record (Graham's defensive criteria use 10 years of earnings and 20 of dividends)")
        
        lines.append("")
