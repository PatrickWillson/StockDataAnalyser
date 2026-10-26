"""
Property-Based Tests for Combined P/E × P/B Test Calculator

This module tests the combined P/E × P/B test calculation using property-based testing
with Hypothesis. Tests verify that the calculation follows Graham's methodology correctly
across all valid inputs.

Feature: graham-metrics-enhancement
Property: 11
Validates: Requirements 5.1, 5.3, 5.4
"""

import pytest
from hypothesis import given
from decimal import Decimal

from core.graham_math import GrahamCalculator
from tests.test_utils_decimal import (
    to_decimal,
    decimal_strategy,
    assert_decimal_equal
)
from tests.fixtures_graham_metrics import GrahamMetricsFixtures


# Property 11: Combined P/E × P/B Test Calculation
@given(
    eps=decimal_strategy(min_value="0.01", max_value="100", places=2),
    total_equity=decimal_strategy(min_value="1000", max_value="10000000", places=2),
    shares_outstanding=decimal_strategy(min_value="100", max_value="10000000", places=2),
    price=decimal_strategy(min_value="1", max_value="1000", places=2)
)
def test_property_11_combined_pe_pb_product_calculation(eps, total_equity, shares_outstanding, price):
    """
    Feature: graham-metrics-enhancement, Property 11: Combined P/E × P/B Test Calculation
    
    For any valid P/E and P/B ratios, the combined test product should equal P/E × P/B,
    and the result should be "PASS" if product ≤ 22.5, otherwise "FAIL".
    
    **Validates: Requirements 5.1, 5.3, 5.4**
    
    This test verifies:
    - Product is calculated as P/E × P/B
    - Result is "PASS" when product ≤ 22.5
    - Result is "FAIL" when product > 22.5
    """
    # Arrange: Create financial data
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=eps,
        total_equity=total_equity,
        shares_outstanding=shares_outstanding,
        price=price
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act: Calculate combined test
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert: Verify product calculation
    pe_ratio = result['pe_ratio']
    pb_ratio = result['pb_ratio']
    product = result['product']
    test_result = result['result']
    
    # Should not be "N/A" since we have valid inputs
    assert pe_ratio != "N/A", "P/E ratio should be calculable with positive EPS"
    assert pb_ratio != "N/A", "P/B ratio should be calculable with positive equity"
    assert product != "N/A", "Product should be calculable with valid P/E and P/B"
    
    # Calculate expected P/E
    expected_pe = price / eps
    assert_decimal_equal(
        to_decimal(pe_ratio),
        expected_pe,
        tolerance=Decimal('0.01'),
        message=f"P/E ratio {pe_ratio} does not match expected {expected_pe}"
    )
    
    # Calculate expected P/B
    book_value_per_share = total_equity / shares_outstanding
    expected_pb = price / book_value_per_share
    assert_decimal_equal(
        to_decimal(pb_ratio),
        expected_pb,
        tolerance=Decimal('0.01'),
        message=f"P/B ratio {pb_ratio} does not match expected {expected_pb}"
    )
    
    # Calculate expected product from the ROUNDED values
    # This is important because the implementation rounds P/E and P/B first,
    # then multiplies them, which can introduce small rounding differences
    expected_product_from_rounded = to_decimal(pe_ratio) * to_decimal(pb_ratio)
    assert_decimal_equal(
        to_decimal(product),
        expected_product_from_rounded,
        tolerance=Decimal('0.02'),  # Slightly larger tolerance for compound rounding
        message=f"Product {product} does not match expected {expected_product_from_rounded}"
    )
    
    # Verify threshold comparison
    if product <= 22.5:
        assert test_result == "PASS", \
            f"Result should be PASS when product ({product}) ≤ 22.5"
    else:
        assert test_result == "FAIL", \
            f"Result should be FAIL when product ({product}) > 22.5"


