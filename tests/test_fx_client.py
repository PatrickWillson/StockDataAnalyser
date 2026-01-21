"""
Tests for FX Client

Tests the FX rate fetching functionality.
"""

import pytest
from unittest.mock import Mock, patch
from clients.fx_client import FXClient


def test_same_currency_returns_one():
    """Test that converting same currency returns 1.0."""
    client = FXClient()
    rate = client.get_rate('USD', 'USD')
    assert rate == 1.0


def test_fx_rate_caching():
    """Test that FX rates are cached to avoid repeated API calls."""
    client = FXClient()
    
    with patch.object(client.session, 'get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rates': {'USD': 1.10}
        }
        mock_get.return_value = mock_response
        
        # First call should hit the API
        rate1 = client.get_rate('EUR', 'USD')
        assert rate1 == 1.10
        assert mock_get.call_count == 1
        
        # Second call should use cache
        rate2 = client.get_rate('EUR', 'USD')
        assert rate2 == 1.10
        assert mock_get.call_count == 1  # Still 1, not 2


def test_clear_cache():
    """Test that clearing cache forces new API calls."""
    client = FXClient()
    
    with patch.object(client.session, 'get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rates': {'USD': 1.10}
        }
        mock_get.return_value = mock_response
        
        # First call
        client.get_rate('EUR', 'USD')
        assert mock_get.call_count == 1
        
        # Clear cache
        client.clear_cache()
        
        # Second call should hit API again
        client.get_rate('EUR', 'USD')
        assert mock_get.call_count == 2


def test_api_failure_returns_none():
    """Test that API failures return None gracefully."""
    client = FXClient()
    
    with patch.object(client.session, 'get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        rate = client.get_rate('EUR', 'USD')
        assert rate is None


def test_network_error_returns_none():
    """Test that network errors return None gracefully."""
    client = FXClient()
    
    with patch.object(client.session, 'get') as mock_get:
        mock_get.side_effect = Exception("Network error")
        
        rate = client.get_rate('EUR', 'USD')
        assert rate is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
