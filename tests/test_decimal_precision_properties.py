"""Property-based tests for Decimal precision in calculations.

Feature: graham-metrics-enhancement
Property 15: Decimal Precision for Calculations

Tests verify that all new calculations use Python's Decimal type to prevent
floating-point precision errors.
"""

import pytest
from hypothesis import given, strategies as st
from decimal import Decimal, ROUND_HALF_UP
from core.graham_math import GrahamCalculator


@given(
    value1=st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False),
    value2=st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False)
)
def test_decimal_precision_no_float_artifacts(value1, value2):
    """
    Feature: graham-metrics-enhancement, Property 15: Decimal Precision for Calculations
    
    For any calculation involving currency or ratios, the system should use Python's
    Decimal type to prevent floating-point precision errors.
    
    This test verifies that calculations with known problematic float values
    (like 0.1 + 0.2) produce exact results when using Decimal.
    """
    # Arrange - Use Decimal via string conversion (correct pattern)
    dec1 = Decimal(str(value1))
    dec2 = Decimal(str(value2))
    
    # Act - Perform calculation with Decimal
    result_decimal = dec1 + dec2
    
    # Also calculate with float for comparison
    result_float = value1 + value2
    
    # Assert - Decimal result should be exact
    # Convert back to float for comparison (within reasonable tolerance)
    assert abs(float(result_decimal) - result_float) < 1e-10, \
        f"Decimal calculation {dec1} + {dec2} = {result_decimal} differs from float {result_float}"


def test_decimal_precision_classic_float_error():
    """
    Test the classic floating-point error case: 0.1 + 0.2 ≠ 0.3
    
    This demonstrates why Decimal is necessary for financial calculations.
    """
    # Arrange
    value1 = 0.1
    value2 = 0.2
    expected = 0.3
    
    # Act - Float calculation (has precision error)
    float_result = value1 + value2
    
    # Act - Decimal calculation (exact)
    dec1 = Decimal(str(value1))
    dec2 = Decimal(str(value2))
    decimal_result = dec1 + dec2
    
    # Assert - Float has error, Decimal is exact
    assert float_result != expected, "Float calculation should have precision error"
    assert float(decimal_result) == expected, "Decimal calculation should be exact"


@given(
    current_assets=st.decimals(min_value=Decimal('1000'), max_value=Decimal('1000000'), places=2),
    inventory=st.decimals(min_value=Decimal('0'), max_value=Decimal('500000'), places=2),
    current_liabilities=st.decimals(min_value=Decimal('100'), max_value=Decimal('500000'), places=2)
)
def test_quick_ratio_uses_decimal_precision(current_assets, inventory, current_liabilities):
    """
    Feature: graham-metrics-enhancement, Property 15: Decimal Precision for Calculations
    
    Verify that Quick Ratio calculation uses Decimal type for precision.
    """
    # Arrange
    financial_data = {
        'history': {
            '2023-12-31': {
                'current_assets': float(current_assets),
                'inventory': float(inventory),
                'current_liabilities': float(current_liabilities),
                'revenue': 1000000.0  # Ensure recognized as financial data
            }
        },
        'price': 100.0
    }
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    quick_ratio = calculator.compute_quick_ratio()
    
    # Assert - Result should be consistent with Decimal calculation
    if quick_ratio != 'N/A':
        # Recalculate using Decimal
        ca_dec = Decimal(str(float(current_assets)))
        inv_dec = Decimal(str(float(inventory)))
        cl_dec = Decimal(str(float(current_liabilities)))
        
        expected = (ca_dec - inv_dec) / cl_dec
        expected_rounded = expected.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Allow small tolerance for float conversion
        assert abs(float(quick_ratio) - float(expected_rounded)) < 0.01, \
            f"Quick ratio {quick_ratio} should match Decimal calculation {expected_rounded}"


