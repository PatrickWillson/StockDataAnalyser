"""
Tests for FX Client

Tests the FX rate fetching functionality using yfinance.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from clients.fx_client import FXClient


def test_same_currency_returns_one():
    """Test that converting same currency returns 1.0."""
    client = FXClient()
    rate = client.get_rate('USD', 'USD')
    assert rate == 1.0


def test_fx_rate_caching():
    """Test that FX rates are cached to avoid repeated API calls."""
    client = FXClient()
    
    with patch('yfinance.Ticker') as mock_ticker_class:
        # Create mock ticker object with lazy-loading dict behavior
        mock_ticker = MagicMock()
        mock_ticker.fast_info = {'lastPrice': 1.10}
        mock_ticker_class.return_value = mock_ticker
        
        # First call should hit the API
        rate1 = client.get_rate('EUR', 'USD')
        assert rate1 == 1.10
        assert mock_ticker_class.call_count == 1
        
        # Second call should use cache
        rate2 = client.get_rate('EUR', 'USD')
        assert rate2 == 1.10
        assert mock_ticker_class.call_count == 1  # Still 1, not 2


def test_clear_cache():
    """Test that clearing cache forces new API calls."""
    client = FXClient()
    
    with patch('yfinance.Ticker') as mock_ticker_class:
        # Create mock ticker object with lazy-loading dict behavior
        mock_ticker = MagicMock()
        mock_ticker.fast_info = {'lastPrice': 1.10}
        mock_ticker_class.return_value = mock_ticker
        
        # First call
        client.get_rate('EUR', 'USD')
        assert mock_ticker_class.call_count == 1
        
        # Clear cache
        client.clear_cache()
        
        # Second call should hit API again
        client.get_rate('EUR', 'USD')
        assert mock_ticker_class.call_count == 2


def test_api_failure_returns_none():
    """Test that API failures return None gracefully."""
    client = FXClient()
    
    with patch('yfinance.Ticker') as mock_ticker_class:
        # Create mock ticker with no price data
        mock_ticker = MagicMock()
        mock_ticker.fast_info = {}
        mock_ticker.info.get.return_value = None
        mock_ticker_class.return_value = mock_ticker
        
        rate = client.get_rate('EUR', 'USD')
        assert rate is None


def test_network_error_returns_none():
    """Test that network errors return None gracefully."""
    client = FXClient()
    
    with patch('yfinance.Ticker') as mock_ticker_class:
        mock_ticker_class.side_effect = Exception("Network error")
        
        rate = client.get_rate('EUR', 'USD')
        assert rate is None


def test_invalid_rate_returns_none():
    """Test that invalid rates (zero or negative) return None."""
    client = FXClient()
    
    with patch('yfinance.Ticker') as mock_ticker_class:
        # Create mock ticker with invalid price
        mock_ticker = MagicMock()
        mock_ticker.fast_info = {'lastPrice': 0}
        mock_ticker_class.return_value = mock_ticker
        
        rate = client.get_rate('EUR', 'USD')
        assert rate is None


def test_fx_ticker_format():
    """Test that FX ticker is formatted correctly for yfinance."""
    client = FXClient()
    
    with patch('yfinance.Ticker') as mock_ticker_class:
        # Create mock ticker object
        mock_ticker = MagicMock()
        mock_ticker.fast_info = {'lastPrice': 1.25}
        mock_ticker_class.return_value = mock_ticker
        
        # Get rate
        rate = client.get_rate('GBP', 'USD')
        
        # Verify yfinance.Ticker was called with correct format
        mock_ticker_class.assert_called_once_with('GBPUSD=X')
        assert rate == 1.25


def test_debug_mode():
    """Test that debug mode enables logging."""
    client = FXClient(debug=True)
    
    # Verify debug is enabled
    assert client.debug is True
    
    with patch('yfinance.Ticker') as mock_ticker_class:
        mock_ticker = MagicMock()
        mock_ticker.fast_info = {'lastPrice': 1.10}
        mock_ticker_class.return_value = mock_ticker
        
        # Should work normally with debug enabled
        rate = client.get_rate('EUR', 'USD')
        assert rate == 1.10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