@given(
    eps=decimal_strategy(min_value="0.01", max_value="100", places=2),
    total_equity=decimal_strategy(min_value="1000", max_value="10000000", places=2),
    shares_outstanding=decimal_strategy(min_value="100", max_value="10000000", places=2),
    price=decimal_strategy(min_value="1", max_value="1000", places=2)
)
def test_property_11_threshold_22_5(eps, total_equity, shares_outstanding, price):
    """
    Feature: graham-metrics-enhancement, Property 11: Combined P/E × P/B Test Calculation
    
    Verify that the threshold of 22.5 is correctly applied to determine PASS/FAIL.
    
    **Validates: Requirements 5.3, 5.4**
    
    Graham's rule: P/E × P/B should not exceed 22.5
    """
    # Arrange
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=eps,
        total_equity=total_equity,
        shares_outstanding=shares_outstanding,
        price=price
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert
    product = result['product']
    test_result = result['result']
    
    if product != "N/A":
        # Verify the threshold logic
        threshold = Decimal('22.5')
        product_dec = to_decimal(product)
        
        if product_dec <= threshold:
            assert test_result == "PASS", \
                f"Should PASS when product ({product}) ≤ 22.5"
        else:
            assert test_result == "FAIL", \
                f"Should FAIL when product ({product}) > 22.5"


@given(
    eps=decimal_strategy(min_value="-100", max_value="0", places=2),
    total_equity=decimal_strategy(min_value="1000", max_value="10000000", places=2),
    shares_outstanding=decimal_strategy(min_value="100", max_value="10000000", places=2),
    price=decimal_strategy(min_value="1", max_value="1000", places=2)
)
def test_property_11_invalid_pe_returns_na(eps, total_equity, shares_outstanding, price):
    """
    Feature: graham-metrics-enhancement, Property 11: Combined P/E × P/B Test Calculation
    
    When P/E is invalid (EPS ≤ 0), the entire test should return "N/A".
    
    **Validates: Requirements 5.2**
    """
    # Arrange: EPS is zero or negative
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=eps,
        total_equity=total_equity,
        shares_outstanding=shares_outstanding,
        price=price
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert
    assert result['pe_ratio'] == "N/A", \
        "P/E ratio should be N/A when EPS is zero or negative"
    assert result['product'] == "N/A", \
        "Product should be N/A when P/E is invalid"
    assert result['result'] == "N/A", \
        "Test result should be N/A when P/E is invalid"


@given(
    eps=decimal_strategy(min_value="0.01", max_value="100", places=2),
    total_equity=decimal_strategy(min_value="-10000000", max_value="0", places=2),
    shares_outstanding=decimal_strategy(min_value="100", max_value="10000000", places=2),
    price=decimal_strategy(min_value="1", max_value="1000", places=2)
)
def test_property_11_invalid_pb_returns_na(eps, total_equity, shares_outstanding, price):
    """
    Feature: graham-metrics-enhancement, Property 11: Combined P/E × P/B Test Calculation
    
    When P/B is invalid (equity ≤ 0), the entire test should return "N/A".
    
    **Validates: Requirements 5.2**
    """
    # Arrange: Total equity is zero or negative
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=eps,
        total_equity=total_equity,
        shares_outstanding=shares_outstanding,
        price=price
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert
    assert result['pb_ratio'] == "N/A", \
        "P/B ratio should be N/A when equity is zero or negative"
    assert result['product'] == "N/A", \
        "Product should be N/A when P/B is invalid"
    assert result['result'] == "N/A", \
        "Test result should be N/A when P/B is invalid"


