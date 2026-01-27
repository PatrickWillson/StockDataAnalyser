"""
Property-based tests for earnings stability with incomplete years.

Tests the fix for the bug where incomplete years (dividend-only, no financials)
were incorrectly counted in earnings stability tests, causing false failures.

Bug: MPE.LSE showed FAIL for Enterprising Investor earnings stability despite
having 10 consecutive years of positive earnings, because year 2025 had a
declared dividend but no financial statements yet.
"""

import pytest
from hypothesis import given, strategies as st
from core.graham_math import GrahamCalculator


class TestEarningsStabilityIncompleteYears:
    """Test earnings stability handling of incomplete years."""
    
    def test_incomplete_future_year_defensive(self):
        """
        Test that incomplete future year doesn't cause false failure (Defensive).
        
        Scenario: Company has 10 years of positive earnings, but year 2025
        has only dividend declared (no financials yet). Should still PASS
        defensive test (requires 8 of 10 years positive).
        """
        # Create history with 10 complete years (all positive) + 1 incomplete future year
        history = {}
        
        # Incomplete future year (dividend only)
        history['2025-12-31'] = {
            'dividend': 0.77,
            'revenue': 0.0,
            'net_income': 0.0,
            'total_equity': 0.0,
            'shares_outstanding': 50000000
        }
        
        # 10 complete years with positive earnings
        for i, year in enumerate(range(2024, 2014, -1)):
            history[f'{year}-12-31'] = {
                'dividend': 0.50,
                'revenue': 100000000 + i * 10000000,
                'net_income': 10000000 + i * 1000000,  # All positive
                'total_equity': 50000000 + i * 5000000,
                'shares_outstanding': 50000000,
                'eps': (10000000 + i * 1000000) / 50000000
            }
        
        financial_data = {
            'ticker': 'TEST.US',
            'price': 100.0,
            'history': history
        }
        
        calculator = GrahamCalculator(financial_data)
        
        # Test defensive investor (requires 8 of 10 years positive)
        result = calculator._test_earnings_stability(
            history, 
            sorted(history.keys(), reverse=True),
            min_years=8,
            period=10
        )
        
        assert result == 'PASS', "Should PASS when 10 complete years all positive (ignoring incomplete year)"
    
    def test_incomplete_future_year_enterprising(self):
        """
        Test that incomplete future year doesn't cause false failure (Enterprising).
        
        This is the exact MPE.LSE bug scenario: 5 complete years all positive,
        but incomplete 2025 year was counted, causing false FAIL.
        """
        # Create history with 5 complete years (all positive) + 1 incomplete future year
        history = {}
        
        # Incomplete future year (dividend only)
        history['2025-12-31'] = {
            'dividend': 0.77,
            'revenue': 0.0,
            'net_income': 0.0,
            'total_equity': 0.0,
            'shares_outstanding': 50000000
        }
        
        # 5 complete years with positive earnings
        for i, year in enumerate(range(2024, 2019, -1)):
            history[f'{year}-12-31'] = {
                'dividend': 0.50,
                'revenue': 100000000 + i * 10000000,
                'net_income': 10000000 + i * 1000000,  # All positive
                'total_equity': 50000000 + i * 5000000,
                'shares_outstanding': 50000000,
                'eps': (10000000 + i * 1000000) / 50000000
            }
        
        financial_data = {
            'ticker': 'TEST.US',
            'price': 100.0,
            'history': history
        }
        
        calculator = GrahamCalculator(financial_data)
        
        # Test enterprising investor (requires 5 of 5 years positive)
        result = calculator._test_earnings_stability(
            history, 
            sorted(history.keys(), reverse=True),
            min_years=5,
            period=5
        )
        
        assert result == 'PASS', "Should PASS when 5 complete years all positive (ignoring incomplete year)"
    
    def test_multiple_incomplete_years(self):
        """Test handling of multiple incomplete years."""
        history = {}
        
        # 2 incomplete future years
        history['2026-12-31'] = {
            'dividend': 0.80,
            'revenue': 0.0,
            'net_income': 0.0,
            'total_equity': 0.0,
            'shares_outstanding': 50000000
        }
        history['2025-12-31'] = {
            'dividend': 0.77,
            'revenue': 0.0,
            'net_income': 0.0,
            'total_equity': 0.0,
            'shares_outstanding': 50000000
        }
        
        # 5 complete years with positive earnings
        for i, year in enumerate(range(2024, 2019, -1)):
            history[f'{year}-12-31'] = {
                'dividend': 0.50,
                'revenue': 100000000,
                'net_income': 10000000,
                'total_equity': 50000000,
                'shares_outstanding': 50000000,
                'eps': 0.20
            }
        
        financial_data = {
            'ticker': 'TEST.US',
            'price': 100.0,
            'history': history
        }
        
        calculator = GrahamCalculator(financial_data)
        
        # Should skip both incomplete years and test the 5 complete years
        result = calculator._test_earnings_stability(
            history, 
            sorted(history.keys(), reverse=True),
            min_years=5,
            period=5
        )
        
        assert result == 'PASS', "Should skip multiple incomplete years"
    
    def test_incomplete_year_with_loss_years(self):
        """Test that incomplete years don't mask actual loss years."""
        history = {}
        
        # Incomplete future year
        history['2025-12-31'] = {
            'dividend': 0.77,
            'revenue': 0.0,
            'net_income': 0.0,
            'total_equity': 0.0,
            'shares_outstanding': 50000000
        }
        
        # 5 complete years: 3 positive, 2 losses
        years_data = [
            (2024, 10000000),   # Positive
            (2023, -5000000),   # Loss
            (2022, 10000000),   # Positive
            (2021, -3000000),   # Loss
            (2020, 10000000),   # Positive
        ]
        
        for year, net_income in years_data:
            history[f'{year}-12-31'] = {
                'dividend': 0.50 if net_income > 0 else 0.0,
                'revenue': 100000000,
                'net_income': net_income,
                'total_equity': 50000000,
                'shares_outstanding': 50000000,
                'eps': net_income / 50000000
            }
        
        financial_data = {
            'ticker': 'TEST.US',
            'price': 100.0,
            'history': history
        }
        
        calculator = GrahamCalculator(financial_data)
        
        # Enterprising requires 5 of 5 years positive - should FAIL (only 3 positive)
        result = calculator._test_earnings_stability(
            history, 
            sorted(history.keys(), reverse=True),
            min_years=5,
            period=5
        )
        
        assert result == 'FAIL', "Should correctly FAIL when actual loss years exist"
    
    def test_insufficient_complete_years(self):
        """Test FAIL when not enough complete years available."""
        history = {}
        
        # Incomplete future year
        history['2025-12-31'] = {
            'dividend': 0.77,
            'revenue': 0.0,
            'net_income': 0.0,
            'total_equity': 0.0,
            'shares_outstanding': 50000000
        }
        
        # Only 3 complete years (need 5 for enterprising)
        for year in [2024, 2023, 2022]:
            history[f'{year}-12-31'] = {
                'dividend': 0.50,
                'revenue': 100000000,
                'net_income': 10000000,
                'total_equity': 50000000,
                'shares_outstanding': 50000000,
                'eps': 0.20
            }
        
        financial_data = {
            'ticker': 'TEST.US',
            'price': 100.0,
            'history': history
        }
        
        calculator = GrahamCalculator(financial_data)
        
        # Enterprising requires 5 years - should FAIL (only 3 available)
        result = calculator._test_earnings_stability(
            history, 
            sorted(history.keys(), reverse=True),
            min_years=5,
            period=5
        )
        
        assert result == 'FAIL', "Should FAIL when insufficient complete years"
    
    def test_negative_equity_is_complete_year(self):
        """Test that negative equity counts as complete financial data."""
        history = {}
        
        # Year with negative equity (distressed company) - still complete data
        history['2024-12-31'] = {
            'dividend': 0.0,
            'revenue': 50000000,
            'net_income': -10000000,  # Loss
            'total_equity': -5000000,  # Negative equity
            'shares_outstanding': 50000000,
            'eps': -0.20
        }
        
        # 4 more complete years with positive earnings
        for year in [2023, 2022, 2021, 2020]:
            history[f'{year}-12-31'] = {
                'dividend': 0.50,
                'revenue': 100000000,
                'net_income': 10000000,
                'total_equity': 50000000,
                'shares_outstanding': 50000000,
                'eps': 0.20
            }
        
        financial_data = {
            'ticker': 'TEST.US',
            'price': 100.0,
            'history': history
        }
        
        calculator = GrahamCalculator(financial_data)
        
        # Should count 2024 as complete year (even with negative values)
        # Enterprising requires 5 of 5 positive - should FAIL (only 4 positive, 1 loss)
        result = calculator._test_earnings_stability(
            history, 
            sorted(history.keys(), reverse=True),
            min_years=5,
            period=5
        )
        
        assert result == 'FAIL', "Negative equity year should count as complete (and show loss)"
    
    @given(
        num_complete_years=st.integers(min_value=5, max_value=15),
        num_incomplete_years=st.integers(min_value=0, max_value=3),
        positive_ratio=st.floats(min_value=0.5, max_value=1.0)
    )
    def test_incomplete_years_property(self, num_complete_years, num_incomplete_years, positive_ratio):
        """
        Property: Incomplete years should never affect test outcome.
        
        Test that adding incomplete years (dividend-only) doesn't change
        the test result compared to testing without them.
        """
        # Create complete years
        history_complete = {}
        num_positive = int(num_complete_years * positive_ratio)
        
        for i in range(num_complete_years):
            year = 2024 - i
            is_positive = i < num_positive
            history_complete[f'{year}-12-31'] = {
                'dividend': 0.50 if is_positive else 0.0,
                'revenue': 100000000,
                'net_income': 10000000 if is_positive else -5000000,
                'total_equity': 50000000,
                'shares_outstanding': 50000000,
                'eps': 0.20 if is_positive else -0.10
            }
        
        # Create history with incomplete years added
        history_with_incomplete = history_complete.copy()
        for i in range(num_incomplete_years):
            year = 2025 + i
            history_with_incomplete[f'{year}-12-31'] = {
                'dividend': 0.77,
                'revenue': 0.0,
                'net_income': 0.0,
                'total_equity': 0.0,
                'shares_outstanding': 50000000
            }
        
        financial_data_complete = {
            'ticker': 'TEST.US',
            'price': 100.0,
            'history': history_complete
        }
        
        financial_data_incomplete = {
            'ticker': 'TEST.US',
            'price': 100.0,
            'history': history_with_incomplete
        }
        
        calculator_complete = GrahamCalculator(financial_data_complete)
        calculator_incomplete = GrahamCalculator(financial_data_incomplete)
        
        # Test with both defensive and enterprising criteria
        for min_years, period in [(8, 10), (5, 5)]:
            result_complete = calculator_complete._test_earnings_stability(
                history_complete,
                sorted(history_complete.keys(), reverse=True),
                min_years=min_years,
                period=period
            )
            
            result_incomplete = calculator_incomplete._test_earnings_stability(
                history_with_incomplete,
                sorted(history_with_incomplete.keys(), reverse=True),
                min_years=min_years,
                period=period
            )
            
            # Results should be identical - incomplete years should not affect outcome
            assert result_complete == result_incomplete, \
                f"Incomplete years changed result: {result_complete} -> {result_incomplete}"


