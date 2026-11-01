"""Calculation Details section generator for dossier.

This module generates the calculation details section of the stock analysis dossier,
providing detailed breakdowns of key calculations for transparency and verification.
This includes share count disclosure, BVPS calculation, Graham Number calculation,
Net-Net Value calculation, currency conversion details, and EPV methodology clarification.
"""

from typing import List, Dict, Any, Optional, Union
from config.graham_constants import COST_OF_CAPITAL, GRAHAM_MULTIPLIER
from config.valuation_config import EPV_MAX_YEARS, EPV_MIN_YEARS
from config.data_quality_config import BVPS_MAX_DIFF_PCT
from output.sections.base import DossierSection
from core.report_context import ReportContext, build_report_context, fiscal_year
from core.models import FinancialData, EPVDetails, GrahamResult, or_default


class CalculationDetailsSection(DossierSection):
    """Generates the calculation details section of the dossier.
    
    This section provides detailed breakdowns of key calculations including:
    - Share count disclosure and source
    - Book Value Per Share (BVPS) calculation
    - Graham Number calculation with formula
    - Net-Net Value calculation
    - Currency conversion details (if applicable)
    - EPV methodology clarification
    
    Requirements: 2.5
    """
    
    def __init__(self, financial_data: Dict[str, Any], metrics: Union[GrahamResult, Dict[str, Any]],
                 context: Optional[ReportContext] = None):
        """Initialize calculation details section.
        
        Args:
            financial_data: Dictionary containing financial data (FinancialData DTO)
            metrics: Graham metrics (GrahamResult, or its dict form)
        """
        self.financial_data = FinancialData.from_dict(financial_data)
        self.metrics = GrahamResult.from_dict(metrics)
        self.context = context or build_report_context(financial_data, metrics)
    
    def generate(self) -> List[str]:
        """Generate calculation details section content.
        
        Returns:
            List[str]: List of markdown lines for calculation details section
        """
        lines = []
        
        # Section header
        lines.append("")
        lines.append("## CALCULATION DETAILS")
        lines.append("*Detailed breakdown of key calculations for transparency and verification*")
        lines.append("")
        
        # Extract currency and history
        unified_currency = or_default(self.financial_data.currency, 'USD')
        original_stock_currency = or_default(self.financial_data.original_stock_currency, unified_currency)
        
        # Get most recent year data for calculations
        latest_year_calc = self.context.latest_year
        latest_data_calc = self.context.latest_row if latest_year_calc else None
        
        if latest_year_calc and latest_data_calc:
            year_label = fiscal_year(latest_year_calc)
            
            # 1. Share Count Disclosure
            self._add_share_count_disclosure(lines, latest_data_calc, year_label)
            
            # 2. Book Value Per Share Calculation
            shares_used = or_default(latest_data_calc.shares_outstanding, 0)
            tbvps, bvps = self._add_bvps_calculation(lines, latest_data_calc, shares_used, unified_currency)
            
            # 3. Graham Number Calculation
            self._add_graham_number_calculation(lines, latest_data_calc, tbvps, unified_currency)
            
            # 4. Net-Net Value Calculation
            self._add_net_net_calculation(lines, latest_data_calc, shares_used, unified_currency)
            
            # 5. Currency Conversion Details (if applicable)
            self._add_currency_conversion_details(lines, original_stock_currency, unified_currency)
            
            # 6. EPV Methodology Clarification
            self._add_epv_methodology_clarification(lines)
        
        lines.append("")
        lines.append("---")
        
        return lines
    
    def _add_share_count_disclosure(self, lines: List[str], latest_data: Dict[str, Any], 
                                    year_label: str) -> None:
        """Add share count disclosure section.
        
        Args:
            lines: List to append lines to
            latest_data: Latest year financial data
            year_label: Year label for display
        """
        lines.append("### Share Count Used:")
        shares_used = or_default(latest_data.shares_outstanding, 0)
        
        if shares_used > 0:
            lines.append(f"- **Shares Outstanding**: {shares_used:,.0f} shares")
            lines.append(f"- **Source**: Financial statements (outstandingShares.annual for {year_label})")
            lines.append("- **Note**: This is the year-specific share count from audited financials, used for accurate per-share calculations")
            
            # Compare to SharesStats if significantly different
            lines.append("- **Why This Matters**: Market data sources may show different share counts (e.g., public float vs. total issued shares)")
            lines.append("  - Graham methodology requires using shares from the same period as the financial statements")
            lines.append("  - Using market float instead of financial statement shares can inflate per-share metrics by 5-10%")
        
        lines.append("")
    
    def _add_bvps_calculation(self, lines: List[str], latest_data: Dict[str, Any], 
                             shares_used: int, unified_currency: str) -> tuple:
        """Add Book Value Per Share calculation section.
        
        Args:
            lines: List to append lines to
            latest_data: Latest year financial data
            shares_used: Number of shares outstanding
            unified_currency: Currency for display
            
        Returns:
            tuple: (tbvps, bvps) values
        """
        lines.append("### Book Value Per Share (BVPS) Calculation:")
        
        total_equity = or_default(latest_data.total_equity, 0)
        intangibles = or_default(latest_data.intangible_assets, 0)
        goodwill = or_default(latest_data.goodwill, 0)
        
        # Initialize tbvps and bvps to avoid UnboundLocalError
        tbvps = 0
        bvps = 0
        
        if total_equity > 0 and shares_used > 0:
            lines.append(f"- **Total Stockholder Equity**: {total_equity:,.0f} {unified_currency}")
            lines.append(f"- **Less: Intangible Assets**: {intangibles:,.0f} {unified_currency}")
            lines.append(f"- **Less: Goodwill**: {goodwill:,.0f} {unified_currency}")
            
            tangible_book = self.context.latest_tangible_equity
            lines.append(f"- **Tangible Book Value**: {tangible_book:,.0f} {unified_currency}")
            lines.append(f"- **Divided by Shares**: {shares_used:,.0f}")
            
            tbvps = self.context.latest_tbvps
            bvps = self.context.latest_bvps
            
            lines.append(f"- **Tangible Book Value Per Share (TBVPS)**: {tbvps:.2f} {unified_currency}")
            lines.append(f"- **Book Value Per Share (BVPS)**: {bvps:.2f} {unified_currency} (without subtracting intangibles)")
            
            # Compare to API if available
            api_bvps = or_default(self.financial_data.book_value_per_share, None) or 0
            diff_pct = self.context.api_bvps_diff_pct
            if diff_pct is not None:
                if diff_pct > BVPS_MAX_DIFF_PCT:
                    lines.append(f"- **API Book Value**: {api_bvps:.2f} {unified_currency} ({diff_pct:.1f}% difference)")
                    lines.append("  - **Explanation**: Differences may be due to:")
                    lines.append("    - Different share count (API may use basic vs. diluted)")
                    lines.append("    - Different accounting treatment of intangibles")
                    lines.append("    - Timing differences (API may use more recent data)")
                    lines.append("    - Our calculation uses audited financial statement data per Graham methodology")
        
        lines.append("")
        
        return tbvps, bvps
    
    def _add_graham_number_calculation(self, lines: List[str], latest_data: Dict[str, Any], 
                                       tbvps: float, unified_currency: str) -> None:
        """Add Graham Number calculation section.
        
        Args:
            lines: List to append lines to
            latest_data: Latest year financial data
            tbvps: Tangible Book Value Per Share
            unified_currency: Currency for display
        """
        graham_number = or_default(self.metrics.graham_number, 0)
        
        if isinstance(graham_number, (int, float)) and graham_number > 0:
            lines.append("### Graham Number Calculation:")
            eps_for_graham = or_default(latest_data.eps, 0)
            
            if eps_for_graham > 0 and tbvps > 0:
                lines.append(f"- **Formula**: √({GRAHAM_MULTIPLIER:g} × EPS × TBVPS)")
                lines.append(f"- **EPS**: {eps_for_graham:.2f} {unified_currency}")
                lines.append(f"- **TBVPS**: {tbvps:.2f} {unified_currency}")
                lines.append(f"- **Calculation**: √({GRAHAM_MULTIPLIER:g} × {eps_for_graham:.2f} × {tbvps:.2f}) = √({GRAHAM_MULTIPLIER * eps_for_graham * tbvps:.2f})")
                lines.append(f"- **Graham Number**: {graham_number:.2f} {unified_currency}")
                lines.append("- **Note**: Uses unrounded intermediate values for precision")
            
            lines.append("")
    
    def _add_net_net_calculation(self, lines: List[str], latest_data: Dict[str, Any], 
                                 shares_used: int, unified_currency: str) -> None:
        """Add Net-Net Value calculation section.
        
        Args:
            lines: List to append lines to
            latest_data: Latest year financial data
            shares_used: Number of shares outstanding
            unified_currency: Currency for display
        """
        net_net = or_default(self.metrics.net_net_value, 0)
        
        if isinstance(net_net, (int, float)) and net_net > 0:
            lines.append("### Net-Net Value Calculation:")
            current_assets = or_default(latest_data.current_assets, 0)
            total_liabilities = or_default(latest_data.total_liabilities, 0)
            
            if current_assets > 0 and total_liabilities > 0 and shares_used > 0:
                lines.append(f"- **Current Assets**: {current_assets:,.0f} {unified_currency}")
                lines.append(f"- **Total Liabilities**: {total_liabilities:,.0f} {unified_currency}")
                claims_outside_equity = or_default(latest_data.claims_outside_equity, 0.0)
                if claims_outside_equity > 0:
                    lines.append(f"- **Less: Minority Interest and Other Claims Outside Common Equity**: "
                                 f"{claims_outside_equity:,.0f} {unified_currency}")
                
                net_current_assets = self.context.latest_ncav
                lines.append(f"- **Net Current Assets**: {net_current_assets:,.0f} {unified_currency}")
                lines.append(f"- **Divided by Shares**: {shares_used:,.0f}")
                lines.append(f"- **Net-Net Value Per Share**: {net_net:.2f} {unified_currency}")
                lines.append("- **Formula Used**: NCAV (Net Current Asset Value) = (Current Assets - Total Liabilities - claims ahead of the common) / Shares")
                lines.append("  - **Note**: Graham's own measure: \"current assets alone, minus all liabilities and claims ahead of the issue\"")
                lines.append("  - **Stricter alternative**: Graham's liquidating-value haircuts (Security Analysis ch. 43): cash 100%,")
                lines.append("    receivables 75-90%, inventories 50-75%, fixed assets 1-50% (not applied here)")
            
            lines.append("")
    
    def _add_currency_conversion_details(self, lines: List[str], 
                                        original_stock_currency: str, 
                                        unified_currency: str) -> None:
        """Add currency conversion details section.
        
        Args:
            lines: List to append lines to
            original_stock_currency: Original stock trading currency
            unified_currency: Unified currency for analysis
        """
        # The price unit follows the quote currency code (F6), e.g. GBp = pence
        quote_currency = self.context.quote_currency
        minor_unit_quote = self.context.quote_is_minor_unit
        if original_stock_currency != unified_currency or minor_unit_quote:
            lines.append("### Currency Conversion Details:")
            fx_rate = or_default(self.financial_data.fx_rate_used, 0)
            
            if minor_unit_quote:
                major = self.context.quote_major_currency
                name = "London Fix" if major == "GBP" else "Minor-Unit Conversion"
                lines.append(f"- **Stock Trading Currency**: {original_stock_currency} (price quoted in {quote_currency})")
                lines.append(f"- **Financial Statements Currency**: {unified_currency}")
                lines.append(f"- **{name} Applied**: Yes ({quote_currency} → {major} conversion)")
                lines.append(f"  - The quote currency {quote_currency} is a minor unit (1/100 of {major})")
                lines.append("  - Current price, 52-week range and historical prices divided by 100")
                lines.append(f"  - Example: 1,650 {quote_currency} = 16.50 {major}")
            
            if fx_rate is not None and fx_rate > 0 and fx_rate != 1.0:
                lines.append(f"- **FX Conversion Rate**: {fx_rate:.4f} ({original_stock_currency} → {unified_currency})")
                lines.append("- **Source**: Live FX rates from Frankfurter API (ECB data)")
                lines.append("- **What Was Converted**:")
                lines.append("  - Current stock price")
                lines.append("  - Dividend amounts (if from Dividend API)")
                lines.append(f"  - All values unified to {unified_currency} for consistent analysis")
            
            lines.append("- **Why Currency Unification Matters**:")
            lines.append("  - Ensures all per-share calculations use the same currency")
            lines.append("  - Prevents mixing GBX prices with GBP financials (100x error)")
            lines.append("  - Allows accurate comparison of price to intrinsic value")
            
            lines.append("")
    
    def _add_epv_methodology_clarification(self, lines: List[str]) -> None:
        """Add EPV methodology clarification section.
        
        Args:
            lines: List to append lines to
        """
        epv_value = or_default(self.metrics.epv, 0)
        
        if isinstance(epv_value, (int, float)) and epv_value > 0:
            epv_details = or_default(self.metrics.epv_details, EPVDetails())
            cost_of_capital = or_default(epv_details.cost_of_capital, COST_OF_CAPITAL)
            
            lines.append("### EPV Methodology Clarification:")
            lines.append("- **Approach Used**: Simplified Earnings Capitalization")
            lines.append(f"- **Formula**: Average Net Income ({EPV_MIN_YEARS}-{EPV_MAX_YEARS} years) / {COST_OF_CAPITAL:.0%}")
            lines.append(f"- **Basis**: Graham capitalised average past earnings at a multiplier kept within a reasonable range (maximum 10 in 1976); dividing by {COST_OF_CAPITAL:.0%} is a multiplier of {1 / COST_OF_CAPITAL:g}")
            lines.append(f"- **Cost of Capital**: {cost_of_capital:.0%} (conservative fixed rate for simplicity)")
            lines.append("- **Includes Loss Years**: Yes (full business cycle)")
            lines.append("")
            lines.append("**Relation to Graham's Work**:")
            lines.append("- Graham defined past earning power as average earnings over a stated period (five, seven or ten years)")
            lines.append(f"- The Graham Number (√({GRAHAM_MULTIPLIER:g} × EPS × TBVPS)) is not a formula Graham published; it is derived from his defensive criteria 6 and 7")
            lines.append("- This EPV uses net income, including loss years and special items, over 7-10 years")
            lines.append("")
            lines.append("**This Differs From Modern EPV (Greenwald, 2001)**:")
            lines.append("- Modern EPV uses normalized EBIT, not net income")
            lines.append("- Modern EPV subtracts maintenance CapEx")
            lines.append("- Modern EPV uses company-specific WACC (typically 8-12%)")
            lines.append("- Modern EPV is more precise but requires more estimation")
            lines.append("")
            lines.append("**Why We Use This Simplified Approach**:")
            lines.append("- Deterministic (no WACC estimation required)")
            lines.append("- Conservative (uses net income, not EBIT)")
            lines.append("- Consistent with other Graham-inspired metrics")
            lines.append("- Transparent and auditable")
            lines.append("- Provides reasonable valuation estimate for comparison")
