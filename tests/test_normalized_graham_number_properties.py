"""
Property-based tests for normalized Graham Number using Hypothesis.

Tests universal properties for compute_normalized_graham_number() function
used in normalized Margin of Safety calculations.

Each test runs 100+ iterations with randomly generated data to verify correctness
across all valid inputs and edge cases.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
import math
from core.graham_math import GrahamCalculator
from config.graham_constants import GRAHAM_MULTIPLIER


# Feature: normalized-margin-of-safety, Property 1: Formula Correctness
# Validates: Requirements 1.1, 1.2
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    # Generate 3 positive EPS values
    eps_values=st.lists(
        st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False),
        min_size=3,
        max_size=3
    ),
    # Generate positive TBVPS
    tbvps=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_normalized_graham_number_formula_correctness(eps_values, tbvps):
    """
    Property 1: Formula Correctness
    
    For any financial history with 3 valid years of positive EPS data and positive TBVPS,
    the normalized Graham Number should equal √(22.5 × EPS_3yr_avg × TBVPS).
    
    **Validates: Requirements 1.1, 1.2**
    """
    # Arrange: Create financial data with 3 years of positive EPS
    # We need to reverse-engineer equity from TBVPS
    shares = 1000000.0  # Fixed shares for simplicity
    total_equity = tbvps * shares
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
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
    
    # Assert: Verify formula correctness
    # Calculate expected value: √(22.5 × EPS_3yr_avg × TBVPS)
    eps_3yr_avg = sum(eps_values) / 3
    expected_normalized_gn = math.sqrt(GRAHAM_MULTIPLIER * eps_3yr_avg * tbvps)
    
    assert isinstance(result, float), f"Expected float, got {type(result)}"
    
    # Result is rounded to 2 decimals, so tolerance should account for rounding
    assert abs(result - expected_normalized_gn) < 0.01, \
        f"Normalized Graham Number mismatch: expected ~{round(expected_normalized_gn, 2)}, got {result}"
    
    # Verify the result is properly rounded to 2 decimals
    assert result == round(result, 2), \
        f"Result should be rounded to 2 decimals, got {result}"


# Feature: normalized-margin-of-safety, Property 2: Negative/Zero Rejection
# Validates: Requirements 1.3, 5.1, 5.2, 5.3
@settings(max_examples=100)
@given(
    # Generate 3 EPS values where the average will be <= 0
    eps_values=st.lists(
        st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        min_size=3,
        max_size=3
    ).filter(lambda x: sum(x) / 3 <= 0),  # Ensure average is <= 0
    # Generate positive TBVPS
    tbvps=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_normalized_graham_number_negative_zero_rejection(eps_values, tbvps):
    """
    Property 2: Negative or Zero Average EPS Rejection
    
    For any financial history where the 3-year average EPS is ≤ 0, the normalized
    Graham Number should return "N/A" and include a warning explaining the company
    is unsuitable for Graham methodology.
    
    **Validates: Requirements 1.3, 5.1, 5.2, 5.3**
    """
    # Arrange: Create financial data with EPS values that average to <= 0
    shares = 1000000.0
    total_equity = tbvps * shares
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
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
    
    # Assert: Should return "N/A"
    assert result == "N/A", \
        f"Expected 'N/A' for negative/zero average EPS, got {result}"
    
    # Verify warning was added
    eps_3yr_avg = sum(eps_values) / 3
    assert any(f"Negative 3-year average EPS ({eps_3yr_avg:.2f})" in w for w in calculator.warnings), \
        f"Expected warning about negative 3-year average EPS, got warnings: {calculator.warnings}"
    
    assert any("unsuitable for Graham methodology" in w for w in calculator.warnings), \
        f"Expected warning about Graham methodology, got warnings: {calculator.warnings}"


# Feature: normalized-margin-of-safety, Property 3: Insufficient Data
# Validates: Requirements 1.4, 4.1, 4.2
@settings(max_examples=100)
@given(
    # Generate 0-2 years of data
    num_years=st.integers(min_value=0, max_value=2),
    # Generate positive EPS values
    eps_values=st.lists(
        st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False),
        min_size=0,
        max_size=2
    ),
    # Generate positive TBVPS
    tbvps=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_normalized_graham_number_insufficient_data(num_years, eps_values, tbvps):
    """
    Property 3: Insufficient Data Handling
    
    For any financial history with fewer than 3 years of EPS data, the normalized
    Graham Number should return "N/A" and include a warning explaining insufficient data.
    
    **Validates: Requirements 1.4, 4.1, 4.2**
    """
    # Ensure we have the right number of EPS values
    assume(len(eps_values) == num_years)
    
    # Arrange: Create financial data with fewer than 3 years
    shares = 1000000.0
    total_equity = tbvps * shares
    
    history = {}
    for i in range(num_years):
        year = f"{2024 - i}-12-31"
        history[year] = {
            'total_equity': total_equity,
            'intangible_assets': 0.0,
            'goodwill': 0.0,
            'shares_outstanding': shares,
            'eps': eps_values[i],
            'revenue': 1000000.0,
            'net_income': eps_values[i] * shares
        }
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
        'currency': 'USD',
        'history': history
    }
    
    # Act: Calculate normalized Graham Number
    calculator = GrahamCalculator(financial_data)
    result = calculator.compute_normalized_graham_number()
    
    # Assert: Should return "N/A"
    assert result == "N/A", \
        f"Expected 'N/A' for {num_years} years of data, got {result}"
    
    # Verify warning was added (only for cases with 1-2 years)
    # When num_years=0, TBVPS returns "N/A" first, so no warning is added
    # When num_years=1-2, TBVPS is valid but insufficient EPS data triggers warning
    if num_years > 0:
        # Insufficient years case (1 or 2 years)
        assert any("Insufficient data" in w or ("Only" in w and "years available" in w) for w in calculator.warnings), \
            f"Expected warning about insufficient data for {num_years} years, got warnings: {calculator.warnings}"


# Feature: normalized-margin-of-safety, Property 4: Decimal Precision
# Validates: Requirements 1.5
@settings(max_examples=100)
@given(
    # Generate 3 positive EPS values with many decimal places
    eps_values=st.lists(
        st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False),
        min_size=3,
        max_size=3
    ),
    # Generate positive TBVPS with many decimal places
    tbvps=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_normalized_graham_number_decimal_precision(eps_values, tbvps):
    """
    Property 4: Decimal Precision Consistency
    
    For any valid normalized Graham Number calculation, the result should be
    rounded to exactly 2 decimal places.
    
    **Validates: Requirements 1.5**
    """
    # Arrange: Create financial data with 3 years of positive EPS
    shares = 1000000.0
    total_equity = tbvps * shares
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
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
    
    # Assert: Should be a float (not "N/A")
    assert isinstance(result, float), \
        f"Expected float for positive EPS values, got {type(result)}"
    
    # Verify the result is rounded to exactly 2 decimal places
    # Check by converting to string and counting decimal places
    result_str = f"{result:.10f}"  # Format with many decimals
    decimal_part = result_str.split('.')[1]
    
    # Remove trailing zeros to find actual precision
    decimal_part_stripped = decimal_part.rstrip('0')
    
    assert len(decimal_part_stripped) <= 2, \
        f"Result should have at most 2 decimal places, got {result} ({len(decimal_part_stripped)} decimals)"
    
    # Verify that rounding to 2 decimals gives the same value
    assert result == round(result, 2), \
        f"Result should equal its 2-decimal rounded value, got {result} vs {round(result, 2)}"


# Feature: normalized-margin-of-safety, Property 4 (Unrounded): Unrounded Result Option
# Validates: Requirements 1.5
@settings(max_examples=100)
@given(
    # Generate 3 positive EPS values
    eps_values=st.lists(
        st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False),
        min_size=3,
        max_size=3
    ),
    # Generate positive TBVPS
    tbvps=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_normalized_graham_number_unrounded_option(eps_values, tbvps):
    """
    Property 4 (Unrounded): Unrounded Result Option
    
    For any valid normalized Graham Number calculation with round_result=False,
    the result should be the raw unrounded value for calculation accuracy.
    
    **Validates: Requirements 1.5**
    """
    # Arrange: Create financial data with 3 years of positive EPS
    shares = 1000000.0
    total_equity = tbvps * shares
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
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
    
    # Act: Calculate normalized Graham Number with and without rounding
    calculator = GrahamCalculator(financial_data)
    result_rounded = calculator.compute_normalized_graham_number(round_result=True)
    result_unrounded = calculator.compute_normalized_graham_number(round_result=False)
    
    # Assert: Both should be floats
    assert isinstance(result_rounded, float), \
        f"Expected float for rounded result, got {type(result_rounded)}"
    assert isinstance(result_unrounded, float), \
        f"Expected float for unrounded result, got {type(result_unrounded)}"
    
    # Verify rounded result equals round(unrounded, 2)
    assert result_rounded == round(result_unrounded, 2), \
        f"Rounded result ({result_rounded}) should equal round(unrounded, 2) ({round(result_unrounded, 2)})"
    
    # Verify unrounded result matches the exact formula
    eps_3yr_avg = sum(eps_values) / 3
    expected_unrounded = math.sqrt(GRAHAM_MULTIPLIER * eps_3yr_avg * tbvps)
    
    assert abs(result_unrounded - expected_unrounded) < 1e-10, \
        f"Unrounded result mismatch: expected {expected_unrounded}, got {result_unrounded}"


# Feature: normalized-margin-of-safety, Property 1 (Audit Trail): EPS Values Stored
# Validates: Requirements 8.1, 8.5
@settings(max_examples=100)
@given(
    # Generate 3 positive EPS values
    eps_values=st.lists(
        st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False),
        min_size=3,
        max_size=3
    ),
    # Generate positive TBVPS
    tbvps=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_normalized_graham_number_audit_trail(eps_values, tbvps):
    """
    Property 1 (Audit Trail): EPS Values Stored
    
    For any normalized Graham Number calculation (whether successful or failed),
    the system should store the 3 individual EPS values and their corresponding
    years for audit trail purposes.
    
    **Validates: Requirements 8.1, 8.5**
    """
    # Arrange: Create financial data with 3 years of positive EPS
    shares = 1000000.0
    total_equity = tbvps * shares
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
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
    
    # Assert: Verify audit trail is stored
    assert hasattr(calculator, 'eps_3year_values'), \
        "Calculator should store eps_3year_values for audit trail"
    
    assert hasattr(calculator, 'eps_3year_years'), \
        "Calculator should store eps_3year_years for audit trail"
    
    assert hasattr(calculator, 'eps_3year_avg'), \
        "Calculator should store eps_3year_avg for audit trail"
    
    # Verify the stored values match the input
    assert calculator.eps_3year_values == eps_values, \
        f"Stored EPS values {calculator.eps_3year_values} should match input {eps_values}"
    
    assert calculator.eps_3year_years == ['2024-12-31', '2023-12-31', '2022-12-31'], \
        f"Stored years should be ['2024-12-31', '2023-12-31', '2022-12-31'], got {calculator.eps_3year_years}"
    
    # Verify the stored average matches the calculation
    expected_avg = sum(eps_values) / 3
    assert abs(calculator.eps_3year_avg - expected_avg) < 1e-10, \
        f"Stored average {calculator.eps_3year_avg} should match calculated {expected_avg}"


# Feature: normalized-margin-of-safety, Property 2 (Mixed EPS): Mixed Positive/Negative EPS
# Validates: Requirements 5.4
@settings(max_examples=100)
@given(
    # Generate 3 EPS values with at least one positive and one negative
    eps_1=st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False),
    eps_2=st.floats(min_value=-1000.0, max_value=-0.01, allow_nan=False, allow_infinity=False),
    eps_3=st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    # Generate positive TBVPS
    tbvps=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_normalized_graham_number_mixed_eps(eps_1, eps_2, eps_3, tbvps):
    """
    Property 2 (Mixed EPS): Mixed Positive/Negative EPS
    
    For any financial history with mixed positive and negative EPS values,
    the system should compute the arithmetic mean correctly, handling both
    positive and negative values.
    
    **Validates: Requirements 5.4**
    """
    eps_values = [eps_1, eps_2, eps_3]
    
    # Arrange: Create financial data with mixed EPS values
    shares = 1000000.0
    total_equity = tbvps * shares
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
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
    
    # Assert: Verify behavior based on average
    eps_3yr_avg = sum(eps_values) / 3
    
    if eps_3yr_avg > 0:
        # Should calculate normalized Graham Number
        assert isinstance(result, float), \
            f"Expected float for positive average ({eps_3yr_avg:.2f}), got {type(result)}"
        
        expected_normalized_gn = math.sqrt(GRAHAM_MULTIPLIER * eps_3yr_avg * tbvps)
        assert abs(result - expected_normalized_gn) < 0.01, \
            f"Normalized Graham Number mismatch: expected ~{round(expected_normalized_gn, 2)}, got {result}"
    else:
        # Should return "N/A"
        assert result == "N/A", \
            f"Expected 'N/A' for non-positive average ({eps_3yr_avg:.2f}), got {result}"
        
        assert any("Negative 3-year average EPS" in w for w in calculator.warnings), \
            f"Expected warning about negative average, got warnings: {calculator.warnings}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


# Feature: normalized-margin-of-safety, Property 10: Dual Calculation Preservation
# Validates: Requirements 3.1, 3.2
@settings(max_examples=100)
@given(
    # Generate 3 positive EPS values
    eps_values=st.lists(
        st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False),
        min_size=3,
        max_size=3
    ),
    # Generate positive TBVPS
    tbvps=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_dual_calculation_preservation(eps_values, tbvps):
    """
    Property 10: Dual Calculation Preservation
    
    For any financial data, the system should calculate and store both the legacy
    single-year Graham Number and the new normalized Graham Number as separate fields,
    ensuring both are available in the output.
    
    **Validates: Requirements 3.1, 3.2, 3.3**
    """
    # Arrange: Create financial data with 3 years of positive EPS
    shares = 1000000.0
    total_equity = tbvps * shares
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
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
    
    # Act: Calculate all metrics
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    
    # Assert: Verify both Graham Numbers are calculated and stored
    assert 'graham_number' in metrics, \
        "Legacy single-year Graham Number should be in metrics"
    
    assert 'normalized_graham_number' in metrics, \
        "Normalized 3-year average Graham Number should be in metrics"
    
    # Verify both are numeric (not "N/A") for positive EPS values
    assert isinstance(metrics['graham_number'], float), \
        f"Expected float for graham_number, got {type(metrics['graham_number'])}"
    
    assert isinstance(metrics['normalized_graham_number'], float), \
        f"Expected float for normalized_graham_number, got {type(metrics['normalized_graham_number'])}"
    
    # Verify single-year Graham Number uses most recent EPS
    expected_single_gn = math.sqrt(GRAHAM_MULTIPLIER * eps_values[0] * tbvps)
    assert abs(metrics['graham_number'] - expected_single_gn) < 0.01, \
        f"Single-year Graham Number should use most recent EPS: expected ~{round(expected_single_gn, 2)}, got {metrics['graham_number']}"
    
    # Verify normalized Graham Number uses 3-year average EPS
    eps_3yr_avg = sum(eps_values) / 3
    expected_normalized_gn = math.sqrt(GRAHAM_MULTIPLIER * eps_3yr_avg * tbvps)
    assert abs(metrics['normalized_graham_number'] - expected_normalized_gn) < 0.01, \
        f"Normalized Graham Number should use 3-year average EPS: expected ~{round(expected_normalized_gn, 2)}, got {metrics['normalized_graham_number']}"
    
    # Verify they are different (unless the average equals the most recent value)
    # Note: Even with varying EPS values, the average can equal the most recent value
    # Example: [467, 1, 933] has average 467 which equals the most recent value
    if abs(eps_values[0] - eps_3yr_avg) > 0.01:
        # Allow small tolerance for rounding
        assert abs(metrics['graham_number'] - metrics['normalized_graham_number']) > 0.01, \
            f"Graham Numbers should differ when most recent EPS differs from average: single={metrics['graham_number']}, normalized={metrics['normalized_graham_number']}"
    
    # Verify margin_of_safety_details includes both values
    assert 'margin_of_safety_details' in metrics, \
        "Margin of Safety details should be in metrics"
    
    mos_details = metrics['margin_of_safety_details']
    assert 'normalized_graham_number' in mos_details, \
        "MoS details should include normalized_graham_number"
    
    assert mos_details['normalized_graham_number'] == metrics['normalized_graham_number'], \
        "MoS details normalized_graham_number should match metrics normalized_graham_number"
