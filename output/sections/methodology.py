"""Methodology Notes section generator for dossier.

This module generates the methodology notes section of the stock analysis dossier,
explaining how key valuation metrics are calculated including P/E ratio, Graham Number,
EPV (Earnings Power Value), Net-Net Value, and Margin of Safety.
"""

from typing import List, Dict, Any, Optional, Union
from output.formatting import format_price_display
from config.graham_constants import COST_OF_CAPITAL, GRAHAM_MULTIPLIER
from config.investor_thresholds import DEFENSIVE
from config.valuation_config import EPV_MAX_YEARS, EPV_MIN_YEARS
from output.sections.base import DossierSection
from core.report_context import ReportContext, build_report_context, fiscal_year
from core.models import (FinancialData, CombinedPEPBTest, EPVDetails, GrahamResult, MarginOfSafetyDetails, NCADetails,
                         ThreeYearAvgPE, or_default)


class MethodologySection(DossierSection):
    """Generates the methodology notes section of the dossier.
    
    This section explains how key valuation metrics are calculated:
    - P/E Ratio calculation methodology
    - Graham Number formula and explanation
    - EPV (Simplified Earnings Power Estimate) with full-cycle earnings
    - Net-Net Value calculation
    - Margin of Safety explanation
    
    Requirements: 2.4
    """
    
    def __init__(self, financial_data: Dict[str, Any], metrics: Union[GrahamResult, Dict[str, Any]],
                 context: Optional[ReportContext] = None):
        """Initialize methodology section.
        
        Args:
            financial_data: Dictionary containing financial data (FinancialData DTO)
            metrics: Graham metrics (GrahamResult, or its dict form)
        """
        self.financial_data = FinancialData.from_dict(financial_data)
        self.metrics = GrahamResult.from_dict(metrics)
        self.context = context or build_report_context(financial_data, metrics)
    
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
        unified_currency = or_default(self.financial_data.currency, 'USD')
        
        # Get EPV details
        epv_details = or_default(self.metrics.epv_details, EPVDetails())
        
        # Get most recent EPS for P/E explanation
        most_recent_eps = or_default(self.context.latest_row.eps, 0) if self.context.latest_year else 0
        
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
        
        # New metrics explanations
        self._add_new_metrics_explanations(lines)
        
        # TTM methodology explanation
        self._add_ttm_methodology_explanation(lines)
        
        lines.append("")
        lines.append("---")
        
        return lines
    
    def _add_pe_ratio_explanation(self, lines: List[str], unified_currency: str, 
                                  most_recent_eps: float) -> None:
        """Add P/E ratio calculation explanation.
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for display
            most_recent_eps: Most recent EPS value
        """
        pe_ratio = or_default(self.financial_data.pe_ratio, 0)
        
        if pe_ratio > 0 and most_recent_eps and most_recent_eps > 0:
            eps_display = format_price_display(most_recent_eps, unified_currency, unified_currency)
            lines.append(f"- **P/E Ratio ({pe_ratio:.2f})**: Current Price / Most Recent Annual EPS")
            lines.append("  - Calculated from audited financials, not API pre-calculated ratios")
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
        graham_number = or_default(self.metrics.graham_number, 0)
        normalized_graham_number = or_default(self.metrics.normalized_graham_number, 0)
        
        # Get 3-year EPS data from calculator if available
        or_default(self.financial_data.history, {})
        
        # Single-Year Graham Number (Legacy)
        if isinstance(graham_number, (int, float)) and graham_number > 0:
            graham_display = format_price_display(graham_number, unified_currency, unified_currency)
            lines.append(f"- **Graham Number - Single-Year EPS ({graham_display})**: √({GRAHAM_MULTIPLIER:g} × EPS × TBVPS)")
            lines.append("  - Conservative intrinsic value estimate")
            lines.append(f"  - Not a formula Graham published: the highest price passing his defensive criteria 6 (P/E ≤ {DEFENSIVE.MAX_PE_RATIO:g}) and 7 (P/B ≤ {DEFENSIVE.MAX_PB_RATIO:g}), as {DEFENSIVE.MAX_PE_RATIO:g} × {DEFENSIVE.MAX_PB_RATIO:g} = {GRAHAM_MULTIPLIER:g}")
            lines.append("  - Uses most recent annual EPS")
        
        # Normalized Graham Number (3-Year Average)
        lines.append("")
        lines.append("- **Graham Number - 3-Year Average EPS (Normalized)**:")
        
        if isinstance(normalized_graham_number, (int, float)) and normalized_graham_number > 0:
            normalized_display = format_price_display(normalized_graham_number, unified_currency, unified_currency)
            lines.append(f"  - **Value**: {normalized_display}")
            lines.append(f"  - **Formula**: √({GRAHAM_MULTIPLIER:g} × EPS_3yr_avg × TBVPS)")
            lines.append("")
            lines.append("  **Rationale**: Smooths cyclical volatility and prevents 'bull traps' where one peak year")
            lines.append("  makes a cyclical company appear undervalued despite being a value destroyer over the")
            lines.append("  full business cycle. This follows Graham's sixth defensive criterion: price not more than")
            lines.append(f"  {DEFENSIVE.MAX_PE_RATIO:g} times average earnings of the past three years.")
            lines.append("")
            
            # Display 3-year EPS breakdown
            self._add_3year_eps_breakdown(lines, unified_currency)
        else:
            # Normalized Graham Number is "N/A" - still show breakdown if available
            lines.append("  - **Value**: N/A")
            lines.append(f"  - **Formula**: √({GRAHAM_MULTIPLIER:g} × EPS_3yr_avg × TBVPS)")
            lines.append("")
            lines.append("  **Rationale**: Smooths cyclical volatility and prevents 'bull traps'")
            lines.append("")
            
            # Try to show breakdown even when calculation failed
            self._add_3year_eps_breakdown(lines, unified_currency)
    
    def _add_epv_explanation(self, lines: List[str], unified_currency: str, 
                            epv_details: EPVDetails) -> None:
        """Add EPV (Earnings Power Value) methodology explanation.
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for display
            epv_details: EPV calculation details
        """
        epv_value = or_default(self.metrics.epv, 0)
        
        if isinstance(epv_value, (int, float)) and epv_value > 0:
            ticker = or_default(self.financial_data.ticker, 'UNKNOWN')
            epv_per_share = or_default(epv_details.epv_per_share, 0)
            normalized_earnings = or_default(epv_details.normalized_earnings, 0)
            years_used = or_default(epv_details.years_used, 0)
            cost_of_capital = or_default(epv_details.cost_of_capital, COST_OF_CAPITAL)
            years_included = or_default(epv_details.years_included, ())
            net_incomes = or_default(epv_details.net_incomes, ())
            
            lines.append("- **EPV - Simplified Earnings Power Estimate**")
            lines.append("")
            lines.append("  **Methodology:**")
            lines.append(f"  - Uses {EPV_MIN_YEARS}-{EPV_MAX_YEARS} year average of net income")
            lines.append("  - **Includes ALL years** (profitable and unprofitable)")
            lines.append("  - Loss years reduce the average (real value destruction)")
            lines.append(f"  - Capitalizes earnings at {COST_OF_CAPITAL:.0%} discount rate")
            lines.append("  - Per share: the same years' average EPS (each year's earnings over that year's shares), capitalized the same way")
            lines.append("  - Graham's method: average past earnings capitalised at a multiplier kept \"within a reasonable range of variation\"; in 1976 he set a maximum multiple of 10")
            lines.append("")
            lines.append(f"  **Note**: Dividing by {COST_OF_CAPITAL:.0%} is a multiplier of {1 / COST_OF_CAPITAL:g}. The name 'EPV' comes from Greenwald (2001), whose method differs (normalised EBIT, maintenance capex, cost of capital).")
            lines.append("")
            lines.append(f"  **Calculation for {ticker}:**")
            lines.append(f"  - Years Used: {years_used}")
            
            # Show years range and net incomes
            if years_included and net_incomes:
                # Format net incomes with currency
                net_income_strs = []
                for ni in net_incomes:
                    if ni >= 0:
                        net_income_strs.append(f"{ni:,.0f} {unified_currency}")
                    else:
                        net_income_strs.append(f"-{abs(ni):,.0f} {unified_currency}")
                
                # Show years range
                if len(years_included) > 0:
                    first_year = fiscal_year(years_included[-1])  # Oldest year
                    last_year = fiscal_year(years_included[0])    # Most recent year
                    lines.append(f"  - Years: {first_year}-{last_year}")
                
                # Show net incomes
                lines.append(f"  - Net Incomes: {', '.join(net_income_strs)}")
            
            if normalized_earnings > 0:
                lines.append(f"  - Normalized Earnings: {normalized_earnings:,.0f} {unified_currency} (average including losses)")
            
            lines.append(f"  - EPV: {epv_value:,.0f} {unified_currency} ({normalized_earnings:,.0f} {unified_currency} / {cost_of_capital:.0%})")
            
            eps_values = or_default(epv_details.eps_values, ())
            normalized_eps = or_default(epv_details.normalized_eps, None)
            if eps_values and all(eps is not None for eps in eps_values):
                lines.append(f"  - Earnings per share on the present capitalization: "
                             f"{', '.join(f'{eps:,.2f}' for eps in eps_values)} {unified_currency}")
                share_basis = or_default(epv_details.share_basis, None)
                if share_basis:
                    lines.append(f"  - Share basis: {share_basis}")
            if isinstance(epv_per_share, (int, float)):
                epv_per_share_display = format_price_display(epv_per_share, unified_currency, unified_currency)
                basis = (f" (average EPS {normalized_eps:,.2f} {unified_currency} / {cost_of_capital:.0%})"
                         if isinstance(normalized_eps, (int, float)) else "")
                lines.append(f"  - EPV Per Share: {epv_per_share_display}{basis}")
            elif not isinstance(epv_per_share, (int, float)):
                reason = or_default(epv_details.epv_per_share_reason, "no per-share earnings")
                lines.append(f"  - EPV Per Share: N/A ({reason})")
            
            lines.append("")
            
            # Add note about loss years or consistent profitability
            loss_years = [ni for ni in net_incomes if ni < 0]
            if loss_years:
                loss_count = len(loss_years)
                # Identify which years were losses
                loss_year_labels = []
                for i, ni in enumerate(net_incomes):
                    if ni < 0 and i < len(years_included):
                        loss_year_labels.append(fiscal_year(years_included[i]))
                
                if loss_year_labels:
                    loss_years_str = ', '.join(loss_year_labels)
                    lines.append(f"  **Note**: The {years_used}-year average includes {loss_count} loss year{'s' if loss_count > 1 else ''} ({loss_years_str}), reflecting the company's full business cycle performance per Graham's methodology.")
                else:
                    lines.append(f"  **Note**: The {years_used}-year average includes {loss_count} loss year{'s' if loss_count > 1 else ''}, reflecting the company's full business cycle performance per Graham's methodology.")
            else:
                lines.append(f"  **Note**: All {years_used} years were profitable, demonstrating consistent earnings power.")
            
            lines.append("")
            lines.append("  **Graham on earning power**: *\"Past earning power … should mean the average earnings over a stated period which would ordinarily be identified in the discussion. But if not so identified it would be some representative period such as five or seven or perhaps ten years in the past.\"* (Graham, Current Problems in Security Analysis, Lecture 4, 1946–47)")
    
    def _add_net_net_explanation(self, lines: List[str], unified_currency: str) -> None:
        """Add Net-Net Value calculation explanation.
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for display
        """
        net_net = or_default(self.metrics.net_net_value, 0)
        
        if isinstance(net_net, (int, float)) and net_net > 0:
            net_net_display = format_price_display(net_net, unified_currency, unified_currency)
            lines.append(f"- **Net-Net Value ({net_net_display})**: (Current Assets - Total Liabilities - minority interests and other claims ahead of the common) / Shares")
            lines.append("  - Graham's net current asset value: \"current assets alone, minus all liabilities and claims ahead of the issue\"")
            lines.append("  - Graham bought at no more than two-thirds of it, as a diversified group")
    
    def _add_margin_of_safety_explanation(self, lines: List[str]) -> None:
        """Add Margin of Safety calculation explanation.
        
        Args:
            lines: List to append lines to
        """
        mos_details = or_default(self.metrics.margin_of_safety_details, MarginOfSafetyDetails())
        mos = or_default(self.metrics.margin_of_safety, 0)
        
        # Get values for explanation
        normalized_gn = or_default(mos_details.normalized_graham_number, 0)
        epv_per_share = or_default(mos_details.epv_per_share, 0)
        intrinsic_value_used = or_default(mos_details.intrinsic_value_used, 0)
        limiting_factor = or_default(mos_details.limiting_factor, 'N/A')
        both_anchors = isinstance(normalized_gn, (int, float)) and isinstance(epv_per_share, (int, float))
        
        unified_currency = or_default(self.financial_data.currency, 'USD')
        
        lines.append("")
        lines.append("- **Margin of Safety - Conservative Dual-Anchor Approach**:")
        
        if isinstance(mos, (int, float)):
            lines.append(f"  - **Value**: {mos:.1f}%")
        else:
            lines.append("  - **Value**: N/A")
        
        lines.append("  - **Formula**: ((Intrinsic Value - Current Price) / Intrinsic Value) × 100")
        lines.append("")
        lines.append("  **Conservative Dual-Anchor Methodology**:")
        lines.append("")
        lines.append("  This system uses the **lower** of two valuation methods as the intrinsic value:")
        lines.append("  1. **Normalized Graham Number** (3-year average EPS)")
        lines.append(f"  2. **EPV per share** ({EPV_MIN_YEARS}-{EPV_MAX_YEARS} year normalized earnings)")
        lines.append("")
        lines.append("  **Why This Is Conservative** (Graham's Philosophy):")
        lines.append("  - Graham emphasized buying with a margin of safety")
        lines.append("  - Using the lower value ensures we don't overpay")
        lines.append("  - If a company looks cheap on assets (Graham Number) but has poor earnings")
        lines.append("    power (EPV), the EPV reveals the true value")
        lines.append("  - If a company has strong earnings (EPV) but trades above asset value")
        lines.append("    (Graham Number), we use the more conservative asset-based valuation")
        lines.append("")
        
        # Show which metric was the limiting factor for this stock
        if limiting_factor != 'N/A':
            lines.append("  **For This Stock**:")
            
            if isinstance(normalized_gn, (int, float)):
                normalized_display = format_price_display(normalized_gn, unified_currency, unified_currency)
                lines.append(f"  - Normalized Graham Number: {normalized_display}")
            else:
                lines.append("  - Normalized Graham Number: N/A")
            
            if isinstance(epv_per_share, (int, float)):
                epv_display = format_price_display(epv_per_share, unified_currency, unified_currency)
                lines.append(f"  - EPV per share: {epv_display}")
            else:
                lines.append("  - EPV per share: N/A")
            
            if isinstance(intrinsic_value_used, (int, float)):
                intrinsic_display = format_price_display(intrinsic_value_used, unified_currency, unified_currency)
                basis = f"Capped by {limiting_factor}" if both_anchors else f"{limiting_factor} only"
                lines.append(f"  - **Intrinsic Value Used**: {intrinsic_display} ({basis})")
            else:
                lines.append("  - **Intrinsic Value Used**: N/A")
            
            lines.append("")
            
            # Add interpretation based on limiting factor (a comparison only when both exist)
            mos_note = or_default(mos_details.note, None)
            if not both_anchors:
                reason = f" ({mos_note})" if mos_note else ""
                lines.append(f"  **Interpretation**: Only the {limiting_factor} is available{reason}.")
            elif limiting_factor == "EPV":
                lines.append("  **Interpretation**: EPV is lower than Normalized Graham Number, indicating")
                lines.append("  that long-term earnings power is weaker than asset-based valuation suggests.")
                lines.append("  This is a red flag - the company may be destroying value over the full cycle.")
            elif limiting_factor == "Normalized Graham Number":
                lines.append("  **Interpretation**: Normalized Graham Number is lower than EPV, indicating")
                lines.append("  the stock trades at a premium to its asset value despite strong earnings power.")
                lines.append("  Graham would prefer to buy at a discount to both metrics.")
        
        lines.append("")
        lines.append("  **Graham's Principle**: *\"The margin of safety is always dependent on the price paid.\"*")
        lines.append("  Graham counted an issue a bargain when its indicated value was at least 50% above the price (price at most")
        lines.append("  two-thirds of value), and a net-current-asset issue at no more than two-thirds of NCAV.")
    
    def _add_3year_eps_breakdown(self, lines: List[str], unified_currency: str) -> None:
        """Add 3-year EPS breakdown display.
        
        Shows individual EPS values and years in descending order (most recent first).
        Format: "3-Year EPS: [Year1: $X.XX, Year2: $Y.YY, Year3: $Z.ZZ] → Avg: $A.AA"
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for display
        """
        eps_data = self.context.three_year_eps
        if eps_data is None:
            lines.append("  **3-Year EPS**: No financial history available")
            return
        
        if not eps_data['valid']:
            # Show why calculation failed
            lines.append(f"  **3-Year EPS**: {eps_data.get('warning', 'Insufficient data')}")
            return
        
        # Format the breakdown
        eps_values = eps_data['eps_values']
        years = eps_data['years']
        
        # Display years in descending order (most recent first)
        eps_parts = []
        for i, (year, eps) in enumerate(zip(years, eps_values)):
            year_label = fiscal_year(year)  # Fiscal year of the period end
            eps_display = format_price_display(eps, unified_currency, unified_currency)
            eps_parts.append(f"{year_label}: {eps_display}")
        
        eps_avg = self.context.three_year_eps_avg
        avg_display = format_price_display(eps_avg, unified_currency, unified_currency)
        
        # Format: "3-Year EPS: [Year1: $X.XX, Year2: $Y.YY, Year3: $Z.ZZ] → Avg: $A.AA"
        breakdown = f"  **3-Year EPS**: [{', '.join(eps_parts)}] → Avg: {avg_display}"
        lines.append(breakdown)
    
    def _add_new_metrics_explanations(self, lines: List[str]) -> None:
        """Add explanations for new Graham metrics.
        
        Args:
            lines: List to append lines to
        """
        or_default(self.financial_data.currency, 'USD')
        
        # Three-Year Average P/E
        three_year_pe = self.metrics.three_year_avg_pe
        if isinstance(three_year_pe, ThreeYearAvgPE) and three_year_pe.to_dict():
            lines.append("")
            lines.append("### P/E Ratio (3-Year Average)")
            lines.append("")
            lines.append("**Graham's Defensive Criterion #6** states: *\"Price should not exceed 15 times average earnings of the past three years.\"*")
            lines.append("")
            lines.append("We calculate the 3-year average EPS by taking the arithmetic mean of the most recent three years of annual EPS data, **including loss years (negative EPS)**. This provides a more stable valuation metric that smooths out cyclical fluctuations.")
            lines.append("")
            lines.append("**Formula**: P/E (3-Year Avg) = Current Price / ((EPS_Y1 + EPS_Y2 + EPS_Y3) / 3)")
            lines.append("")
            lines.append("**Note**: Loss years are included in the average as negative values, which reduces the average EPS and increases the P/E ratio, reflecting the company's historical volatility.")
        
        # Quick Ratio
        quick_ratio = or_default(self.metrics.quick_ratio, None)
        if quick_ratio is not None:
            lines.append("")
            lines.append("### Quick Ratio (Acid Test)")
            lines.append("")
            lines.append("The Quick Ratio is a more stringent liquidity test than the Current Ratio. It excludes inventory from current assets, as inventory may not be quickly convertible to cash.")
            lines.append("")
            lines.append("**Formula**: Quick Ratio = (Current Assets - Inventory) / Current Liabilities")
            lines.append("")
            lines.append("A Quick Ratio > 1.0 indicates the company can meet short-term obligations without relying on inventory sales. It is shown for information only: Graham's criteria use the current ratio.")
            lines.append("")
            lines.append("**Note**: When inventory is not reported in the annual balance sheet, the Quick Ratio is N/A (never estimated).")
        
        # NCA and Debt Coverage
        nca_details = self.metrics.nca_details
        if isinstance(nca_details, NCADetails) and nca_details.to_dict():
            lines.append("")
            lines.append("### Net Current Assets (Working Capital) and Debt Coverage")
            lines.append("")
            lines.append("Net current assets here are working capital, as in Graham's defensive debt test (not the net-net value, which deducts all liabilities).")
            lines.append("")
            lines.append("**Formula**: NCA = Current Assets - Current Liabilities")
            lines.append("")
            lines.append("**Debt Coverage Ratio** = Long-term Debt / NCA")
            lines.append("")
            lines.append("Graham's defensive investor test: long-term debt \"should not exceed the net current assets (or working capital)\" (ratio at most 1.0).")
            lines.append("")
            lines.append("**Note**: For regulated utilities Graham uses debt ≤ 2 × stock equity instead; for financial companies NCA analysis may not be applicable.")
        
        # Combined P/E × P/B Test
        combined_test = self.metrics.combined_pe_pb_test
        if isinstance(combined_test, CombinedPEPBTest) and combined_test.to_dict():
            lines.append("")
            lines.append("### Combined P/E × P/B Test")
            lines.append("")
            lines.append(f"Graham: \"a multiplier of earnings below {DEFENSIVE.MAX_PE_RATIO:g} could justify a correspondingly higher multiplier of assets ... the product of the multiplier times the ratio of price to book value should not exceed {GRAHAM_MULTIPLIER:g}\" (The Intelligent Investor, ch. 14). So criterion 7 (P/B ≤ {DEFENSIVE.MAX_PB_RATIO:g}) is also met when the product is within {GRAHAM_MULTIPLIER:g}:")
            lines.append("")
            lines.append(f"- P/E of {DEFENSIVE.MAX_PE_RATIO:g} allows P/B up to {GRAHAM_MULTIPLIER / DEFENSIVE.MAX_PE_RATIO:g}")
            lines.append(f"- P/E of 9 allows P/B up to {GRAHAM_MULTIPLIER / 9:g} (Graham's example: \"9 times earnings and 2.5 times asset value\")")
            lines.append(f"- It relaxes the P/B limit only: the P/E must still be ≤ {DEFENSIVE.MAX_PE_RATIO:g} (criterion 6)")
            lines.append("")
            lines.append(f"**Formula**: P/E (3-year average EPS) × P/B (tangible book value per share) ≤ {GRAHAM_MULTIPLIER:g}")
        
        # WCPS and Payout Ratio (from financial history)
        history = or_default(self.financial_data.history, {})
        if history:
            # Check if any year has WCPS or payout_ratio
            has_wcps = any(or_default(year_data.wcps, None) is not None for year_data in history.values())
            has_payout = any(or_default(year_data.payout_ratio, None) is not None for year_data in history.values())
            
            if has_wcps or has_payout:
                lines.append("")
                lines.append("### Historical Trend Metrics")
                lines.append("")
                
                if has_wcps:
                    lines.append("**Working Capital Per Share (WCPS)**: (Current Assets - Current Liabilities) / Shares Outstanding")
                    lines.append("- Measures the company's liquid net worth per share")
                    lines.append("- Positive values indicate financial strength; negative values indicate liquidity concerns")
                    lines.append("- Trend analysis: Increasing WCPS shows improving financial strength over time")
                    lines.append("")
                
                if has_payout:
                    lines.append("**Payout Ratio**: (Dividend / EPS) × 100")
                    lines.append("- Percentage of earnings paid as dividends")
                    lines.append("- Values > 100% indicate unsustainable dividends (paying more than earned)")
                    lines.append("- Values < 50% indicate conservative dividend policy with room for growth")
                    lines.append("- 'N/A' shown for years with zero or negative earnings (cannot assess sustainability against losses)")
                    lines.append("")
    
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
