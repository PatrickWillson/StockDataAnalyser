"""
Property-Based Tests for Payout Ratio Calculator

This module tests the Payout Ratio calculation methods using property-based testing with Hypothesis.
All tests run 100+ iterations with random valid inputs to verify universal correctness properties.

Feature: graham-metrics-enhancement
"""

import pytest
from decimal import Decimal
from hypothesis import given, settings

from core.financial_data_processor import FinancialDataProcessor
from tests.test_utils_decimal import (
    decimal_strategy,
    assert_decimal_equal
)


class TestPayoutRatioCalculationAndFormatting:
    """
    Property 12: Payout Ratio Calculation and Formatting
    
    For any year with EPS > 0 and dividend ≥ 0, the payout ratio should equal
    (dividend / EPS) × 100 and be formatted as a percentage with one decimal place.
    
    Validates: Requirements 6.1, 6.4
    """
    
    @given(
        eps=decimal_strategy(min_value="0.01", max_value="1000"),
        dividend=decimal_strategy(min_value="0", max_value="100")
    )
    @settings(max_examples=100)
    def test_payout_ratio_equals_formula(self, eps, dividend):
        """
        Property: Payout Ratio = (Dividend / EPS) × 100
        
        For any year with EPS > 0 and dividend ≥ 0, payout ratio should equal
        (dividend / EPS) × 100 formatted as percentage with 1 decimal place
        """
        # Arrange - Create balance sheet and income statement data
        shares_outstanding = Decimal('1000000')
        
        balance_sheet = {
            '2023-12-31': {
                'current_assets': 1000000.0,
                'current_liabilities': 400000.0,
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 400000.0,
                'long_term_debt': 0.0,
                'total_assets': 1000000.0,
                'total_debt': 0.0,
                'shares_outstanding': float(shares_outstanding)
            }
        }
        
        income_statement = {
            '2023-12-31': {
                'revenue': 1000000.0,
                'net_income': float(eps * shares_outstanding),
                'eps': float(eps)
            }
        }
        
        dividend_history = {
            '2023': float(dividend)
        }
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            float(shares_outstanding)
        )
        
        # Assert
        payout_ratio = result['2023-12-31']['payout_ratio']
        
        if dividend == 0:
            # Special case: zero dividend should return "0.0%"
            assert payout_ratio == "0.0%", \
                f"Expected '0.0%' for zero dividend, got '{payout_ratio}'"
        else:
            # Normal case: calculate expected payout ratio
            expected_ratio = (dividend / eps) * Decimal('100')
            
            # Extract numeric value from percentage string
            assert isinstance(payout_ratio, str), \
                f"Payout ratio should be string, got {type(payout_ratio)}"
            assert payout_ratio.endswith('%'), \
                f"Payout ratio should end with '%', got '{payout_ratio}'"
            
            actual_value = Decimal(payout_ratio.rstrip('%'))
            
            # Verify formula correctness (tolerance for rounding)
            assert_decimal_equal(
                actual_value,
                expected_ratio,
                tolerance=Decimal('0.1'),
                message=f"Payout ratio {actual_value}% does not match expected {expected_ratio}%"
            )
            
            # Verify formatting: one decimal place
            decimal_places = len(payout_ratio.rstrip('%').split('.')[-1])
            assert decimal_places == 1, \
                f"Payout ratio should have 1 decimal place, got {decimal_places} in '{payout_ratio}'"
    
    def test_payout_ratio_zero_eps(self):
        """
        Edge Case: EPS = 0 should return "N/A"
        
        Validates: Requirements 6.2
        """
        # Arrange
        shares_outstanding = Decimal('1000000')
        
        balance_sheet = {
            '2023-12-31': {
                'current_assets': 1000000.0,
                'current_liabilities': 400000.0,
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 400000.0,
                'long_term_debt': 0.0,
                'total_assets': 1000000.0,
                'total_debt': 0.0,
                'shares_outstanding': float(shares_outstanding)
            }
        }
        
        income_statement = {
            '2023-12-31': {
                'revenue': 1000000.0,
                'net_income': 0.0,
                'eps': 0.0
            }
        }
        
        dividend_history = {
            '2023': 1.0
        }
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            float(shares_outstanding)
        )
        
        # Assert
        payout_ratio = result['2023-12-31']['payout_ratio']
        assert payout_ratio == "N/A", \
            f"Expected 'N/A' for zero EPS, got '{payout_ratio}'"
    
    def test_payout_ratio_negative_eps(self):
        """
        Edge Case: Negative EPS should return "N/A"
        
        Validates: Requirements 6.2
        """
        # Arrange
        shares_outstanding = Decimal('1000000')
        
        balance_sheet = {
            '2023-12-31': {
                'current_assets': 1000000.0,
                'current_liabilities': 400000.0,
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 400000.0,
                'long_term_debt': 0.0,
                'total_assets': 1000000.0,
                'total_debt': 0.0,
                'shares_outstanding': float(shares_outstanding)
            }
        }
        
        income_statement = {
            '2023-12-31': {
                'revenue': 1000000.0,
                'net_income': -100000.0,
                'eps': -0.1
            }
        }
        
        dividend_history = {
            '2023': 1.0
        }
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            float(shares_outstanding)
        )
        
        # Assert
        payout_ratio = result['2023-12-31']['payout_ratio']
        assert payout_ratio == "N/A", \
            f"Expected 'N/A' for negative EPS, got '{payout_ratio}'"
    
    def test_payout_ratio_zero_dividend(self):
        """
        Edge Case: Zero dividend with positive EPS should return "0.0%"
        
        Validates: Requirements 6.3
        """
        # Arrange
        shares_outstanding = Decimal('1000000')
        
        balance_sheet = {
            '2023-12-31': {
                'current_assets': 1000000.0,
                'current_liabilities': 400000.0,
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 400000.0,
                'long_term_debt': 0.0,
                'total_assets': 1000000.0,
                'total_debt': 0.0,
                'shares_outstanding': float(shares_outstanding)
            }
        }
        
        income_statement = {
            '2023-12-31': {
                'revenue': 1000000.0,
                'net_income': 100000.0,
                'eps': 0.1
            }
        }
        
        dividend_history = {
            '2023': 0.0
        }
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            float(shares_outstanding)
        )
        
        # Assert
        payout_ratio = result['2023-12-31']['payout_ratio']
        assert payout_ratio == "0.0%", \
            f"Expected '0.0%' for zero dividend, got '{payout_ratio}'"
    
    def test_payout_ratio_over_100_percent(self):
        """
        Edge Case: Payout ratio > 100% should be displayed without capping
        
        Validates: Requirements 6.6
        """
        # Arrange
        shares_outstanding = Decimal('1000000')
        eps = Decimal('2.0')
        dividend = Decimal('3.0')  # Dividend > EPS
        
        balance_sheet = {
            '2023-12-31': {
                'current_assets': 1000000.0,
                'current_liabilities': 400000.0,
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 400000.0,
                'long_term_debt': 0.0,
                'total_assets': 1000000.0,
                'total_debt': 0.0,
                'shares_outstanding': float(shares_outstanding)
            }
        }
        
        income_statement = {
            '2023-12-31': {
                'revenue': 1000000.0,
                'net_income': float(eps * shares_outstanding),
                'eps': float(eps)
            }
        }
        
        dividend_history = {
            '2023': float(dividend)
        }
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            float(shares_outstanding)
        )
        
        # Assert
        payout_ratio = result['2023-12-31']['payout_ratio']
        
        # Extract numeric value
        assert isinstance(payout_ratio, str) and payout_ratio.endswith('%'), \
            f"Payout ratio should be percentage string, got '{payout_ratio}'"
        
        actual_value = Decimal(payout_ratio.rstrip('%'))
        expected_ratio = (dividend / eps) * Decimal('100')
        
        # Verify it's over 100%
        assert actual_value > 100, \
            f"Expected payout ratio > 100%, got {actual_value}%"
        
        # Verify formula correctness
        assert_decimal_equal(
            actual_value,
            expected_ratio,
            tolerance=Decimal('0.1'),
            message=f"Payout ratio {actual_value}% does not match expected {expected_ratio}%"
        )


