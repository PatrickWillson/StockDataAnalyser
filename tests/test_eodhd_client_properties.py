"""
Property-based tests for EODHD Client

These tests verify universal properties that should hold across all valid inputs.
Each test runs 100+ iterations with randomly generated data.
"""

from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch
from clients.eodhd_client import EODHDClient


# Feature: stock-data-analyser, Property 1: Ticker suffix preservation
@settings(max_examples=100)
@given(
    base_ticker=st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=('Lu',))),
    suffix=st.sampled_from(['.US', '.L', '.TO', '.PA', '.DE', '.ST'])
)
def test_ticker_suffix_preservation(base_ticker, suffix):
    """
    Property 1: Ticker suffix preservation
    
    For any valid EODHD ticker suffix, when the system processes the ticker,
    the suffix should be passed to the API without modification.
    
    **Validates: Requirements 1.4**
    """
    ticker = f"{base_ticker}{suffix}"
    client = EODHDClient("test_api_key")
    
    # Mock the session.get to capture the URL
    with patch.object(client.session, 'get') as mock_get:
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'General': {
                'Code': base_ticker,
                'Exchange': 'TEST',
                'CurrencyCode': 'USD',
                'Officers': []
            },
            'SharesStats': {'SharesOutstanding': 1000000},
            'Financials': {
                'Balance_Sheet': {'yearly': {}},
                'Income_Statement': {'yearly': {}}
            },
            'SplitsDividends': {'NumberDividendsByYear': {}},
            'Highlights': {'SharePrice': 100.0}
        }
        mock_get.return_value = mock_response
        
        # Call the method
        try:
            client.fetch_all_data(ticker)
        except SystemExit:
            # Ignore system exits for this test
            pass
        
        # Verify the ticker was passed to the API without modification
        if mock_get.called:
            call_args = mock_get.call_args
            url = call_args[0][0] if call_args[0] else call_args[1].get('url', '')
            
            # The URL should contain the full ticker with suffix
            assert ticker in url, f"Ticker {ticker} should be preserved in API URL"



# Feature: stock-data-analyser, Property 3: London Fix application
@settings(max_examples=100)
@given(
    price=st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    eps=st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False),
    exchange=st.sampled_from(['LSE', 'NASDAQ', 'NYSE', 'TSX'])
)
def test_london_fix_application(price, eps, exchange):
    """
    Property 3: London Fix application
    
    For any LSE ticker data with varying P/E ratios:
    - Verify price is divided by 100 when P/E > 500
    - Verify price is unchanged when P/E <= 500
    
    **Validates: Requirements 3.2**
    """
    from core.currency_converter import CurrencyConverter
    
    converter = CurrencyConverter()
    
    # Calculate P/E ratio
    pe_ratio = price / eps
    
    # Apply London Fix
    adjusted_price, fix_applied = converter.apply_london_fix(price, eps, exchange)
    
    if exchange == "LSE" and pe_ratio > 500:
        # Price should be divided by 100
        expected_price = price / 100
        assert abs(adjusted_price - expected_price) < 0.01, \
            f"London Fix should divide price by 100 when P/E > 500 (P/E={pe_ratio:.2f})"
        assert fix_applied, "London Fix should be marked as applied"
    else:
        # Price should remain unchanged
        assert adjusted_price == price, \
            f"Price should not change when exchange is not LSE or P/E <= 500 (exchange={exchange}, P/E={pe_ratio:.2f})"
        assert not fix_applied, "London Fix should not be marked as applied"



# Feature: stock-data-analyser, Property 2: Currency conversion application
@settings(max_examples=100)
@given(
    price=st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    currency_pair=st.sampled_from([
        ('EUR', 'USD'), ('USD', 'EUR'), ('GBP', 'USD'), ('USD', 'GBP'),
        ('CAD', 'USD'), ('USD', 'CAD'), ('SEK', 'USD'), ('USD', 'SEK'),
        ('EUR', 'GBP'), ('GBP', 'EUR'), ('USD', 'USD'), ('EUR', 'EUR')
    ])
)
def test_currency_conversion_application(price, currency_pair):
    """
    Property 2: Currency conversion application
    
    For any currency pairs and financial data:
    - Verify conversion is applied when currencies differ
    - Verify no conversion when currencies match
    
    **Validates: Requirements 1.8**
    """
    from clients.fx_client import FXClient
    from core.currency_converter import CurrencyConverter
    
    # Create a mock FX client with fixed rates for testing
    mock_fx_client = Mock(spec=FXClient)
    mock_fx_client.get_rate = Mock(side_effect=lambda from_c, to_c: 
        1.0 if from_c == to_c else 1.5  # Simple mock: 1.5 for any conversion
    )
    
    converter = CurrencyConverter(fx_client=mock_fx_client)
    
    price_currency, financials_currency = currency_pair
    
    # Apply currency conversion
    converted_price, success = converter.convert(
        price, price_currency, financials_currency
    )
    
    if price_currency == financials_currency:
        # No conversion should occur
        assert converted_price == price, \
            f"Price should not change when currencies match ({price_currency})"
        assert success, "Conversion should succeed for same currency"
    else:
        # Conversion should occur with mocked rate
        expected_price = price * 1.5
        assert abs(converted_price - expected_price) < 0.01, \
            "Price should be converted using FX rate"
        assert abs(converted_price - expected_price) < 0.01, \
            f"Converted price should match expected (got {converted_price}, expected {expected_price})"
        assert success, "Conversion should succeed"
