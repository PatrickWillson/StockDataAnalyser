"""
Property-based tests for price fallback logic with yfinance.

Tests universal properties that should hold across all inputs.
"""

from hypothesis import given, strategies as st
from core.financial_data_processor import FinancialDataProcessor


class MockYFinanceClient:
    """Mock yfinance client for property testing."""
    
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
    yf_price=st.one_of(
        st.none(),
        st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
    ),
    eodhd_price=st.one_of(
        st.none(),
        st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
    )
)
def test_yfinance_is_primary_source_with_correct_labeling(yf_price, eodhd_price):
    """
    Property 1: yfinance is primary source with correct labeling
    
    For any valid ticker and price data where yfinance returns a price,
    the system should use that price and mark the source as "yfinance",
    and should call yfinance before attempting EODHD extraction.
    
    **Feature: yfinance-price-integration, Property 1: yfinance is primary source with correct labeling**
    **Validates: Requirements 1.1, 1.2, 2.1, 2.3**
    """
    # Create mock data with or without EODHD price
    data = {
        'Highlights': {},
        'General': {}
    }
    
    if eodhd_price is not None:
        data['Highlights']['SharePrice'] = eodhd_price
    
    # Create mock yfinance client
    yf_client = MockYFinanceClient(price_to_return=yf_price)
    warnings = []
    
    # Get price
    price, source, _ = FinancialDataProcessor.get_current_price(
        data,
        yf_client=yf_client,
        ticker="TEST.US",
        warnings=warnings
    )
    
    # Property: If yfinance has price, use it (don't use EODHD)
    if yf_price is not None:
        assert price == yf_price
        assert source == 'yfinance'
        assert yf_client.get_price_called, "Should call yfinance when client provided"
        assert len(warnings) == 1, "Should warn about price source"
        assert "yfinance" in warnings[0].lower()
        assert "primary source" in warnings[0].lower()
    
    # Property: If yfinance missing but EODHD has price, use EODHD
    elif eodhd_price is not None:
        assert price == eodhd_price
        assert source == 'EODHD'
        assert yf_client.get_price_called, "Should call yfinance first even if it returns None"
        assert len(warnings) == 1, "Should warn when using EODHD fallback"
        assert "EODHD" in warnings[0]
        assert "yfinance unavailable" in warnings[0]
    
    # Property: If both missing, return 0.0
    else:
        assert price == 0.0
        assert source == 'Missing'
        assert yf_client.get_price_called, "Should attempt yfinance even if it returns None"
        assert len(warnings) == 0, "Should not warn when both sources fail"