@given(
    eps=decimal_strategy(min_value="0.01", max_value="100", places=2),
    total_equity=decimal_strategy(min_value="1000", max_value="10000000", places=2),
    shares_outstanding=decimal_strategy(min_value="100", max_value="10000000", places=2),
    price=decimal_strategy(min_value="1", max_value="1000", places=2)
)
def test_property_11_rounding_precision(eps, total_equity, shares_outstanding, price):
    """
    Feature: graham-metrics-enhancement, Property 11: Combined P/E × P/B Test Calculation
    
    Verify that all ratios and the product are rounded to 2 decimal places using
    proper Decimal arithmetic to avoid floating-point errors.
    
    **Validates: Requirements 10.2**
    """
    # Arrange
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=eps,
        total_equity=total_equity,
        shares_outstanding=shares_outstanding,
        price=price
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert
    pe_ratio = result['pe_ratio']
    pb_ratio = result['pb_ratio']
    product = result['product']
    
    if pe_ratio != "N/A":
        # Verify P/E is a float
        assert isinstance(pe_ratio, float), "P/E should be a float"
        # Verify rounding by checking that multiplying by 100 and rounding gives an integer
        pe_cents = round(pe_ratio * 100)
        assert abs(pe_ratio - pe_cents / 100) < 0.001, \
            f"P/E should be rounded to 2 decimal places, got {pe_ratio}"
    
    if pb_ratio != "N/A":
        # Verify P/B is a float
        assert isinstance(pb_ratio, float), "P/B should be a float"
        # Verify rounding by checking that multiplying by 100 and rounding gives an integer
        pb_cents = round(pb_ratio * 100)
        assert abs(pb_ratio - pb_cents / 100) < 0.001, \
            f"P/B should be rounded to 2 decimal places, got {pb_ratio}"
    
    if product != "N/A":
        # Verify product is a float
        assert isinstance(product, float), "Product should be a float"
        # Verify rounding by checking that multiplying by 100 and rounding gives an integer
        product_cents = round(product * 100)
        assert abs(product - product_cents / 100) < 0.001, \
            f"Product should be rounded to 2 decimal places, got {product}"


@given(
    eps=decimal_strategy(min_value="0.01", max_value="100", places=2),
    total_equity=decimal_strategy(min_value="1000", max_value="10000000", places=2),
    shares_outstanding=decimal_strategy(min_value="100", max_value="10000000", places=2),
    price=decimal_strategy(min_value="1", max_value="1000", places=2)
)
def test_property_11_flexibility_rule(eps, total_equity, shares_outstanding, price):
    """
    Feature: graham-metrics-enhancement, Property 11: Combined P/E × P/B Test Calculation
    
    Verify Graham's flexibility rule: a company can have a higher P/E if it has a low P/B,
    or vice versa, as long as the product doesn't exceed 22.5.
    
    **Validates: Requirements 5.1, 5.3**
    
    Examples:
    - P/E of 15 can have P/B up to 1.5 (15 × 1.5 = 22.5)
    - P/E of 10 can have P/B up to 2.25 (10 × 2.25 = 22.5)
    - P/B of 0.5 can have P/E up to 45 (45 × 0.5 = 22.5)
    """
    # Arrange
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=eps,
        total_equity=total_equity,
        shares_outstanding=shares_outstanding,
        price=price
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert
    pe_ratio = result['pe_ratio']
    pb_ratio = result['pb_ratio']
    product = result['product']
    test_result = result['result']
    
    if product != "N/A":
        # Verify the flexibility: if one ratio is low, the other can be higher
        # as long as product ≤ 22.5
        
        # If P/E is high (> 15) but product passes, P/B must be low
        if pe_ratio > 15 and test_result == "PASS":
            max_allowed_pb = 22.5 / pe_ratio
            assert pb_ratio <= max_allowed_pb + 0.01, \
                f"With high P/E ({pe_ratio}), P/B ({pb_ratio}) should be ≤ {max_allowed_pb}"
        
        # If P/B is high (> 1.5) but product passes, P/E must be low
        if pb_ratio > 1.5 and test_result == "PASS":
            max_allowed_pe = 22.5 / pb_ratio
            assert pe_ratio <= max_allowed_pe + 0.01, \
                f"With high P/B ({pb_ratio}), P/E ({pe_ratio}) should be ≤ {max_allowed_pe}"


