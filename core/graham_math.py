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
from typing import Dict, Union, List


class GrahamCalculator:
    """
    Performs all Graham methodology calculations with strict formulas.
    
    Handles edge cases gracefully:
    - Negative equity (TBVPS < 0)
    - Negative earnings (EPS < 0)
    - Young companies (< 10 years history)
    - Missing data
    """
    
    # Graham methodology constants
    GRAHAM_MULTIPLIER = 22.5
    COST_OF_CAPITAL = 0.10  # 10%
    
    # Defensive Investor test thresholds
    MIN_CURRENT_RATIO = 2.0
    MIN_EARNINGS_YEARS = 8
    MAX_PE_RATIO = 15
    MAX_PB_RATIO = 1.5
    MIN_EARNINGS_GROWTH = 1.33  # One-third growth = 33%
    
    # Enterprising Investor test thresholds
    ENT_MIN_CURRENT_RATIO = 1.5
    ENT_MAX_DEBT_ASSETS = 1.10  # Debt < 110% of Net Current Assets
    ENT_MIN_EARNINGS_YEARS = 5
    ENT_MAX_PE_RATIO = 10.0
    ENT_MAX_PB_RATIO = 1.2
    
    def __init__(self, financial_data: dict):
        """
        Initialize calculator with financial data.
        
        Args:
            financial_data: Dictionary containing ticker, price, currency, history, etc.
        """
        self.data = financial_data
        self.warnings = []
    
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
        
        # Get most recent fiscal year
        years = sorted(history.keys(), reverse=True)
        if not years:
            return "N/A"
        
        latest_year = years[0]
        year_data = history[latest_year]
        
        # Extract required fields
        total_equity = year_data.get('total_equity', 0.0)
        intangible_assets = year_data.get('intangible_assets', 0.0)
        goodwill = year_data.get('goodwill', 0.0)
        shares_outstanding = year_data.get('shares_outstanding', 0.0)
        
        # Validate shares outstanding
        if shares_outstanding == 0:
            return "N/A"
        
        # Calculate TBVPS
        tangible_equity = total_equity - intangible_assets - goodwill
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
        
        # Get most recent EPS
        history = self.data.get('history', {})
        if not history:
            return "N/A"
        
        years = sorted(history.keys(), reverse=True)
        if not years:
            return "N/A"
        
        latest_year = years[0]
        eps = history[latest_year].get('eps', 0.0)
        
        # Handle negative EPS
        if eps <= 0:
            return "N/A"
        
        # Calculate Graham Number
        graham_number = math.sqrt(self.GRAHAM_MULTIPLIER * eps * tbvps)
        
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
        
        # Get most recent fiscal year
        years = sorted(history.keys(), reverse=True)
        if not years:
            return "N/A"
        
        latest_year = years[0]
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
    
    def compute_epv(self) -> float:
        """
        Calculate Earnings Power Value (EPV).
        
        Formula: Normalized Earnings / Cost of Capital
        Normalized Earnings = Average of last 5-10 years
        Cost of Capital = 10%
        
        Returns:
            float: EPV rounded to 2 decimals
        """
        history = self.data.get('history', {})
        if not history:
            return 0.0
        
        # Get years sorted descending (most recent first)
        years = sorted(history.keys(), reverse=True)
        if not years:
            return 0.0
        
        # Get last 5-10 years of net income
        earnings = []
        for year in years[:10]:  # Take up to 10 most recent years
            net_income = history[year].get('net_income')
            if net_income is not None:
                earnings.append(net_income)
        
        # Need at least 5 years for normalization
        if len(earnings) < 5:
            return 0.0
        
        # Calculate normalized earnings (average)
        normalized_earnings = sum(earnings) / len(earnings)
        
        # Calculate EPV
        epv = normalized_earnings / self.COST_OF_CAPITAL
        
        return round(epv, 2)
    
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
        # Test 1: Earnings stability - positive earnings in >= 8 of last 10 years
        earnings_stability = self._test_earnings_stability(history, years, min_years=self.MIN_EARNINGS_YEARS, period=10)
        
        # Test 2: Current ratio >= 2.0
        current_ratio_test = self._test_current_ratio(history, years, min_ratio=self.MIN_CURRENT_RATIO)
        
        # Test 3: Long-term debt < net current assets
        debt_test = self._test_debt_to_assets(history, years)
        
        # Test 4: Dividend record
        dividend_test = self._test_dividend_record(history, years, num_years)
        
        # Test 5: Earnings growth >= 33% over 10 years
        earnings_growth_test = self._test_earnings_growth(history, years, num_years)
        
        # Test 6: P/E ratio < 15
        pe_test = self._test_pe_ratio(history, years, price, max_pe=self.MAX_PE_RATIO)
        
        # Test 7: P/B ratio < 1.5
        pb_test = self._test_pb_ratio(history, years, price, max_pb=self.MAX_PB_RATIO)
        
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
        earnings_stability = self._test_earnings_stability(history, years, min_years=self.ENT_MIN_EARNINGS_YEARS, period=5)
        
        # Test 2: Current ratio > 1.5
        current_ratio_test = self._test_current_ratio(history, years, min_ratio=self.ENT_MIN_CURRENT_RATIO)
        
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
        """Test if company has positive earnings in required number of years."""
        test_years = years[:period]
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
        
        latest_year = years[0]
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
        
        latest_year = years[0]
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
        
        # Get earnings from 10 years ago and most recent
        oldest_year = years[9]  # 10th year (0-indexed)
        latest_year = years[0]
        
        old_earnings = history[oldest_year].get('net_income', 0.0)
        recent_earnings = history[latest_year].get('net_income', 0.0)
        
        if old_earnings <= 0:
            return 'FAIL'
        
        growth_ratio = recent_earnings / old_earnings
        return 'PASS' if growth_ratio >= self.MIN_EARNINGS_GROWTH else 'FAIL'
    
    def _test_pe_ratio(self, history: dict, years: list, price: float, max_pe: float = 15) -> str:
        """Test if P/E ratio is below maximum threshold."""
        if not years or price == 0:
            return 'FAIL'
        
        latest_year = years[0]
        eps = history[latest_year].get('eps', 0.0)
        
        if eps <= 0:
            return 'FAIL'
        
        pe_ratio = price / eps
        return 'PASS' if pe_ratio < max_pe else 'FAIL'
    
    def _test_pb_ratio(self, history: dict, years: list, price: float, max_pb: float = 1.5) -> str:
        """Test if P/B ratio is below maximum threshold."""
        if not years or price == 0:
            return 'FAIL'
        
        latest_year = years[0]
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
        
        latest_year = years[0]
        long_term_debt = history[latest_year].get('long_term_debt', 0.0)
        current_assets = history[latest_year].get('current_assets', 0.0)
        current_liabilities = history[latest_year].get('current_liabilities', 0.0)
        
        net_current_assets = current_assets - current_liabilities
        max_allowed_debt = net_current_assets * self.ENT_MAX_DEBT_ASSETS
        
        return 'PASS' if long_term_debt < max_allowed_debt else 'FAIL'
    
    def _test_current_dividend(self, history: dict, years: list) -> str:
        """Test if company currently pays a dividend (last year > 0)."""
        if not years:
            return 'FAIL'
        
        latest_year = years[0]
        dividend = history[latest_year].get('dividend', 0.0)
        
        return 'PASS' if dividend > 0 else 'FAIL'
    
    def _test_enterprising_price(self, history: dict, years: list, price: float) -> str:
        """Test if P/E < 10 OR Price < 120% of Net Tangible Assets."""
        if not years or price == 0:
            return 'FAIL'
        
        latest_year = years[0]
        
        # Test 1: P/E < 10
        eps = history[latest_year].get('eps', 0.0)
        if eps > 0:
            pe_ratio = price / eps
            if pe_ratio < self.ENT_MAX_PE_RATIO:
                return 'PASS'
        
        # Test 2: Price < 120% of Net Tangible Assets (Net-Net Value)
        net_net_value = self.compute_net_net()
        if isinstance(net_net_value, float) and net_net_value > 0:
            max_price = net_net_value * 1.20
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
        epv = self.compute_epv()
        
        price = self.data.get('price', 0.0)
        margin_of_safety = self.compute_margin_of_safety(graham_number, price)
        
        # Check for deep value opportunity (use unrounded value for accurate comparison)
        if isinstance(net_net_value_raw, float) and price > 0 and price < net_net_value_raw:
            self.warnings.append("DEEP VALUE OPPORTUNITY - Price below Net-Net Value")
        
        # Run both defensive and enterprising tests
        defensive_tests = self.run_investor_tests("defensive")
        enterprising_tests = self.run_investor_tests("enterprising")
        
        # Determine verdict
        verdict = self._determine_verdict(graham_number, margin_of_safety, epv, 
                                         defensive_tests, enterprising_tests)
        
        metrics = {
            'graham_number': graham_number,
            'epv': epv,
            'net_net_value': net_net_value,
            'margin_of_safety': margin_of_safety,
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
        
        # Handle positive margin of safety
        if isinstance(margin_of_safety, float):
            if margin_of_safety > 0:
                return "UNDERVALUED"
            else:
                return "OVERVALUED"
        
        return "PENDING"
