"""Key Metrics section generator for dossier.

This module generates the key metrics section of the stock analysis dossier,
including profitability metrics, book value, ownership, and risk metrics.
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
    
    def __init__(self, financial_data: Dict[str, Any], metrics: Dict[str, Any] = None):
        """Initialize key metrics section.
        
        Args:
            financial_data: Dictionary containing financial data (FinancialData DTO)
            metrics: Dictionary containing Graham metrics (GrahamMetrics DTO) - optional for backward compatibility
        """
        self.financial_data = financial_data
        self.metrics = metrics or {}
    
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
        unified_currency = self.financial_data.get('currency', 'USD')
        
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
        roe = self.financial_data.get('roe', 0)
        roa = self.financial_data.get('roa', 0)
        profit_margin = self.financial_data.get('profit_margin', 0)
        
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
        history = self.financial_data.get('history', {})
        if history:
            sorted_years = sorted(history.keys(), reverse=True)
            # Find most recent year with financial data
            for year in sorted_years:
                year_data = history[year]
                if year_data.get('revenue', 0.0) > 0 or year_data.get('net_income', 0.0) != 0 or year_data.get('total_equity', 0.0) > 0:
                    most_recent_data = year_data
                    total_equity = most_recent_data.get('total_equity', 0)
                    shares = most_recent_data.get('shares_outstanding', 0)
                    if shares > 0 and total_equity > 0:
                        book_value = round(total_equity / shares, 2)
                        # Book value is already in unified currency
                        bvps_display = format_price_display(book_value, unified_currency, unified_currency)
                        lines.append(f"- Book Value Per Share: {bvps_display}")
                    break
    
    def _add_liquidity_analysis(self, lines: List[str], unified_currency: str) -> None:
        """Add liquidity analysis including Current Ratio, Quick Ratio, and NCA details.
        
        Args:
            lines: List to append lines to
            unified_currency: Currency for display
        """
        lines.append("")
        lines.append("### Liquidity Analysis")
        lines.append("")
        
        # Current Ratio (from financial_data if available)
        current_ratio = self.financial_data.get('current_ratio', 0)
        if current_ratio > 0:
            lines.append(f"- **Current Ratio**: {current_ratio:.2f} (Current Assets / Current Liabilities)")
        
        # Quick Ratio (from metrics if available)
        quick_ratio = self.metrics.get('quick_ratio')
        if quick_ratio and quick_ratio != 'N/A':
            lines.append(f"- **Quick Ratio**: {quick_ratio:.2f} (Acid Test - excludes inventory)")
        elif quick_ratio == 'N/A':
            lines.append(f"- **Quick Ratio**: N/A")
        
        # NCA Details (from metrics if available)
        nca_details = self.metrics.get('nca_details', {})
        if nca_details and isinstance(nca_details, dict):
            lines.append("")
            lines.append("### Net Current Assets (NCA) Analysis")
            lines.append("")
            
            current_assets = nca_details.get('current_assets')
            total_liabilities = nca_details.get('total_liabilities')
            nca = nca_details.get('nca')
            long_term_debt = nca_details.get('long_term_debt')
            debt_coverage_ratio = nca_details.get('debt_coverage_ratio')
            debt_coverage_pct = nca_details.get('debt_coverage_pct')
            
            # Display values
            if current_assets is not None and current_assets != 'N/A':
                ca_display = format_price_display(current_assets, unified_currency, unified_currency)
                lines.append(f"- **Current Assets**: {ca_display}")
            
            if total_liabilities is not None and total_liabilities != 'N/A':
                tl_display = format_price_display(total_liabilities, unified_currency, unified_currency)
                lines.append(f"- **Total Liabilities**: {tl_display}")
            
            if nca is not None and nca != 'N/A':
                nca_display = format_price_display(nca, unified_currency, unified_currency)
                lines.append(f"- **Net Current Assets**: {nca_display}")
            
            if long_term_debt is not None and long_term_debt != 'N/A':
                ltd_display = format_price_display(long_term_debt, unified_currency, unified_currency)
                lines.append(f"- **Long-term Debt**: {ltd_display}")
            
            if debt_coverage_ratio is not None and debt_coverage_ratio != 'N/A':
                lines.append(f"- **Debt Coverage Ratio**: {debt_coverage_ratio:.2f} ({debt_coverage_pct}) - Long-term Debt / NCA")
                lines.append("")
                lines.append("*Graham's defensive test requires long-term debt < NCA (ratio < 1.0). This ensures the company could theoretically pay off all long-term debt using only its liquid assets.*")
            elif debt_coverage_ratio == 'N/A':
                lines.append(f"- **Debt Coverage Ratio**: N/A")

    
    def _add_ownership_metrics(self, lines: List[str]) -> None:
        """Add ownership metrics (Insider, Institutional).
        
        Args:
            lines: List to append lines to
        """
        insider = self.financial_data.get('insider_ownership', 0)
        institutional = self.financial_data.get('institutional_ownership', 0)
        
        if insider > 0:
            lines.append(f"- Insider Ownership: {insider:.2f}%")
        if institutional > 0:
            lines.append(f"- Institutional Ownership: {institutional:.2f}%")
    
    def _add_risk_metrics(self, lines: List[str]) -> None:
        """Add risk metrics (Beta).
        
        Args:
            lines: List to append lines to
        """
        beta = self.financial_data.get('beta', 0)
        if beta is None:
            beta = 0
        if beta > 0:
            lines.append(f"- Beta (Volatility): {beta:.3f}")
