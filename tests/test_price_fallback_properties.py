"""
Property-based tests for price fallback logic.

Tests universal properties that should hold across all inputs.
"""

import pytest
from hypothesis import given, strategies as st, assume
from core.financial_data_processor import FinancialDataProcessor


class MockAlphaVantageClient:
    """Mock Alpha Vantage client for property testing."""
    
    def __init__(self, price_to_return=None):
        self.price_to_return = price_to_return
        self.get_price_called = False
        self.ticker_received = None
    
    def get_price(self, ticker):
        """Mock get_price method."""
        self.get_price_called = True
        self.ticker_received = ticker
        return self.price_to_return


@given(
    eodhd_price=st.one_of(
        st.none(),
        st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
    ),
    av_price=st.one_of(
        st.none(),
        st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
    )
)
def test_price_fallback_ordering(eodhd_price, av_price):
    """
    Property 1: Price Fallback Ordering
    
    For any ticker where EODHD price is unavailable, the system should 
    attempt Alpha Vantage fallback before failing.
    
    **Validates: Requirements 1.1, 1.2**
    """
    # Create mock data with or without EODHD price
    data = {
        'Highlights': {},
        'General': {}
    }
    
    if eodhd_price is not None:
        data['Highlights']['SharePrice'] = eodhd_price
    
    # Create mock AV client
    av_client = MockAlphaVantageClient(price_to_return=av_price)
    warnings = []
    
    # Get price
    price, source = FinancialDataProcessor.get_current_price(
        data,
        av_client=av_client,
        ticker="TEST.US",
        warnings=warnings
    )
    
    # Property: If EODHD has price, use it (don't call AV)
    if eodhd_price is not None:
        assert price == eodhd_price
        assert source == 'EODHD'
        assert not av_client.get_price_called, "Should not call AV when EODHD has price"
        assert len(warnings) == 0, "Should not warn when using EODHD price"
    
    # Property: If EODHD missing but AV has price, use AV
    elif av_price is not None:
        assert price == av_price
        assert source == 'Alpha Vantage'
        assert av_client.get_price_called, "Should call AV when EODHD missing"
        assert len(warnings) == 1, "Should warn when using AV price"
        assert "Alpha Vantage" in warnings[0]
    
    # Property: If both missing, return 0.0
    else:
        assert price == 0.0
        assert source == 'Missing'
        assert av_client.get_price_called, "Should attempt AV even if it returns None"
        assert len(warnings) == 0, "Should not warn when both sources fail"


@given(
    price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_eodhd_always_takes_priority(price):
    """
    Property: EODHD price always takes priority over Alpha Vantage.
    
    For any valid price from EODHD, the system should use it regardless
    of whether Alpha Vantage is available.
    
    **Validates: Requirements 1.1**
    """
    data = {
        'Highlights': {
            'SharePrice': price
        }
    }
    
    # Create AV client that would return a different price
    av_client = MockAlphaVantageClient(price_to_return=price * 2)
    warnings = []
    
    result_price, source = FinancialDataProcessor.get_current_price(
        data,
        av_client=av_client,
        ticker="TEST.US",
        warnings=warnings
    )
    
    # Should use EODHD price, not AV
    assert result_price == price
    assert source == 'EODHD'
    assert not av_client.get_price_called
    assert len(warnings) == 0


@given(
    av_price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_av_fallback_adds_warning(av_price):
    """
    Property: Using Alpha Vantage fallback always adds a warning.
    
    For any price from Alpha Vantage, a warning should be added to
    indicate the data source.
    
    **Validates: Requirements 1.6**
    """
    data = {
        'Highlights': {},
        'General': {}
    }
    
    av_client = MockAlphaVantageClient(price_to_return=av_price)
    warnings = []
    
    result_price, source = FinancialDataProcessor.get_current_price(
        data,
        av_client=av_client,
        ticker="TEST.US",
        warnings=warnings
    )
    
    assert result_price == av_price
    assert source == 'Alpha Vantage'
    assert len(warnings) == 1
    assert "Price from Alpha Vantage" in warnings[0]
    assert "EODHD price unavailable" in warnings[0]


@given(
    location=st.sampled_from(['Highlights', 'General.SharePrice', 'General.LastPrice']),
    price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_eodhd_price_from_any_location(location, price):
    """
    Property: EODHD price should be extracted from any valid location.
    
    For any valid EODHD price location, the system should successfully
    extract and use the price.
    
    **Validates: Requirements 1.1**
    """
    data = {
        'Highlights': {},
        'General': {}
    }
    
    # Set price in the specified location
    if location == 'Highlights':
        data['Highlights']['SharePrice'] = price
    elif location == 'General.SharePrice':
        data['General']['SharePrice'] = price
    elif location == 'General.LastPrice':
        data['General']['LastPrice'] = price
    
    warnings = []
    result_price, source = FinancialDataProcessor.get_current_price(data, warnings=warnings)
    
    assert result_price == price
    assert source == 'EODHD'
    assert len(warnings) == 0


@given(
    ticker=st.text(min_size=3, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    av_price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_ticker_passed_to_av_client(ticker, av_price):
    """
    Property: Ticker should be correctly passed to Alpha Vantage client.
    
    For any ticker, when Alpha Vantage fallback is used, the ticker
    should be passed correctly to the AV client.
    
    **Validates: Requirements 1.1**
    """
    # Ensure ticker has a dot (valid format)
    if '.' not in ticker:
        ticker = ticker + ".US"
    
    data = {
        'Highlights': {},
        'General': {}
    }
    
    av_client = MockAlphaVantageClient(price_to_return=av_price)
    warnings = []
    
    FinancialDataProcessor.get_current_price(
        data,
        av_client=av_client,
        ticker=ticker,
        warnings=warnings
    )
    
    assert av_client.get_price_called
    assert av_client.ticker_received == ticker


@given(
    na_value=st.sampled_from([None, '', 'NA', 'N/A', 0, 0.0])
)
def test_sanitizes_invalid_eodhd_values(na_value):
    """
    Property: Invalid EODHD values should be sanitized to 0.0.
    
    For any invalid value (None, empty string, 'NA', etc.), the system
    should treat it as missing and attempt fallback.
    
    **Validates: Requirements 1.1, 1.2**
    """
    data = {
        'Highlights': {
            'SharePrice': na_value
        }
    }
    
    av_client = MockAlphaVantageClient(price_to_return=100.0)
    warnings = []
    
    result_price, source = FinancialDataProcessor.get_current_price(
        data,
        av_client=av_client,
        ticker="TEST.US",
        warnings=warnings
    )
    
    # Should fall back to AV since EODHD value is invalid
    assert result_price == 100.0
    assert source == 'Alpha Vantage'
    assert av_client.get_price_called
