"""
Property-based tests for currency display consistency.

**Feature: graham-data-quality, Property 7: Currency Display Consistency**
**Validates: Requirements 4.1, 4.2**

Tests that currency display format is consistent across all price values
and correctly shows trading currency first with optional conversion.
"""

import pytest
from hypothesis import given, strategies as st
from stock_data_analyser import format_price_display


# Common currency codes
CURRENCY_CODES = ['USD', 'GBP', 'GBX', 'EUR', 'JPY', 'CAD', 'AUD', 'CHF']


@given(
    price=st.floats(min_value=0.01, max_value=1000000.0, allow_nan=False, allow_infinity=False),
    currency=st.sampled_from(CURRENCY_CODES)
)
def test_single_currency_always_shows_currency_code(price, currency):
    """
    Property 7: Currency Display Consistency
    
    For any price and currency, when trading and financials currencies are the same,
    the display should always include the currency code.
    
    **Validates: Requirements 4.1**
    """
    result = format_price_display(price, currency, currency)
    
    # Should contain the currency code
    assert currency in result
    
    # Should not contain parentheses (no conversion)
    assert '(' not in result
    assert ')' not in result


@given(
    price=st.floats(min_value=0.01, max_value=1000000.0, allow_nan=False, allow_infinity=False),
    trading_currency=st.sampled_from(CURRENCY_CODES),
    financials_currency=st.sampled_from(CURRENCY_CODES),
    converted_value=st.floats(min_value=0.01, max_value=1000000.0, allow_nan=False, allow_infinity=False)
)
def test_dual_currency_shows_both_currencies(price, trading_currency, financials_currency, converted_value):
    """
    Property 7: Currency Display Consistency
    
    For any price with different trading and financials currencies,
    the display should show both currencies with trading currency first.
    
    **Validates: Requirements 4.1, 4.2**
    """
    if trading_currency == financials_currency:
        # Skip when currencies are the same
        return
    
    result = format_price_display(price, trading_currency, financials_currency, converted_value)
    
    # Should contain both currency codes
    assert trading_currency in result
    assert financials_currency in result
    
    # Trading currency should appear before financials currency
    trading_pos = result.index(trading_currency)
    financials_pos = result.index(financials_currency)
    assert trading_pos < financials_pos
    
    # Should contain parentheses for conversion
    assert '(' in result
    assert ')' in result


@given(
    price=st.floats(min_value=0.01, max_value=1000000.0, allow_nan=False, allow_infinity=False),
    trading_currency=st.sampled_from(CURRENCY_CODES),
    financials_currency=st.sampled_from(CURRENCY_CODES),
    converted_value=st.floats(min_value=0.01, max_value=1000000.0, allow_nan=False, allow_infinity=False)
)
def test_trading_currency_always_appears_first(price, trading_currency, financials_currency, converted_value):
    """
    Property 7: Currency Display Consistency
    
    For any price display, the trading currency should always appear
    before the financials currency in the output string.
    
    **Validates: Requirements 4.1**
    """
    # Skip when currencies are the same (only one currency appears)
    if trading_currency == financials_currency:
        return
    
    result = format_price_display(price, trading_currency, financials_currency, converted_value)
    
    # Find positions of both currencies
    trading_pos = result.find(trading_currency)
    financials_pos = result.find(financials_currency)
    
    # Trading currency should always appear first
    assert trading_pos < financials_pos


@given(
    price=st.floats(min_value=0.01, max_value=1000000.0, allow_nan=False, allow_infinity=False),
    trading_currency=st.sampled_from(CURRENCY_CODES)
)
def test_format_contains_numeric_value(price, trading_currency):
    """
    Property 7: Currency Display Consistency
    
    For any price, the formatted output should contain a numeric representation
    of the price value.
    
    **Validates: Requirements 4.1**
    """
    result = format_price_display(price, trading_currency, trading_currency)
    
    # Should contain at least one digit
    assert any(c.isdigit() for c in result)
    
    # Should contain decimal point for precision
    assert '.' in result


@given(
    prices=st.lists(
        st.floats(min_value=0.01, max_value=1000000.0, allow_nan=False, allow_infinity=False),
        min_size=3,
        max_size=10
    ),
    trading_currency=st.sampled_from(CURRENCY_CODES),
    financials_currency=st.sampled_from(CURRENCY_CODES)
)
def test_format_consistency_across_multiple_prices(prices, trading_currency, financials_currency):
    """
    Property 7: Currency Display Consistency
    
    For any list of prices with the same currency pair, all formatted outputs
    should follow the same structural pattern.
    
    **Validates: Requirements 4.4**
    """
    if trading_currency == financials_currency:
        # Single currency case
        results = [format_price_display(p, trading_currency, financials_currency) for p in prices]
        
        # All should NOT contain parentheses
        for result in results:
            assert '(' not in result
            assert ')' not in result
            assert trading_currency in result
    else:
        # Dual currency case
        converted_values = [p * 1.2 for p in prices]  # Arbitrary conversion
        results = [
            format_price_display(p, trading_currency, financials_currency, cv)
            for p, cv in zip(prices, converted_values)
        ]
        
        # All should contain parentheses and both currencies
        for result in results:
            assert '(' in result
            assert ')' in result
            assert trading_currency in result
            assert financials_currency in result


@given(
    price=st.floats(min_value=0.01, max_value=1000000.0, allow_nan=False, allow_infinity=False),
    trading_currency=st.sampled_from(CURRENCY_CODES),
    financials_currency=st.sampled_from(CURRENCY_CODES),
    converted_value=st.floats(min_value=0.01, max_value=1000000.0, allow_nan=False, allow_infinity=False)
)
def test_conversion_value_appears_in_parentheses(price, trading_currency, financials_currency, converted_value):
    """
    Property 7: Currency Display Consistency
    
    For any price with currency conversion, the converted value should appear
    within parentheses in the output.
    
    **Validates: Requirements 4.2**
    """
    if trading_currency == financials_currency:
        # Skip when currencies are the same
        return
    
    result = format_price_display(price, trading_currency, financials_currency, converted_value)
    
    # Extract content within parentheses
    if '(' in result and ')' in result:
        start = result.index('(')
        end = result.index(')')
        parentheses_content = result[start+1:end]
        
        # Should contain the financials currency
        assert financials_currency in parentheses_content
        
        # Should contain at least one digit (the converted value)
        assert any(c.isdigit() for c in parentheses_content)