# Unit Tests for Edge Cases
def test_edge_case_exactly_at_threshold():
    """
    Test behavior when product equals exactly 22.5.
    
    **Validates: Requirements 5.3, 5.4**
    """
    # Arrange: P/E = 15, P/B = 1.5, Product = 22.5
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=Decimal('10.0'),
        total_equity=Decimal('1500000.0'),
        shares_outstanding=Decimal('100000.0'),
        price=Decimal('150.0')  # P/E = 150/10 = 15, P/B = 150/15 = 10, need to adjust
    )
    
    # Adjust to get exactly 22.5
    # P/E = 15, P/B = 1.5 → Product = 22.5
    # Price / EPS = 15 → Price = 15 * EPS
    # Price / BVPS = 1.5 → Price = 1.5 * BVPS
    # BVPS = total_equity / shares = 1500000 / 100000 = 15
    # Price = 1.5 * 15 = 22.5
    # EPS = Price / 15 = 22.5 / 15 = 1.5
    
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=Decimal('1.5'),
        total_equity=Decimal('1500000.0'),
        shares_outstanding=Decimal('100000.0'),
        price=Decimal('22.5')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert: Should PASS at exactly 22.5
    assert result['product'] == 22.5, "Product should be exactly 22.5"
    assert result['result'] == "PASS", "Should PASS when product equals 22.5"


def test_edge_case_just_below_threshold():
    """
    Test behavior when product is just below 22.5.
    
    **Validates: Requirements 5.3, 5.4**
    """
    # Arrange: Product = 22.4
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=Decimal('1.5'),
        total_equity=Decimal('1500000.0'),
        shares_outstanding=Decimal('100000.0'),
        price=Decimal('22.4')  # Slightly below threshold
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert
    assert result['product'] < 22.5, "Product should be below 22.5"
    assert result['result'] == "PASS", "Should PASS when product < 22.5"


def test_edge_case_just_above_threshold():
    """
    Test behavior when product is just above 22.5.
    
    **Validates: Requirements 5.3, 5.4**
    """
    # Arrange: Product = 22.6
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=Decimal('1.5'),
        total_equity=Decimal('1500000.0'),
        shares_outstanding=Decimal('100000.0'),
        price=Decimal('22.6')  # Slightly above threshold
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert
    assert result['product'] > 22.5, "Product should be above 22.5"
    assert result['result'] == "FAIL", "Should FAIL when product > 22.5"


