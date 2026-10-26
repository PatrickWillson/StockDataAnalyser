"""Calculation Details section generator for dossier.

This module generates the calculation details section of the stock analysis dossier,
providing detailed breakdowns of key calculations for transparency and verification.
This includes share count disclosure, BVPS calculation, Graham Number calculation,
Net-Net Value calculation, currency conversion details, and EPV methodology clarification.
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


class CalculationDetailsSection:
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
    
    def __init__(self, financial_data: Dict[str, Any], metrics: Dict[str, Any]):
        """Initialize calculation details section.
        
        Args:
            financial_data: Dictionary containing financial data (FinancialData DTO)
            metrics: Dictionary containing Graham metrics (GrahamMetrics DTO)
        """
        self.financial_data = financial_data
        self.metrics = metrics
    
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
        unified_currency = self.financial_data.get('currency', 'USD')
        original_stock_currency = self.financial_data.get('original_stock_currency', unified_currency)
        history = self.financial_data.get('history', {})
        
        # Get most recent year data for calculations
        latest_year_calc, latest_data_calc = self._get_latest_year_data(history)
        
        if latest_year_calc and latest_data_calc:
            year_label = latest_year_calc.split('-')[0]
            
            # 1. Share Count Disclosure
            self._add_share_count_disclosure(lines, latest_data_calc, year_label)
            
            # 2. Book Value Per Share Calculation
            shares_used = latest_data_calc.get('shares_outstanding', 0)
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
    
    def _get_latest_year_data(self, history: Dict[str, Any]) -> tuple:
        """Get the most recent year with financial data.
        
        Args:
            history: Financial history dictionary
            
        Returns:
            tuple: (latest_year, latest_data) or (None, None) if not found
        """
        if not history:
            return None, None
        
        sorted_years = sorted(history.keys(), reverse=True)
        for year in sorted_years:
            year_data = history[year]
            if year_data.get('revenue', 0.0) > 0 or year_data.get('net_income', 0.0) != 0 or year_data.get('total_equity', 0.0) > 0:
                return year, year_data
        
        return None, None
    
    def _add_share_count_disclosure(self, lines: List[str], latest_data: Dict[str, Any], 
                                    year_label: str) -> None:
        """Add share count disclosure section.
        
        Args:
            lines: List to append lines to
            latest_data: Latest year financial data
            year_label: Year label for display
        """
        lines.append("### Share Count Used:")
        shares_used = latest_data.get('shares_outstanding', 0)
        
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
        
        total_equity = latest_data.get('total_equity', 0)
        intangibles = latest_data.get('intangible_assets', 0)
        goodwill = latest_data.get('goodwill', 0)
        
        # Initialize tbvps and bvps to avoid UnboundLocalError
        tbvps = 0
        bvps = 0
        
        if total_equity > 0 and shares_used > 0:
            lines.append(f"- **Total Stockholder Equity**: {unified_currency}{total_equity:,.0f}")
            lines.append(f"- **Less: Intangible Assets**: {unified_currency}{intangibles:,.0f}")
            lines.append(f"- **Less: Goodwill**: {unified_currency}{goodwill:,.0f}")
            
            tangible_equity = total_equity - abs(intangibles) - abs(goodwill)
            lines.append(f"- **Tangible Book Value**: {unified_currency}{tangible_equity:,.0f}")
            lines.append(f"- **Divided by Shares**: {shares_used:,.0f}")
            
            tbvps = tangible_equity / shares_used
            bvps = total_equity / shares_used
            
            lines.append(f"- **Tangible Book Value Per Share (TBVPS)**: {unified_currency}{tbvps:.2f}")
            lines.append(f"- **Book Value Per Share (BVPS)**: {unified_currency}{bvps:.2f} (without subtracting intangibles)")
            
            # Compare to API if available
            api_bvps = self.financial_data.get('book_value_per_share', 0)
            if api_bvps is None:
                api_bvps = 0
            if api_bvps > 0:
                diff_pct = abs(bvps - api_bvps) / api_bvps * 100
                if diff_pct > 15:
                    lines.append(f"- **API Book Value**: {unified_currency}{api_bvps:.2f} ({diff_pct:.1f}% difference)")
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
        graham_number = self.metrics.get('graham_number', 0)
        
        if isinstance(graham_number, (int, float)) and graham_number > 0:
            lines.append("### Graham Number Calculation:")
            eps_for_graham = latest_data.get('eps', 0)
            
            if eps_for_graham > 0 and tbvps > 0:
                lines.append("- **Formula**: √(22.5 × EPS × TBVPS)")
                lines.append(f"- **EPS**: {unified_currency}{eps_for_graham:.2f}")
                lines.append(f"- **TBVPS**: {unified_currency}{tbvps:.2f}")
                lines.append(f"- **Calculation**: √(22.5 × {eps_for_graham:.2f} × {tbvps:.2f}) = √({22.5 * eps_for_graham * tbvps:.2f})")
                lines.append(f"- **Graham Number**: {unified_currency}{graham_number:.2f}")
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
        net_net = self.metrics.get('net_net_value', 0)
        
        if isinstance(net_net, (int, float)) and net_net > 0:
            lines.append("### Net-Net Value Calculation:")
            current_assets = latest_data.get('current_assets', 0)
            total_liabilities = latest_data.get('total_liabilities', 0)
            
            if current_assets > 0 and total_liabilities > 0 and shares_used > 0:
                lines.append(f"- **Current Assets**: {unified_currency}{current_assets:,.0f}")
                lines.append(f"- **Total Liabilities**: {unified_currency}{total_liabilities:,.0f}")
                
                net_current_assets = current_assets - total_liabilities
                lines.append(f"- **Net Current Assets**: {unified_currency}{net_current_assets:,.0f}")
                lines.append(f"- **Divided by Shares**: {shares_used:,.0f}")
                lines.append(f"- **Net-Net Value Per Share**: {unified_currency}{net_net:.2f}")
                lines.append("- **Formula Used**: NCAV (Net Current Asset Value) = (Current Assets - Total Liabilities) / Shares")
                lines.append("  - **Note**: This is the standard 'Net-Net' formula used by most value investors")
                lines.append("  - **Alternative**: Graham's more conservative NNWC formula applies haircuts to current assets")
                lines.append("    - NNWC = (Cash + 0.75×AR + 0.5×Inventory - Total Liabilities) / Shares")
                lines.append("    - We use NCAV for consistency with common practice")
            
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
        if original_stock_currency != unified_currency:
            lines.append("### Currency Conversion Details:")
            fx_rate = self.financial_data.get('fx_rate_used', 0)
            
            # Check if London Fix was applied
            exchange = self.financial_data.get('exchange', '')
            london_fix_applied = False
            if exchange == "LSE" and original_stock_currency == "GBX":
                london_fix_applied = True
            
            if london_fix_applied:
                lines.append(f"- **Stock Trading Currency**: {original_stock_currency} (pence)")
                lines.append(f"- **Financial Statements Currency**: {unified_currency}")
                lines.append("- **London Fix Applied**: Yes (GBX → GBP conversion)")
                lines.append("  - LSE stocks trade in pence (GBX) but financials are in pounds (GBP)")
                lines.append("  - Price divided by 100 when P/E ratio > 500 (indicates pence vs pounds mismatch)")
                lines.append("  - Example: 1,650 GBX = 16.50 GBP")
            
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
        epv_value = self.metrics.get('epv', 0)
        
        if epv_value > 0:
            epv_details = self.metrics.get('epv_details', {})
            cost_of_capital = epv_details.get('cost_of_capital', 0.10)
            
            lines.append("### EPV Methodology Clarification:")
            lines.append("- **Approach Used**: Simplified Earnings Capitalization")
            lines.append("- **Formula**: Average Net Income (7-10 years) / 10%")
            lines.append("- **Inspiration**: Graham's emphasis on full-cycle earnings (not a direct Graham formula)")
            lines.append(f"- **Cost of Capital**: {cost_of_capital:.0%} (conservative fixed rate for simplicity)")
            lines.append("- **Includes Loss Years**: Yes (full business cycle)")
            lines.append("")
            lines.append("**This Differs From Graham's Original Work**:")
            lines.append("- Graham discussed 'earning power' conceptually but didn't provide this specific formula")
            lines.append("- Graham Number (√(22.5 × EPS × BVPS)) is Graham's actual intrinsic value formula")
            lines.append("- Our EPV is a simplified interpretation of Graham's principles")
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
