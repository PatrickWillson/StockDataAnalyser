"""
Property-Based Tests for Working Capital Per Share (WCPS) Calculator

This module tests the WCPS calculation methods using property-based testing with Hypothesis.
All tests run 100+ iterations with random valid inputs to verify universal correctness properties.

Feature: graham-metrics-enhancement
"""

from decimal import Decimal
from hypothesis import given, settings

from core.financial_data_processor import FinancialDataProcessor
from tests.test_utils_decimal import (
    currency_strategy,
    shares_strategy,
    to_decimal,
    assert_decimal_equal
)
from tests.fixtures_graham_metrics import (
    EdgeCaseFixtures
)


class TestWCPSCalculationCorrectness:
    """
    Property 7: WCPS Calculation Correctness
    
    For any year with current_assets, current_liabilities, and shares_outstanding > 0,
    the WCPS should equal (current_assets - current_liabilities) / shares_outstanding.
    
    Validates: Requirements 3.1
    """
    
    @given(
        current_assets=currency_strategy(min_value="0", max_value="1000000000000"),
        current_liabilities=currency_strategy(min_value="0", max_value="1000000000000"),
        shares_outstanding=shares_strategy(min_value="1", max_value="100000000000")
    )
    @settings(max_examples=100)
    def test_wcps_equals_formula(
        self, current_assets, current_liabilities, shares_outstanding
    ):
        """
        Property: WCPS = (Current Assets - Current Liabilities) / Shares Outstanding
        
        For any year with shares_outstanding > 0, WCPS should equal
        (current_assets - current_liabilities) / shares_outstanding
        """
        # Arrange - Create balance sheet and income statement data
        balance_sheet = {
            '2023-12-31': {
                'current_assets': float(current_assets),
                'current_liabilities': float(current_liabilities),
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': float(current_liabilities),
                'long_term_debt': 0.0,
                'total_assets': float(current_assets),
                'total_debt': 0.0,
                'shares_outstanding': float(shares_outstanding)
            }
        }
        
        income_statement = {
            '2023-12-31': {
                'revenue': 1000000.0,
                'net_income': 100000.0,
                'eps': 1.0
            }
        }
        
        dividend_history = {}
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            float(shares_outstanding)
        )
        
        # Assert
        wcps = result['2023-12-31']['wcps']
        
        if wcps != "N/A":
            # Calculate expected WCPS
            working_capital = current_assets - current_liabilities
            expected = working_capital / shares_outstanding
            actual = to_decimal(wcps)
            
            assert_decimal_equal(
                actual,
                expected,
                tolerance=Decimal('0.01'),
                message=f"WCPS {actual} should equal (current_assets {current_assets} - current_liabilities {current_liabilities}) / shares_outstanding {shares_outstanding} = {expected}"
            )
    
    def test_wcps_with_known_values(self):
        """
        Unit test: Verify WCPS calculation with known values.
        """
        # Arrange
        balance_sheet = {
            '2023-12-31': {
                'current_assets': 1000000.0,
                'current_liabilities': 400000.0,
                'total_equity': 1200000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 800000.0,
                'long_term_debt': 400000.0,
                'total_assets': 2000000.0,
                'total_debt': 400000.0,
                'shares_outstanding': 100000.0
            }
        }
        
        income_statement = {
            '2023-12-31': {
                'revenue': 5000000.0,
                'net_income': 500000.0,
                'eps': 5.0
            }
        }
        
        dividend_history = {}
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            100000.0
        )
        
        # Assert
        # (1,000,000 - 400,000) / 100,000 = 600,000 / 100,000 = 6.0
        wcps = result['2023-12-31']['wcps']
        expected = Decimal('6.0')
        actual = to_decimal(wcps)
        
        assert_decimal_equal(
            actual,
            expected,
            tolerance=Decimal('0.01'),
            message=f"WCPS should be {expected}"
        )
    
    def test_wcps_with_negative_working_capital(self):
        """
        Unit test: WCPS with negative working capital (liabilities > assets).
        """
        # Arrange
        balance_sheet = {
            '2023-12-31': {
                'current_assets': 400000.0,
                'current_liabilities': 1000000.0,  # Liabilities exceed assets
                'total_equity': 500000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 1500000.0,
                'long_term_debt': 500000.0,
                'total_assets': 2000000.0,
                'total_debt': 500000.0,
                'shares_outstanding': 100000.0
            }
        }
        
        income_statement = {
            '2023-12-31': {
                'revenue': 5000000.0,
                'net_income': 500000.0,
                'eps': 5.0
            }
        }
        
        dividend_history = {}
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            100000.0
        )
        
        # Assert
        # (400,000 - 1,000,000) / 100,000 = -600,000 / 100,000 = -6.0
        wcps = result['2023-12-31']['wcps']
        expected = Decimal('-6.0')
        actual = to_decimal(wcps)
        
        assert_decimal_equal(
            actual,
            expected,
            tolerance=Decimal('0.01'),
            message="WCPS should be negative when current liabilities exceed current assets"
        )
        
        # Verify it's a negative number, not "N/A"
        assert wcps != "N/A", "Negative WCPS should be displayed as a number, not N/A"
        assert wcps < 0, "WCPS should be negative"
    
    def test_wcps_with_zero_working_capital(self):
        """
        Unit test: WCPS when working capital is exactly zero.
        """
        # Arrange
        balance_sheet = {
            '2023-12-31': {
                'current_assets': 500000.0,
                'current_liabilities': 500000.0,  # Equal to assets
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 1000000.0,
                'long_term_debt': 500000.0,
                'total_assets': 2000000.0,
                'total_debt': 500000.0,
                'shares_outstanding': 100000.0
            }
        }
        
        income_statement = {
            '2023-12-31': {
                'revenue': 5000000.0,
                'net_income': 500000.0,
                'eps': 5.0
            }
        }
        
        dividend_history = {}
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            100000.0
        )
        
        # Assert
        # (500,000 - 500,000) / 100,000 = 0 / 100,000 = 0.0
        wcps = result['2023-12-31']['wcps']
        expected = Decimal('0.0')
        actual = to_decimal(wcps)
        
        assert_decimal_equal(
            actual,
            expected,
            tolerance=Decimal('0.01'),
            message="WCPS should be 0.0 when working capital is zero"
        )
    
    def test_wcps_multiple_years(self):
        """
        Unit test: WCPS calculated correctly for multiple years.
        """
        # Arrange - 3 years of data with varying working capital
        balance_sheet = {
            '2023-12-31': {
                'current_assets': 1200000.0,
                'current_liabilities': 400000.0,
                'total_equity': 1500000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 800000.0,
                'long_term_debt': 400000.0,
                'total_assets': 2300000.0,
                'total_debt': 400000.0,
                'shares_outstanding': 100000.0
            },
            '2022-12-31': {
                'current_assets': 1000000.0,
                'current_liabilities': 500000.0,
                'total_equity': 1200000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 900000.0,
                'long_term_debt': 400000.0,
                'total_assets': 2100000.0,
                'total_debt': 400000.0,
                'shares_outstanding': 100000.0
            },
            '2021-12-31': {
                'current_assets': 800000.0,
                'current_liabilities': 600000.0,
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 1000000.0,
                'long_term_debt': 400000.0,
                'total_assets': 2000000.0,
                'total_debt': 400000.0,
                'shares_outstanding': 100000.0
            }
        }
        
        income_statement = {
            '2023-12-31': {'revenue': 5000000.0, 'net_income': 500000.0, 'eps': 5.0},
            '2022-12-31': {'revenue': 4500000.0, 'net_income': 450000.0, 'eps': 4.5},
            '2021-12-31': {'revenue': 4000000.0, 'net_income': 400000.0, 'eps': 4.0}
        }
        
        dividend_history = {}
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            100000.0
        )
        
        # Assert - Verify WCPS for each year
        # 2023: (1,200,000 - 400,000) / 100,000 = 8.0
        wcps_2023 = result['2023-12-31']['wcps']
        assert_decimal_equal(to_decimal(wcps_2023), Decimal('8.0'), tolerance=Decimal('0.01'))
        
        # 2022: (1,000,000 - 500,000) / 100,000 = 5.0
        wcps_2022 = result['2022-12-31']['wcps']
        assert_decimal_equal(to_decimal(wcps_2022), Decimal('5.0'), tolerance=Decimal('0.01'))
        
        # 2021: (800,000 - 600,000) / 100,000 = 2.0
        wcps_2021 = result['2021-12-31']['wcps']
        assert_decimal_equal(to_decimal(wcps_2021), Decimal('2.0'), tolerance=Decimal('0.01'))
    
    def test_wcps_rounding_precision(self):
        """
        Unit test: Verify WCPS is rounded to 2 decimal places.
        """
        # Arrange - values that produce a result requiring rounding
        balance_sheet = {
            '2023-12-31': {
                'current_assets': 1000000.0,
                'current_liabilities': 333333.0,
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 333333.0,
                'long_term_debt': 0.0,
                'total_assets': 1000000.0,
                'total_debt': 0.0,
                'shares_outstanding': 100000.0
            }
        }
        
        income_statement = {
            '2023-12-31': {
                'revenue': 5000000.0,
                'net_income': 500000.0,
                'eps': 5.0
            }
        }
        
        dividend_history = {}
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            100000.0
        )
        
        # Assert
        # (1,000,000 - 333,333) / 100,000 = 666,667 / 100,000 = 6.66667
        # Should round to 6.67
        wcps = result['2023-12-31']['wcps']
        
        assert isinstance(wcps, float), "WCPS should return float"
        
        # Verify it's rounded to 2 decimal places
        wcps_str = f"{wcps:.2f}"
        assert wcps_str == "6.67", \
            f"WCPS should be rounded to 2 decimal places: expected 6.67, got {wcps_str}"
    
    def test_wcps_very_large_values(self):
        """
        Unit test: WCPS with very large values should be handled correctly.
        """
        # Arrange
        balance_sheet = {
            '2023-12-31': {
                'current_assets': 999999999999.0,  # ~1 trillion
                'current_liabilities': 500000000000.0,  # 500 billion
                'total_equity': 1000000000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 500000000000.0,
                'long_term_debt': 0.0,
                'total_assets': 1500000000000.0,
                'total_debt': 0.0,
                'shares_outstanding': 10000000000.0  # 10 billion shares
            }
        }
        
        income_statement = {
            '2023-12-31': {
                'revenue': 5000000000000.0,
                'net_income': 500000000000.0,
                'eps': 50.0
            }
        }
        
        dividend_history = {}
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            10000000000.0
        )
        
        # Assert
        wcps = result['2023-12-31']['wcps']
        assert wcps != "N/A", "Should handle large values"
        
        # Verify calculation is correct
        # (999,999,999,999 - 500,000,000,000) / 10,000,000,000 = 49.9999999999 ≈ 50.0
        expected = Decimal('50.0')
        actual = to_decimal(wcps)
        assert_decimal_equal(actual, expected, tolerance=Decimal('0.01'))


