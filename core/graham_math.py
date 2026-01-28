"""
Graham Calculator - Core calculation engine for Benjamin Graham methodology.

This module implements strict Graham formulas for value investing analysis:
- Graham Number (intrinsic value)
- Tangible Book Value Per Share (TBVPS)
- Net-Net Working Capital Value
- Margin of Safety
- Earnings Power Value (EPV)
- Defensive Investor Tests
"""

import math
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Union, List, Any

from config.graham_constants import GRAHAM_MULTIPLIER, COST_OF_CAPITAL
from config.investor_thresholds import DEFENSIVE, ENTERPRISING


class GrahamCalculator:
    """
    Performs all Graham methodology calculations with strict formulas.
    
    Handles edge cases gracefully:
    - Negative equity (TBVPS < 0)
    - Negative earnings (EPS < 0)
    - Young companies (< 10 years history)
    - Missing data
    """
    
    def __init__(self, financial_data: dict):
        """
        Initialize calculator with financial data.
        
        Args:
            financial_data: Dictionary containing ticker, price, currency, history, etc.
        """
        self.data = financial_data
        self.warnings = []
    
    def _get_latest_financial_year(self, history: dict, years: list) -> str:
        """
        Get the most recent year with actual financial data.
        
        Skips years that only have dividend data (e.g., future years where
        dividends are declared but annual financials aren't available yet).
        
        Args:
            history: Financial history dictionary
            years: List of years sorted in reverse chronological order
            
        Returns:
            Most recent year with financial data, or None if not found
        """
        for year in years:
            year_data = history[year]
            # Check if year has actual financial data (not just dividend)
            has_financial_data = (
                year_data.get('revenue', 0.0) > 0 or
                year_data.get('net_income', 0.0) != 0 or
                year_data.get('total_equity', 0.0) > 0 or
                year_data.get('current_assets', 0.0) > 0
            )
            if has_financial_data:
                return year
        return None
    
    def compute_tbvps(self, round_result: bool = True) -> Union[float, str]:
        """
        Calculate Tangible Book Value Per Share.
        
        Formula: (Total Equity - Intangible Assets - Goodwill) / Shares Outstanding
        
        Args:
            round_result: If True, round to 2 decimals. If False, return raw value.
        
        Returns:
            float: TBVPS value, or "N/A" if data unavailable or negative
        """
        history = self.data.get('history', {})
        if not history:
            return "N/A"
        
        # Get most recent fiscal year with financial data
        years = sorted(history.keys(), reverse=True)
        if not years:
            return "N/A"
        
        latest_year = self._get_latest_financial_year(history, years)
        if not latest_year:
            return "N/A"
        
        year_data = history[latest_year]
        
        # Extract required fields
        total_equity = year_data.get('total_equity', 0.0)
        intangible_assets = year_data.get('intangible_assets', 0.0)
        goodwill = year_data.get('goodwill', 0.0)
        shares_outstanding = year_data.get('shares_outstanding', 0.0)
        
        # Validate shares outstanding
        if shares_outstanding == 0:
            return "N/A"
        
        # Calculate TBVPS - use absolute values to handle negative reporting
        tangible_equity = total_equity - abs(intangible_assets) - abs(goodwill)
        tbvps = tangible_equity / shares_outstanding
        
        # Handle negative TBVPS
        if tbvps < 0:
            self.warnings.append("Negative Tangible Book Value - Company has negative equity")
            return "N/A"
        
        return round(tbvps, 2) if round_result else tbvps
    
    def compute_graham_number(self) -> Union[float, str]:
        """
        Calculate Graham Number (intrinsic value estimate).
        
        Formula: sqrt(22.5 × EPS × TBVPS)
        
        Returns:
            float: Graham Number rounded to 2 decimals, or "N/A" if invalid inputs
        """
        # Get TBVPS (unrounded for calculation accuracy)
        tbvps = self.compute_tbvps(round_result=False)
        if tbvps == "N/A":
            return "N/A"
        
        # Get most recent EPS from year with financial data
        history = self.data.get('history', {})
        if not history:
            return "N/A"
        
        years = sorted(history.keys(), reverse=True)
        if not years:
            return "N/A"
        
        latest_year = self._get_latest_financial_year(history, years)
        if not latest_year:
            return "N/A"
        
        eps = history[latest_year].get('eps', 0.0)
        
        # Handle negative EPS
        if eps <= 0:
            return "N/A"
        
        # Calculate Graham Number
        graham_number = math.sqrt(GRAHAM_MULTIPLIER * eps * tbvps)
        
        return round(graham_number, 2)
    
    def compute_net_net(self, round_result: bool = True) -> Union[float, str]:
        """
        Calculate Net-Net Working Capital Value.
        
        Formula: (Current Assets - Total Liabilities) / Shares Outstanding
        
        Args:
            round_result: If True, round to 2 decimals. If False, return raw value.
        
        Returns:
            float: Net-Net Value rounded to 2 decimals, or "N/A" if data unavailable
        """
        history = self.data.get('history', {})
        if not history:
            return "N/A"
        
        # Get most recent fiscal year with financial data
        years = sorted(history.keys(), reverse=True)
        if not years:
            return "N/A"
        
        latest_year = self._get_latest_financial_year(history, years)
        if not latest_year:
            return "N/A"
        
        year_data = history[latest_year]
        
        # Extract required fields
        current_assets = year_data.get('current_assets')
        total_liabilities = year_data.get('total_liabilities')
        shares_outstanding = year_data.get('shares_outstanding', 0.0)
        
        # Handle missing data
        if current_assets is None or total_liabilities is None:
            return "N/A"
        
        # Validate shares outstanding
        if shares_outstanding == 0:
            return "N/A"
        
        # Calculate Net-Net Value
        net_net = (current_assets - total_liabilities) / shares_outstanding
        
        return round(net_net, 2) if round_result else net_net
    
    def compute_nca_details(self) -> Dict[str, Union[float, str]]:
        """
        Calculate Net Current Assets with detailed breakdown.
        
        NCA represents the company's liquid net worth after paying all liabilities.
        Graham's defensive investor test requires long-term debt < NCA.
        
        Formula: NCA = Current Assets - Total Liabilities
        Debt Coverage Ratio = Long-term Debt / NCA
        
        Returns:
            Dictionary with:
                - current_assets: float
                - total_liabilities: float
                - nca: float
                - long_term_debt: float
                - debt_coverage_ratio: Union[float, str] (or "N/A")
                - debt_coverage_pct: str ("X.XX%" or "N/A")
                - warnings: List[str]
        """
        history = self.data.get('history', {})
        if not history:
            return {
                'current_assets': "N/A",
                'total_liabilities': "N/A",
                'nca': "N/A",
                'long_term_debt': "N/A",
                'debt_coverage_ratio': "N/A",
                'debt_coverage_pct': "N/A",
                'warnings': ["No financial history available"]
            }
        
        # Get most recent fiscal year with financial data
        years = sorted(history.keys(), reverse=True)
        if not years:
            return {
                'current_assets': "N/A",
                'total_liabilities': "N/A",
                'nca': "N/A",
                'long_term_debt': "N/A",
                'debt_coverage_ratio': "N/A",
                'debt_coverage_pct': "N/A",
                'warnings': ["No financial years available"]
            }
        
        latest_year = self._get_latest_financial_year(history, years)
        if not latest_year:
            return {
                'current_assets': "N/A",
                'total_liabilities': "N/A",
                'nca': "N/A",
                'long_term_debt': "N/A",
                'debt_coverage_ratio': "N/A",
                'debt_coverage_pct': "N/A",
                'warnings': ["No financial data available"]
            }
        
        year_data = history[latest_year]
        warnings = []
        
        # Extract required fields
        current_assets = year_data.get('current_assets')
        total_liabilities = year_data.get('total_liabilities')
        long_term_debt = year_data.get('long_term_debt', 0.0)
        
        # Handle missing balance sheet data
        if current_assets is None or total_liabilities is None:
            return {
                'current_assets': "N/A",
                'total_liabilities': "N/A",
                'nca': "N/A",
                'long_term_debt': "N/A",
                'debt_coverage_ratio': "N/A",
                'debt_coverage_pct': "N/A",
                'warnings': ["Balance sheet data unavailable"]
            }
        
        # Convert to Decimal for precise calculation
        current_assets_dec = Decimal(str(current_assets))
        total_liabilities_dec = Decimal(str(total_liabilities))
        long_term_debt_dec = Decimal(str(long_term_debt))
        
        # Calculate NCA
        nca_dec = current_assets_dec - total_liabilities_dec
        
        # Check for sector-specific warnings
        sector = self.data.get('sector', '').lower()
        if 'financial' in sector or 'bank' in sector:
            warnings.append("NCA analysis may not be applicable for Financial companies due to balance sheet structure")
        elif 'utility' in sector or 'utilities' in sector:
            warnings.append("NCA analysis may not be applicable for Utility companies due to balance sheet structure")
        
        # Calculate debt coverage ratio
        debt_coverage_ratio = "N/A"
        debt_coverage_pct = "N/A"
        
        if nca_dec <= 0:
            warnings.append("NCA is zero or negative - cannot calculate debt coverage ratio")
            debt_coverage_ratio = "N/A"
            debt_coverage_pct = "N/A"
        else:
            # Calculate ratio: Long-term Debt / NCA
            ratio_dec = long_term_debt_dec / nca_dec
            debt_coverage_ratio = float(ratio_dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            
            # Format as percentage
            pct_dec = ratio_dec * 100
            debt_coverage_pct = f"{float(pct_dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))}%"
        
        # Round NCA for display
        nca_rounded = float(nca_dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        return {
            'current_assets': current_assets,
            'total_liabilities': total_liabilities,
            'nca': nca_rounded,
            'long_term_debt': long_term_debt,
            'debt_coverage_ratio': debt_coverage_ratio,
            'debt_coverage_pct': debt_coverage_pct,
            'warnings': warnings
        }
    
    def compute_quick_ratio(self) -> Union[float, str]:
        """
        Calculate Quick Ratio (Acid Test).
        
        The Quick Ratio is a more stringent liquidity test than the Current Ratio.
        It excludes inventory from current assets, as inventory may not be quickly
        convertible to cash.
        
        Formula: (Current Assets - Inventory) / Current Liabilities
        
        Returns:
            float: Quick Ratio rounded to 2 decimals, or "N/A" if cannot calculate
        """
        history = self.data.get('history', {})
        if not history:
            return "N/A"
        
        # Get most recent fiscal year with financial data
        years = sorted(history.keys(), reverse=True)
        if not years:
            return "N/A"
        
        latest_year = self._get_latest_financial_year(history, years)
        if not latest_year:
            return "N/A"
        
        year_data = history[latest_year]
        
        # Extract required fields
        current_assets = year_data.get('current_assets')
        inventory = year_data.get('inventory')
        current_liabilities = year_data.get('current_liabilities')
        
        # Handle missing current assets or current liabilities
        if current_assets is None or current_liabilities is None:
            return "N/A"
        
        # Handle zero current liabilities
        if current_liabilities == 0:
            self.warnings.append("Quick Ratio: Cannot calculate - current liabilities is zero")
            return "N/A"
        
        # Handle missing inventory based on sector
        sector = self.data.get('sector', '').lower()
        is_low_inventory_sector = 'service' in sector or 'technology' in sector or 'software' in sector
        
        if inventory is None:
            if is_low_inventory_sector:
                # Services and Technology companies typically have minimal inventory
                # Use current assets directly (equivalent to current ratio)
                self.warnings.append(f"Quick Ratio: Inventory data unavailable - using Current Assets ({self.data.get('sector', 'Unknown')} sector)")
                inventory = 0.0
            else:
                # Conservative approach: cannot calculate without inventory for other sectors
                self.warnings.append(f"Quick Ratio: Cannot calculate - inventory data unavailable for {self.data.get('sector', 'Unknown')} sector")
                return "N/A"
        
        # Convert to Decimal for precise calculation
        current_assets_dec = Decimal(str(current_assets))
        inventory_dec = Decimal(str(inventory))
        current_liabilities_dec = Decimal(str(current_liabilities))
        
        # Calculate Quick Ratio
        quick_ratio_dec = (current_assets_dec - inventory_dec) / current_liabilities_dec
        
        # Round to 2 decimal places
        quick_ratio_rounded = quick_ratio_dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Convert back to float for return
        return float(quick_ratio_rounded)
    
    def compute_three_year_avg_pe(self) -> Dict[str, Union[float, str]]:
        """
        Calculate P/E ratio based on 3-year average earnings.
        
        Graham's Defensive Criterion #6: "Price should not exceed 15 times 
        average earnings of the past three years"
        
        This method calculates the average EPS over the most recent three years,
        including loss years (negative EPS), which reduces the average and reflects
        the company's historical volatility.
        
        Returns:
            Dictionary with:
                - three_year_avg_eps: Union[float, str] - Average EPS or "N/A"
                - pe_on_avg: Union[float, str] - P/E ratio or "N/A"
                - years_used: List[str] - Years included in average
        """
        history = self.data.get('history', {})
        if not history:
            return {
                'three_year_avg_eps': "N/A",
                'pe_on_avg': "N/A",
                'years_used': []
            }
        
        # Get sorted years (most recent first)
        sorted_years = sorted(history.keys(), reverse=True)
        
        # Filter out incomplete years (years with no financial data, only dividends)
        complete_years = []
        for year in sorted_years:
            year_data = history[year]
            has_financial_data = (
                year_data.get('revenue', 0.0) > 0 or
                year_data.get('net_income', 0.0) != 0 or  # Can be negative (loss)
                year_data.get('total_equity', 0.0) > 0
            )
            if has_financial_data:
                complete_years.append(year)
        
        # Need at least 3 years of data
        if len(complete_years) < 3:
            self.warnings.append(f"Three-Year Average P/E: Insufficient data - need 3 years, have {len(complete_years)}")
            return {
                'three_year_avg_eps': "N/A",
                'pe_on_avg': "N/A",
                'years_used': complete_years
            }
        
        # Get most recent 3 years with financial data
        years_to_use = complete_years[:3]
        
        # Extract EPS for each year (including negative values for losses)
        eps_values = []
        for year in years_to_use:
            eps = history[year].get('eps', 0.0)
            eps_values.append(eps)
        
        # Convert to Decimal for precise calculation
        eps_decimals = [Decimal(str(eps)) for eps in eps_values]
        
        # Calculate average: sum(eps_values) / 3
        # Include loss years (negative EPS) per Graham's methodology
        avg_eps_dec = sum(eps_decimals) / Decimal('3')
        
        # Round average EPS to 2 decimal places
        avg_eps_rounded = avg_eps_dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        avg_eps = float(avg_eps_rounded)
        
        # Calculate P/E ratio
        price = self.data.get('price', 0.0)
        
        if avg_eps <= 0:
            # Cannot calculate meaningful P/E with zero or negative average earnings
            return {
                'three_year_avg_eps': avg_eps,
                'pe_on_avg': "N/A",
                'years_used': years_to_use
            }
        
        # Calculate P/E = Current Price / Three-Year Average EPS
        price_dec = Decimal(str(price))
        pe_ratio_dec = price_dec / avg_eps_dec
        
        # Round P/E to 2 decimal places
        pe_ratio_rounded = pe_ratio_dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        pe_ratio = float(pe_ratio_rounded)
        
        return {
            'three_year_avg_eps': avg_eps,
            'pe_on_avg': pe_ratio,
            'years_used': years_to_use
        }
    
    def compute_combined_pe_pb_test(self) -> Dict[str, Union[float, str]]:
        """
        Calculate combined P/E × P/B test.
        
        Graham's Rule: P/E × P/B should not exceed 22.5
        
        This test provides flexibility in valuation:
        - A company with P/E of 15 can have P/B up to 1.5 (15 × 1.5 = 22.5)
        - A company with P/E of 10 can have P/B up to 2.25 (10 × 2.25 = 22.5)
        - A company with P/B of 0.5 can have P/E up to 45 (45 × 0.5 = 22.5)
        
        Returns:
            Dictionary with:
                - pe_ratio: Union[float, str] - P/E ratio or "N/A"
                - pb_ratio: Union[float, str] - P/B ratio or "N/A"
                - product: Union[float, str] - P/E × P/B or "N/A"
                - result: str - "PASS", "FAIL", or "N/A"
        """
        history = self.data.get('history', {})
        price = self.data.get('price', 0.0)
        
        if not history or price == 0:
            return {
                'pe_ratio': "N/A",
                'pb_ratio': "N/A",
                'product': "N/A",
                'result': "N/A"
            }
        
        # Get sorted years (most recent first)
        sorted_years = sorted(history.keys(), reverse=True)
        if not sorted_years:
            return {
                'pe_ratio': "N/A",
                'pb_ratio': "N/A",
                'product': "N/A",
                'result': "N/A"
            }
        
        # Get most recent year with financial data
        latest_year = self._get_latest_financial_year(history, sorted_years)
        if not latest_year:
            return {
                'pe_ratio': "N/A",
                'pb_ratio': "N/A",
                'product': "N/A",
                'result': "N/A"
            }
        
        year_data = history[latest_year]
        
        # Calculate P/E ratio
        eps = year_data.get('eps', 0.0)
        if eps <= 0:
            pe_ratio = "N/A"
        else:
            price_dec = Decimal(str(price))
            eps_dec = Decimal(str(eps))
            pe_ratio_dec = price_dec / eps_dec
            pe_ratio = float(pe_ratio_dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        # Calculate P/B ratio
        total_equity = year_data.get('total_equity', 0.0)
        shares_outstanding = year_data.get('shares_outstanding', 0.0)
        
        if shares_outstanding == 0 or total_equity <= 0:
            pb_ratio = "N/A"
        else:
            total_equity_dec = Decimal(str(total_equity))
            shares_dec = Decimal(str(shares_outstanding))
            price_dec = Decimal(str(price))
            
            book_value_per_share_dec = total_equity_dec / shares_dec
            pb_ratio_dec = price_dec / book_value_per_share_dec
            pb_ratio = float(pb_ratio_dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        # Calculate product and determine result
        if pe_ratio == "N/A" or pb_ratio == "N/A":
            product = "N/A"
            result = "N/A"
        else:
            pe_dec = Decimal(str(pe_ratio))
            pb_dec = Decimal(str(pb_ratio))
            product_dec = pe_dec * pb_dec
            product = float(product_dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            
            # Compare to Graham's threshold of 22.5
            threshold = Decimal('22.5')
            result = "PASS" if product_dec <= threshold else "FAIL"
        
        return {
            'pe_ratio': pe_ratio,
            'pb_ratio': pb_ratio,
            'product': product,
            'result': result
        }
    
    def compute_margin_of_safety(self, graham_number: Union[float, str], price: float) -> Union[float, str]:
        """
        Calculate Margin of Safety.
        
        Formula: ((Graham Number - Price) / Graham Number) × 100
        
        Args:
            graham_number: Graham Number or "N/A"
            price: Current stock price
        
        Returns:
            float: Margin of Safety as percentage rounded to 1 decimal, or "N/A" if Graham Number is "N/A"
        """
        # Handle "N/A" Graham Number
        if graham_number == "N/A":
            return "N/A"
        
        # Calculate Margin of Safety
        margin_of_safety = ((graham_number - price) / graham_number) * 100
        
        return round(margin_of_safety, 1)
    
    def compute_epv_normalized(self, history: Dict[str, Dict[str, float]], 
                              round_result: bool = True) -> Union[Dict[str, any], str]:
        """
        Calculate Earnings Power Value using simplified earnings capitalization.
        
        This method uses a simplified approach inspired by Graham's emphasis on
        full-cycle earnings, but is not a direct Graham formula. It capitalizes
        the average of 7-10 years of net income at a 10% discount rate.
        
        Methodology:
        - Use 7-10 years of earnings data
        - Include ALL years (profitable and unprofitable)
        - Loss years reduce the average (they're real value destruction)
        - Only exclude truly extraordinary one-time events (not cyclical losses)
        
        Formula: Average Net Income (7-10 years) / 10%
        
        Note: This differs from both Graham's original work and Greenwald's
        modern EPV methodology. See dossier for detailed disclaimers.
        
        Args:
            history: Financial history data
            round_result: Whether to round results
            
        Returns:
            Dictionary with EPV details or "N/A" string if insufficient data
        """
        if not history:
            return "N/A - No financial history"
        
        # Get sorted years (most recent first)
        sorted_years = sorted(history.keys(), reverse=True)
        
        # Filter out incomplete years (years with no financial data, only dividends)
        # Incomplete years have revenue=0, net_income=0, total_equity=0
        complete_years = []
        for year in sorted_years:
            year_data = history[year]
            has_financial_data = (
                year_data.get('revenue', 0.0) > 0 or
                year_data.get('net_income', 0.0) != 0 or  # Can be negative (loss)
                year_data.get('total_equity', 0.0) > 0
            )
            if has_financial_data:
                complete_years.append(year)
        
        # Need at least 7 years per Graham's methodology
        if len(complete_years) < 7:
            return f"N/A - Insufficient history ({len(complete_years)} complete years, minimum 7 required)"
        
        # Use up to 10 complete years
        years_to_use = complete_years[:10]
        
        # Calculate average net income INCLUDING loss years
        net_incomes = []
        for year in years_to_use:
            net_income = history[year].get('net_income', 0.0)
            net_incomes.append(net_income)
        
        # Arithmetic mean of all years (including losses)
        normalized_earnings = sum(net_incomes) / len(net_incomes)
        
        # If average is negative, company is unprofitable over the cycle
        if normalized_earnings <= 0:
            return "N/A - Negative normalized earnings (company unprofitable over cycle)"
        
        # Calculate EPV
        epv = normalized_earnings / COST_OF_CAPITAL
        
        # Get shares for per-share calculation from most recent year with financial data
        latest_year = self._get_latest_financial_year(history, sorted_years)
        if not latest_year:
            return "N/A - No financial data available"
        
        shares = history[latest_year].get('shares_outstanding', 0)
        epv_per_share = epv / shares if shares > 0 else 0.0
        
        result = {
            'epv': round(epv, 2) if round_result else epv,
            'epv_per_share': round(epv_per_share, 2) if round_result else epv_per_share,
            'normalized_earnings': round(normalized_earnings, 2) if round_result else normalized_earnings,
            'years_used': len(years_to_use),
            'years_included': years_to_use,
            'net_incomes': [round(ni, 2) if round_result else ni for ni in net_incomes]
        }
        
        return result
    
    def compute_epv(self) -> dict:
        """
        Calculate Earnings Power Value (EPV) with detailed breakdown.
        
        This method maintains backward compatibility by wrapping compute_epv_normalized.
        
        Formula: Normalized Earnings / Cost of Capital
        Normalized Earnings = Average of last 7-10 years (including loss years)
        Cost of Capital = 10%
        
        Returns:
            dict: {
                'epv': float (enterprise value),
                'normalized_earnings': float,
                'years_used': int,
                'cost_of_capital': float,
                'epv_per_share': float
            }
        """
        history = self.data.get('history', {})
        
        # Call the new normalized method
        result = self.compute_epv_normalized(history, round_result=True)
        
        # Handle string return (N/A cases)
        if isinstance(result, str):
            return {
                'epv': 0.0,
                'normalized_earnings': 0.0,
                'years_used': 0,
                'cost_of_capital': COST_OF_CAPITAL,
                'epv_per_share': 0.0
            }
        
        # Add cost_of_capital for backward compatibility
        result['cost_of_capital'] = COST_OF_CAPITAL
        
        return result
    
    def run_investor_tests(self, investor_type: str = "defensive") -> dict:
        """
        Run Graham Investor tests based on investor type.
        
        Args:
            investor_type: "defensive" or "enterprising"
        
        Returns:
            Dictionary with test names as keys and PASS/FAIL/"N/A" as values
        """
        history = self.data.get('history', {})
        price = self.data.get('price', 0.0)
        
        if not history:
            return self._get_empty_test_results(investor_type)
        
        years = sorted(history.keys(), reverse=True)
        num_years = len(years)
        
        if investor_type == "enterprising":
            return self._run_enterprising_tests(history, years, num_years, price)
        else:
            return self._run_defensive_tests(history, years, num_years, price)
    
    def _get_empty_test_results(self, investor_type: str) -> dict:
        """Return empty test results when no history available."""
        if investor_type == "enterprising":
            return {
                'earnings_stability': 'FAIL',
                'current_ratio': 'FAIL',
                'debt_to_assets': 'FAIL',
                'dividend_record': 'FAIL',
                'earnings_growth': 'N/A - Not Required',
                'price_test': 'FAIL'
            }
        else:
            return {
                'earnings_stability': 'FAIL',
                'current_ratio': 'FAIL',
                'debt_to_assets': 'FAIL',
                'dividend_record': 'FAIL',
                'earnings_growth': 'FAIL',
                'pe_ratio': 'FAIL',
                'pb_ratio': 'FAIL'
            }
    
    def _run_defensive_tests(self, history: dict, years: list, num_years: int, price: float) -> dict:
        """Run all 7 Graham Defensive Investor tests."""
        # Test 1: Earnings stability - positive earnings in ALL of last 10 years (strict Graham)
        earnings_stability = self._test_earnings_stability(history, years, min_years=DEFENSIVE.MIN_EARNINGS_YEARS, period=10)
        
        # Test 2: Current ratio >= 2.0
        current_ratio_test = self._test_current_ratio(history, years, min_ratio=DEFENSIVE.MIN_CURRENT_RATIO)
        
        # Test 3: Long-term debt < net current assets
        debt_test = self._test_debt_to_assets(history, years)
        
        # Test 4: Dividend record
        dividend_test = self._test_dividend_record(history, years, num_years)
        
        # Test 5: Earnings growth >= 33% over 10 years
        earnings_growth_test = self._test_earnings_growth(history, years, num_years)
        
        # Test 6: P/E ratio < 15
        pe_test = self._test_pe_ratio(history, years, price, max_pe=DEFENSIVE.MAX_PE_RATIO)
        
        # Test 7: P/B ratio < 1.5
        pb_test = self._test_pb_ratio(history, years, price, max_pb=DEFENSIVE.MAX_PB_RATIO)
        
        return {
            'earnings_stability': earnings_stability,
            'current_ratio': current_ratio_test,
            'debt_to_assets': debt_test,
            'dividend_record': dividend_test,
            'earnings_growth': earnings_growth_test,
            'pe_ratio': pe_test,
            'pb_ratio': pb_test
        }
    
    def _run_enterprising_tests(self, history: dict, years: list, num_years: int, price: float) -> dict:
        """Run Graham Enterprising Investor tests."""
        # Test 1: Earnings stability - positive earnings for last 5 years
        earnings_stability = self._test_earnings_stability(history, years, min_years=ENTERPRISING.MIN_EARNINGS_YEARS, period=5)
        
        # Test 2: Current ratio > 1.5
        current_ratio_test = self._test_current_ratio(history, years, min_ratio=ENTERPRISING.MIN_CURRENT_RATIO)
        
        # Test 3: Debt < 110% of Net Current Assets
        debt_test = self._test_enterprising_debt(history, years)
        
        # Test 4: Currently pays a dividend (last year > 0)
        dividend_test = self._test_current_dividend(history, years)
        
        # Test 5: Earnings growth - not required for enterprising
        earnings_growth_test = 'N/A - Not Required'
        
        # Test 6: Price test - P/E < 10 OR Price < 120% of Net Tangible Assets
        price_test = self._test_enterprising_price(history, years, price)
        
        return {
            'earnings_stability': earnings_stability,
            'current_ratio': current_ratio_test,
            'debt_to_assets': debt_test,
            'dividend_record': dividend_test,
            'earnings_growth': earnings_growth_test,
            'price_test': price_test
        }
    
    # Keep old method name for backward compatibility
    def run_defensive_tests(self) -> dict:
        """
        Run all 7 Graham Defensive Investor tests.
        
        Returns:
            Dictionary with test names as keys and PASS/FAIL/"N/A (Too Young)" as values
        """
        return self.run_investor_tests("defensive")
    
    def _test_earnings_stability(self, history: dict, years: list, min_years: int = 8, period: int = 10) -> str:
        """
        Test if company has positive earnings in required number of years.
        
        Graham's Earnings Stability Criteria:
        - Defensive Investor: Positive earnings in each of the past 10 years
        - Enterprising Investor: Profitability in most recent year and 5 of past 7 years
        
        Filters out incomplete years (years with only dividend data but no financial statements)
        to ensure accurate testing. This is consistent with other test methods that use
        _get_latest_financial_year() to skip incomplete years.
        
        Args:
            history: Financial history dictionary
            years: List of years sorted in reverse chronological order
            min_years: Minimum number of years with positive earnings required
                      (10 for defensive, 5 for enterprising)
            period: Number of years to examine
                   (10 for defensive, 7 for enterprising)
            
        Returns:
            'PASS' if positive_years >= min_years, 'FAIL' otherwise
        """
        # Filter out incomplete years (years with no financial data, only dividends)
        # An incomplete year has revenue=0, net_income=0, and total_equity=0
        complete_years = []
        for year in years:
            year_data = history[year]
            has_financial_data = (
                year_data.get('revenue', 0.0) > 0 or
                year_data.get('net_income', 0.0) != 0 or  # Can be negative (loss)
                year_data.get('total_equity', 0.0) > 0
            )
            if has_financial_data:
                complete_years.append(year)
        
        # Take required period from complete years only
        test_years = complete_years[:period]
        
        # Need enough complete years to test
        if len(test_years) < min_years:
            return 'FAIL'
        
        positive_years = 0
        for year in test_years:
            net_income = history[year].get('net_income', 0.0)
            if net_income > 0:
                positive_years += 1
        
        return 'PASS' if positive_years >= min_years else 'FAIL'
    
    def _test_current_ratio(self, history: dict, years: list, min_ratio: float = 2.0) -> str:
        """Test if current ratio meets minimum threshold."""
        if not years:
            return 'FAIL'
        
        # Find most recent year with actual financial data (not just dividend data)
        latest_year = None
        for year in years:
            if history[year].get('current_assets', 0.0) > 0 or history[year].get('total_equity', 0.0) > 0:
                latest_year = year
                break
        
        if not latest_year:
            return 'FAIL'
        
        current_assets = history[latest_year].get('current_assets', 0.0)
        current_liabilities = history[latest_year].get('current_liabilities', 0.0)
        
        if current_liabilities == 0:
            return 'FAIL'
        
        current_ratio = current_assets / current_liabilities
        return 'PASS' if current_ratio >= min_ratio else 'FAIL'
    
    def _test_debt_to_assets(self, history: dict, years: list) -> str:
        """Test if long-term debt < net current assets."""
        if not years:
            return 'FAIL'
        
        latest_year = self._get_latest_financial_year(history, years)
        if not latest_year:
            return 'FAIL'
        
        long_term_debt = history[latest_year].get('long_term_debt', 0.0)
        current_assets = history[latest_year].get('current_assets', 0.0)
        current_liabilities = history[latest_year].get('current_liabilities', 0.0)
        
        net_current_assets = current_assets - current_liabilities
        return 'PASS' if long_term_debt < net_current_assets else 'FAIL'
    
    def _test_dividend_record(self, history: dict, years: list, num_years: int) -> str:
        """Test if there is an uninterrupted dividend record."""
        # If < 20 years, test entire history; if >= 20 years, test last 20
        years_to_check = min(num_years, 20)
        years_subset = years[:years_to_check]
        
        for year in years_subset:
            dividend = history[year].get('dividend', 0.0)
            if dividend <= 0:
                return 'FAIL'
        
        return 'PASS'
    
    def _test_earnings_growth(self, history: dict, years: list, num_years: int) -> str:
        """Test if earnings have grown by >= 33% over 10 years."""
        # If < 10 years, mark as "N/A (Too Young)"
        if num_years < 10:
            return 'N/A (Too Young)'
        
        # Get earnings from 10 years ago and most recent with financial data
        # Find the most recent year with financial data
        latest_year = self._get_latest_financial_year(history, years)
        if not latest_year:
            return 'FAIL'
        
        # Find the index of the latest financial year
        latest_index = years.index(latest_year)
        
        # Get the year 10 years before the latest financial year
        # (not just years[9] which might include dividend-only years)
        financial_years = [y for y in years if self._get_latest_financial_year(history, [y])]
        if len(financial_years) < 10:
            return 'N/A (Too Young)'
        
        oldest_year = financial_years[9]  # 10th financial year
        
        old_earnings = history[oldest_year].get('net_income', 0.0)
        recent_earnings = history[latest_year].get('net_income', 0.0)
        
        if old_earnings <= 0:
            return 'FAIL'
        
        growth_ratio = recent_earnings / old_earnings
        return 'PASS' if growth_ratio >= DEFENSIVE.MIN_EARNINGS_GROWTH else 'FAIL'
    
    def _test_pe_ratio(self, history: dict, years: list, price: float, max_pe: float = 15) -> str:
        """Test if P/E ratio is below maximum threshold."""
        if not years or price == 0:
            return 'FAIL'
        
        latest_year = self._get_latest_financial_year(history, years)
        if not latest_year:
            return 'FAIL'
        
        eps = history[latest_year].get('eps', 0.0)
        
        if eps <= 0:
            return 'FAIL'
        
        pe_ratio = price / eps
        return 'PASS' if pe_ratio < max_pe else 'FAIL'
    
    def _test_pb_ratio(self, history: dict, years: list, price: float, max_pb: float = 1.5) -> str:
        """Test if P/B ratio is below maximum threshold."""
        if not years or price == 0:
            return 'FAIL'
        
        latest_year = self._get_latest_financial_year(history, years)
        if not latest_year:
            return 'FAIL'
        
        total_equity = history[latest_year].get('total_equity', 0.0)
        shares_outstanding = history[latest_year].get('shares_outstanding', 0.0)
        
        if shares_outstanding == 0 or total_equity <= 0:
            return 'FAIL'
        
        book_value_per_share = total_equity / shares_outstanding
        pb_ratio = price / book_value_per_share
        return 'PASS' if pb_ratio < max_pb else 'FAIL'
    
    def _test_enterprising_debt(self, history: dict, years: list) -> str:
        """Test if debt < 110% of Net Current Assets (Enterprising)."""
        if not years:
            return 'FAIL'
        
        latest_year = self._get_latest_financial_year(history, years)
        if not latest_year:
            return 'FAIL'
        
        long_term_debt = history[latest_year].get('long_term_debt', 0.0)
        current_assets = history[latest_year].get('current_assets', 0.0)
        current_liabilities = history[latest_year].get('current_liabilities', 0.0)
        
        net_current_assets = current_assets - current_liabilities
        max_allowed_debt = net_current_assets * ENTERPRISING.MAX_DEBT_ASSETS
        
        return 'PASS' if long_term_debt < max_allowed_debt else 'FAIL'
    
    def _test_current_dividend(self, history: dict, years: list) -> str:
        """Test if company currently pays a dividend (last year > 0)."""
        if not years:
            return 'FAIL'
        
        latest_year = self._get_latest_financial_year(history, years)
        if not latest_year:
            return 'FAIL'
        
        dividend = history[latest_year].get('dividend', 0.0)
        
        return 'PASS' if dividend > 0 else 'FAIL'
    
    def _test_enterprising_price(self, history: dict, years: list, price: float) -> str:
        """Test if P/E < 10 OR Price < 120% of Net Tangible Assets."""
        if not years or price == 0:
            return 'FAIL'
        
        latest_year = self._get_latest_financial_year(history, years)
        if not latest_year:
            return 'FAIL'
        
        # Test 1: P/E < 10
        eps = history[latest_year].get('eps', 0.0)
        if eps > 0:
            pe_ratio = price / eps
            if pe_ratio < ENTERPRISING.MAX_PE_RATIO:
                return 'PASS'
        
        # Test 2: Price < 120% of Tangible Book Value (not Net-Net)
        # Graham's standard rule: buy at discount to book value
        tbvps = self.compute_tbvps(round_result=False)
        if isinstance(tbvps, float) and tbvps > 0:
            max_price = tbvps * 1.20
            if price < max_price:
                return 'PASS'
        
        return 'FAIL'
    
    def compute_all(self) -> dict:
        """
        Compute all Graham metrics.
        
        Returns:
            Dictionary containing all calculated metrics and test results
        """
        # Calculate all metrics
        graham_number = self.compute_graham_number()
        net_net_value = self.compute_net_net()  # Rounded for display
        net_net_value_raw = self.compute_net_net(round_result=False)  # Unrounded for comparison
        epv_data = self.compute_epv()  # Now returns dict
        nca_details = self.compute_nca_details()
        quick_ratio = self.compute_quick_ratio()
        three_year_avg_pe = self.compute_three_year_avg_pe()
        combined_pe_pb_test = self.compute_combined_pe_pb_test()
        
        price = self.data.get('price', 0.0)
        margin_of_safety = self.compute_margin_of_safety(graham_number, price)
        
        # Check for deep value opportunity (use unrounded value for accurate comparison)
        # Use a small tolerance to avoid flagging when price and net-net are approximately equal
        # Only flag if price is meaningfully below net-net (more than 2% difference)
        if isinstance(net_net_value_raw, float) and price > 0:
            # Calculate percentage difference: (net_net - price) / net_net * 100
            pct_below = ((net_net_value_raw - price) / net_net_value_raw * 100) if net_net_value_raw > 0 else 0
            if pct_below > 2.0:  # Price is more than 2% below net-net
                self.warnings.append("DEEP VALUE OPPORTUNITY - Price below Net-Net Value")
        
        # Run both defensive and enterprising tests
        defensive_tests = self.run_investor_tests("defensive")
        enterprising_tests = self.run_investor_tests("enterprising")
        
        # Determine verdict (pass EPV value for backward compatibility)
        verdict = self._determine_verdict(graham_number, margin_of_safety, epv_data['epv'], 
                                         defensive_tests, enterprising_tests)
        
        metrics = {
            'graham_number': graham_number,
            'epv': epv_data['epv'],  # Keep backward compatibility
            'epv_details': epv_data,  # Add detailed breakdown
            'net_net_value': net_net_value,
            'margin_of_safety': margin_of_safety,
            'nca_details': nca_details,
            'quick_ratio': quick_ratio,
            'three_year_avg_pe': three_year_avg_pe,
            'combined_pe_pb_test': combined_pe_pb_test,
            'verdict': verdict,
            'defensive_tests': defensive_tests,
            'enterprising_tests': enterprising_tests,
            'warnings': self.warnings.copy()
        }
        
        return metrics
    
    def _determine_verdict(self, graham_number: Union[float, str], 
                          margin_of_safety: Union[float, str], 
                          epv: float,
                          defensive_tests: dict = None,
                          enterprising_tests: dict = None) -> str:
        """
        Determine investment verdict based on metrics.
        
        Args:
            graham_number: Graham Number or "N/A"
            margin_of_safety: Margin of Safety or "N/A"
            epv: Earnings Power Value
            defensive_tests: Results from defensive investor tests
            enterprising_tests: Results from enterprising investor tests
        
        Returns:
            Verdict string
        """
        # Handle negative equity case
        if graham_number == "N/A":
            return "Rely on EPV - Negative Equity"
        
        # Check if passes enterprising tests (if defensive fails)
        if defensive_tests and enterprising_tests:
            defensive_pass = all(v == 'PASS' or 'N/A' in str(v) for v in defensive_tests.values())
            enterprising_pass = all(v == 'PASS' or 'N/A' in str(v) for v in enterprising_tests.values())
            
            if not defensive_pass and enterprising_pass:
                return "ENTERPRISING BUY"
        
        # Handle positive margin of safety with tiers
        if isinstance(margin_of_safety, float):
            if margin_of_safety >= 20:
                return "STRONG BUY (Undervalued)"
            elif margin_of_safety > 0:
                return "UNDERVALUED"
            else:
                return "OVERVALUED"
        
        return "PENDING"
