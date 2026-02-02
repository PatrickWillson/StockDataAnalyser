"""
Unit tests for normalized Graham Number edge cases.

Tests specific examples and scenarios from the design document to validate
exact behavior for normalized Graham Number calculations.
"""

import pytest
import math
from core.graham_math import GrahamCalculator
from config.graham_constants import GRAHAM_MULTIPLIER


class TestNormalizedGrahamNumberEdgeCases:
    """Unit tests for specific normalized Graham Number scenarios."""
    
    def test_untc_example_scenario_1a(self):
        """
        Test UNTC example (Scenario 1a): Cyclical earnings smoothing.
        
        EPS values: [4.85, 25.51, 14.40] (2024, 2023, 2022)
        TBVPS: $23.85
        Expected normalized Graham Number: $89.48
        
        This demonstrates how normalized earnings smooth cyclical volatility.
        Single-year Graham Number based on depressed 2024 EPS would be $51.00,
        but normalized approach reveals true value of $89.48.
        """
        # Arrange: Create financial data matching UNTC example
        eps_values = [4.85, 25.51, 14.40]  # 2024 (depressed), 2023 (peak), 2022 (normal)
        tbvps = 23.85
        shares = 1000000.0
        total_equity = tbvps * shares
        
        financial_data = {
            'ticker': 'UNTC.US',
            'price': 32.88,
            'currency': 'USD',
            'history': {
                '2024-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[0],
                    'revenue': 1000000.0,
                    'net_income': eps_values[0] * shares
                },
                '2023-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[1],
                    'revenue': 1100000.0,
                    'net_income': eps_values[1] * shares
                },
                '2022-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[2],
                    'revenue': 1200000.0,
                    'net_income': eps_values[2] * shares
                }
            }
        }
        
        # Act: Calculate normalized Graham Number
        calculator = GrahamCalculator(financial_data)
        normalized_gn = calculator.compute_normalized_graham_number()
        
        # Assert: Verify normalized Graham Number
        # 3-year average EPS = (4.85 + 25.51 + 14.40) / 3 = 14.92
        # Normalized GN = √(22.5 × 14.92 × 23.85) = √(8003.01) ≈ 89.46
        eps_3yr_avg = sum(eps_values) / 3
        expected_normalized_gn = math.sqrt(GRAHAM_MULTIPLIER * eps_3yr_avg * tbvps)
        
        assert isinstance(normalized_gn, float), \
            f"Expected float, got {type(normalized_gn)}"
        
        assert normalized_gn == pytest.approx(89.48, abs=0.01), \
            f"Expected normalized Graham Number ~$89.48, got ${normalized_gn}"
        
        # Verify it matches the formula
        assert normalized_gn == pytest.approx(expected_normalized_gn, abs=0.01), \
            f"Normalized GN should match formula: expected {expected_normalized_gn:.2f}, got {normalized_gn}"
        
        # Verify audit trail is stored
        assert hasattr(calculator, 'eps_3year_values'), \
            "Calculator should store eps_3year_values"
        assert calculator.eps_3year_values == eps_values, \
            f"Stored EPS values should match input: {calculator.eps_3year_values} vs {eps_values}"
        assert calculator.eps_3year_avg == pytest.approx(14.92, abs=0.01), \
            f"Stored average should be 14.92, got {calculator.eps_3year_avg}"
    
    def test_bull_trap_scenario_1b(self):
        """
        Test bull trap (Scenario 1b): One peak year masking chronic losses.
        
        EPS values: [5.00, -2.00, -1.00] (2024, 2023, 2022)
        TBVPS: $20.00
        Expected normalized Graham Number: $17.33
        
        This demonstrates how normalized earnings catch "bull traps" where
        one record year masks chronic losses. Single-year Graham Number
        would be $67.08 (dangerously optimistic), but normalized approach
        reveals low true value of $17.33.
        """
        # Arrange: Create financial data with bull trap pattern
        eps_values = [5.00, -2.00, -1.00]  # 2024 (peak!), 2023 (loss), 2022 (loss)
        tbvps = 20.00
        shares = 1000000.0
        total_equity = tbvps * shares
        
        financial_data = {
            'ticker': 'TRAP.US',
            'price': 30.00,
            'currency': 'USD',
            'history': {
                '2024-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[0],
                    'revenue': 1000000.0,
                    'net_income': eps_values[0] * shares
                },
                '2023-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[1],
                    'revenue': 800000.0,
                    'net_income': eps_values[1] * shares
                },
                '2022-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[2],
                    'revenue': 900000.0,
                    'net_income': eps_values[2] * shares
                }
            }
        }
        
        # Act: Calculate both single-year and normalized Graham Numbers
        calculator = GrahamCalculator(financial_data)
        single_year_gn = calculator.compute_graham_number()
        normalized_gn = calculator.compute_normalized_graham_number()
        
        # Assert: Verify single-year Graham Number (dangerously optimistic)
        # Single-year GN = √(22.5 × 5.00 × 20.00) = √(2250) ≈ 47.43
        expected_single_gn = math.sqrt(GRAHAM_MULTIPLIER * eps_values[0] * tbvps)
        assert single_year_gn == pytest.approx(expected_single_gn, abs=0.01), \
            f"Single-year GN should be ~{expected_single_gn:.2f}, got {single_year_gn}"
        
        # Assert: Verify normalized Graham Number (reveals low true value)
        # 3-year average EPS = (5.00 + (-2.00) + (-1.00)) / 3 = 0.67
        # Normalized GN = √(22.5 × 0.67 × 20.00) = √(301.5) ≈ 17.36
        eps_3yr_avg = sum(eps_values) / 3
        expected_normalized_gn = math.sqrt(GRAHAM_MULTIPLIER * eps_3yr_avg * tbvps)
        
        assert isinstance(normalized_gn, float), \
            f"Expected float, got {type(normalized_gn)}"
        
        assert normalized_gn == pytest.approx(17.33, abs=0.10), \
            f"Expected normalized Graham Number ~$17.33, got ${normalized_gn}"
        
        # Verify it matches the formula
        assert normalized_gn == pytest.approx(expected_normalized_gn, abs=0.10), \
            f"Normalized GN should match formula: expected {expected_normalized_gn:.2f}, got {normalized_gn}"
        
        # Verify the dramatic difference between single-year and normalized
        assert single_year_gn > normalized_gn * 2, \
            f"Single-year GN ({single_year_gn}) should be much higher than normalized ({normalized_gn})"
        
        # This is the "bull trap" the feature is designed to catch
    
    def test_young_company_2_years_data(self):
        """
        Test young company with only 2 years of data.
        
        Should return "N/A" with warning explaining insufficient data.
        """
        # Arrange: Create financial data with only 2 years
        financial_data = {
            'ticker': 'YOUNG.US',
            'price': 50.00,
            'currency': 'USD',
            'history': {
                '2024-12-31': {
                    'total_equity': 10000000.0,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': 1000000.0,
                    'eps': 5.00,
                    'revenue': 1000000.0,
                    'net_income': 5000000.0
                },
                '2023-12-31': {
                    'total_equity': 9000000.0,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': 1000000.0,
                    'eps': 4.50,
                    'revenue': 900000.0,
                    'net_income': 4500000.0
                }
            }
        }
        
        # Act: Calculate normalized Graham Number
        calculator = GrahamCalculator(financial_data)
        result = calculator.compute_normalized_graham_number()
        
        # Assert: Should return "N/A"
        assert result == "N/A", \
            f"Expected 'N/A' for 2 years of data, got {result}"
        
        # Verify warning was added
        assert any("Insufficient data" in w or "Only 2 years available" in w for w in calculator.warnings), \
            f"Expected warning about insufficient data, got warnings: {calculator.warnings}"
    
    def test_mixed_positive_negative_eps(self):
        """
        Test mixed positive/negative EPS: [10.0, -5.0, 7.0].
        
        Should calculate valid normalized Graham Number since average is positive.
        Average = (10.0 + (-5.0) + 7.0) / 3 = 4.0 (positive)
        """
        # Arrange: Create financial data with mixed EPS
        eps_values = [10.0, -5.0, 7.0]
        tbvps = 15.0
        shares = 1000000.0
        total_equity = tbvps * shares
        
        financial_data = {
            'ticker': 'MIXED.US',
            'price': 40.00,
            'currency': 'USD',
            'history': {
                '2024-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[0],
                    'revenue': 1000000.0,
                    'net_income': eps_values[0] * shares
                },
                '2023-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[1],
                    'revenue': 800000.0,
                    'net_income': eps_values[1] * shares
                },
                '2022-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[2],
                    'revenue': 1100000.0,
                    'net_income': eps_values[2] * shares
                }
            }
        }
        
        # Act: Calculate normalized Graham Number
        calculator = GrahamCalculator(financial_data)
        result = calculator.compute_normalized_graham_number()
        
        # Assert: Should calculate valid result
        eps_3yr_avg = sum(eps_values) / 3  # = 4.0
        expected_normalized_gn = math.sqrt(GRAHAM_MULTIPLIER * eps_3yr_avg * tbvps)
        
        assert isinstance(result, float), \
            f"Expected float for positive average EPS, got {type(result)}"
        
        assert result == pytest.approx(expected_normalized_gn, abs=0.01), \
            f"Expected normalized GN ~{expected_normalized_gn:.2f}, got {result}"
        
        # Verify average is positive
        assert calculator.eps_3year_avg == pytest.approx(4.0, abs=0.01), \
            f"Expected 3-year average of 4.0, got {calculator.eps_3year_avg}"
        
        # Verify no warnings about negative EPS (average is positive)
        assert not any("Negative 3-year average EPS" in w for w in calculator.warnings), \
            f"Should not have negative EPS warning, got warnings: {calculator.warnings}"
    
    def test_negative_tbvps_returns_na(self):
        """
        Test that negative TBVPS returns "N/A" for normalized Graham Number.
        
        When a company has negative tangible book value (negative equity),
        the normalized Graham Number should return "N/A" just like the
        single-year Graham Number does.
        """
        # Arrange: Create financial data with negative equity
        eps_values = [5.0, 4.5, 4.0]  # Positive EPS
        shares = 1000000.0
        total_equity = -5000000.0  # Negative equity
        
        financial_data = {
            'ticker': 'NEGEQ.US',
            'price': 30.00,
            'currency': 'USD',
            'history': {
                '2024-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[0],
                    'revenue': 1000000.0,
                    'net_income': eps_values[0] * shares
                },
                '2023-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[1],
                    'revenue': 1000000.0,
                    'net_income': eps_values[1] * shares
                },
                '2022-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[2],
                    'revenue': 1000000.0,
                    'net_income': eps_values[2] * shares
                }
            }
        }
        
        # Act: Calculate normalized Graham Number
        calculator = GrahamCalculator(financial_data)
        result = calculator.compute_normalized_graham_number()
        
        # Assert: Should return "N/A" due to negative TBVPS
        assert result == "N/A", \
            f"Expected 'N/A' for negative TBVPS, got {result}"
        
        # Verify TBVPS warning was added
        assert any("Negative Tangible Book Value" in w for w in calculator.warnings), \
            f"Expected warning about negative TBVPS, got warnings: {calculator.warnings}"
    
    def test_zero_eps_average_returns_na(self):
        """
        Test that zero 3-year average EPS returns "N/A".
        
        EPS values: [1.0, -0.5, -0.5] → Average = 0.0
        """
        # Arrange: Create financial data with zero average EPS
        eps_values = [1.0, -0.5, -0.5]
        tbvps = 20.0
        shares = 1000000.0
        total_equity = tbvps * shares
        
        financial_data = {
            'ticker': 'ZERO.US',
            'price': 30.00,
            'currency': 'USD',
            'history': {
                '2024-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[0],
                    'revenue': 1000000.0,
                    'net_income': eps_values[0] * shares
                },
                '2023-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[1],
                    'revenue': 900000.0,
                    'net_income': eps_values[1] * shares
                },
                '2022-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[2],
                    'revenue': 950000.0,
                    'net_income': eps_values[2] * shares
                }
            }
        }
        
        # Act: Calculate normalized Graham Number
        calculator = GrahamCalculator(financial_data)
        result = calculator.compute_normalized_graham_number()
        
        # Assert: Should return "N/A"
        assert result == "N/A", \
            f"Expected 'N/A' for zero average EPS, got {result}"
        
        # Verify warning was added
        assert any("Negative 3-year average EPS (0.00)" in w for w in calculator.warnings), \
            f"Expected warning about zero average EPS, got warnings: {calculator.warnings}"
        
        # Verify average is stored correctly
        assert hasattr(calculator, 'eps_3year_avg'), \
            "Calculator should store eps_3year_avg even when returning N/A"
        assert calculator.eps_3year_avg == pytest.approx(0.0, abs=0.01), \
            f"Expected average of 0.0, got {calculator.eps_3year_avg}"
    
    def test_all_negative_eps_returns_na(self):
        """
        Test that all negative EPS values return "N/A".
        
        EPS values: [-2.0, -3.0, -1.5] → Average = -2.17 (negative)
        """
        # Arrange: Create financial data with all negative EPS
        eps_values = [-2.0, -3.0, -1.5]
        tbvps = 20.0
        shares = 1000000.0
        total_equity = tbvps * shares
        
        financial_data = {
            'ticker': 'LOSS.US',
            'price': 30.00,
            'currency': 'USD',
            'history': {
                '2024-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[0],
                    'revenue': 1000000.0,
                    'net_income': eps_values[0] * shares
                },
                '2023-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[1],
                    'revenue': 900000.0,
                    'net_income': eps_values[1] * shares
                },
                '2022-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[2],
                    'revenue': 950000.0,
                    'net_income': eps_values[2] * shares
                }
            }
        }
        
        # Act: Calculate normalized Graham Number
        calculator = GrahamCalculator(financial_data)
        result = calculator.compute_normalized_graham_number()
        
        # Assert: Should return "N/A"
        assert result == "N/A", \
            f"Expected 'N/A' for negative average EPS, got {result}"
        
        # Verify warning was added
        eps_3yr_avg = sum(eps_values) / 3
        assert any(f"Negative 3-year average EPS ({eps_3yr_avg:.2f})" in w for w in calculator.warnings), \
            f"Expected warning about negative average EPS, got warnings: {calculator.warnings}"
        
        assert any("unsuitable for Graham methodology" in w for w in calculator.warnings), \
            f"Expected warning about Graham methodology, got warnings: {calculator.warnings}"
    
    def test_rounding_to_2_decimals(self):
        """
        Test that normalized Graham Number is rounded to exactly 2 decimal places.
        """
        # Arrange: Create financial data that will produce non-round result
        eps_values = [3.33, 4.44, 5.55]  # Average = 4.44
        tbvps = 17.77
        shares = 1000000.0
        total_equity = tbvps * shares
        
        financial_data = {
            'ticker': 'ROUND.US',
            'price': 40.00,
            'currency': 'USD',
            'history': {
                '2024-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[0],
                    'revenue': 1000000.0,
                    'net_income': eps_values[0] * shares
                },
                '2023-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[1],
                    'revenue': 1000000.0,
                    'net_income': eps_values[1] * shares
                },
                '2022-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[2],
                    'revenue': 1000000.0,
                    'net_income': eps_values[2] * shares
                }
            }
        }
        
        # Act: Calculate normalized Graham Number
        calculator = GrahamCalculator(financial_data)
        result = calculator.compute_normalized_graham_number()
        
        # Assert: Should be rounded to 2 decimals
        assert isinstance(result, float), \
            f"Expected float, got {type(result)}"
        
        # Verify rounding by checking string representation
        result_str = f"{result:.10f}"
        decimal_part = result_str.split('.')[1]
        decimal_part_stripped = decimal_part.rstrip('0')
        
        assert len(decimal_part_stripped) <= 2, \
            f"Result should have at most 2 decimal places, got {result} ({len(decimal_part_stripped)} decimals)"
        
        # Verify that rounding to 2 decimals gives the same value
        assert result == round(result, 2), \
            f"Result should equal its 2-decimal rounded value, got {result} vs {round(result, 2)}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
