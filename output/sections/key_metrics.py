"""Key Metrics section generator for dossier.

This module generates the key metrics section of the stock analysis dossier,
including profitability metrics, book value, ownership, and risk metrics.
"""

from typing import List, Dict, Any, Optional, Union
from output.sections.base import DossierSection
from core.report_context import ReportContext, build_report_context
from core.models import FinancialData, CurrentRatio, GrahamResult, NCADetails, or_default
from output.formatting import format_price_display


class KeyMetricsSection(DossierSection):
    """Generates the key metrics section of the dossier.
    
    This section includes:
    - Profitability metrics (ROE, ROA, Profit Margin)
    - Book Value Per Share
    - Liquidity metrics (Current Ratio, Quick Ratio)
    - Net Current Assets (NCA) Analysis
    - Ownership metrics (Insider, Institutional)
    - Risk metrics (Beta)
    
    Requirements: 2.2
    """
    
    def __init__(self, financial_data: Dict[str, Any], metrics: Union[GrahamResult, Dict[str, Any], None] = None,
                 context: Optional[ReportContext] = None):
        """Initialize key metrics section.
        
        Args:
            financial_data: Dictionary containing financial data (FinancialData DTO)
            metrics: Graham metrics (GrahamResult, or its dict form) - optional for backward compatibility
        """
        self.financial_data = FinancialData.from_dict(financial_data)
        self.metrics = GrahamResult.from_dict(metrics or {})
        self.context = context or build_report_context(financial_data, self.metrics)
    
    def generate(self) -> List[str]:
        """Generate key metrics section content.
        
        Returns:
            List[str]: List of markdown lines for key metrics section
        """
        lines = []
        
        # Section header
        lines.append("")
        lines.append("## SECTION 2: KEY METRICS")
        
        # Extract currency information
        unified_currency = or_default(self.financial_data.currency, 'USD')
        
        # Profitability metrics
        self._add_profitability_metrics(lines)
        
        # Book value per share
        self._add_book_value(lines, unified_currency)
        
        # Liquidity Analysis (Current Ratio, Quick Ratio, NCA)
        self._add_liquidity_analysis(lines, unified_currency)
        
        # Ownership metrics
        self._add_ownership_metrics(lines)
        
        # Risk metrics
        self._add_risk_metrics(lines)
        
        lines.append("")
        lines.append("---")
        
        return lines
    
    def _add_profitability_metrics(self, lines: List[str]) -> None:
        """Add profitability metrics (ROE, ROA, Profit Margin).
        
        Args:
            lines: List to append lines to
        """
        roe = or_default(self.financial_data.roe, 0)
        roa = or_default(self.financial_data.roa, 0)
        profit_margin = or_default(self.financial_data.profit_margin, 0)
        
        if roe > 0:
            lines.append(f"- Return on Equity (ROE): {roe*100:.2f}%")
        if roa > 0:
            lines.append(f"- Return on Assets (ROA): {roa*100:.2f}%")
        if profit_margin > 0:
            lines.append(f"- Profit Margin: {profit_margin*100:.2f}%")
    
    def _add_book_value(self, lines: List[str], unified_currency: str) -> None:
        """Add book value per share calculation.
        
        Calculate from most recent balance sheet data for consistency with table.
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for display
        """
        if self.context.latest_year and self.context.latest_bvps is not None:
            # Book value is already in unified currency
            book_value = round(self.context.latest_bvps, 2)
            bvps_display = format_price_display(book_value, unified_currency, unified_currency)
            lines.append(f"- Book Value Per Share: {bvps_display}")
    
    def _add_liquidity_analysis(self, lines: List[str], unified_currency: str) -> None:
        """Add liquidity analysis including Current Ratio, Quick Ratio, and NCA details.
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for display
        """
        lines.append("")
        lines.append("### Liquidity Analysis")
        lines.append("")
        
        # Current Ratio (calculated in core from the latest annual balance sheet)
        current_ratio = self.metrics.current_ratio
        if isinstance(current_ratio, CurrentRatio):
            ratio = or_default(current_ratio.ratio, None)
            fiscal_year_end = or_default(current_ratio.fiscal_year_end, None)
            if isinstance(ratio, (int, float)):
                lines.append(f"- **Current Ratio**: {ratio:.2f} (Current Assets / Current Liabilities, "
                             f"fiscal year ending {fiscal_year_end})")
            else:
                lines.append("- **Current Ratio**: N/A (current liabilities not reported)")
        
        # Quick Ratio (from metrics if available)
        quick_ratio = or_default(self.metrics.quick_ratio, None)
        if quick_ratio and quick_ratio != 'N/A':
            lines.append(f"- **Quick Ratio**: {quick_ratio:.2f} (Acid Test - excludes inventory)")
        elif quick_ratio == 'N/A':
            lines.append("- **Quick Ratio**: N/A")
        
        # NCA Details (from metrics if available)
        nca_details = self.metrics.nca_details
        if isinstance(nca_details, NCADetails) and nca_details.to_dict():
            lines.append("")
            lines.append("### Net Current Assets (Working Capital) and Debt")
            lines.append("")
            
            current_assets = or_default(nca_details.current_assets, None)
            current_liabilities = or_default(nca_details.current_liabilities, None)
            nca = or_default(nca_details.nca, None)
            long_term_debt = or_default(nca_details.long_term_debt, None)
            debt_coverage_ratio = or_default(nca_details.debt_coverage_ratio, None)
            debt_coverage_pct = or_default(nca_details.debt_coverage_pct, None)
            
            # Display values
            if current_assets is not None and current_assets != 'N/A':
                ca_display = format_price_display(current_assets, unified_currency, unified_currency)
                lines.append(f"- **Current Assets**: {ca_display}")
            
            if current_liabilities is not None and current_liabilities != 'N/A':
                cl_display = format_price_display(current_liabilities, unified_currency, unified_currency)
                lines.append(f"- **Current Liabilities**: {cl_display}")
            
            if nca is not None and nca != 'N/A':
                nca_display = format_price_display(nca, unified_currency, unified_currency)
                lines.append(f"- **Net Current Assets**: {nca_display}")
            
            if long_term_debt is not None and long_term_debt != 'N/A':
                ltd_display = format_price_display(long_term_debt, unified_currency, unified_currency)
                lines.append(f"- **Long-term Debt**: {ltd_display}")
            
            if debt_coverage_ratio is not None and debt_coverage_ratio != 'N/A':
                lines.append(f"- **Debt Coverage Ratio**: {debt_coverage_ratio:.2f} ({debt_coverage_pct}) - Long-term Debt / NCA")
                lines.append("")
                lines.append("*Graham's defensive test: long-term debt should not exceed net current assets (working capital), i.e. a ratio of at most 1.0.*")
            elif debt_coverage_ratio == 'N/A':
                lines.append("- **Debt Coverage Ratio**: N/A")

    
    def _add_ownership_metrics(self, lines: List[str]) -> None:
        """Add ownership metrics (Insider, Institutional).
        
        Args:
            lines: List to append lines to
        """
        insider = or_default(self.financial_data.insider_ownership, 0)
        institutional = or_default(self.financial_data.institutional_ownership, 0)
        
        if insider > 0:
            lines.append(f"- Insider Ownership: {insider:.2f}%")
        if institutional > 0:
            lines.append(f"- Institutional Ownership: {institutional:.2f}%")
    
    def _add_risk_metrics(self, lines: List[str]) -> None:
        """Add risk metrics (Beta).
        
        Args:
            lines: List to append lines to
        """
        beta = or_default(self.financial_data.beta, 0)
        if beta is None:
            beta = 0
        if beta > 0:
            lines.append(f"- Beta (Volatility): {beta:.3f}")