class TestEarningsStabilityIntegration:
    """Integration tests with full investor test suite."""
    
    def test_mpe_scenario_defensive(self):
        """Test the exact MPE scenario for defensive investor."""
        # MPE has 10 years of positive earnings + 1 incomplete future year
        history = {}
        
        # Incomplete 2025
        history['2025-12-31'] = {
            'dividend': 0.77,
            'revenue': 0.0,
            'net_income': 0.0,
            'total_equity': 0.0,
            'current_assets': 0.0,
            'current_liabilities': 0.0,
            'shares_outstanding': 53223600
        }
        
        # 10 complete years (simplified MPE data)
        net_incomes = [90632000, 56398000, 78361000, 91782000, 22169000,
                      7470000, 7161000, 26416000, 16431000, 7817000]
        
        for i, year in enumerate(range(2024, 2014, -1)):
            history[f'{year}-12-31'] = {
                'dividend': 0.50,
                'revenue': 100000000 + i * 10000000,
                'net_income': net_incomes[i],
                'total_equity': 500000000,
                'current_assets': 100000000,
                'current_liabilities': 40000000,
                'shares_outstanding': 53223600,
                'eps': net_incomes[i] / 53223600
            }
        
        financial_data = {
            'ticker': 'MPE.LSE',
            'price': 18.14,
            'history': history
        }
        
        calculator = GrahamCalculator(financial_data)
        tests = calculator.run_investor_tests("defensive")
        
        # Should PASS earnings stability (10 positive years)
        assert tests['earnings_stability'] == 'PASS', \
            "MPE should PASS defensive earnings stability (10 positive years)"
    
    def test_mpe_scenario_enterprising(self):
        """Test the exact MPE scenario for enterprising investor (the bug case)."""
        # MPE has 10 years of positive earnings + 1 incomplete future year
        history = {}
        
        # Incomplete 2025
        history['2025-12-31'] = {
            'dividend': 0.77,
            'revenue': 0.0,
            'net_income': 0.0,
            'total_equity': 0.0,
            'current_assets': 0.0,
            'current_liabilities': 0.0,
            'long_term_debt': 0.0,
            'shares_outstanding': 53223600
        }
        
        # 10 complete years (simplified MPE data)
        net_incomes = [90632000, 56398000, 78361000, 91782000, 22169000,
                      7470000, 7161000, 26416000, 16431000, 7817000]
        
        for i, year in enumerate(range(2024, 2014, -1)):
            history[f'{year}-12-31'] = {
                'dividend': 0.50,
                'revenue': 100000000 + i * 10000000,
                'net_income': net_incomes[i],
                'total_equity': 500000000,
                'current_assets': 100000000,
                'current_liabilities': 40000000,
                'long_term_debt': 20000000,
                'shares_outstanding': 53223600,
                'eps': net_incomes[i] / 53223600
            }
        
        financial_data = {
            'ticker': 'MPE.LSE',
            'price': 18.14,
            'history': history
        }
        
        calculator = GrahamCalculator(financial_data)
        tests = calculator.run_investor_tests("enterprising")
        
        # Should PASS earnings stability (5+ positive years in last 5 complete years)
        assert tests['earnings_stability'] == 'PASS', \
            "MPE should PASS enterprising earnings stability (5+ positive years)"
