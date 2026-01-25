"""
Property-Based Tests for FinancialDataProcessor Historical FX Rate Application

Tests the apply_historical_fx_rates() method using Hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from core.financial_data_processor import FinancialDataProcessor


# Property 2: Fallback Consistency
# Validates: Requirements 1.5, 5.2, 5.3
@given(
    num_years=st.integers(min_value=1, max_value=20),
    current_rate=st.floats(min_value=0.5, max_value=2.0),
    fallback_ratio=st.floats(min_value=0.0, max_value=1.0)
)
@settings(max_examples=100)
def test_fallback_rate_used_when_historical_missing(num_years, current_rate, fallback_ratio):
    """
    **Feature: historical-fx-rates, Property 2: Fallback Consistency**
    
    Property: For any year with missing historical FX rate (None), the current
    rate should be used and a warning should be generated.
    
    This ensures graceful degradation when historical rates are unavailable.
    """
    # Create history with random years
    history = {}
    for i in range(num_years):
        year = f"{2020 + i}-12-31"
        history[year] = {
            'revenue': 1000.0 + i * 100,
            'net_income': 100.0 + i * 10,
            'eps': 1.0 + i * 0.1,
            'dividend': 0.5 + i * 0.05
        }
    
    # Create historical_fx_rates with some None values based on fallback_ratio
    historical_fx_rates = {}
    expected_fallback_count = 0
    for year in history.keys():
        # Use hash to deterministically decide if this year has a rate
        if hash(year) % 100 < fallback_ratio * 100:
            historical_fx_rates[year] = None
            expected_fallback_count += 1
        else:
            historical_fx_rates[year] = 1.2 + (hash(year) % 10) / 10.0
    
    # Apply historical FX rates
    converted_history, warnings = FinancialDataProcessor.apply_historical_fx_rates(
        history,
        historical_fx_rates,
        'GBP',
        'USD',
        current_rate
    )
    
    # Verify property: Warnings generated for fallback years
    if expected_fallback_count > 0:
        assert len(warnings) > 0, "Should generate warnings when fallback is used"
        # Check that warning mentions fallback
        assert any('fallback' in w.lower() for w in warnings), "Warning should mention fallback"
    
    # Verify property: All monetary values were converted
    for year, data in converted_history.items():
        fx_rate = historical_fx_rates.get(year, current_rate)
        if fx_rate is None:
            fx_rate = current_rate
        
        # Check that revenue was converted correctly
        if 'revenue' in history[year] and history[year]['revenue'] != 0:
            expected = history[year]['revenue'] * fx_rate
            assert abs(converted_history[year]['revenue'] - expected) < 0.01, \
                f"Revenue should be converted using {'current' if historical_fx_rates.get(year) is None else 'historical'} rate"


# Property 6: Monetary Field Conversion Completeness
# Validates: Requirements 3.1, 3.2, 3.3, 3.4
@given(
    revenue=st.floats(min_value=1000, max_value=1000000),
    net_income=st.floats(min_value=-10000, max_value=100000),
    eps=st.floats(min_value=-10, max_value=100),
    dividend=st.floats(min_value=0, max_value=10),
    total_equity=st.floats(min_value=1000, max_value=1000000),
    fx_rate=st.floats(min_value=0.5, max_value=2.0)
)
@settings(max_examples=100)
def test_monetary_field_conversion_completeness(revenue, net_income, eps, dividend, total_equity, fx_rate):
    """
    **Feature: historical-fx-rates, Property 6: Monetary Field Conversion Completeness**
    
    Property: For any historical financial record, all monetary fields should be
    converted using the same FX rate for that fiscal year end date.
    
    This ensures consistent currency conversion across all financial metrics.
    """
    year = '2023-12-31'
    
    # Create history with various monetary fields
    history = {
        year: {
            'revenue': revenue,
            'net_income': net_income,
            'eps': eps,
            'dividend': dividend,
            'total_equity': total_equity,
            'current_assets': 50000.0,
            'total_debt': 20000.0,
            'shares_outstanding': 1000000.0  # Non-monetary field
        }
    }
    
    # Create historical FX rates
    historical_fx_rates = {year: fx_rate}
    
    # Apply historical FX rates
    converted_history, warnings = FinancialDataProcessor.apply_historical_fx_rates(
        history,
        historical_fx_rates,
        'GBP',
        'USD',
        1.0  # Current rate (not used since historical rate exists)
    )
    
    # Verify property: All monetary fields converted with same rate
    converted_data = converted_history[year]
    
    # Check each monetary field
    assert abs(converted_data['revenue'] - revenue * fx_rate) < 0.01, "Revenue should be converted"
    assert abs(converted_data['net_income'] - net_income * fx_rate) < 0.01, "Net income should be converted"
    assert abs(converted_data['eps'] - eps * fx_rate) < 0.01, "EPS should be converted"
    assert abs(converted_data['dividend'] - dividend * fx_rate) < 0.01, "Dividend should be converted"
    assert abs(converted_data['total_equity'] - total_equity * fx_rate) < 0.01, "Total equity should be converted"
    assert abs(converted_data['current_assets'] - 50000.0 * fx_rate) < 0.01, "Current assets should be converted"
    assert abs(converted_data['total_debt'] - 20000.0 * fx_rate) < 0.01, "Total debt should be converted"
    
    # Non-monetary field should remain unchanged
    assert converted_data['shares_outstanding'] == 1000000.0, "Shares outstanding should not be converted"


# Property 3: Currency Conversion Idempotence (Round-Trip)
# Validates: Requirements 3.1, 3.2, 3.3
@given(
    value=st.floats(min_value=1.0, max_value=1000000.0),
    rate_forward=st.floats(min_value=0.5, max_value=2.0)
)
@settings(max_examples=100)
def test_currency_conversion_round_trip(value, rate_forward):
    """
    **Feature: historical-fx-rates, Property 3: Currency Conversion Idempotence**
    
    Property: Converting a value from currency A to B, then back from B to A
    using inverse rates, should return the original value (within precision).
    
    This validates the mathematical correctness of the conversion logic.
    """
    # Avoid division by zero
    assume(rate_forward > 0.01)
    
    rate_backward = 1.0 / rate_forward
    
    year = '2023-12-31'
    
    # Create history with a monetary value
    history = {
        year: {
            'revenue': value,
            'net_income': value / 10.0
        }
    }
    
    # Forward conversion (GBP → USD)
    historical_fx_rates_forward = {year: rate_forward}
    converted_forward, _ = FinancialDataProcessor.apply_historical_fx_rates(
        history,
        historical_fx_rates_forward,
        'GBP',
        'USD',
        rate_forward
    )
    
    # Backward conversion (USD → GBP)
    historical_fx_rates_backward = {year: rate_backward}
    converted_backward, _ = FinancialDataProcessor.apply_historical_fx_rates(
        converted_forward,
        historical_fx_rates_backward,
        'USD',
        'GBP',
        rate_backward
    )
    
    # Verify round-trip: should be within 0.01% of original
    round_trip_revenue = converted_backward[year]['revenue']
    assert abs(round_trip_revenue - value) / value < 0.0001, \
        f"Round-trip conversion should preserve value: {value} → {round_trip_revenue}"


# Test: Zero values are not converted
@given(
    fx_rate=st.floats(min_value=0.5, max_value=2.0)
)
@settings(max_examples=50)
def test_zero_values_not_converted(fx_rate):
    """
    Property: Zero values should remain zero after conversion.
    """
    year = '2023-12-31'
    
    history = {
        year: {
            'revenue': 0.0,
            'net_income': 0.0,
            'eps': 0.0,
            'dividend': 0.0
        }
    }
    
    historical_fx_rates = {year: fx_rate}
    
    converted_history, _ = FinancialDataProcessor.apply_historical_fx_rates(
        history,
        historical_fx_rates,
        'GBP',
        'USD',
        1.0
    )
    
    # All zero values should remain zero
    assert converted_history[year]['revenue'] == 0.0
    assert converted_history[year]['net_income'] == 0.0
    assert converted_history[year]['eps'] == 0.0
    assert converted_history[year]['dividend'] == 0.0


# Test: None values are preserved
@given(
    fx_rate=st.floats(min_value=0.5, max_value=2.0)
)
@settings(max_examples=50)
def test_none_values_preserved(fx_rate):
    """
    Property: None values should remain None after conversion.
    """
    year = '2023-12-31'
    
    history = {
        year: {
            'revenue': 1000.0,
            'year_end_price': None  # Missing price
        }
    }
    
    historical_fx_rates = {year: fx_rate}
    
    converted_history, _ = FinancialDataProcessor.apply_historical_fx_rates(
        history,
        historical_fx_rates,
        'GBP',
        'USD',
        1.0
    )
    
    # Revenue should be converted
    assert abs(converted_history[year]['revenue'] - 1000.0 * fx_rate) < 0.01
    
    # None value should remain None
    assert converted_history[year]['year_end_price'] is None


# Test: Multiple years with different rates
def test_multiple_years_different_rates():
    """
    Test that different years use their respective historical rates.
    """
    history = {
        '2023-12-31': {'revenue': 1000.0},
        '2022-12-31': {'revenue': 1000.0},
        '2021-12-31': {'revenue': 1000.0}
    }
    
    historical_fx_rates = {
        '2023-12-31': 1.30,
        '2022-12-31': 1.20,
        '2021-12-31': 1.10
    }
    
    converted_history, warnings = FinancialDataProcessor.apply_historical_fx_rates(
        history,
        historical_fx_rates,
        'GBP',
        'USD',
        1.0
    )
    
    # Each year should use its own rate
    assert abs(converted_history['2023-12-31']['revenue'] - 1300.0) < 0.01
    assert abs(converted_history['2022-12-31']['revenue'] - 1200.0) < 0.01
    assert abs(converted_history['2021-12-31']['revenue'] - 1100.0) < 0.01
    
    # No warnings (all rates available)
    assert len(warnings) == 0


# Test: Warning message format
def test_warning_message_format():
    """
    Test that warning messages are properly formatted with year list.
    """
    history = {
        '2023-12-31': {'revenue': 1000.0},
        '2022-12-31': {'revenue': 1000.0},
        '2021-12-31': {'revenue': 1000.0}
    }
    
    # Only 2023 has a rate, others will fall back
    historical_fx_rates = {
        '2023-12-31': 1.30,
        '2022-12-31': None,
        '2021-12-31': None
    }
    
    converted_history, warnings = FinancialDataProcessor.apply_historical_fx_rates(
        history,
        historical_fx_rates,
        'GBP',
        'USD',
        1.25
    )
    
    # Should have one warning
    assert len(warnings) == 1
    
    # Warning should mention both fallback years
    warning = warnings[0]
    assert '2022' in warning
    assert '2021' in warning
    assert 'fallback' in warning.lower()
    assert '1.2500' in warning  # Current rate


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