class TestWCPSNegativeValueIndication:
    """
    Property 8: WCPS Negative Value Indication
    
    For any year where WCPS is negative (working capital < 0), the system should
    display the negative value (not "N/A").
    
    Validates: Requirements 3.5
    """
    
    @given(
        current_assets=currency_strategy(min_value="0", max_value="1000000000"),
        current_liabilities=currency_strategy(min_value="1", max_value="1000000000"),
        shares_outstanding=shares_strategy(min_value="1", max_value="100000000")
    )
    @settings(max_examples=100)
    def test_negative_wcps_displayed_as_number(
        self, current_assets, current_liabilities, shares_outstanding
    ):
        """
        Property: Negative WCPS should be displayed as a negative number, not "N/A".
        
        When current liabilities exceed current assets, WCPS should be negative.
        This is informational (indicates liquidity concern) but not an error.
        """
        # Ensure current_liabilities > current_assets to guarantee negative working capital
        if current_liabilities <= current_assets:
            current_liabilities = current_assets + Decimal('1000')
        
        # Arrange
        balance_sheet = {
            '2023-12-31': {
                'current_assets': float(current_assets),
                'current_liabilities': float(current_liabilities),
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': float(current_liabilities),
                'long_term_debt': 0.0,
                'total_assets': float(current_assets),
                'total_debt': 0.0,
                'shares_outstanding': float(shares_outstanding)
            }
        }
        
        income_statement = {
            '2023-12-31': {
                'revenue': 1000000.0,
                'net_income': 100000.0,
                'eps': 1.0
            }
        }
        
        dividend_history = {}
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            float(shares_outstanding)
        )
        
        # Assert
        wcps = result['2023-12-31']['wcps']
        
        # Should NOT be "N/A"
        assert wcps != "N/A", \
            "Negative WCPS should be displayed as a number, not N/A"
        
        # Should be a negative number (or -0.0 in edge case where both are very small)
        assert isinstance(wcps, (int, float)), \
            f"WCPS should be a number, got {type(wcps)}"
        # Handle -0.0 edge case: if working capital is negative, WCPS should be <= 0
        working_capital = current_assets - current_liabilities
        if working_capital < 0:
            assert wcps <= 0, \
                f"WCPS should be <= 0 when current liabilities exceed current assets, got {wcps}"
        
        # Verify calculation is correct
        working_capital = current_assets - current_liabilities
        expected = working_capital / shares_outstanding
        actual = to_decimal(wcps)
        
        assert_decimal_equal(
            actual,
            expected,
            tolerance=Decimal('0.01'),
            message=f"Negative WCPS {actual} should equal formula result {expected}"
        )
    
    def test_negative_wcps_example(self):
        """
        Unit test: Specific example of negative WCPS.
        """
        # Arrange - Company with liquidity issues
        financial_data = EdgeCaseFixtures.get_negative_working_capital_data()
        
        # Extract the data for merge
        balance_sheet = {}
        income_statement = {}
        
        for year, year_data in financial_data['history'].items():
            balance_sheet[year] = {
                'current_assets': year_data['current_assets'],
                'current_liabilities': year_data['current_liabilities'],
                'total_equity': year_data.get('total_equity', 1000000.0),
                'intangible_assets': year_data.get('intangible_assets', 0.0),
                'goodwill': year_data.get('goodwill', 0.0),
                'total_liabilities': year_data.get('total_liabilities', year_data['current_liabilities']),
                'long_term_debt': year_data.get('long_term_debt', 0.0),
                'total_assets': year_data.get('total_assets', year_data['current_assets']),
                'total_debt': year_data.get('total_debt', 0.0),
                'shares_outstanding': year_data['shares_outstanding']
            }
            income_statement[year] = {
                'revenue': year_data.get('revenue', 1000000.0),
                'net_income': year_data.get('net_income', 100000.0),
                'eps': year_data.get('eps', 1.0)
            }
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            {},
            1000000.0
        )
        
        # Assert - Check that negative WCPS years are displayed as negative numbers
        for year, year_data in result.items():
            wcps = year_data['wcps']
            working_capital = year_data['current_assets'] - year_data['current_liabilities']
            
            if working_capital < 0:
                assert wcps != "N/A", \
                    f"Year {year}: Negative working capital should produce numeric WCPS, not N/A"
                assert wcps < 0, \
                    f"Year {year}: WCPS should be negative when working capital is negative"


