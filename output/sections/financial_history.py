"""Financial History section generator for dossier.

This module generates the 20-year financial history table section of the stock
analysis dossier, showing revenue, net income, EPS, dividends, book value
per share, total debt, shares outstanding, historical prices, and valuation ratios.
"""

from typing import List, Dict, Any, Optional


class FinancialHistorySection:
    """Generates the 20-year financial history table section of the dossier.
    
    This section includes:
    - 20-year table of key financial metrics
    - Revenue, Net Income, EPS, Dividend, and BVPS columns
    - Total Debt, Shares Outstanding, Year-End Price columns (Graham trend analysis)
    - Historical P/E and P/B ratios
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
    
    @staticmethod
    def format_debt(value: float, currency: str = None) -> str:
        """
        Format debt in billions or millions.
        
        Args:
            value: Debt value
            currency: Currency symbol (unused - kept for backward compatibility)
            
        Returns:
            Formatted string (e.g., "42.69B", "500.00M", "N/A")
            
        Note:
            Currency prefix removed for consistency with other columns.
            Section header indicates unified currency for all values.
        """
        if value == 0:
            return "N/A"
        if value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.2f}B"
        return f"{value / 1_000_000:.2f}M"
    
    @staticmethod
    def format_shares(value: float) -> str:
        """
        Format shares in billions or millions.
        
        Args:
            value: Share count
            
        Returns:
            Formatted string (e.g., "7.469B", "500.00M", "N/A")
        """
        if value == 0:
            return "N/A"
        if value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.3f}B"
        return f"{value / 1_000_000:.2f}M"
    
    @staticmethod
    def format_price(value: Optional[float], currency: str = None) -> str:
        """
        Format price.
        
        Args:
            value: Price value (or None if unavailable)
            currency: Currency symbol (unused - kept for backward compatibility)
            
        Returns:
            Formatted string (e.g., "450.12", "N/A")
            
        Note:
            Currency prefix removed for consistency with other columns.
            Section header indicates unified currency for all values.
        """
        if value is None:
            return "N/A"
        return f"{value:.2f}"
    
    @staticmethod
    def calculate_historical_pe(price: Optional[float], eps: float) -> str:
        """
        Calculate P/E ratio.
        
        Graham's method: Show losses explicitly, don't hide them as "N/A".
        This signals earnings instability to the analyst.
        
        Args:
            price: Year-end price (or None if unavailable)
            eps: Earnings per share
            
        Returns:
            Formatted P/E ratio or "Negative" for loss years or "N/A" for missing data
        """
        if price is None or eps is None:
            return "N/A"
        if eps < 0:
            return "Negative"  # Explicitly shows loss year per Graham's methodology
        if eps == 0:
            return "N/A"
        return f"{price / eps:.1f}"
    
    @staticmethod
    def calculate_historical_pb(price: Optional[float], bvps: float) -> str:
        """
        Calculate P/B ratio.
        
        Args:
            price: Year-end price (or None if unavailable)
            bvps: Book value per share
            
        Returns:
            Formatted P/B ratio or "N/A" for missing/invalid data
        """
        if price is None or bvps is None or bvps <= 0:
            return "N/A"
        return f"{price / bvps:.1f}"
    
    def generate(self) -> List[str]:
        """Generate financial history section content.
        
        Returns:
            List[str]: List of markdown lines for financial history section
        """
        lines = []
        
        # Extract currency information
        unified_currency = self.financial_data.get('currency', 'USD')
        currency_symbol = unified_currency  # Use full currency code as symbol
        
        # Section header
        lines.append("")
        lines.append("## SECTION 6: 20-YEAR FINANCIALS (STANDARDIZED)")
        lines.append(f"*All values in {unified_currency}*")
        lines.append("")
        
        # Determine dividend column header
        is_dividend_amounts = self.financial_data.get('is_dividend_amounts', False)
        div_header = "Div/Share" if is_dividend_amounts else "Div Count"
        
        # Table header with 13 columns (added WCPS and Payout Ratio)
        lines.append(f"| Year | Revenue | Net Income | EPS | {div_header} | BVPS | WCPS | Payout Ratio | Total Debt | Shares (B) | Price | P/E | P/B |")
        lines.append("|------|---------|------------|-----|-------------|------|------|--------------|------------|------------|-------|-----|-----|")
        
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
            total_debt = data.get('total_debt', 0.0)
            shares_outstanding = data.get('shares_outstanding', 0.0)
            year_end_price = data.get('year_end_price')  # Can be None
            
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
                wcps_str = "[Data Unavailable]"
                payout_ratio_str = "[Data Unavailable]"
                debt_str = "[Data Unavailable]"
                shares_str = "[Data Unavailable]"
                price_str = "[Data Unavailable]"
                pe_str = "[Data Unavailable]"
                pb_str = "[Data Unavailable]"
                
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
                bvps = round(total_equity / shares, 2) if shares > 0 and total_equity > 0 else 0
                bvps_str = str(bvps) if bvps > 0 else 'N/A'
                
                # Get WCPS (already calculated in financial_data_processor)
                wcps = data.get('wcps')
                if wcps == 'N/A' or wcps is None:
                    wcps_str = 'N/A'
                elif isinstance(wcps, (int, float)):
                    # Add warning indicator for negative WCPS
                    if wcps < 0:
                        wcps_str = f"⚠️ {wcps:.2f}"
                    else:
                        wcps_str = f"{wcps:.2f}"
                else:
                    wcps_str = str(wcps)
                
                # Get Payout Ratio (already calculated in financial_data_processor)
                payout_ratio = data.get('payout_ratio', 'N/A')
                payout_ratio_str = str(payout_ratio)
                
                # Format new columns using helper functions
                debt_str = self.format_debt(total_debt, currency_symbol)
                shares_str = self.format_shares(shares_outstanding)
                price_str = self.format_price(year_end_price, currency_symbol)
                
                # Calculate historical ratios
                pe_str = self.calculate_historical_pe(year_end_price, eps)
                pb_str = self.calculate_historical_pb(year_end_price, bvps if bvps > 0 else None)
            
            # Extract year display (e.g., '2024-06-30' → '2024')
            year_display = year.split('-')[0]
            
            row = f"| {year_display} | {revenue_str} | {net_income_str} | {eps_str} | {dividend_str} | {bvps_str} | {wcps_str} | {payout_ratio_str} | {debt_str} | {shares_str} | {price_str} | {pe_str} | {pb_str} |"
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
        
        # Add note on new columns
        lines.append("")
        lines.append("**Graham Trend Analysis Columns:**")
        lines.append("- **WCPS (Working Capital Per Share)**: (Current Assets - Current Liabilities) / Shares Outstanding")
        lines.append("  - Measures the company's liquid net worth per share")
        lines.append("  - Positive values indicate financial strength")
        lines.append("  - ⚠️ Negative values indicate current liabilities exceed current assets (liquidity concern)")
        lines.append("  - Trend analysis: Increasing WCPS shows improving financial strength")
        lines.append("- **Payout Ratio**: (Dividend / EPS) × 100")
        lines.append("  - Percentage of earnings paid as dividends")
        lines.append("  - Values > 100% indicate unsustainable dividends (paying more than earned)")
        lines.append("  - Values < 50% indicate conservative dividend policy with room for growth")
        lines.append("  - 'N/A' shown for years with zero or negative earnings")
        lines.append("- **Total Debt**: Sum of long-term and short-term debt. Graham emphasized tracking debt trends to distinguish companies that grow through retained earnings vs leverage.")
        lines.append("- **Shares (B)**: Common shares outstanding in billions. Tracks shareholder dilution (increasing shares) or buyback programs (decreasing shares).")
        lines.append("- **Price**: Year-end stock price on fiscal year end date (or last trading day within 7 days prior). Source: Yahoo Finance via yfinance.")
        lines.append("- **P/E**: Historical Price-to-Earnings ratio (Price ÷ EPS). Shows how the market valued earnings power over time. 'Negative' indicates loss year (Graham's method: show losses explicitly).")
        lines.append("- **P/B**: Historical Price-to-Book ratio (Price ÷ BVPS). Shows how the market valued net assets over time.")
        lines.append("")
        
        # Add note about FX rate methodology
        historical_fx_rates = self.financial_data.get('historical_fx_rates', {})
        if historical_fx_rates:
            # Historical FX rates were used
            lines.append("*Note: Historical prices converted to unified currency using date-matched historical FX rates from yfinance. This ensures accurate historical P/E and P/B ratios that reflect actual market conditions at the time.*")
        else:
            # Legacy behavior: current FX rate used for all years
            lines.append("*Note: Historical prices converted to unified currency using current FX rates. Historical FX rates not used - actual historical valuations may differ due to FX fluctuations.*")
        
        return lines
