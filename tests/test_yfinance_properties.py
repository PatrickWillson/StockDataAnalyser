"""
Property-based tests for yfinance client.

Tests universal properties that should hold across all valid inputs.
"""

import pytest
from hypothesis import given, strategies as st
from clients.yfinance_client import YFinanceClient


class TestYFinanceProperties:
    """Property-based tests for YFinanceClient."""
    
    @given(
        eodhd_exchange=st.sampled_from(list(YFinanceClient.EXCHANGE_MAPPING.keys()))
    )
    def test_exchange_translation_consistency(self, eodhd_exchange):
        """
        Property 7: Ticker translation correctness
        
        For any EODHD exchange code in the mapping table, translating to 
        yfinance format should produce a valid result.
        
        **Validates: Requirements 7.1, 7.3**
        """
        client = YFinanceClient()
        yf_ticker = client._translate_ticker("TEST", eodhd_exchange)
        
        # Should never return None for mapped exchanges
        assert yf_ticker is not None, f"Translation returned None for mapped exchange: {eodhd_exchange}"
        
        # US stocks should have no suffix
        if eodhd_exchange == 'US':
            assert yf_ticker == "TEST", f"US stocks should have no suffix, got: {yf_ticker}"
        else:
            # Other exchanges should have a suffix (either dot notation or just the symbol)
            # The suffix is defined in EXCHANGE_MAPPING
            expected_suffix = YFinanceClient.EXCHANGE_MAPPING[eodhd_exchange]
            expected_ticker = f"TEST{expected_suffix}"
            assert yf_ticker == expected_ticker, f"Expected {expected_ticker}, got {yf_ticker}"
    
    @given(
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
        eodhd_exchange=st.sampled_from(list(YFinanceClient.EXCHANGE_MAPPING.keys()))
    )
    def test_translation_preserves_symbol(self, symbol, eodhd_exchange):
        """
        Property: Translation should always preserve the original symbol.
        
        For any valid symbol and mapped exchange, the translated ticker should
        start with the original symbol.
        """
        client = YFinanceClient()
        yf_ticker = client._translate_ticker(symbol, eodhd_exchange)
        
        assert yf_ticker is not None
        assert yf_ticker.startswith(symbol), f"Translated ticker {yf_ticker} should start with {symbol}"
    
    @given(
        ticker_symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
        eodhd_exchange=st.sampled_from(list(YFinanceClient.EXCHANGE_MAPPING.keys()))
    )
    def test_parse_and_translate_roundtrip(self, ticker_symbol, eodhd_exchange):
        """
        Property: Parsing and translating should be consistent.
        
        For any valid EODHD ticker, parsing it and then translating should
        produce a valid yfinance ticker.
        """
        client = YFinanceClient()
        
        # Create EODHD ticker
        eodhd_ticker = f"{ticker_symbol}.{eodhd_exchange}"
        
        # Parse it
        parsed_symbol, parsed_exchange = client._parse_ticker(eodhd_ticker)
        
        # Should parse correctly
        assert parsed_symbol == ticker_symbol
        assert parsed_exchange == eodhd_exchange
        
        # Translate it
        yf_ticker = client._translate_ticker(parsed_symbol, parsed_exchange)
        
        # Should produce valid result
        assert yf_ticker is not None
        assert yf_ticker.startswith(ticker_symbol)
    
    @given(
        unmapped_exchange=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd')))
            .filter(lambda x: x not in YFinanceClient.EXCHANGE_MAPPING)
    )
    def test_unmapped_exchanges_return_symbol(self, unmapped_exchange):
        """
        Property 8: Unmapped exchange handling
        
        For any exchange code not in the mapping table, translation should
        return the symbol without suffix (attempting to use it as-is).
        
        **Validates: Requirements 7.2**
        """
        client = YFinanceClient(debug=False)
        yf_ticker = client._translate_ticker("TEST", unmapped_exchange)
        
        # Should return the symbol without suffix for unmapped exchanges
        assert yf_ticker == "TEST", f"Unmapped exchange {unmapped_exchange} should return symbol without suffix"