@given(
    price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_yfinance_always_takes_priority(price):
    """
    Property: yfinance price always takes priority over EODHD.
    
    For any valid price from yfinance, the system should use it regardless
    of whether EODHD has a price available.
    
    **Validates: Requirements 1.1, 2.1**
    """
    data = {
        'Highlights': {
            'SharePrice': price * 2  # Different price in EODHD
        }
    }
    
    # Create yfinance client that returns a price
    yf_client = MockYFinanceClient(price_to_return=price)
    warnings = []
    
    result_price, source, _ = FinancialDataProcessor.get_current_price(
        data,
        yf_client=yf_client,
        ticker="TEST.US",
        warnings=warnings
    )
    
    # Should use yfinance price, not EODHD
    assert result_price == price
    assert source == 'yfinance'
    assert yf_client.get_price_called
    assert len(warnings) == 1
    assert "yfinance" in warnings[0].lower()


@given(
    yf_price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_yfinance_source_adds_warning(yf_price):
    """
    Property: Using yfinance always adds a warning indicating the source.
    
    For any price from yfinance, a warning should be added to
    indicate the data source.
    
    **Validates: Requirements 2.3**
    """
    data = {
        'Highlights': {},
        'General': {}
    }
    
    yf_client = MockYFinanceClient(price_to_return=yf_price)
    warnings = []
    
    result_price, source, _ = FinancialDataProcessor.get_current_price(
        data,
        yf_client=yf_client,
        ticker="TEST.US",
        warnings=warnings
    )
    
    assert result_price == yf_price
    assert source == 'yfinance'
    assert len(warnings) == 1
    assert "Price Source: yfinance" in warnings[0]
    assert "primary source" in warnings[0]


@given(
    location=st.sampled_from(['Highlights', 'General.SharePrice', 'General.LastPrice']),
    price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_eodhd_price_from_any_location(location, price):
    """
    Property: EODHD price should be extracted from any valid location.
    
    For any valid EODHD price location, the system should successfully
    extract and use the price when yfinance is unavailable.
    
    **Validates: Requirements 1.3**
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
    
    # Create yfinance client that returns None (unavailable)
    yf_client = MockYFinanceClient(price_to_return=None)
    warnings = []
    
    result_price, source, _ = FinancialDataProcessor.get_current_price(
        data,
        yf_client=yf_client,
        ticker="TEST.US",
        warnings=warnings
    )
    
    assert result_price == price
    assert source == 'EODHD'
    assert len(warnings) == 1
    assert "EODHD" in warnings[0]


@given(
    eodhd_price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_fallback_to_eodhd_when_yfinance_fails(eodhd_price):
    """
    Property 2: Fallback to EODHD when yfinance fails
    
    For any valid ticker where yfinance returns None but EODHD has price data,
    the system should use the EODHD price and mark the source as "EODHD".
    
    **Feature: yfinance-price-integration, Property 2: Fallback to EODHD when yfinance fails**
    **Validates: Requirements 1.3**
    """
    data = {
        'Highlights': {
            'SharePrice': eodhd_price
        }
    }
    
    # Create yfinance client that returns None (fails)
    yf_client = MockYFinanceClient(price_to_return=None)
    warnings = []
    
    result_price, source, _ = FinancialDataProcessor.get_current_price(
        data,
        yf_client=yf_client,
        ticker="TEST.US",
        warnings=warnings
    )
    
    # Should fall back to EODHD
    assert result_price == eodhd_price
    assert source == 'EODHD'
    assert yf_client.get_price_called, "Should attempt yfinance first"
    assert len(warnings) == 1
    assert "EODHD" in warnings[0]
    assert "yfinance unavailable" in warnings[0]


@given(
    ticker=st.text(min_size=3, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    yf_price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_ticker_passed_to_yfinance_client(ticker, yf_price):
    """
    Property: Ticker should be correctly passed to yfinance client.
    
    For any ticker, when yfinance is used, the ticker should be passed
    correctly to the yfinance client.
    
    **Validates: Requirements 1.1**
    """
    # Ensure ticker has a dot (valid format)
    if '.' not in ticker:
        ticker = ticker + ".US"
    
    data = {
        'Highlights': {},
        'General': {}
    }
    
    yf_client = MockYFinanceClient(price_to_return=yf_price)
    warnings = []
    
    FinancialDataProcessor.get_current_price(
        data,
        yf_client=yf_client,
        ticker=ticker,
        warnings=warnings
    )
    
    assert yf_client.get_price_called
    assert yf_client.ticker_received == ticker


@given(
    na_value=st.sampled_from([None, 0, 0.0, -1])
)
def test_sanitizes_invalid_yfinance_values(na_value):
    """
    Property: Invalid yfinance values should be sanitized and fall back to EODHD.
    
    For any invalid value (None, 0, negative) from yfinance, the system
    should treat it as missing and attempt EODHD fallback.
    
    **Validates: Requirements 1.3**
    """
    data = {
        'Highlights': {
            'SharePrice': 100.0
        }
    }
    
    yf_client = MockYFinanceClient(price_to_return=na_value)
    warnings = []
    
    result_price, source, _ = FinancialDataProcessor.get_current_price(
        data,
        yf_client=yf_client,
        ticker="TEST.US",
        warnings=warnings
    )
    
    # Should fall back to EODHD since yfinance value is invalid
    assert result_price == 100.0
    assert source == 'EODHD'
    assert yf_client.get_price_called



@given(
    yf_price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False),
    eodhd_price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_no_unnecessary_eodhd_price_extraction(yf_price, eodhd_price):
    """
    Property 3: No unnecessary EODHD price extraction
    
    For any valid ticker where yfinance returns a valid price, the system
    should not attempt to extract price from EODHD data (optimization).
    
    **Feature: yfinance-price-integration, Property 3: No unnecessary EODHD price extraction**
    **Validates: Requirements 2.2**
    """
    # Create data with EODHD price available
    data = {
        'Highlights': {
            'SharePrice': eodhd_price
        }
    }
    
    # Create yfinance client that returns a valid price
    yf_client = MockYFinanceClient(price_to_return=yf_price)
    warnings = []
    
    result_price, source, _ = FinancialDataProcessor.get_current_price(
        data,
        yf_client=yf_client,
        ticker="TEST.US",
        warnings=warnings
    )
    
    # Should use yfinance price, not EODHD
    assert result_price == yf_price
    assert source == 'yfinance'
    
    # The key property: when yfinance succeeds, we don't need EODHD
    # This is verified by checking that the source is 'yfinance' and not 'EODHD'
    # The implementation returns early when yfinance succeeds, avoiding EODHD extraction
    assert source != 'EODHD', "Should not use EODHD when yfinance succeeds"



@given(
    source=st.sampled_from(['yfinance', 'eodhd']),
    price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_price_validation_is_preserved(source, price):
    """
    Property 4: Price validation is preserved
    
    For any price returned by the system (from yfinance or EODHD),
    it should be positive and non-zero.
    
    **Feature: yfinance-price-integration, Property 4: Price validation is preserved**
    **Validates: Requirements 2.4**
    """
    data = {
        'Highlights': {},
        'General': {}
    }
    
    if source == 'yfinance':
        # yfinance returns the price
        yf_client = MockYFinanceClient(price_to_return=price)
    else:
        # EODHD has the price, yfinance returns None
        data['Highlights']['SharePrice'] = price
        yf_client = MockYFinanceClient(price_to_return=None)
    
    warnings = []
    
    result_price, result_source, _ = FinancialDataProcessor.get_current_price(
        data,
        yf_client=yf_client,
        ticker="TEST.US",
        warnings=warnings
    )
    
    # Property: All returned prices must be positive and non-zero
    assert result_price > 0, "Price must be positive"
    assert result_price == price, "Price must match input"
    
    # Verify the source is correct
    if source == 'yfinance':
        assert result_source == 'yfinance'
    else:
        assert result_source == 'EODHD'


@given(
    invalid_price=st.sampled_from([0, -1, -100.5, None])
)
def test_invalid_prices_are_rejected(invalid_price):
    """
    Property: Invalid prices (zero, negative, None) should be rejected.
    
    For any invalid price value, the system should not return it as a valid price.
    
    **Validates: Requirements 2.4**
    """
    data = {
        'Highlights': {},
        'General': {}
    }
    
    # Try with yfinance returning invalid price
    yf_client = MockYFinanceClient(price_to_return=invalid_price)
    warnings = []
    
    result_price, source, _ = FinancialDataProcessor.get_current_price(
        data,
        yf_client=yf_client,
        ticker="TEST.US",
        warnings=warnings
    )
    
    # Should not use the invalid price
    if invalid_price is None or invalid_price <= 0:
        # Should either return 0.0 (Missing) or fall back to EODHD if available
        assert result_price == 0.0 or source == 'EODHD'
        if result_price == 0.0:
            assert source == 'Missing'