def test_edge_case_zero_eps():
    """
    Test behavior when EPS is exactly zero.
    
    **Validates: Requirements 5.2**
    """
    # Arrange
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=Decimal('0.0'),
        total_equity=Decimal('1500000.0'),
        shares_outstanding=Decimal('100000.0'),
        price=Decimal('100.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert
    assert result['pe_ratio'] == "N/A", "P/E should be N/A with zero EPS"
    assert result['product'] == "N/A", "Product should be N/A"
    assert result['result'] == "N/A", "Result should be N/A"


def test_edge_case_negative_eps():
    """
    Test behavior when EPS is negative (company has losses).
    
    **Validates: Requirements 5.2**
    """
    # Arrange
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=Decimal('-5.0'),
        total_equity=Decimal('1500000.0'),
        shares_outstanding=Decimal('100000.0'),
        price=Decimal('100.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert
    assert result['pe_ratio'] == "N/A", "P/E should be N/A with negative EPS"
    assert result['product'] == "N/A", "Product should be N/A"
    assert result['result'] == "N/A", "Result should be N/A"


def test_edge_case_zero_equity():
    """
    Test behavior when total equity is exactly zero.
    
    **Validates: Requirements 5.2**
    """
    # Arrange
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=Decimal('5.0'),
        total_equity=Decimal('0.0'),
        shares_outstanding=Decimal('100000.0'),
        price=Decimal('100.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert
    assert result['pb_ratio'] == "N/A", "P/B should be N/A with zero equity"
    assert result['product'] == "N/A", "Product should be N/A"
    assert result['result'] == "N/A", "Result should be N/A"


def test_edge_case_negative_equity():
    """
    Test behavior when total equity is negative (company is insolvent).
    
    **Validates: Requirements 5.2**
    """
    # Arrange
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=Decimal('5.0'),
        total_equity=Decimal('-1000000.0'),
        shares_outstanding=Decimal('100000.0'),
        price=Decimal('100.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert
    assert result['pb_ratio'] == "N/A", "P/B should be N/A with negative equity"
    assert result['product'] == "N/A", "Product should be N/A"
    assert result['result'] == "N/A", "Result should be N/A"


def test_edge_case_zero_shares():
    """
    Test behavior when shares outstanding is zero.
    
    **Validates: Requirements 5.2**
    """
    # Arrange
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=Decimal('5.0'),
        total_equity=Decimal('1500000.0'),
        shares_outstanding=Decimal('0.0'),
        price=Decimal('100.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert
    assert result['pb_ratio'] == "N/A", "P/B should be N/A with zero shares"
    assert result['product'] == "N/A", "Product should be N/A"
    assert result['result'] == "N/A", "Result should be N/A"


def test_edge_case_no_history():
    """
    Test behavior when no financial history is available.
    
    **Validates: Requirements 8.1**
    """
    # Arrange
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
        'currency': 'USD',
        'sector': 'Technology',
        'history': {}
    }
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert
    assert result['pe_ratio'] == "N/A", "P/E should be N/A with no history"
    assert result['pb_ratio'] == "N/A", "P/B should be N/A with no history"
    assert result['product'] == "N/A", "Product should be N/A"
    assert result['result'] == "N/A", "Result should be N/A"


def test_edge_case_zero_price():
    """
    Test behavior when price is zero.
    
    **Validates: Requirements 8.1**
    """
    # Arrange
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=Decimal('5.0'),
        total_equity=Decimal('1500000.0'),
        shares_outstanding=Decimal('100000.0'),
        price=Decimal('0.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert
    assert result['pe_ratio'] == "N/A", "P/E should be N/A with zero price"
    assert result['pb_ratio'] == "N/A", "P/B should be N/A with zero price"
    assert result['product'] == "N/A", "Product should be N/A"
    assert result['result'] == "N/A", "Result should be N/A"


def test_edge_case_very_high_pe_low_pb():
    """
    Test Graham's flexibility rule: high P/E can be compensated by low P/B.
    
    **Validates: Requirements 5.1, 5.3**
    """
    # Arrange: P/E = 45, P/B = 0.5, Product = 22.5 (exactly at threshold)
    # Price / EPS = 45 → EPS = Price / 45
    # Price / BVPS = 0.5 → BVPS = Price / 0.5 = 2 * Price
    # BVPS = total_equity / shares
    # Let Price = 90, then EPS = 2, BVPS = 180
    # total_equity = BVPS * shares = 180 * 100000 = 18000000
    
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=Decimal('2.0'),
        total_equity=Decimal('18000000.0'),
        shares_outstanding=Decimal('100000.0'),
        price=Decimal('90.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert
    assert result['pe_ratio'] == 45.0, "P/E should be 45"
    assert result['pb_ratio'] == 0.5, "P/B should be 0.5"
    assert result['product'] == 22.5, "Product should be 22.5"
    assert result['result'] == "PASS", "Should PASS with high P/E but low P/B"


def test_edge_case_low_pe_high_pb():
    """
    Test Graham's flexibility rule: low P/E can compensate for high P/B.
    
    **Validates: Requirements 5.1, 5.3**
    """
    # Arrange: P/E = 10, P/B = 2.25, Product = 22.5 (exactly at threshold)
    # Price / EPS = 10 → EPS = Price / 10
    # Price / BVPS = 2.25 → BVPS = Price / 2.25
    # Let Price = 90, then EPS = 9, BVPS = 40
    # total_equity = BVPS * shares = 40 * 100000 = 4000000
    
    financial_data = GrahamMetricsFixtures.get_combined_pe_pb_test_data(
        eps=Decimal('9.0'),
        total_equity=Decimal('4000000.0'),
        shares_outstanding=Decimal('100000.0'),
        price=Decimal('90.0')
    )
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    result = calculator.compute_combined_pe_pb_test()
    
    # Assert
    assert result['pe_ratio'] == 10.0, "P/E should be 10"
    assert result['pb_ratio'] == 2.25, "P/B should be 2.25"
    assert result['product'] == 22.5, "Product should be 22.5"
    assert result['result'] == "PASS", "Should PASS with low P/E but high P/B"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
