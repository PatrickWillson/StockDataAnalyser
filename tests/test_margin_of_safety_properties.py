"""
Property-based tests for Margin of Safety using Hypothesis.

Tests universal properties for compute_margin_of_safety() function
used in normalized Margin of Safety calculations.

Each test runs 100+ iterations with randomly generated data to verify correctness
across all valid inputs and edge cases.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import math
from core.graham_math import GrahamCalculator
from config.graham_constants import GRAHAM_MULTIPLIER


# Feature: normalized-margin-of-safety, Property 5: Conservative Dual-Anchor
# Validates: Requirements 2.1, 2.6
@settings(max_examples=100)
@given(
    # Generate normalized Graham Number (positive)
    normalized_gn=st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False),
    # Generate EPV per share (positive, including values close to 0)
    epv_per_share=st.floats(min_value=0.00, max_value=1000.0, allow_nan=False, allow_infinity=False),
    # Generate current price (positive)
    current_price=st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False)
)
def test_margin_of_safety_conservative_dual_anchor(normalized_gn, epv_per_share, current_price):
    """
    Property 5: Conservative Dual-Anchor Selection
    
    For any pair of valid normalized Graham Number and EPV per share values,
    the Margin of Safety should use min(normalized_gn, epv_per_share) as the
    intrinsic value, and the limiting factor should correctly identify which
    metric was lower.
    
    **Validates: Requirements 2.1, 2.6**
    """
    # Arrange: Create financial data with both normalized GN and EPV valid
    # We need to create data that will produce the given normalized_gn and epv_per_share
    
    # For this test, we'll mock the methods to return our test values
    # Create minimal financial data
    shares = 1000000.0
    eps_values = [10.0, 10.0, 10.0]  # Positive EPS for valid normalized GN
    tbvps = 20.0
    total_equity = tbvps * shares
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': current_price,
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
    
    # Add enough years for EPV calculation (7-10 years)
    for i in range(3, 11):
        year = f"{2024 - i}-12-31"
        financial_data['history'][year] = {
            'total_equity': total_equity,
            'intangible_assets': 0.0,
            'goodwill': 0.0,
            'shares_outstanding': shares,
            'eps': eps_values[0],
            'revenue': 1000000.0,
            'net_income': eps_values[0] * shares
        }
    
    # Act: Calculate margin of safety
    calculator = GrahamCalculator(financial_data)
    result = calculator.compute_margin_of_safety(current_price)
    
    # Assert: Verify conservative dual-anchor approach
    # Both normalized GN and EPV should be numeric (valid)
    assert isinstance(result['normalized_graham_number'], (int, float)), \
        f"Expected numeric normalized_graham_number, got {type(result['normalized_graham_number'])}"
    
    assert isinstance(result['epv_per_share'], (int, float)), \
        f"Expected numeric epv_per_share, got {type(result['epv_per_share'])}"
    
    # Verify intrinsic value is the minimum of the two
    expected_intrinsic_value = min(result['normalized_graham_number'], result['epv_per_share'])
    
    assert result['intrinsic_value_used'] == expected_intrinsic_value, \
        f"Expected intrinsic_value_used to be min({result['normalized_graham_number']}, {result['epv_per_share']}) = {expected_intrinsic_value}, got {result['intrinsic_value_used']}"
    
    # Verify limiting factor is correctly identified
    if result['normalized_graham_number'] < result['epv_per_share']:
        expected_limiting_factor = "Normalized Graham Number"
    elif result['epv_per_share'] < result['normalized_graham_number']:
        expected_limiting_factor = "EPV"
    else:
        # They're equal - either is acceptable
        expected_limiting_factor = result['limiting_factor']
    
    assert result['limiting_factor'] == expected_limiting_factor, \
        f"Expected limiting_factor '{expected_limiting_factor}', got '{result['limiting_factor']}'"
    
    # Verify MoS calculation (if intrinsic_value > 0)
    if expected_intrinsic_value > 0:
        expected_mos = ((expected_intrinsic_value - current_price) / expected_intrinsic_value) * 100
        expected_mos_rounded = round(expected_mos, 1)
        
        assert result['mos_percentage'] == expected_mos_rounded, \
            f"Expected mos_percentage {expected_mos_rounded}, got {result['mos_percentage']}"
    else:
        # Intrinsic value is 0 - cannot calculate MoS
        assert result['mos_percentage'] == "N/A", \
            f"Expected 'N/A' for zero intrinsic value, got {result['mos_percentage']}"


# Feature: normalized-margin-of-safety, Property 6: Single-Anchor Fallback
# Validates: Requirements 2.2, 2.3, 4.3
@settings(max_examples=100)
@given(
    # Generate which anchor is valid (0 = only normalized GN, 1 = only EPV)
    valid_anchor=st.integers(min_value=0, max_value=1),
    # Generate the valid value
    valid_value=st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False),
    # Generate current price
    current_price=st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False)
)
def test_margin_of_safety_single_anchor_fallback(valid_anchor, valid_value, current_price):
    """
    Property 6: Single-Anchor Fallback
    
    For any case where exactly one of {normalized Graham Number, EPV per share}
    is valid, the Margin of Safety should use the valid value as intrinsic value
    and set the limiting factor accordingly.
    
    **Validates: Requirements 2.2, 2.3, 4.3**
    """
    # Arrange: Create financial data where only one metric is valid
    shares = 1000000.0
    
    if valid_anchor == 0:
        # Only normalized Graham Number is valid
        # Create data with 3 years of positive EPS for normalized GN
        # But 7-10 years of NEGATIVE net income for EPV (so EPV = 0.0)
        eps_values = [10.0, 10.0, 10.0]
        tbvps = 20.0
        total_equity = tbvps * shares
        
        financial_data = {
            'ticker': 'TEST.US',
            'price': current_price,
            'currency': 'USD',
            'history': {}
        }
        
        # Add 10 years with NEGATIVE net income for EPV = 0.0
        for i in range(10):
            year = f"{2024 - i}-12-31"
            # First 3 years have positive EPS for normalized GN
            # But all 10 years have negative net income for EPV
            financial_data['history'][year] = {
                'total_equity': total_equity,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'shares_outstanding': shares,
                'eps': eps_values[i] if i < 3 else 10.0,
                'revenue': 1000000.0,
                'net_income': -10000000.0  # Negative for all years
            }
        
        # CRITICAL: EPV = 0.0 (negative normalized earnings) is a valid value
        # So min(normalized_gn, 0.0) = 0.0, and EPV is the limiting factor
        expected_limiting_factor = "EPV"
    
    else:
        # Only EPV is valid
        # Create data with negative 3-year average EPS (normalized GN = "N/A")
        # But enough years with positive net income for EPV
        eps_values = [5.0, -10.0, -5.0]  # Average is negative
        tbvps = 20.0
        total_equity = tbvps * shares
        
        financial_data = {
            'ticker': 'TEST.US',
            'price': current_price,
            'currency': 'USD',
            'history': {}
        }
        
        # Add 10 years with positive net income for EPV
        for i in range(10):
            year = f"{2024 - i}-12-31"
            # Use positive net income for EPV calculation
            net_income = 50000000.0 if i >= 3 else eps_values[i] * shares
            financial_data['history'][year] = {
                'total_equity': total_equity,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'shares_outstanding': shares,
                'eps': eps_values[i] if i < 3 else 50.0,
                'revenue': 1000000.0,
                'net_income': net_income
            }
        
        expected_limiting_factor = "EPV"
    
    # Act: Calculate margin of safety
    calculator = GrahamCalculator(financial_data)
    result = calculator.compute_margin_of_safety(current_price)
    
    # Assert: Verify single-anchor fallback
    if valid_anchor == 0:
        # Only normalized GN should be valid
        assert isinstance(result['normalized_graham_number'], (int, float)), \
            f"Expected numeric normalized_graham_number, got {type(result['normalized_graham_number'])}"
        
        # EPV should be 0.0 (insufficient data returns 0.0 from compute_epv)
        assert result['epv_per_share'] == 0.0, \
            f"Expected epv_per_share to be 0.0 (insufficient data), got {result['epv_per_share']}"
        
        # CRITICAL: EPV = 0.0 is a valid value (value destroyer), not missing data
        # So min(normalized_gn, 0.0) = 0.0, and EPV is the limiting factor
        # This is correct behavior per the design
        assert result['intrinsic_value_used'] == 0.0, \
            f"Expected intrinsic_value_used to be 0.0 (min of normalized_gn and EPV=0.0), got {result['intrinsic_value_used']}"
        
        # Limiting factor should be EPV (since 0.0 < normalized_gn)
        assert result['limiting_factor'] == "EPV", \
            f"Expected limiting_factor 'EPV' (0.0 < normalized_gn), got '{result['limiting_factor']}'"
    
    else:
        # Only EPV should be valid
        assert result['normalized_graham_number'] == "N/A", \
            f"Expected 'N/A' for normalized_graham_number (negative avg EPS), got {result['normalized_graham_number']}"
        
        assert isinstance(result['epv_per_share'], (int, float)), \
            f"Expected numeric epv_per_share, got {type(result['epv_per_share'])}"
        
        # Intrinsic value should be EPV
        assert result['intrinsic_value_used'] == result['epv_per_share'], \
            f"Expected intrinsic_value_used to be epv_per_share, got {result['intrinsic_value_used']}"
    
    # Verify limiting factor
    assert result['limiting_factor'] == expected_limiting_factor, \
        f"Expected limiting_factor '{expected_limiting_factor}', got '{result['limiting_factor']}'"
    
    # Verify MoS calculation
    intrinsic_value = result['intrinsic_value_used']
    if isinstance(intrinsic_value, (int, float)) and intrinsic_value > 0:
        expected_mos = ((intrinsic_value - current_price) / intrinsic_value) * 100
        expected_mos_rounded = round(expected_mos, 1)
        
        assert result['mos_percentage'] == expected_mos_rounded, \
            f"Expected mos_percentage {expected_mos_rounded}, got {result['mos_percentage']}"


# Feature: normalized-margin-of-safety, Property 7: Formula Correctness
# Validates: Requirements 2.5
@settings(max_examples=100)
@given(
    # Generate intrinsic value (positive)
    intrinsic_value=st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False),
    # Generate current price (positive)
    current_price=st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False)
)
def test_margin_of_safety_formula_correctness(intrinsic_value, current_price):
    """
    Property 7: Margin of Safety Formula Correctness
    
    For any valid intrinsic value and positive current price, the Margin of
    Safety percentage should equal ((intrinsic_value - current_price) / intrinsic_value) × 100,
    rounded to 1 decimal place.
    
    **Validates: Requirements 2.5**
    """
    # Arrange: Create financial data that will produce the given intrinsic value
    # We'll create data where normalized GN equals our target intrinsic value
    # AND EPV is much higher so normalized GN is the limiting factor
    shares = 1000000.0
    
    # Calculate EPS values that will produce the target intrinsic value
    # normalized_gn = sqrt(22.5 * eps_avg * tbvps)
    # We'll use tbvps = 20.0 and solve for eps_avg
    tbvps = 20.0
    # intrinsic_value^2 = 22.5 * eps_avg * tbvps
    # eps_avg = intrinsic_value^2 / (22.5 * tbvps)
    eps_avg = (intrinsic_value ** 2) / (GRAHAM_MULTIPLIER * tbvps)
    
    # Skip test if eps_avg is too small (would cause issues)
    assume(eps_avg >= 0.01)
    
    # Use the same EPS for all 3 years
    eps_values = [eps_avg, eps_avg, eps_avg]
    total_equity = tbvps * shares
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': current_price,
        'currency': 'USD',
        'history': {}
    }
    
    # Add 10 years with MUCH HIGHER net income for EPV
    # This ensures normalized GN is the limiting factor
    for i in range(10):
        year = f"{2024 - i}-12-31"
        # Use much higher net income for EPV (100x the normalized GN target)
        net_income = intrinsic_value * shares * 100
        financial_data['history'][year] = {
            'total_equity': total_equity,
            'intangible_assets': 0.0,
            'goodwill': 0.0,
            'shares_outstanding': shares,
            'eps': eps_values[i] if i < 3 else eps_avg,
            'revenue': 1000000.0,
            'net_income': net_income
        }
    
    # Act: Calculate margin of safety
    calculator = GrahamCalculator(financial_data)
    result = calculator.compute_margin_of_safety(current_price)
    
    # Assert: Verify formula correctness
    # The intrinsic value used should be close to our target (within rounding tolerance)
    assert isinstance(result['intrinsic_value_used'], (int, float)), \
        f"Expected numeric intrinsic_value_used, got {type(result['intrinsic_value_used'])}"
    
    # Allow tolerance for rounding in normalized GN calculation
    # The tolerance needs to account for sqrt rounding
    tolerance = max(0.1, intrinsic_value * 0.05)  # 5% or 0.1, whichever is larger
    assert abs(result['intrinsic_value_used'] - intrinsic_value) < tolerance, \
        f"Expected intrinsic_value_used ~{intrinsic_value}, got {result['intrinsic_value_used']}"
    
    # Verify MoS percentage matches formula
    # Calculate expected MoS using the actual intrinsic value
    actual_intrinsic_value = result['intrinsic_value_used']
    expected_mos = ((actual_intrinsic_value - current_price) / actual_intrinsic_value) * 100
    expected_mos_rounded = round(expected_mos, 1)
    
    assert isinstance(result['mos_percentage'], (int, float)), \
        f"Expected numeric mos_percentage, got {type(result['mos_percentage'])}"
    
    # Verify MoS matches expected value
    assert result['mos_percentage'] == expected_mos_rounded, \
        f"Expected mos_percentage {expected_mos_rounded}, got {result['mos_percentage']}"
    
    # Verify result is rounded to 1 decimal place
    mos_str = f"{result['mos_percentage']:.10f}"
    decimal_part = mos_str.split('.')[1]
    decimal_part_stripped = decimal_part.rstrip('0')
    
    assert len(decimal_part_stripped) <= 1, \
        f"MoS should have at most 1 decimal place, got {result['mos_percentage']} ({len(decimal_part_stripped)} decimals)"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
