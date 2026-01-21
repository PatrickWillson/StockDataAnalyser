"""Financial History section generator for dossier.

This module generates the 20-year financial history table section of the stock
analysis dossier, showing revenue, net income, EPS, dividends, and book value
per share over time.
"""

from typing import List, Dict, Any


class FinancialHistorySection:
    """Generates the 20-year financial history table section of the dossier.
    
    This section includes:
    - 20-year table of key financial metrics
    - Revenue, Net Income, EPS, Dividend, and BVPS columns
    - Handling of incomplete years (dividend data without financial statements)
    - Notes on data completeness and Graham's principles
    
    Requirements: 2.7
    """
    
    def __init__(self, financial_data: Dict[str, Any]):
        """Initialize financial history section.
        
        Args:
            financial_data: Dictionary containing financial data (FinancialData DTO)
        """
        self.financial_data = financial_data
    
    def generate(self) -> List[str]:
        """Generate financial history section content.
        
        Returns:
            List[str]: List of markdown lines for financial history section
        """
        lines = []
        
        # Extract currency information
        unified_currency = self.financial_data.get('currency', 'USD')
        
        # Section header
        lines.append("")
        lines.append("## SECTION 6: 20-YEAR FINANCIALS (STANDARDIZED)")
        lines.append(f"*All values in {unified_currency}*")
        lines.append("")
        
        # Determine dividend column header
        is_dividend_amounts = self.financial_data.get('is_dividend_amounts', False)
        div_header = "Div/Share" if is_dividend_amounts else "Div Count"
        
        # Table header
        lines.append(f"| Year | Revenue | Net Income | EPS | {div_header} | BVPS |")
        lines.append("|------|---------|------------|-----|-------------|------|")
        
        # Get history and sort years descending (most recent first)
        history = self.financial_data.get('history', {})
        sorted_years = sorted(history.keys(), reverse=True)[:20]
        
        # Track incomplete years for notes
        incomplete_years = []
        
        # Generate table rows
        for year in sorted_years:
            data = history[year]
            revenue = data.get('revenue', 0.0)
            net_income = data.get('net_income', 0.0)
            eps = data.get('eps', 0.0)
            dividend = data.get('dividend', 0.0)
            
            # Check if this year has actual financial data or just dividend data
            has_financial_data = revenue > 0 or net_income != 0 or eps != 0
            
            # Format values - show "[Data Unavailable]" for years without financial statements
            if not has_financial_data and dividend > 0:
                # Year has dividend but no financial statements yet
                revenue_str = "[Data Unavailable]"
                net_income_str = "[Data Unavailable]"
                eps_str = "[Data Unavailable]"
                dividend_str = str(dividend)
                bvps_str = "[Data Unavailable]"
                
                # Track incomplete year
                year_only = year.split('-')[0]
                incomplete_years.append(year_only)
            else:
                # Normal year with financial data
                revenue_str = str(revenue) if revenue != 0 else 'N/A'
                net_income_str = str(net_income) if net_income != 0 else 'N/A'
                eps_str = str(eps) if eps != 0 else 'N/A'
                dividend_str = str(dividend) if dividend != 0 else 'N/A'
                
                # Calculate BVPS from balance sheet data
                total_equity = data.get('total_equity', 0)
                shares = data.get('shares_outstanding', 0)
                bvps = round(total_equity / shares, 2) if shares > 0 and total_equity > 0 else 'N/A'
                bvps_str = str(bvps)
            
            row = f"| {year} | {revenue_str} | {net_income_str} | {eps_str} | {dividend_str} | {bvps_str} |"
            lines.append(row)
        
        # Add notes on data completeness
        lines.append("")
        lines.append("**Note on Data Completeness:**")
        
        if incomplete_years:
            years_str = ", ".join(incomplete_years)
            lines.append(f"- Years marked '[Data Unavailable]' ({years_str}) show declared dividends but lack complete audited annual financial statements")
            lines.append(f"- **Graham's Principle**: Analysis and valuations use only complete annual data from audited financial statements")
            lines.append(f"- Declared dividends are shown for income investors but excluded from historical calculations")
        
        # Add note if showing counts instead of amounts
        if not is_dividend_amounts:
            lines.append("")
            lines.append("*Note: Dividend column shows number of payments per year (actual amounts not available from data source)*")
        
        return lines