class TestWCPSEdgeCases:
    """
    Unit tests for WCPS edge cases.
    
    Tests specific scenarios that should be handled gracefully.
    Validates: Requirements 3.2, 3.5
    """
    
    def test_zero_shares_outstanding(self):
        """
        Edge case: Zero shares outstanding should return N/A.
        
        Validates: Requirement 3.2
        """
        # Arrange
        balance_sheet = {
            '2023-12-31': {
                'current_assets': 1000000.0,
                'current_liabilities': 400000.0,
                'total_equity': 1200000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 800000.0,
                'long_term_debt': 400000.0,
                'total_assets': 2000000.0,
                'total_debt': 400000.0,
                'shares_outstanding': 0.0  # Zero shares
            }
        }
        
        income_statement = {
            '2023-12-31': {
                'revenue': 5000000.0,
                'net_income': 500000.0,
                'eps': 0.0
            }
        }
        
        dividend_history = {}
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            0.0  # Zero shares as fallback too
        )
        
        # Assert
        wcps = result['2023-12-31']['wcps']
        assert wcps == "N/A", \
            "WCPS should be N/A when shares outstanding is zero"
    
    def test_missing_current_assets(self):
        """
        Edge case: Missing current assets (defaults to 0).
        """
        # Arrange
        balance_sheet = {
            '2023-12-31': {
                # Missing current_assets
                'current_liabilities': 400000.0,
                'total_equity': 1200000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 800000.0,
                'long_term_debt': 400000.0,
                'total_assets': 2000000.0,
                'total_debt': 400000.0,
                'shares_outstanding': 100000.0
            }
        }
        
        income_statement = {
            '2023-12-31': {
                'revenue': 5000000.0,
                'net_income': 500000.0,
                'eps': 5.0
            }
        }
        
        dividend_history = {}
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            100000.0
        )
        
        # Assert
        # Missing current_assets defaults to 0.0
        # (0 - 400,000) / 100,000 = -4.0
        wcps = result['2023-12-31']['wcps']
        assert wcps != "N/A", "Should calculate WCPS even with missing current assets (defaults to 0)"
        assert wcps < 0, "WCPS should be negative when current assets is missing (defaults to 0)"
    
    def test_missing_current_liabilities(self):
        """
        Edge case: Missing current liabilities (defaults to 0).
        """
        # Arrange
        balance_sheet = {
            '2023-12-31': {
                'current_assets': 1000000.0,
                # Missing current_liabilities
                'total_equity': 1200000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 800000.0,
                'long_term_debt': 400000.0,
                'total_assets': 2000000.0,
                'total_debt': 400000.0,
                'shares_outstanding': 100000.0
            }
        }
        
        income_statement = {
            '2023-12-31': {
                'revenue': 5000000.0,
                'net_income': 500000.0,
                'eps': 5.0
            }
        }
        
        dividend_history = {}
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            100000.0
        )
        
        # Assert
        # Missing current_liabilities defaults to 0.0
        # (1,000,000 - 0) / 100,000 = 10.0
        wcps = result['2023-12-31']['wcps']
        expected = Decimal('10.0')
        actual = to_decimal(wcps)
        
        assert_decimal_equal(
            actual,
            expected,
            tolerance=Decimal('0.01'),
            message="Should calculate WCPS with missing current liabilities (defaults to 0)"
        )
    
    def test_year_specific_shares_outstanding(self):
        """
        Edge case: Year-specific shares outstanding should be used.
        """
        # Arrange
        balance_sheet = {
            '2023-12-31': {
                'current_assets': 1000000.0,
                'current_liabilities': 400000.0,
                'total_equity': 1200000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 800000.0,
                'long_term_debt': 400000.0,
                'total_assets': 2000000.0,
                'total_debt': 400000.0,
                'shares_outstanding': 100000.0  # Balance sheet shares
            }
        }
        
        income_statement = {
            '2023-12-31': {
                'revenue': 5000000.0,
                'net_income': 500000.0,
                'eps': 5.0
            }
        }
        
        dividend_history = {}
        
        # Year-specific shares (should take priority)
        outstanding_shares_by_year = {
            '2023': 200000.0  # Different from balance sheet
        }
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            150000.0,  # Fallback shares
            outstanding_shares_by_year
        )
        
        # Assert
        # Should use year-specific shares (200,000)
        # (1,000,000 - 400,000) / 200,000 = 3.0
        wcps = result['2023-12-31']['wcps']
        expected = Decimal('3.0')
        actual = to_decimal(wcps)
        
        assert_decimal_equal(
            actual,
            expected,
            tolerance=Decimal('0.01'),
            message="Should use year-specific shares outstanding for WCPS calculation"
        )
