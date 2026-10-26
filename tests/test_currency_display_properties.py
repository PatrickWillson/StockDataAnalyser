"""
Property-based tests for currency display consistency.

**Feature: graham-data-quality, Property 7: Currency Display Consistency**
**Validates: Requirements 4.1, 4.2**

Tests that currency display format is consistent across all price values
and correctly shows trading currency first with optional conversion.
"""

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



@given(
    price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False),
    price_currency=st.sampled_from(['USD', 'GBP', 'GBX', 'EUR', 'CAD']),
    financials_currency=st.sampled_from(['USD', 'GBP', 'EUR', 'CAD']),
    fx_rate=st.floats(min_value=0.5, max_value=2.0, allow_nan=False, allow_infinity=False)
)
def test_yfinance_price_currency_conversion_preserved(price, price_currency, financials_currency, fx_rate):
    """
    Property 5: Currency handling is preserved
    
    For any price from yfinance, if currency conversion is needed,
    the system should apply FX conversion and generate appropriate warnings.
    
    **Feature: yfinance-price-integration, Property 5: Currency handling is preserved**
    **Validates: Requirements 5.1, 5.2, 5.4**
    """
    from core.currency_converter import CurrencyConverter
    
    # Create a mock FX client that returns our test rate
    class MockFXClient:
        def get_rate(self, from_currency, to_currency):
            if from_currency == to_currency:
                return 1.0
            return fx_rate
    
    converter = CurrencyConverter(fx_client=MockFXClient())
    
    # Apply currency conversion
    converted_price, success = converter.convert(
        price, price_currency, financials_currency
    )
    
    if price_currency == financials_currency:
        # No conversion needed
        assert converted_price == price
        assert success
    elif (price_currency == 'GBX' and financials_currency == 'GBP') or \
         (price_currency == 'GBP' and financials_currency == 'GBX'):
        # Special case: GBX ↔ GBP conversion (not using FX rate)
        if price_currency == 'GBX' and financials_currency == 'GBP':
            expected_price = price / 100
        else:  # GBP to GBX
            expected_price = price * 100
        assert abs(converted_price - expected_price) < 0.01
        assert success
        
        # Check conversion history
        warning = converter.get_consolidated_warning()
        assert 'GBX' in warning or 'GBP' in warning
    else:
        # Conversion should be applied using FX rate
        expected_price = price * fx_rate
        assert abs(converted_price - expected_price) < 0.01
        assert success
        
        # Check conversion history
        warning = converter.get_consolidated_warning()
        assert price_currency in warning and financials_currency in warning



@given(
    price=st.floats(min_value=100.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    eps=st.floats(min_value=0.01, max_value=20.0, allow_nan=False, allow_infinity=False)
)
def test_london_fix_applies_to_yfinance_prices(price, eps):
    """
    Property 6: London Fix applies to yfinance prices
    
    For any LSE stock where yfinance returns a price and P/E ratio > 500,
    the system should apply the London Fix (divide by 100) and log the conversion.
    
    **Feature: yfinance-price-integration, Property 6: London Fix applies to yfinance prices**
    **Validates: Requirements 5.3**
    """
    from core.currency_converter import CurrencyConverter
    
    converter = CurrencyConverter()
    
    # Calculate P/E ratio
    pe_ratio = price / eps
    
    # Apply London Fix
    adjusted_price, fix_applied = converter.apply_london_fix(price, eps, 'LSE')
    
    if pe_ratio > 500:
        # London Fix should be applied (price divided by 100)
        expected_price = price / 100
        assert abs(adjusted_price - expected_price) < 0.01
        assert fix_applied
    else:
        # London Fix should NOT be applied
        assert adjusted_price == price
        assert not fix_applied


@given(
    price=st.floats(min_value=100.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    eps=st.floats(min_value=0.01, max_value=20.0, allow_nan=False, allow_infinity=False),
    exchange=st.sampled_from(['US', 'NYSE', 'NASDAQ', 'TO', 'XETRA'])
)
def test_london_fix_only_applies_to_lse(price, eps, exchange):
    """
    Property 6: London Fix applies to yfinance prices (LSE only)
    
    For any non-LSE stock, the London Fix should never be applied
    regardless of P/E ratio.
    
    **Feature: yfinance-price-integration, Property 6: London Fix applies to yfinance prices**
    **Validates: Requirements 5.3**
    """
    from core.currency_converter import CurrencyConverter
    
    converter = CurrencyConverter()
    
    # Apply London Fix
    adjusted_price, fix_applied = converter.apply_london_fix(price, eps, exchange)
    
    # London Fix should NOT be applied for non-LSE exchanges
    assert adjusted_price == price
    assert not fix_applied
