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

from core.models import FinancialData, GrahamResult, or_default
from core.formulas import graham_number, margin_of_safety_pct, net_current_asset_value, tangible_equity
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional, Union

from config.graham_constants import GRAHAM_MULTIPLIER, COST_OF_CAPITAL
from core.history import fiscal_year, has_statement_data, has_statement_or_current_assets, row_at
from core.investor_tests import defensive, enterprising
from core.investor_tests.criteria import latest_current_ratio
from core.verdict import determine_verdict
from config.valuation_config import (DEEP_VALUE_MIN_DISCOUNT_PCT, EPV_MAX_YEARS, EPV_MIN_YEARS,
                                     NORMALIZED_EPS_YEARS)


# Default for "not precomputed by compute_all" (None and "N/A" are real results)
_UNSET = object()

# compute_epv_normalized's reason when average earnings over the cycle are not positive: a real
# finding (no earning power, EPV 0), unlike missing data (EPV "N/A")
NEGATIVE_EARNINGS_REASON = "N/A - Negative normalized earnings (company unprofitable over cycle)"


class GrahamCalculator:
    """
    Performs all Graham methodology calculations with strict formulas.
    
    Handles edge cases gracefully:
    - Negative equity (TBVPS < 0)
    - Negative earnings (EPS < 0)
    - Young companies (< 10 years history)
    - Missing data
    """
    
    def __init__(self, financial_data: Union[FinancialData, dict]):
        """
        Initialize calculator with financial data.
        
        Args:
            financial_data: FinancialData (or its dict form): ticker, price, currency, history, etc.
        """
        self.data = FinancialData.from_dict(financial_data)
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
            has_financial_data = has_statement_or_current_assets(year_data)
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
        history = or_default(self.data.history, {})
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
        total_equity = or_default(year_data.total_equity, 0.0)
        intangible_assets = or_default(year_data.intangible_assets, 0.0)
        goodwill = or_default(year_data.goodwill, 0.0)
        shares_outstanding = or_default(year_data.shares_outstanding, 0.0)
        
        # Validate shares outstanding
        if shares_outstanding == 0:
            return "N/A"
        
        # Calculate TBVPS - use absolute values to handle negative reporting
        preferred_stock = or_default(year_data.preferred_stock, 0.0)
        tbvps = tangible_equity(total_equity, intangible_assets, goodwill, preferred_stock) / shares_outstanding
        
        # Handle negative TBVPS
        if tbvps < 0:
            self.warnings.append("Negative Tangible Book Value - Company has negative equity")
            return "N/A"
        
        return round(tbvps, 2) if round_result else tbvps
    
    def compute_graham_number(self, tbvps=_UNSET) -> Union[float, str]:
        """
        Calculate Graham Number (intrinsic value estimate).
        
        Formula: sqrt(22.5 × EPS × TBVPS)
        
        Args:
            tbvps: Unrounded TBVPS already computed by compute_all (computed here if omitted)
        
        Returns:
            float: Graham Number rounded to 2 decimals, or "N/A" if invalid inputs
        """
        # Get TBVPS (unrounded for calculation accuracy)
        if tbvps is _UNSET:
            tbvps = self.compute_tbvps(round_result=False)
        if tbvps == "N/A":
            return "N/A"
        
        # Get most recent EPS from year with financial data
        history = or_default(self.data.history, {})
        if not history:
            return "N/A"
        
        years = sorted(history.keys(), reverse=True)
        if not years:
            return "N/A"
        
        latest_year = self._get_latest_financial_year(history, years)
        if not latest_year:
            return "N/A"
        
        eps = or_default(history[latest_year].eps, 0.0)
        
        # Handle negative EPS
        if eps <= 0:
            return "N/A"
        
        return round(graham_number(eps, tbvps), 2)
    
    def compute_normalized_graham_number(self, round_result: bool = True, tbvps=_UNSET) -> Union[float, str]:
        """
        Calculate normalized Graham Number using 3-year average EPS.
        
        This method uses 3-year average EPS instead of single-year EPS to smooth
        cyclical volatility and prevent "bull traps" where one peak year makes
        a cyclical company appear undervalued.
        
        Formula: √(22.5 × EPS_3yr_avg × TBVPS)
        
        Args:
            round_result: If True, round to 2 decimals. If False, return raw value.
            tbvps: Unrounded TBVPS already computed by compute_all (computed here if omitted)
        
        Returns:
            float: Normalized Graham Number rounded to 2 decimals
            str: "N/A" if insufficient data or negative average EPS
        """
        from core.financial_data_processor import FinancialDataProcessor
        
        # Get TBVPS (unrounded for calculation accuracy)
        if tbvps is _UNSET:
            tbvps = self.compute_tbvps(round_result=False)
        if tbvps == "N/A":
            return "N/A"
        
        # Get financial history
        history = or_default(self.data.history, {})
        if not history:
            self.warnings.append("Normalized Graham Number: No financial history available")
            return "N/A"
        
        # Extract 3-year EPS data
        eps_data = FinancialDataProcessor.extract_3year_eps_data(history)
        
        # Check if extraction was successful
        if not eps_data['valid']:
            # Add warning from extraction
            if eps_data['warning']:
                self.warnings.append(f"Normalized Graham Number: {eps_data['warning']}")
            return "N/A"
        
        # Calculate arithmetic mean of 3-year EPS
        eps_values = eps_data['eps_values']
        eps_3yr_avg = sum(eps_values) / NORMALIZED_EPS_YEARS
        
        # Store individual EPS values and years for audit trail
        self.eps_3year_values = eps_values
        self.eps_3year_years = eps_data['years']
        self.eps_3year_avg = eps_3yr_avg
        
        # Handle negative or zero average EPS
        if eps_3yr_avg <= 0:
            self.warnings.append(f"Negative 3-year average EPS ({eps_3yr_avg:.2f}) - Company unsuitable for Graham methodology")
            return "N/A"
        
        # Calculate normalized Graham Number
        normalized_graham_number = graham_number(eps_3yr_avg, tbvps)
        
        return round(normalized_graham_number, 2) if round_result else normalized_graham_number
    
    def _net_net_yearly_fall(self, history: dict, latest_year: Optional[str], net_net_value) -> Optional[float]:
        """
        How far NCAV per share fell from the year before (negative when it rose), or None when not comparable. Per
        share, because a buyback at a price above NCAV is no loss to the holder (Keros 2025: current assets 589M to
        315M after a tender offer, NCAV per share higher). Graham compares balance sheets to see whether current
        assets are being lost (GRAHAM_METHODOLOGY §3.7).
        """
        if latest_year is None or not isinstance(net_net_value, float):
            return None
        for year in sorted((y for y in history if y < latest_year), reverse=True):
            row = row_at(history, year)
            current_assets, liabilities = or_default(row.current_assets, None), or_default(row.total_liabilities, None)
            shares = or_default(row.shares_outstanding, 0.0)
            if current_assets and liabilities is not None and shares:
                earlier = net_current_asset_value(current_assets, liabilities, or_default(row.claims_outside_equity, 0.0),
                                                  or_default(row.preferred_stock, 0.0)) / shares
                return earlier - net_net_value
        return None

    def compute_net_net(self, round_result: bool = True) -> Union[float, str]:
        """
        Calculate Net-Net Working Capital Value.
        
        Formula: (Current Assets - Total Liabilities) / Shares Outstanding
        
        Args:
            round_result: If True, round to 2 decimals. If False, return raw value.
        
        Returns:
            float: Net-Net Value rounded to 2 decimals, or "N/A" if data unavailable
        """
        history = or_default(self.data.history, {})
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
        current_assets = or_default(year_data.current_assets, None)
        total_liabilities = or_default(year_data.total_liabilities, None)
        shares_outstanding = or_default(year_data.shares_outstanding, 0.0)
        
        # Handle missing data
        if current_assets is None or total_liabilities is None:
            return "N/A"
        
        # Validate shares outstanding
        if shares_outstanding == 0:
            return "N/A"
        
        # Calculate Net-Net Value
        claims_outside_equity = or_default(year_data.claims_outside_equity, 0.0)
        net_net = net_current_asset_value(current_assets, total_liabilities, claims_outside_equity,
                                          or_default(year_data.preferred_stock, 0.0)) / shares_outstanding
        
        return round(net_net, 2) if round_result else net_net
    
    def compute_nca_details(self) -> Dict[str, Union[float, str]]:
        """
        Net current assets (working capital) and the debt coverage of defensive criterion 4.2:
        long-term debt "should not exceed the net current assets (or working capital)"
        (GRAHAM_METHODOLOGY §4.2). The same figures as the investor test, for display.
        Not the net-net value (current assets minus all liabilities), which is compute_net_net.
        
        Formula: NCA = Current Assets - Current Liabilities
        Debt Coverage Ratio = Long-term Debt / NCA (Graham: at most 1.0)
        
        Returns:
            Dictionary with current_assets, current_liabilities, nca, long_term_debt,
            debt_coverage_ratio (float rounded to 2dp or "N/A"), debt_coverage_pct ("X.XX%" or
            "N/A") and warnings
        """
        def unavailable(reason):
            return {'current_assets': "N/A", 'current_liabilities': "N/A", 'nca': "N/A",
                    'long_term_debt': "N/A", 'debt_coverage_ratio': "N/A", 'debt_coverage_pct': "N/A",
                    'warnings': [reason]}
        
        history = or_default(self.data.history, {})
        if not history:
            return unavailable("No financial history available")
        latest_year = self._get_latest_financial_year(history, sorted(history.keys(), reverse=True))
        if not latest_year:
            return unavailable("No financial data available")
        
        year_data = history[latest_year]
        current_assets = or_default(year_data.current_assets, None)
        current_liabilities = or_default(year_data.current_liabilities, None)
        long_term_debt = or_default(year_data.long_term_debt, 0.0)
        if current_assets is None or current_liabilities is None:
            return unavailable("Balance sheet data unavailable")
        
        warnings = []
        sector = (or_default(self.data.sector, None) or '').lower()
        if 'financial' in sector or 'bank' in sector:
            warnings.append("NCA analysis may not be applicable for Financial companies due to balance sheet structure")
        
        nca = current_assets - current_liabilities
        if nca <= 0:
            warnings.append("NCA is zero or negative - cannot calculate debt coverage ratio")
            debt_coverage_ratio, debt_coverage_pct = "N/A", "N/A"
        else:
            ratio = long_term_debt / nca
            debt_coverage_ratio = round(ratio, 2)
            debt_coverage_pct = f"{round(ratio * 100, 2)}%"
        
        return {
            'current_assets': current_assets,
            'current_liabilities': current_liabilities,
            'nca': round(nca, 2),
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
        history = or_default(self.data.history, {})
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
        current_assets = or_default(year_data.current_assets, None)
        inventory = or_default(year_data.inventory, None)
        current_liabilities = or_default(year_data.current_liabilities, None)
        
        # Handle missing current assets or current liabilities
        if current_assets is None or current_liabilities is None:
            return "N/A"
        
        # Handle zero current liabilities
        if current_liabilities == 0:
            self.warnings.append("Quick Ratio: Cannot calculate - current liabilities is zero")
            return "N/A"
        
        # Inventory not reported: N/A, never imputed from the sector (GRAHAM_METHODOLOGY §8.4).
        # A reported 0 is a real value (no inventory)
        if inventory is None:
            self.warnings.append("Quick Ratio: Cannot calculate - inventory not reported in the annual balance sheet")
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
        history = or_default(self.data.history, {})
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
            has_financial_data = has_statement_data(year_data)
            if has_financial_data:
                complete_years.append(year)
        
        # Need at least 3 years of data
        if len(complete_years) < NORMALIZED_EPS_YEARS:
            self.warnings.append(f"Three-Year Average P/E: Insufficient data - need {NORMALIZED_EPS_YEARS} years, have {len(complete_years)}")
            return {
                'three_year_avg_eps': "N/A",
                'pe_on_avg': "N/A",
                'years_used': complete_years
            }
        
        # Get most recent 3 years with financial data
        years_to_use = complete_years[:NORMALIZED_EPS_YEARS]
        
        # Extract EPS for each year (including negative values for losses)
        eps_values = []
        for year in years_to_use:
            eps = or_default(history[year].eps, 0.0)
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
        price = or_default(self.data.price, 0.0)
        
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
        The multiples behind defensive criterion 4.7, as tested: P/E on the three-year average
        EPS, P/B on tangible book value, and their product against 22.5
        (investor_tests.defensive.pe_pb_multiples; GRAHAM_METHODOLOGY §4.7).
        
        Returns:
            Dictionary with:
                - pe_ratio: Union[float, str] - P/E (three-year average EPS) or "N/A"
                - pb_ratio: Union[float, str] - P/B (tangible book) or "N/A"
                - product: Union[float, str] - P/E × P/B or "N/A"
                - result: str - "PASS" (product ≤ 22.5), "FAIL", or "N/A"
        """
        history = or_default(self.data.history, {})
        price = or_default(self.data.price, 0.0)
        multiples = defensive.pe_pb_multiples(history, sorted(history.keys(), reverse=True), price)
        
        def shown(value):
            return round(value, 2) if value is not None else "N/A"
        
        product = multiples['product']
        return {
            'pe_ratio': shown(multiples['pe']),
            'pb_ratio': shown(multiples['pb']),
            'product': shown(product),
            'result': "N/A" if product is None else ("PASS" if product <= GRAHAM_MULTIPLIER else "FAIL"),
        }
    
    def compute_margin_of_safety(self, current_price: float, normalized_gn=_UNSET,
                                 epv_data=_UNSET) -> Dict[str, Union[float, str]]:
        """
        Calculate Margin of Safety using conservative dual-anchor approach.
        
        This method uses the lower of normalized Graham Number and EPV per share
        as the intrinsic value, following Graham's conservative principles.
        
        Formula: ((intrinsic_value - current_price) / intrinsic_value) × 100
        
        Args:
            current_price: Current stock price
            normalized_gn: Rounded normalized Graham Number from compute_all (computed if omitted)
            epv_data: compute_epv() result from compute_all (computed if omitted)
        
        Returns:
            dict: {
                'mos_percentage': float or "N/A" - Margin of Safety percentage
                'intrinsic_value_used': float or "N/A" - The intrinsic value used
                'limiting_factor': str - Which metric was lower ("Normalized Graham Number", "EPV", or "N/A")
                'normalized_graham_number': float or "N/A" - Normalized Graham Number value
                'epv_per_share': float or "N/A" - EPV per share value
            }
        """
        # Normalized Graham Number and EPV, unless compute_all already has them
        if normalized_gn is _UNSET:
            normalized_gn = self.compute_normalized_graham_number()
        if epv_data is _UNSET:
            epv_data = self.compute_epv()
        epv_per_share = epv_data.get('epv_per_share', 0.0)
        
        # Determine which values are valid
        # CRITICAL: Distinguish EPV = 0.00 (valid value destroyer) from EPV = "N/A" (missing data)
        normalized_gn_valid = isinstance(normalized_gn, (int, float))
        epv_valid = isinstance(epv_per_share, (int, float))
        
        # Determine intrinsic value and limiting factor
        intrinsic_value = "N/A"
        limiting_factor = "N/A"
        
        if normalized_gn_valid and epv_valid:
            # Both are numeric (including EPV = 0.00) - use the lower value
            intrinsic_value = min(normalized_gn, epv_per_share)
            if intrinsic_value == normalized_gn:
                limiting_factor = "Normalized Graham Number"
            else:
                limiting_factor = "EPV"
        elif normalized_gn_valid:
            # Only normalized Graham Number is valid
            intrinsic_value = normalized_gn
            limiting_factor = "Normalized Graham Number"
        elif epv_valid:
            # Only EPV is valid (including 0.00)
            intrinsic_value = epv_per_share
            limiting_factor = "EPV"
        else:
            # Both are "N/A"
            self.warnings.append("Unable to calculate Margin of Safety: Both normalized Graham Number and EPV are unavailable")
        
        # Calculate Margin of Safety
        mos_percentage = "N/A"
        
        if intrinsic_value != "N/A":
            # Special case: intrinsic_value = 0.00 (cannot divide by zero)
            if intrinsic_value == 0.00:
                mos_percentage = "N/A"
            else:
                mos_percentage = round(margin_of_safety_pct(intrinsic_value, current_price), 1)
        
        # Why the margin of safety is limited or missing, for the dossier
        epv_reason = epv_data.get('unavailable_reason')
        if intrinsic_value == "N/A":
            note = "normalized Graham Number and EPV both unavailable"
        elif intrinsic_value == 0.00:
            note = f"no earning power: {epv_reason}" if epv_reason else "intrinsic value is zero"
        elif not epv_valid and epv_reason:
            note = f"EPV unavailable: {epv_reason}"
        else:
            note = None
        
        return {
            'mos_percentage': mos_percentage,
            'intrinsic_value_used': intrinsic_value,
            'limiting_factor': limiting_factor,
            'normalized_graham_number': normalized_gn,
            'epv_per_share': epv_per_share,
            'note': note,
        }
    
    def compute_epv_normalized(self, history: Dict[str, Dict[str, float]], 
                              round_result: bool = True) -> Union[Dict[str, any], str]:
        """
        Calculate Earnings Power Value using simplified earnings capitalization.
        
        This method uses a simplified approach inspired by Graham's emphasis on
        full-cycle earnings, but is not a direct Graham formula. It capitalizes
        the average of 7-10 years of net income at a 10% discount rate. Per share it
        capitalizes the average of the same years' EPS (each year's earnings over that year's
        shares, GRAHAM_METHODOLOGY §2.4), not the company value over today's shares (F22).
        
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
            has_financial_data = has_statement_data(year_data)
            if has_financial_data:
                complete_years.append(year)
        
        # Need at least 7 years per Graham's methodology
        if len(complete_years) < EPV_MIN_YEARS:
            return f"N/A - Insufficient history ({len(complete_years)} complete years, minimum {EPV_MIN_YEARS} required)"
        
        # Use up to 10 complete years
        years_to_use = complete_years[:EPV_MAX_YEARS]
        
        # Calculate average net income INCLUDING loss years
        net_incomes = []
        for year in years_to_use:
            net_income = or_default(row_at(history, year).net_income, 0.0)
            net_incomes.append(net_income)
        
        # Arithmetic mean of all years (including losses)
        normalized_earnings = sum(net_incomes) / len(net_incomes)
        
        # If average is negative, company is unprofitable over the cycle
        if normalized_earnings <= 0:
            return NEGATIVE_EARNINGS_REASON
        
        # Calculate EPV
        epv = normalized_earnings / COST_OF_CAPITAL
        
        # Per share: average of each year's EPS (reported, else that year's net income / that
        # year's shares). A year whose EPS is 0 despite non-zero earnings had no share count.
        eps_values = []
        for year, net_income in zip(years_to_use, net_incomes):
            eps = or_default(row_at(history, year).eps, None)
            eps_values.append(None if eps is None or (eps == 0 and net_income != 0) else float(eps))
        missing = [fiscal_year(year) for year, eps in zip(years_to_use, eps_values) if eps is None]
        per_share_reason = None
        if missing:
            normalized_eps = epv_per_share = "N/A"
            per_share_reason = f"no per-share earnings for FY{', FY'.join(missing)}"
        else:
            normalized_eps = sum(eps_values) / len(eps_values)
            # share changes can turn a positive company average negative per share: no earning power
            epv_per_share = max(normalized_eps, 0.0) / COST_OF_CAPITAL

        def rounded(value):
            return round(value, 2) if round_result and isinstance(value, float) else value

        result = {
            'epv': rounded(epv),
            'epv_per_share': rounded(epv_per_share),
            'normalized_earnings': rounded(normalized_earnings),
            'normalized_eps': round(normalized_eps, 4) if round_result and isinstance(normalized_eps, float)
                              else normalized_eps,
            'eps_values': eps_values,
            'years_used': len(years_to_use),
            'years_included': years_to_use,
            'net_incomes': [round(ni, 2) if round_result else ni for ni in net_incomes]
        }
        if per_share_reason:
            result['epv_per_share_reason'] = per_share_reason
        
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
        history = or_default(self.data.history, {})
        
        # Call the new normalized method
        result = self.compute_epv_normalized(history, round_result=True)
        
        # Unavailable (too little history, no data): "N/A", never 0, so the margin of safety
        # falls back to the normalized Graham Number (F3). Negative average earnings over the
        # cycle are a real finding: no earning power, EPV 0 (GRAHAM_METHODOLOGY §2.1-2.3)
        if isinstance(result, str):
            value = 0.0 if result == NEGATIVE_EARNINGS_REASON else "N/A"
            return {
                'epv': value,
                'normalized_earnings': "N/A",
                'years_used': 0,
                'cost_of_capital': COST_OF_CAPITAL,
                'epv_per_share': value,
                'unavailable_reason': result.removeprefix("N/A - "),
            }
        
        # Add cost_of_capital for backward compatibility
        result['cost_of_capital'] = COST_OF_CAPITAL
        
        return result
    
    def run_investor_tests(self, investor_type: str = "defensive", tbvps=_UNSET) -> dict:
        """
        Run Graham Investor tests based on investor type.
        
        Args:
            investor_type: "defensive" or "enterprising"
            tbvps: Unrounded TBVPS from compute_all, for the enterprising price test
        
        Returns:
            Dictionary with test names as keys and PASS/FAIL/"N/A" as values
        """
        history = or_default(self.data.history, {})
        price = or_default(self.data.price, 0.0)
        
        if not history:
            return dict(enterprising.EMPTY_RESULTS if investor_type == "enterprising" else defensive.EMPTY_RESULTS)
        
        years = sorted(history.keys(), reverse=True)
        num_years = len(years)
        
        if investor_type == "enterprising":
            if tbvps is _UNSET:
                tbvps = self.compute_tbvps(round_result=False)
            return enterprising.run_enterprising_tests(history, years, num_years, price, tbvps)
        return defensive.run_defensive_tests(history, years, num_years, price, or_default(self.data.industry, None))
    
    # Keep old method name for backward compatibility
    def run_defensive_tests(self) -> dict:
        """
        Run all 7 Graham Defensive Investor tests.
        
        Returns:
            Dictionary with test names as keys and PASS/FAIL/"N/A (Too Young)" as values
        """
        return self.run_investor_tests("defensive")
    
    def compute_current_ratio(self) -> dict:
        """
        Current ratio for display (GRAHAM_METHODOLOGY §4.2: defensive minimum 2.0).

        Returns:
            {'ratio': float rounded to 2dp or "N/A", 'fiscal_year_end': str or None}
        """
        history = or_default(self.data.history, {})
        year, ratio = latest_current_ratio(history, sorted(history.keys(), reverse=True))
        return {
            'ratio': round(ratio, 2) if ratio is not None else "N/A",
            'fiscal_year_end': year,
        }

    def compute(self) -> GrahamResult:
        """compute_all() as a typed GrahamResult (core.models, M7)."""
        return GrahamResult.from_dict(self.compute_all())
    
    def compute_all(self) -> dict:
        """
        Compute all Graham metrics.
        
        Returns:
            Dictionary containing all calculated metrics and test results
        """
        # Shared inputs computed once, so each warning is raised once (M4.3)
        tbvps = self.compute_tbvps(round_result=False)
        graham_number = self.compute_graham_number(tbvps=tbvps)  # Legacy single-year
        normalized_graham_number = self.compute_normalized_graham_number(tbvps=tbvps)  # New 3-year average
        net_net_value = self.compute_net_net()  # Rounded for display
        net_net_value_raw = self.compute_net_net(round_result=False)  # Unrounded for comparison
        epv_data = self.compute_epv()  # Now returns dict
        nca_details = self.compute_nca_details()
        current_ratio = self.compute_current_ratio()
        quick_ratio = self.compute_quick_ratio()
        three_year_avg_pe = self.compute_three_year_avg_pe()
        combined_pe_pb_test = self.compute_combined_pe_pb_test()
        
        price = or_default(self.data.price, 0.0)
        margin_of_safety_data = self.compute_margin_of_safety(price, normalized_gn=normalized_graham_number,
                                                              epv_data=epv_data)
        
        # Check for deep value opportunity (use unrounded value for accurate comparison)
        # Use a small tolerance to avoid flagging when price and net-net are approximately equal
        # Only flag if price is meaningfully below net-net (more than 2% difference)
        if isinstance(net_net_value_raw, float) and price > 0:
            # Calculate percentage difference: (net_net - price) / net_net * 100
            pct_below = ((net_net_value_raw - price) / net_net_value_raw * 100) if net_net_value_raw > 0 else 0
            if pct_below > DEEP_VALUE_MIN_DISCOUNT_PCT:  # Price is more than 2% below net-net
                self.warnings.append("DEEP VALUE OPPORTUNITY - Price below Net-Net Value")
        
        # Run both defensive and enterprising tests
        defensive_tests = self.run_investor_tests("defensive")
        enterprising_tests = self.run_investor_tests("enterprising", tbvps=tbvps)
        
        # Determine verdict (use new MoS structure)
        history = or_default(self.data.history, {})
        latest_year = self._get_latest_financial_year(history, sorted(history.keys(), reverse=True))
        verdict = determine_verdict(margin_of_safety_data, net_net_value_raw, price,
                                    defensive_tests, enterprising_tests,
                                    or_default(row_at(history, latest_year).net_income, None) if latest_year else None,
                                    self._net_net_yearly_fall(history, latest_year, net_net_value_raw))
        
        metrics = {
            'tbvps': round(tbvps, 2) if isinstance(tbvps, float) else "N/A",  # latest annual, for comparisons
            'graham_number': graham_number,  # Legacy single-year
            'normalized_graham_number': normalized_graham_number,  # New 3-year average
            'epv': epv_data['epv'],  # Keep backward compatibility
            'epv_details': epv_data,  # Add detailed breakdown
            'net_net_value': net_net_value,
            'margin_of_safety': margin_of_safety_data['mos_percentage'],  # For backward compatibility
            'margin_of_safety_details': margin_of_safety_data,  # Full details
            'nca_details': nca_details,
            'current_ratio': current_ratio,
            'quick_ratio': quick_ratio,
            'three_year_avg_pe': three_year_avg_pe,
            'combined_pe_pb_test': combined_pe_pb_test,
            'verdict': verdict['verdict'],
            'verdict_reason': verdict['reason'],
            'public_utility': defensive.is_public_utility(or_default(self.data.industry, None)),
            'defensive_tests': defensive_tests,
            'enterprising_tests': enterprising_tests,
            'warnings': self.warnings.copy()
        }
        
        return metrics
    