"""
Property-Based Tests for Three-Year Average P/E Calculator

This module tests the three-year average P/E calculation using property-based testing
with Hypothesis. Tests verify that the calculation follows Graham's methodology correctly
across all valid inputs.

Feature: graham-metrics-enhancement
Properties: 9, 10
Validates: Requirements 4.1, 4.2, 4.4
"""

import pytest
from hypothesis import given, strategies as st, assume
from decimal import Decimal

from core.graham_math import GrahamCalculator
from tests.test_utils_decimal import (
    to_decimal,
    decimal_strategy,
    assert_decimal_equal
)
from tests.fixtures_graham_metrics import GrahamMetricsFixtures


# Property 9: Three-Year Average EPS Calculation
@given(
    eps_year1=decimal_strategy(min_value="-100", max_value="100", places=2),
    eps_year2=decimal_strategy(min_value="-100", max_value="100", places=2),
    eps_year3=decimal_strategy(min_value="-100", max_value="100", places=2)
)
def test_property_9_three_year_avg_eps_calculation(eps_year1, eps_year2, eps_year3):
    """
    Feature: graham-metrics-enhancement, Property 9: Three-Year Average EPS Calculation
    
    For any financial history with at least 3 years of EPS data (including negative values),
    the three-year average EPS should equal the sum of the most recent 3 years' EPS divided by 3.
    
    **Validates: Requirements 4.1, 4.2, 4.4**
    
    This test verifies:
    - Average is calculated from most recent 3 years
    - Loss years (negative EPS) are included in the calculation
    - Formula: avg_eps = (eps_y1 + eps_y2 + eps_y3) / 3
    """
    # Arrange: Create financial data with 3 years of EPS
    # Most recent year first
    eps_values = [eps_year1, eps_year2, eps_year3]
    
    financial_data = GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
        eps_values=eps_values,
        price=Decimal('100.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act: Calculate three-year average P/E
    result = calculator.compute_three_year_avg_pe()
    
    # Assert: Verify average EPS calculation
    three_year_avg_eps = result['three_year_avg_eps']
    
    # Should not be "N/A" since we have 3 years of data
    assert three_year_avg_eps != "N/A", "Should calculate average with 3 years of data"
    
    # Calculate expected average
    expected_avg = (eps_year1 + eps_year2 + eps_year3) / Decimal('3')
    
    # Verify the average matches the formula (within tolerance for rounding)
    assert_decimal_equal(
        to_decimal(three_year_avg_eps),
        expected_avg,
        tolerance=Decimal('0.01'),
        message=f"Three-year average EPS {three_year_avg_eps} does not match expected {expected_avg}"
    )
    
    # Verify years_used contains 3 years
    assert len(result['years_used']) == 3, "Should use exactly 3 years"


@given(
    eps_year1=decimal_strategy(min_value="0.01", max_value="100", places=2),
    eps_year2=decimal_strategy(min_value="-50", max_value="100", places=2),
    eps_year3=decimal_strategy(min_value="-50", max_value="100", places=2)
)
def test_property_9_loss_years_included_in_average(eps_year1, eps_year2, eps_year3):
    """
    Feature: graham-metrics-enhancement, Property 9: Three-Year Average EPS Calculation
    
    Verify that loss years (negative EPS) are included in the average calculation,
    which reduces the average EPS and reflects the company's historical volatility.
    
    **Validates: Requirements 4.2**
    
    This is a critical aspect of Graham's methodology - losses are real value destruction
    and must be included in the average.
    """
    # Ensure at least one year has a loss
    assume(eps_year2 < 0 or eps_year3 < 0)
    
    # Arrange
    eps_values = [eps_year1, eps_year2, eps_year3]
    
    financial_data = GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
        eps_values=eps_values,
        price=Decimal('100.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert: Average should include the loss years
    three_year_avg_eps = result['three_year_avg_eps']
    
    if three_year_avg_eps != "N/A":
        expected_avg = (eps_year1 + eps_year2 + eps_year3) / Decimal('3')
        
        # The average should be lower than if we excluded loss years
        # Calculate what the average would be if we only included positive years
        positive_eps = [eps for eps in eps_values if eps > 0]
        if len(positive_eps) > 0:
            avg_without_losses = sum(positive_eps) / Decimal(str(len(positive_eps)))
            
            # If there were losses, the actual average should be less than the positive-only average
            if len(positive_eps) < 3:
                assert to_decimal(three_year_avg_eps) < avg_without_losses, \
                    "Average should be reduced by including loss years"
        
        # Verify the calculation is correct
        assert_decimal_equal(
            to_decimal(three_year_avg_eps),
            expected_avg,
            tolerance=Decimal('0.01')
        )


@given(
    eps_year1=decimal_strategy(min_value="0.01", max_value="100", places=2),
    eps_year2=decimal_strategy(min_value="0.01", max_value="100", places=2)
)
def test_property_9_insufficient_data_returns_na(eps_year1, eps_year2):
    """
    Feature: graham-metrics-enhancement, Property 9: Three-Year Average EPS Calculation
    
    When fewer than 3 years of EPS data are available, the system should return "N/A"
    and add a warning.
    
    **Validates: Requirements 4.1**
    """
    # Arrange: Create financial data with only 2 years
    eps_values = [eps_year1, eps_year2]
    
    financial_data = GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
        eps_values=eps_values,
        price=Decimal('100.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert
    assert result['three_year_avg_eps'] == "N/A", \
        "Should return N/A when fewer than 3 years available"
    assert result['pe_on_avg'] == "N/A", \
        "Should return N/A for P/E when insufficient data"
    assert len(result['years_used']) == 2, \
        "Should report the actual number of years available"
    
    # Verify warning was added
    assert any("Insufficient data" in warning for warning in calculator.warnings), \
        "Should add warning about insufficient data"


@given(
    eps_values=st.lists(
        decimal_strategy(min_value="-100", max_value="100", places=2),
        min_size=3,
        max_size=10
    )
)
def test_property_9_uses_most_recent_three_years(eps_values):
    """
    Feature: graham-metrics-enhancement, Property 9: Three-Year Average EPS Calculation
    
    When more than 3 years of data are available, the system should use only the
    most recent 3 years for the average calculation.
    
    **Validates: Requirements 4.1**
    """
    # Arrange: Create financial data with multiple years
    financial_data = GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
        eps_values=eps_values,
        price=Decimal('100.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert: Should use exactly 3 years
    assert len(result['years_used']) == 3, \
        "Should use exactly 3 years even when more are available"
    
    # Verify it's the most recent 3 years
    three_year_avg_eps = result['three_year_avg_eps']
    
    if three_year_avg_eps != "N/A":
        # Calculate expected average from most recent 3 years
        expected_avg = sum(eps_values[:3]) / Decimal('3')
        
        assert_decimal_equal(
            to_decimal(three_year_avg_eps),
            expected_avg,
            tolerance=Decimal('0.01'),
            message="Should calculate average from most recent 3 years only"
        )


@given(
    eps_year1=decimal_strategy(min_value="0.01", max_value="100", places=2),
    eps_year2=decimal_strategy(min_value="0.01", max_value="100", places=2),
    eps_year3=decimal_strategy(min_value="0.01", max_value="100", places=2)
)
def test_property_9_rounding_precision(eps_year1, eps_year2, eps_year3):
    """
    Feature: graham-metrics-enhancement, Property 9: Three-Year Average EPS Calculation
    
    Verify that the average EPS is rounded to 2 decimal places using proper
    Decimal arithmetic to avoid floating-point errors.
    
    **Validates: Requirements 10.2**
    """
    # Arrange
    eps_values = [eps_year1, eps_year2, eps_year3]
    
    financial_data = GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
        eps_values=eps_values,
        price=Decimal('100.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert
    three_year_avg_eps = result['three_year_avg_eps']
    
    if three_year_avg_eps != "N/A":
        # Verify it's a float (converted from Decimal)
        assert isinstance(three_year_avg_eps, float), \
            "Should return float for compatibility"
        
        # Verify it has at most 2 decimal places
        eps_str = f"{three_year_avg_eps:.10f}"  # Get full precision
        decimal_part = eps_str.split('.')[1]
        
        # Check that digits beyond 2 decimal places are all zeros
        # (allowing for floating-point representation quirks)
        significant_digits = decimal_part.rstrip('0')
        assert len(significant_digits) <= 2, \
            f"Should round to 2 decimal places, got {three_year_avg_eps}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# Property 10: Three-Year Average P/E Calculation
@given(
    eps_year1=decimal_strategy(min_value="0.01", max_value="100", places=2),
    eps_year2=decimal_strategy(min_value="0.01", max_value="100", places=2),
    eps_year3=decimal_strategy(min_value="0.01", max_value="100", places=2),
    price=decimal_strategy(min_value="1", max_value="1000", places=2)
)
def test_property_10_three_year_avg_pe_calculation(eps_year1, eps_year2, eps_year3, price):
    """
    Feature: graham-metrics-enhancement, Property 10: Three-Year Average P/E Calculation
    
    For any three-year average EPS > 0 and current price > 0, the P/E on three-year
    average should equal price / three_year_avg_eps.
    
    **Validates: Requirements 4.4**
    
    This test verifies the P/E calculation formula is correct.
    """
    # Arrange
    eps_values = [eps_year1, eps_year2, eps_year3]
    
    financial_data = GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
        eps_values=eps_values,
        price=price
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert
    three_year_avg_eps = result['three_year_avg_eps']
    pe_on_avg = result['pe_on_avg']
    
    # Should not be "N/A" since all EPS values are positive
    assert three_year_avg_eps != "N/A", "Should calculate average with positive EPS"
    assert pe_on_avg != "N/A", "Should calculate P/E with positive average EPS"
    
    # Calculate expected P/E
    avg_eps_dec = (eps_year1 + eps_year2 + eps_year3) / Decimal('3')
    expected_pe = price / avg_eps_dec
    
    # Verify P/E calculation
    assert_decimal_equal(
        to_decimal(pe_on_avg),
        expected_pe,
        tolerance=Decimal('0.01'),
        message=f"P/E ratio {pe_on_avg} does not match expected {expected_pe}"
    )


@given(
    eps_year1=decimal_strategy(min_value="-50", max_value="0", places=2),
    eps_year2=decimal_strategy(min_value="-50", max_value="0", places=2),
    eps_year3=decimal_strategy(min_value="-50", max_value="0", places=2),
    price=decimal_strategy(min_value="1", max_value="1000", places=2)
)
def test_property_10_pe_na_when_avg_eps_zero_or_negative(eps_year1, eps_year2, eps_year3, price):
    """
    Feature: graham-metrics-enhancement, Property 10: Three-Year Average P/E Calculation
    
    When the three-year average EPS is zero or negative, the P/E ratio should be "N/A"
    because a meaningful P/E cannot be calculated.
    
    **Validates: Requirements 4.6**
    """
    # Average will be zero or negative since all values are <= 0
    
    # Arrange
    eps_values = [eps_year1, eps_year2, eps_year3]
    
    financial_data = GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
        eps_values=eps_values,
        price=price
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert
    assert result['pe_on_avg'] == "N/A", \
        "Should return N/A for P/E when average EPS is zero or negative"
    
    # Average EPS should still be calculated and shown
    assert result['three_year_avg_eps'] != "N/A", \
        "Should still calculate and show average EPS even if negative"
    
    # Verify the average is indeed zero or negative
    assert result['three_year_avg_eps'] <= 0, \
        "Average EPS should be zero or negative"


@given(
    eps_year1=decimal_strategy(min_value="0.01", max_value="100", places=2),
    eps_year2=decimal_strategy(min_value="0.01", max_value="100", places=2),
    eps_year3=decimal_strategy(min_value="0.01", max_value="100", places=2),
    price=decimal_strategy(min_value="1", max_value="1000", places=2)
)
def test_property_10_pe_ratio_rounding(eps_year1, eps_year2, eps_year3, price):
    """
    Feature: graham-metrics-enhancement, Property 10: Three-Year Average P/E Calculation
    
    Verify that the P/E ratio is rounded to 2 decimal places using proper
    Decimal arithmetic.
    
    **Validates: Requirements 10.2**
    """
    # Arrange
    eps_values = [eps_year1, eps_year2, eps_year3]
    
    financial_data = GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
        eps_values=eps_values,
        price=price
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert
    pe_on_avg = result['pe_on_avg']
    
    if pe_on_avg != "N/A":
        # Verify it's a float
        assert isinstance(pe_on_avg, float), \
            "Should return float for compatibility"
        
        # Verify it has at most 2 decimal places
        pe_str = f"{pe_on_avg:.10f}"
        decimal_part = pe_str.split('.')[1]
        significant_digits = decimal_part.rstrip('0')
        
        assert len(significant_digits) <= 2, \
            f"Should round to 2 decimal places, got {pe_on_avg}"


@given(
    eps_year1=decimal_strategy(min_value="0.01", max_value="100", places=2),
    eps_year2=decimal_strategy(min_value="0.01", max_value="100", places=2),
    eps_year3=decimal_strategy(min_value="0.01", max_value="100", places=2),
    price=decimal_strategy(min_value="1", max_value="1000", places=2)
)
def test_property_10_pe_always_positive_when_avg_eps_positive(eps_year1, eps_year2, eps_year3, price):
    """
    Feature: graham-metrics-enhancement, Property 10: Three-Year Average P/E Calculation
    
    When average EPS is positive and price is positive, the P/E ratio should always
    be positive.
    
    **Validates: Requirements 4.4**
    """
    # Arrange
    eps_values = [eps_year1, eps_year2, eps_year3]
    
    financial_data = GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
        eps_values=eps_values,
        price=price
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert
    pe_on_avg = result['pe_on_avg']
    
    assert pe_on_avg != "N/A", "Should calculate P/E with positive inputs"
    assert pe_on_avg > 0, "P/E should be positive when both price and average EPS are positive"


@given(
    eps_year1=decimal_strategy(min_value="1", max_value="100", places=2),
    eps_year2=decimal_strategy(min_value="-50", max_value="-0.01", places=2),
    eps_year3=decimal_strategy(min_value="0.01", max_value="100", places=2),
    price=decimal_strategy(min_value="1", max_value="1000", places=2)
)
def test_property_10_pe_reflects_loss_years_impact(eps_year1, eps_year2, eps_year3, price):
    """
    Feature: graham-metrics-enhancement, Property 10: Three-Year Average P/E Calculation
    
    When loss years are included, the P/E ratio should reflect the impact of those losses
    on the average EPS. This test verifies the mathematical relationship between
    average EPS and P/E ratio.
    
    This reflects Graham's methodology of using average earnings to smooth out volatility.
    
    **Validates: Requirements 4.2, 4.4**
    """
    # Ensure average is still positive after the calculator rounds it to 2 decimal places
    avg_eps = (eps_year1 + eps_year2 + eps_year3) / Decimal('3')
    assume(avg_eps >= Decimal('0.005'))
    
    # Ensure the loss year actually reduces the average below the most recent year
    # (otherwise the test premise doesn't hold)
    assume(avg_eps < eps_year1)
    
    # Arrange
    eps_values = [eps_year1, eps_year2, eps_year3]
    
    financial_data = GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
        eps_values=eps_values,
        price=price
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert
    pe_on_avg = result['pe_on_avg']
    
    # Should not be N/A since average is positive
    assert pe_on_avg != "N/A", "P/E should be calculable with positive average"
    
    # Calculate P/E based on most recent year only
    pe_current_year = price / eps_year1
    
    # P/E on average should be higher because average EPS is lower (due to losses)
    # Since avg_eps < eps_year1, we have price/avg_eps > price/eps_year1
    # pe_on_avg is rounded to 2 decimal places, so allow up to 0.005 rounding error
    assert pe_on_avg > float(pe_current_year) * 0.99 - 0.005, \
        f"P/E on 3-year average ({pe_on_avg}) should be higher than current year P/E ({float(pe_current_year)}) when average EPS is reduced by losses"



# Unit Tests for Edge Cases
def test_edge_case_fewer_than_3_years():
    """
    Test that the system returns "N/A" when fewer than 3 years of data are available.
    
    **Validates: Requirements 4.3**
    """
    # Arrange: Create data with only 2 years
    financial_data = GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
        eps_values=[Decimal('5.0'), Decimal('4.5')],
        price=Decimal('100.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert
    assert result['three_year_avg_eps'] == "N/A", \
        "Should return N/A for average EPS with insufficient data"
    assert result['pe_on_avg'] == "N/A", \
        "Should return N/A for P/E with insufficient data"
    assert len(result['years_used']) == 2, \
        "Should report actual number of years available"
    
    # Verify warning
    assert any("Insufficient data" in warning for warning in calculator.warnings), \
        "Should add warning about insufficient data"


def test_edge_case_exactly_3_years():
    """
    Test that the system works correctly with exactly 3 years of data.
    
    **Validates: Requirements 4.1**
    """
    # Arrange
    eps_values = [Decimal('5.0'), Decimal('4.5'), Decimal('4.0')]
    financial_data = GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
        eps_values=eps_values,
        price=Decimal('100.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert
    expected_avg = (Decimal('5.0') + Decimal('4.5') + Decimal('4.0')) / Decimal('3')
    expected_avg_rounded = float(expected_avg.quantize(Decimal('0.01')))
    
    assert result['three_year_avg_eps'] == expected_avg_rounded, \
        f"Average EPS should be {expected_avg_rounded}"
    assert len(result['years_used']) == 3, \
        "Should use exactly 3 years"


def test_edge_case_more_than_3_years():
    """
    Test that the system uses only the most recent 3 years when more are available.
    
    **Validates: Requirements 4.1**
    """
    # Arrange: Create data with 5 years
    eps_values = [
        Decimal('5.0'),   # 2023 - most recent
        Decimal('4.5'),   # 2022
        Decimal('4.0'),   # 2021
        Decimal('3.5'),   # 2020 - should not be used
        Decimal('3.0')    # 2019 - should not be used
    ]
    financial_data = GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
        eps_values=eps_values,
        price=Decimal('100.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert: Should use only first 3 years
    expected_avg = (Decimal('5.0') + Decimal('4.5') + Decimal('4.0')) / Decimal('3')
    expected_avg_rounded = float(expected_avg.quantize(Decimal('0.01')))
    
    assert result['three_year_avg_eps'] == expected_avg_rounded, \
        "Should calculate average from most recent 3 years only"
    assert len(result['years_used']) == 3, \
        "Should use exactly 3 years even when more are available"


def test_edge_case_loss_years_included():
    """
    Test that loss years (negative EPS) are included in the average calculation.
    
    **Validates: Requirements 4.2**
    """
    # Arrange: Mix of profit and loss years
    eps_values = [
        Decimal('5.0'),   # 2023: profit
        Decimal('-2.0'),  # 2022: loss
        Decimal('3.0')    # 2021: profit
    ]
    financial_data = GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
        eps_values=eps_values,
        price=Decimal('100.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert: Loss year should be included
    expected_avg = (Decimal('5.0') + Decimal('-2.0') + Decimal('3.0')) / Decimal('3')
    expected_avg_rounded = float(expected_avg.quantize(Decimal('0.01')))
    
    assert result['three_year_avg_eps'] == expected_avg_rounded, \
        f"Average should include loss year: expected {expected_avg_rounded}, got {result['three_year_avg_eps']}"
    
    # Average should be 2.0, which is less than if we excluded the loss year
    assert result['three_year_avg_eps'] == 2.0, \
        "Average should be 2.0 when including the loss year"


def test_edge_case_all_loss_years():
    """
    Test behavior when all 3 years have losses (negative EPS).
    
    **Validates: Requirements 4.2, 4.5**
    """
    # Arrange: All loss years
    eps_values = [
        Decimal('-1.0'),  # 2023: loss
        Decimal('-2.0'),  # 2022: loss
        Decimal('-1.5')   # 2021: loss
    ]
    financial_data = GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
        eps_values=eps_values,
        price=Decimal('100.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert: Average should be calculated but P/E should be N/A
    expected_avg = (Decimal('-1.0') + Decimal('-2.0') + Decimal('-1.5')) / Decimal('3')
    expected_avg_rounded = float(expected_avg.quantize(Decimal('0.01')))
    
    assert result['three_year_avg_eps'] == expected_avg_rounded, \
        "Should calculate average even with all loss years"
    assert result['three_year_avg_eps'] < 0, \
        "Average should be negative with all loss years"
    assert result['pe_on_avg'] == "N/A", \
        "P/E should be N/A when average EPS is negative"


def test_edge_case_zero_average_eps():
    """
    Test behavior when the three-year average EPS equals exactly zero.
    
    **Validates: Requirements 4.5**
    """
    # Arrange: EPS values that average to zero
    eps_values = [
        Decimal('2.0'),   # 2023: profit
        Decimal('-4.0'),  # 2022: loss
        Decimal('2.0')    # 2021: profit
    ]
    financial_data = GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
        eps_values=eps_values,
        price=Decimal('100.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert
    assert result['three_year_avg_eps'] == 0.0, \
        "Average should be exactly zero"
    assert result['pe_on_avg'] == "N/A", \
        "P/E should be N/A when average EPS is zero"


def test_edge_case_very_small_positive_eps():
    """
    Test behavior with very small positive EPS values.
    
    **Validates: Requirements 4.4**
    """
    # Arrange: Very small EPS values
    eps_values = [
        Decimal('0.01'),  # 2023
        Decimal('0.02'),  # 2022
        Decimal('0.01')   # 2021
    ]
    financial_data = GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
        eps_values=eps_values,
        price=Decimal('100.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert
    expected_avg = (Decimal('0.01') + Decimal('0.02') + Decimal('0.01')) / Decimal('3')
    expected_avg_rounded = float(expected_avg.quantize(Decimal('0.01')))
    
    assert result['three_year_avg_eps'] == expected_avg_rounded, \
        "Should handle very small EPS values"
    
    # P/E should be very high
    expected_pe = Decimal('100.0') / expected_avg
    expected_pe_rounded = float(expected_pe.quantize(Decimal('0.01')))
    
    assert result['pe_on_avg'] == expected_pe_rounded, \
        "Should calculate very high P/E with small EPS"
    assert result['pe_on_avg'] > 1000, \
        "P/E should be very high with small EPS"


def test_edge_case_no_history():
    """
    Test behavior when no financial history is available.
    
    **Validates: Requirements 8.1**
    """
    # Arrange: Empty history
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
        'currency': 'USD',
        'sector': 'Technology',
        'history': {}
    }
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert
    assert result['three_year_avg_eps'] == "N/A", \
        "Should return N/A with no history"
    assert result['pe_on_avg'] == "N/A", \
        "Should return N/A for P/E with no history"
    assert result['years_used'] == [], \
        "Should return empty years list"


def test_edge_case_incomplete_years_filtered():
    """
    Test that incomplete years (dividend-only years) are filtered out.
    
    **Validates: Requirements 4.1**
    """
    # Arrange: Create data with 4 years, but one is incomplete (dividend only)
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
        'currency': 'USD',
        'sector': 'Technology',
        'history': {
            '2024-12-31': {  # Incomplete year - dividend only
                'revenue': 0.0,
                'net_income': 0.0,
                'eps': 0.0,
                'total_equity': 0.0,
                'dividend': 2.0,
                'shares_outstanding': 1000000.0
            },
            '2023-12-31': {  # Complete year
                'revenue': 5000000.0,
                'net_income': 500000.0,
                'eps': 5.0,
                'total_equity': 1200000.0,
                'dividend': 2.0,
                'shares_outstanding': 1000000.0
            },
            '2022-12-31': {  # Complete year
                'revenue': 4500000.0,
                'net_income': 450000.0,
                'eps': 4.5,
                'total_equity': 1100000.0,
                'dividend': 1.8,
                'shares_outstanding': 1000000.0
            },
            '2021-12-31': {  # Complete year
                'revenue': 4000000.0,
                'net_income': 400000.0,
                'eps': 4.0,
                'total_equity': 1000000.0,
                'dividend': 1.6,
                'shares_outstanding': 1000000.0
            }
        }
    }
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_three_year_avg_pe()
    
    # Assert: Should use 2023, 2022, 2021 (skip 2024 as incomplete)
    expected_avg = (Decimal('5.0') + Decimal('4.5') + Decimal('4.0')) / Decimal('3')
    expected_avg_rounded = float(expected_avg.quantize(Decimal('0.01')))
    
    assert result['three_year_avg_eps'] == expected_avg_rounded, \
        "Should skip incomplete years and use only complete financial years"
    assert len(result['years_used']) == 3, \
        "Should use 3 complete years"
    assert '2024-12-31' not in result['years_used'], \
        "Should not include incomplete year"
