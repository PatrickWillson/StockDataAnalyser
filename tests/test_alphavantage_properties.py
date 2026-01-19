"""
Property-based tests for Alpha Vantage client.

Tests universal properties that should hold across all valid inputs.
"""

import pytest
from hypothesis import given, strategies as st
from clients.alphavantage_client import AlphaVantageClient


class TestAlphaVantageProperties:
    """Property-based tests for AlphaVantageClient."""
    
    @given(
        eodhd_exchange=st.sampled_from(list(AlphaVantageClient.EXCHANGE_MAPPING.keys()))
    )
    def test_exchange_translation_consistency(self, eodhd_exchange):
        """
        Property 2: Exchange Code Translation Consistency
        
        For any EODHD exchange code in the mapping table, translating to 
        Alpha Vantage format should produce a valid result.
        
        **Validates: Requirements 10.4, 10.5**
        """
        client = AlphaVantageClient(api_key="test_key")
        av_ticker = client._translate_ticker("TEST", eodhd_exchange)
        
        # Should never return None for mapped exchanges
        assert av_ticker is not None, f"Translation returned None for mapped exchange: {eodhd_exchange}"
        
        # US stocks should have no suffix
        if eodhd_exchange == 'US':
            assert av_ticker == "TEST", f"US stocks should have no suffix, got: {av_ticker}"
        else:
            # Other exchanges should have a suffix (either dot notation or just the symbol)
            # The suffix is defined in EXCHANGE_MAPPING
            expected_suffix = AlphaVantageClient.EXCHANGE_MAPPING[eodhd_exchange]
            expected_ticker = f"TEST{expected_suffix}"
            assert av_ticker == expected_ticker, f"Expected {expected_ticker}, got {av_ticker}"
    
    @given(
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
        eodhd_exchange=st.sampled_from(list(AlphaVantageClient.EXCHANGE_MAPPING.keys()))
    )
    def test_translation_preserves_symbol(self, symbol, eodhd_exchange):
        """
        Property: Translation should always preserve the original symbol.
        
        For any valid symbol and mapped exchange, the translated ticker should
        start with the original symbol.
        """
        client = AlphaVantageClient(api_key="test_key")
        av_ticker = client._translate_ticker(symbol, eodhd_exchange)
        
        assert av_ticker is not None
        assert av_ticker.startswith(symbol), f"Translated ticker {av_ticker} should start with {symbol}"
    
    @given(
        ticker_symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
        eodhd_exchange=st.sampled_from(list(AlphaVantageClient.EXCHANGE_MAPPING.keys()))
    )
    def test_parse_and_translate_roundtrip(self, ticker_symbol, eodhd_exchange):
        """
        Property: Parsing and translating should be consistent.
        
        For any valid EODHD ticker, parsing it and then translating should
        produce a valid Alpha Vantage ticker.
        """
        client = AlphaVantageClient(api_key="test_key")
        
        # Create EODHD ticker
        eodhd_ticker = f"{ticker_symbol}.{eodhd_exchange}"
        
        # Parse it
        parsed_symbol, parsed_exchange = client._parse_ticker(eodhd_ticker)
        
        # Should parse correctly
        assert parsed_symbol == ticker_symbol
        assert parsed_exchange == eodhd_exchange
        
        # Translate it
        av_ticker = client._translate_ticker(parsed_symbol, parsed_exchange)
        
        # Should produce valid result
        assert av_ticker is not None
        assert av_ticker.startswith(ticker_symbol)
    
    @given(
        unmapped_exchange=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd')))
            .filter(lambda x: x not in AlphaVantageClient.EXCHANGE_MAPPING)
    )
    def test_unmapped_exchanges_return_none(self, unmapped_exchange):
        """
        Property: Unmapped exchanges should always return None.
        
        For any exchange code not in the mapping table, translation should
        return None consistently.
        """
        client = AlphaVantageClient(api_key="test_key", debug=False)
        av_ticker = client._translate_ticker("TEST", unmapped_exchange)
        
        assert av_ticker is None, f"Unmapped exchange {unmapped_exchange} should return None"