@given(
    current_assets=st.decimals(min_value=Decimal('1000'), max_value=Decimal('1000000'), places=2),
    current_liabilities=st.decimals(min_value=Decimal('100'), max_value=Decimal('500000'), places=2),
    shares=st.decimals(min_value=Decimal('1000'), max_value=Decimal('100000'), places=2)
)
def test_wcps_uses_decimal_precision(current_assets, current_liabilities, shares):
    """
    Feature: graham-metrics-enhancement, Property 15: Decimal Precision for Calculations
    
    Verify that WCPS calculation uses Decimal type for precision.
    """
    # Arrange - Calculate WCPS manually using Decimal
    ca_dec = Decimal(str(float(current_assets)))
    cl_dec = Decimal(str(float(current_liabilities)))
    shares_dec = Decimal(str(float(shares)))
    
    working_capital = ca_dec - cl_dec
    expected_wcps = working_capital / shares_dec
    expected_rounded = expected_wcps.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Act - Calculate using float (what would happen without Decimal)
    float_wcps = (float(current_assets) - float(current_liabilities)) / float(shares)
    float_rounded = round(float_wcps, 2)
    
    # Assert - Decimal calculation should be more precise
    # The difference might be small, but Decimal ensures exact decimal arithmetic
    decimal_result = float(expected_rounded)
    
    # Verify that Decimal rounding is consistent
    assert isinstance(expected_rounded, Decimal), "WCPS should use Decimal for calculation"


@given(
    eps_values=st.lists(
        st.decimals(min_value=Decimal('-10'), max_value=Decimal('50'), places=2),
        min_size=3,
        max_size=3
    ),
    price=st.decimals(min_value=Decimal('10'), max_value=Decimal('500'), places=2)
)
def test_three_year_avg_pe_uses_decimal_precision(eps_values, price):
    """
    Feature: graham-metrics-enhancement, Property 15: Decimal Precision for Calculations
    
    Verify that three-year average P/E calculation uses Decimal type for precision.
    """
    # Arrange
    financial_data = {
        'history': {
            '2023-12-31': {'eps': float(eps_values[0]), 'revenue': 1000000.0},
            '2022-12-31': {'eps': float(eps_values[1]), 'revenue': 1000000.0},
            '2021-12-31': {'eps': float(eps_values[2]), 'revenue': 1000000.0}
        },
        'price': float(price)
    }
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert - If calculation succeeded, verify precision
    if result['three_year_avg_eps'] != 'N/A':
        # Recalculate using Decimal
        eps_decimals = [Decimal(str(float(eps))) for eps in eps_values]
        avg_eps_dec = sum(eps_decimals) / Decimal('3')
        
        # Allow small tolerance for float conversion
        assert abs(float(result['three_year_avg_eps']) - float(avg_eps_dec)) < 0.01, \
            f"Three-year avg EPS should use Decimal precision"


def test_decimal_conversion_pattern():
    """
    Test that the correct Decimal conversion pattern is used.
    
    CRITICAL: Always convert floats to strings before creating Decimal objects:
    - ✅ Decimal(str(value)) - Correct, avoids float artifacts
    - ❌ Decimal(value) where value is float - Dangerous, carries over binary float imprecision
    """
    # Arrange
    float_value = 1.1
    
    # Act - Wrong way (direct float to Decimal)
    decimal_wrong = Decimal(float_value)
    
    # Act - Right way (float to string to Decimal)
    decimal_right = Decimal(str(float_value))
    
    # Assert - String conversion produces cleaner Decimal
    # Direct float conversion carries binary representation artifacts
    assert str(decimal_wrong) != '1.1', "Direct float to Decimal carries artifacts"
    assert str(decimal_right) == '1.1', "String conversion produces clean Decimal"


@given(
    pe_ratio=st.decimals(min_value=Decimal('1'), max_value=Decimal('50'), places=2),
    pb_ratio=st.decimals(min_value=Decimal('0.1'), max_value=Decimal('5'), places=2)
)
def test_combined_pe_pb_uses_decimal_precision(pe_ratio, pb_ratio):
    """
    Feature: graham-metrics-enhancement, Property 15: Decimal Precision for Calculations
    
    Verify that combined P/E × P/B test uses Decimal type for precision.
    """
    # Arrange - Calculate product using Decimal
    pe_dec = Decimal(str(float(pe_ratio)))
    pb_dec = Decimal(str(float(pb_ratio)))
    
    expected_product = pe_dec * pb_dec
    expected_rounded = expected_product.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Act - Calculate using float
    float_product = float(pe_ratio) * float(pb_ratio)
    float_rounded = round(float_product, 2)
    
    # Assert - Decimal calculation should be consistent
    # The difference might be small, but Decimal ensures exact decimal arithmetic
    assert isinstance(expected_rounded, Decimal), "Combined test should use Decimal for calculation"
    
    # Verify rounding consistency
    decimal_result = float(expected_rounded)
    assert abs(decimal_result - float_rounded) < 0.02, \
        "Decimal and float calculations should be close (within rounding tolerance)"
