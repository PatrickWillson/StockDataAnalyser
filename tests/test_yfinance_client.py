"""
Unit tests for yfinance client.

Tests exchange code translation, API response parsing, error handling, and price fetching.
"""

from unittest.mock import patch, MagicMock
from clients.yfinance_client import YFinanceClient
from core.price_quote import PriceQuote


class TestYFinanceClient:
    """Unit tests for YFinanceClient."""
    
    def test_exchange_translation_us_stocks(self):
        """Test that US stocks have no suffix."""
        client = YFinanceClient()
        result = client._translate_ticker("AAPL", "US")
        assert result == "AAPL"
    
    def test_exchange_translation_lse_stocks(self):
        """Test that LSE stocks get .L suffix."""
        client = YFinanceClient()
        result = client._translate_ticker("YU", "LSE")
        assert result == "YU.L"
    
    def test_exchange_translation_all_mapped_exchanges(self):
        """Test exchange code translation for all mapped exchanges."""
        client = YFinanceClient()
        
        # Test a sample from each region
        test_cases = [
            ("AAPL", "US", "AAPL"),  # North America - no suffix
            ("RY", "TO", "RY.TO"),  # Toronto
            ("VOD", "LSE", "VOD.L"),  # London
            ("BMW", "XETRA", "BMW.DE"),  # Germany
            ("BNP", "PA", "BNP.PA"),  # Paris
            ("BHP", "AU", "BHP.AX"),  # Australia
            ("SONY", "TSE", "SONY.T"),  # Tokyo
            ("0700", "HK", "0700.HK"),  # Hong Kong
            ("RELIANCE", "NSE", "RELIANCE.NS"),  # India
            ("VALE", "SA", "VALE.SA"),  # Brazil
        ]
        
        for symbol, exchange, expected in test_cases:
            result = client._translate_ticker(symbol, exchange)
            assert result == expected, f"Failed for {symbol}.{exchange}: expected {expected}, got {result}"
    
    def test_exchange_translation_unmapped_exchange(self):
        """Test that unmapped exchange codes return symbol without suffix."""
        client = YFinanceClient(debug=False)
        result = client._translate_ticker("TEST", "UNKNOWN_EXCHANGE")
        # Should return the symbol without suffix for unmapped exchanges
        assert result == "TEST"
    
    def test_parse_ticker_valid(self):
        """Test parsing valid ticker format."""
        client = YFinanceClient()
        symbol, exchange = client._parse_ticker("YU.LSE")
        assert symbol == "YU"
        assert exchange == "LSE"
    
    def test_parse_ticker_invalid_no_dot(self):
        """Test parsing invalid ticker without dot."""
        client = YFinanceClient()
        symbol, exchange = client._parse_ticker("AAPL")
        assert symbol is None
        assert exchange is None
    
    def test_parse_ticker_share_class_symbol(self):
        """A symbol may contain dots (share classes): split on the last dot."""
        client = YFinanceClient()
        assert client._parse_ticker("BRK.B.US") == ("BRK.B", "US")
        assert client._parse_ticker("BT.A.LSE") == ("BT.A", "LSE")
    
    def test_translate_share_class_uses_dash(self):
        """Yahoo writes share classes with a dash: BRK.B -> BRK-B, BT.A on LSE -> BT-A.L."""
        client = YFinanceClient()
        assert client._translate_ticker("BRK.B", "US") == "BRK-B"
        assert client._translate_ticker("BT.A", "LSE") == "BT-A.L"
    
    def test_saudi_and_london_international_suffixes(self):
        client = YFinanceClient()
        assert client._translate_ticker("2222", "SAU") == "2222.SR"
        assert client._translate_ticker("SMSN", "IL") == "SMSN.IL"
    
    @patch('yfinance.Ticker')
    def test_get_quote_success(self, mock_ticker_class):
        """Test successful price fetch from yfinance."""
        client = YFinanceClient()
        
        # Mock yfinance.Ticker and fast_info
        mock_ticker = MagicMock()
        mock_ticker.fast_info = {'last_price': 150.25, 'currency': 'USD'}
        mock_ticker_class.return_value = mock_ticker
        
        assert client.get_quote("AAPL.US") == PriceQuote(150.25, "USD")
        mock_ticker_class.assert_called_once_with("AAPL")
    
    @patch('yfinance.Ticker')
    def test_get_quote_no_price_in_response(self, mock_ticker_class):
        """Test handling of response without price data."""
        client = YFinanceClient(debug=False)
        
        # Mock response without price
        mock_ticker = MagicMock()
        mock_ticker.fast_info = {}
        mock_ticker_class.return_value = mock_ticker
        
        price = client.get_quote("AAPL.US")
        assert price is None
    
    @patch('yfinance.Ticker')
    def test_get_quote_invalid_ticker_format(self, mock_ticker_class):
        """Test handling of invalid ticker format."""
        client = YFinanceClient(debug=False)
        price = client.get_quote("INVALID_TICKER")
        assert price is None
        # Should not make API request for invalid ticker
        mock_ticker_class.assert_not_called()
    
    @patch('yfinance.Ticker')
    def test_get_quote_unmapped_exchange(self, mock_ticker_class):
        """Test handling of unmapped exchange code."""
        client = YFinanceClient(debug=False)
        
        # Mock yfinance.Ticker
        mock_ticker = MagicMock()
        mock_ticker.fast_info = {'last_price': 100.0, 'currency': 'USD'}
        mock_ticker_class.return_value = mock_ticker
        
        # Still attempts the bare symbol; core rejects the quote unless its currency matches
        assert client.get_quote("TEST.UNKNOWN") == PriceQuote(100.0, "USD")
        mock_ticker_class.assert_called_once_with("TEST")
    
    @patch('yfinance.Ticker')
    def test_get_quote_network_error(self, mock_ticker_class):
        """Test handling of network errors."""
        client = YFinanceClient(debug=False)
        
        mock_ticker_class.side_effect = Exception("Network error")
        
        price = client.get_quote("AAPL.US")
        assert price is None
    
    @patch('yfinance.Ticker')
    def test_get_quote_invalid_price_value(self, mock_ticker_class):
        """Test handling of invalid price values (negative or zero)."""
        client = YFinanceClient(debug=False)
        
        # Test negative price
        mock_ticker = MagicMock()
        mock_ticker.fast_info = {'last_price': -10.0}
        mock_ticker_class.return_value = mock_ticker
        
        price = client.get_quote("AAPL.US")
        assert price is None
        
        # Test zero price
        mock_ticker.fast_info = {'last_price': 0.0}
        price = client.get_quote("AAPL.US")
        assert price is None
    
    @patch('yfinance.Ticker')
    def test_get_quote_none_price(self, mock_ticker_class):
        """Test handling of None price in fast_info."""
        client = YFinanceClient(debug=False)
        
        mock_ticker = MagicMock()
        mock_ticker.fast_info = {'last_price': None}
        mock_ticker_class.return_value = mock_ticker
        
        price = client.get_quote("AAPL.US")
        assert price is None
    
    def test_debug_mode_enabled(self):
        """Test that debug mode can be enabled."""
        client = YFinanceClient(debug=True)
        assert client.debug is True
    
    def test_debug_mode_disabled_by_default(self):
        """Test that debug mode is disabled by default."""
        client = YFinanceClient()
        assert client.debug is False
    
    @patch('yfinance.Ticker')
    def test_get_quote_lse_ticker(self, mock_ticker_class):
        """Test price fetching for LSE ticker."""
        client = YFinanceClient()
        
        mock_ticker = MagicMock()
        mock_ticker.fast_info = {'last_price': 1250.0, 'currency': 'GBp'}
        mock_ticker_class.return_value = mock_ticker
        
        assert client.get_quote("YU.LSE") == PriceQuote(1250.0, "GBp")
        mock_ticker_class.assert_called_once_with("YU.L")
    
    @patch('yfinance.Ticker')
    def test_get_quote_toronto_ticker(self, mock_ticker_class):
        """Test price fetching for Toronto ticker."""
        client = YFinanceClient()
        
        mock_ticker = MagicMock()
        mock_ticker.fast_info = {'last_price': 85.30}
        mock_ticker_class.return_value = mock_ticker
        
        # Currency not reported -> None (core then rejects the quote)
        assert client.get_quote("RY.TO") == PriceQuote(85.30, None)
        mock_ticker_class.assert_called_once_with("RY.TO")
    
    def test_parse_ticker_empty_string(self):
        """Test parsing empty string."""
        client = YFinanceClient()
        symbol, exchange = client._parse_ticker("")
        assert symbol is None
        assert exchange is None
    
    def test_parse_ticker_none(self):
        """Test parsing None."""
        client = YFinanceClient()
        symbol, exchange = client._parse_ticker(None)
        assert symbol is None
        assert exchange is None
    
    def test_translate_ticker_empty_symbol(self):
        """Test translation with empty symbol."""
        client = YFinanceClient()
        result = client._translate_ticker("", "US")
        assert result is None
    
    def test_translate_ticker_empty_exchange(self):
        """Test translation with empty exchange."""
        client = YFinanceClient()
        result = client._translate_ticker("AAPL", "")
        assert result is None

    @patch('yfinance.Ticker')
    def test_historical_prices_are_not_dividend_adjusted(self, mock_ticker_class):
        """F8: split-adjusted 'Close' only (auto_adjust=False), never the dividend-adjusted series."""
        import pandas as pd
        hist = pd.DataFrame({'Close': [100.0], 'Adj Close': [90.0]},
                            index=pd.DatetimeIndex([pd.Timestamp('2023-12-29')]))
        mock_ticker_class.return_value.history.return_value = hist
        prices = YFinanceClient().fetch_historical_prices("AAPL.US", "2023-01-01", "2024-01-01")
        assert prices == {'2023-12-29': 100.0}
        assert mock_ticker_class.return_value.history.call_args.kwargs['auto_adjust'] is False


def test_annual_statements_are_read_from_yahoo(monkeypatch):
    import sys
    from tests.snapshot_fakes import FakeYFinanceModule
    from clients.yfinance_client import YFinanceClient
    fake = FakeYFinanceModule({"HBH.DE": {"last": 80.0, "currency": "EUR", "closes": {}, "statements": {
        "income": {"Total Revenue": {"2026-02-28": 6433.9e6, "2025-02-28": 6200e6}, "Basic EPS": {"2026-02-28": 8.66}},
        "balance": {"Total Assets": {"2026-02-28": 4800e6}}}}})
    monkeypatch.setitem(sys.modules, "yfinance", fake)
    s = YFinanceClient().fetch_annual_statements("HBH.XETRA")
    assert s.yahoo_symbol == "HBH.DE"
    assert s.income["Total Revenue"] == {"2026-02-28": 6433.9e6, "2025-02-28": 6200e6}
    assert s.income["Basic EPS"] == {"2026-02-28": 8.66}                  # empty cell left out
    assert s.balance["Total Assets"] == {"2026-02-28": 4800e6}
    assert YFinanceClient().fetch_annual_statements("NOPE.XETRA") is None
