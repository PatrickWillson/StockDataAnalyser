"""
Unit tests for Alpha Vantage client.

Tests exchange code translation, API response parsing, error handling, and API key validation.
"""

import pytest
from unittest.mock import Mock, patch
from clients.alphavantage_client import AlphaVantageClient
import requests


class TestAlphaVantageClient:
    """Unit tests for AlphaVantageClient."""
    
    def test_exchange_translation_us_stocks(self):
        """Test that US stocks have no suffix."""
        client = AlphaVantageClient(api_key="test_key")
        result = client._translate_ticker("AAPL", "US")
        assert result == "AAPL"
    
    def test_exchange_translation_lse_stocks(self):
        """Test that LSE stocks get .LON suffix."""
        client = AlphaVantageClient(api_key="test_key")
        result = client._translate_ticker("YU", "LSE")
        assert result == "YU.LON"
    
    def test_exchange_translation_all_mapped_exchanges(self):
        """Test exchange code translation for all mapped exchanges."""
        client = AlphaVantageClient(api_key="test_key")
        
        # Test a sample from each region
        test_cases = [
            ("AAPL", "US", "AAPL"),  # North America - no suffix
            ("RY", "TO", "RY.TO"),  # Toronto
            ("VOD", "LSE", "VOD.LON"),  # London
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
        """Test that unmapped exchange codes return None."""
        client = AlphaVantageClient(api_key="test_key", debug=False)
        result = client._translate_ticker("TEST", "UNKNOWN_EXCHANGE")
        assert result is None
    
    def test_parse_ticker_valid(self):
        """Test parsing valid ticker format."""
        client = AlphaVantageClient(api_key="test_key")
        symbol, exchange = client._parse_ticker("YU.LSE")
        assert symbol == "YU"
        assert exchange == "LSE"
    
    def test_parse_ticker_invalid_no_dot(self):
        """Test parsing invalid ticker without dot."""
        client = AlphaVantageClient(api_key="test_key")
        symbol, exchange = client._parse_ticker("AAPL")
        assert symbol is None
        assert exchange is None
    
    def test_parse_ticker_invalid_multiple_dots(self):
        """Test parsing invalid ticker with multiple dots."""
        client = AlphaVantageClient(api_key="test_key")
        symbol, exchange = client._parse_ticker("TEST.SOME.THING")
        assert symbol is None
        assert exchange is None
    
    @patch.object(AlphaVantageClient, '_make_request')
    def test_get_price_success(self, mock_request):
        """Test successful price fetch from GLOBAL_QUOTE."""
        client = AlphaVantageClient(api_key="test_key")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Global Quote': {
                '01. symbol': 'AAPL',
                '05. price': '150.25'
            }
        }
        mock_request.return_value = mock_response
        
        price = client.get_price("AAPL.US")
        assert price == 150.25
    
    @patch.object(AlphaVantageClient, '_make_request')
    def test_get_price_no_price_in_response(self, mock_request):
        """Test handling of response without price data."""
        client = AlphaVantageClient(api_key="test_key", debug=False)
        
        # Mock response without price
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Global Quote': {}
        }
        mock_request.return_value = mock_response
        
        price = client.get_price("AAPL.US")
        assert price is None
    
    @patch.dict('os.environ', {}, clear=True)
    def test_get_price_missing_api_key(self):
        """Test that missing API key returns None with warning."""
        client = AlphaVantageClient(api_key=None, debug=False)
        price = client.get_price("AAPL.US")
        assert price is None
    
    @patch.object(AlphaVantageClient, '_make_request')
    def test_get_price_invalid_ticker_format(self, mock_request):
        """Test handling of invalid ticker format."""
        client = AlphaVantageClient(api_key="test_key", debug=False)
        price = client.get_price("INVALID_TICKER")
        assert price is None
        # Should not make API request for invalid ticker
        mock_request.assert_not_called()
    
    @patch.object(AlphaVantageClient, '_make_request')
    def test_get_price_unmapped_exchange(self, mock_request):
        """Test handling of unmapped exchange code."""
        client = AlphaVantageClient(api_key="test_key", debug=False)
        price = client.get_price("TEST.UNKNOWN")
        assert price is None
        # Should not make API request for unmapped exchange
        mock_request.assert_not_called()
    
    @patch.object(AlphaVantageClient, '_make_request')
    def test_get_price_401_authentication_error(self, mock_request):
        """Test handling of 401 authentication error."""
        client = AlphaVantageClient(api_key="invalid_key", debug=False)
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response
        
        price = client.get_price("AAPL.US")
        assert price is None
    
    @patch.object(AlphaVantageClient, '_make_request')
    def test_get_price_429_rate_limit(self, mock_request):
        """Test handling of 429 rate limit error."""
        client = AlphaVantageClient(api_key="test_key", debug=False)
        
        mock_response = Mock()
        mock_response.status_code = 429
        mock_request.return_value = mock_response
        
        price = client.get_price("AAPL.US")
        assert price is None
    
    @patch.object(AlphaVantageClient, '_make_request')
    def test_get_price_api_error_message(self, mock_request):
        """Test handling of API error message in response."""
        client = AlphaVantageClient(api_key="test_key", debug=False)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Error Message': 'Invalid API call'
        }
        mock_request.return_value = mock_response
        
        price = client.get_price("AAPL.US")
        assert price is None
    
    @patch.object(AlphaVantageClient, '_make_request')
    def test_get_price_rate_limit_note(self, mock_request):
        """Test handling of rate limit note in response."""
        client = AlphaVantageClient(api_key="test_key", debug=False)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Note': 'Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute.'
        }
        mock_request.return_value = mock_response
        
        price = client.get_price("AAPL.US")
        assert price is None
    
    @patch.object(AlphaVantageClient, '_make_request')
    def test_get_price_request_exception(self, mock_request):
        """Test handling of request exceptions."""
        client = AlphaVantageClient(api_key="test_key", debug=False)
        
        mock_request.side_effect = requests.exceptions.RequestException("Network error")
        
        price = client.get_price("AAPL.US")
        assert price is None
    
    @patch.object(AlphaVantageClient, '_make_request')
    def test_get_price_json_parsing_error(self, mock_request):
        """Test handling of JSON parsing errors."""
        client = AlphaVantageClient(api_key="test_key", debug=False)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_request.return_value = mock_response
        
        price = client.get_price("AAPL.US")
        assert price is None
    
    @patch.object(AlphaVantageClient, '_make_request')
    def test_get_price_invalid_price_format(self, mock_request):
        """Test handling of invalid price format in response."""
        client = AlphaVantageClient(api_key="test_key", debug=False)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Global Quote': {
                '05. price': 'not_a_number'
            }
        }
        mock_request.return_value = mock_response
        
        price = client.get_price("AAPL.US")
        assert price is None
    
    @patch.dict('os.environ', {'ALPHAVANTAGE_API_KEY': 'env_key'})
    def test_api_key_from_environment(self):
        """Test that API key is loaded from environment variable."""
        client = AlphaVantageClient()
        assert client.api_key == 'env_key'
    
    def test_api_key_from_parameter(self):
        """Test that API key can be passed as parameter."""
        client = AlphaVantageClient(api_key='param_key')
        assert client.api_key == 'param_key'
    
    def test_debug_mode_enabled(self):
        """Test that debug mode can be enabled."""
        client = AlphaVantageClient(api_key='test_key', debug=True)
        assert client.debug is True
    
    def test_debug_mode_disabled_by_default(self):
        """Test that debug mode is disabled by default."""
        client = AlphaVantageClient(api_key='test_key')
        assert client.debug is False