class TestPayoutRatioMultiYear:
    """Test payout ratio calculation across multiple years."""
    
    def test_payout_ratio_multiple_years(self):
        """
        Test payout ratio calculation for multiple years with varying EPS and dividends.
        """
        # Arrange
        shares_outstanding = Decimal('1000000')
        
        balance_sheet = {
            '2023-12-31': {
                'current_assets': 1000000.0,
                'current_liabilities': 400000.0,
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 400000.0,
                'long_term_debt': 0.0,
                'total_assets': 1000000.0,
                'total_debt': 0.0,
                'shares_outstanding': float(shares_outstanding)
            },
            '2022-12-31': {
                'current_assets': 900000.0,
                'current_liabilities': 350000.0,
                'total_equity': 900000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 350000.0,
                'long_term_debt': 0.0,
                'total_assets': 900000.0,
                'total_debt': 0.0,
                'shares_outstanding': float(shares_outstanding)
            },
            '2021-12-31': {
                'current_assets': 800000.0,
                'current_liabilities': 300000.0,
                'total_equity': 800000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'total_liabilities': 300000.0,
                'long_term_debt': 0.0,
                'total_assets': 800000.0,
                'total_debt': 0.0,
                'shares_outstanding': float(shares_outstanding)
            }
        }
        
        income_statement = {
            '2023-12-31': {
                'revenue': 1000000.0,
                'net_income': 500000.0,
                'eps': 5.0
            },
            '2022-12-31': {
                'revenue': 900000.0,
                'net_income': -100000.0,  # Loss year
                'eps': -1.0
            },
            '2021-12-31': {
                'revenue': 800000.0,
                'net_income': 300000.0,
                'eps': 3.0
            }
        }
        
        dividend_history = {
            '2023': 2.0,
            '2022': 1.0,  # Dividend paid despite loss
            '2021': 0.0   # No dividend
        }
        
        # Act
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet,
            income_statement,
            dividend_history,
            float(shares_outstanding)
        )
        
        # Assert
        # 2023: Normal case (2.0 / 5.0 * 100 = 40.0%)
        payout_2023 = result['2023-12-31']['payout_ratio']
        assert payout_2023 == "40.0%", \
            f"Expected '40.0%' for 2023, got '{payout_2023}'"
        
        # 2022: Loss year with dividend should return "N/A"
        payout_2022 = result['2022-12-31']['payout_ratio']
        assert payout_2022 == "N/A", \
            f"Expected 'N/A' for 2022 (loss year), got '{payout_2022}'"
        
        # 2021: Zero dividend should return "0.0%"
        payout_2021 = result['2021-12-31']['payout_ratio']
        assert payout_2021 == "0.0%", \
            f"Expected '0.0%' for 2021 (no dividend), got '{payout_2021}'"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
