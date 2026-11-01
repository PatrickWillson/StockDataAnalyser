"""
Unit tests for ClientFactory.

Tests client creation, parameter validation, debug flag propagation, and dependency injection.
"""

import pytest
from clients.factory import ClientFactory
from clients.eodhd_client import EODHDClient
from clients.yfinance_client import YFinanceClient
from clients.fx_client import FXClient
from core.currency_converter import CurrencyConverter


class TestClientFactory:
    """Test suite for ClientFactory."""
    
    def test_create_eodhd_client_success(self):
        """Test successful EODHD client creation."""
        api_key = "test_api_key_12345"
        
        client = ClientFactory.create_eodhd_client(api_key, debug=False)
        
        assert isinstance(client, EODHDClient)
        assert client.api_key == api_key
        assert client.debug is False
        assert client.name == "EODHD"
    
    def test_create_eodhd_client_with_debug(self):
        """Test EODHD client creation with debug flag enabled."""
        api_key = "test_api_key_12345"
        
        client = ClientFactory.create_eodhd_client(api_key, debug=True)
        
        assert isinstance(client, EODHDClient)
        assert client.api_key == api_key
        assert client.debug is True
    
    def test_create_eodhd_client_empty_api_key(self):
        """Test EODHD client creation fails with empty API key."""
        with pytest.raises(ValueError, match="EODHD API key is required"):
            ClientFactory.create_eodhd_client("", debug=False)
    
    def test_create_eodhd_client_none_api_key(self):
        """Test EODHD client creation fails with None API key."""
        with pytest.raises(ValueError, match="EODHD API key is required"):
            ClientFactory.create_eodhd_client(None, debug=False)
    
    def test_create_eodhd_client_whitespace_api_key(self):
        """Test EODHD client creation fails with whitespace-only API key."""
        with pytest.raises(ValueError, match="EODHD API key is required"):
            ClientFactory.create_eodhd_client("   ", debug=False)
    
    def test_create_yfinance_client_success(self):
        """Test successful yfinance client creation."""
        client = ClientFactory.create_yfinance_client(debug=False)
        
        assert isinstance(client, YFinanceClient)
        assert client.debug is False
    
    def test_create_yfinance_client_with_debug(self):
        """Test yfinance client creation with debug flag enabled."""
        client = ClientFactory.create_yfinance_client(debug=True)
        
        assert isinstance(client, YFinanceClient)
        assert client.debug is True
    
    def test_create_fx_client_success(self):
        """Test successful FX client creation."""
        client = ClientFactory.create_fx_client()
        
        assert isinstance(client, FXClient)
        assert hasattr(client, '_cache')
    
    def test_create_currency_converter_success(self):
        """Test successful currency converter creation without FX client."""
        converter = ClientFactory.create_currency_converter()
        
        assert isinstance(converter, CurrencyConverter)
        assert isinstance(converter.fx_client, FXClient)
        assert hasattr(converter, 'conversion_history')
    
    def test_create_currency_converter_with_fx_client(self):
        """Test currency converter creation with custom FX client (dependency injection)."""
        # Create custom FX client
        custom_fx_client = FXClient()
        
        # Create converter with custom FX client
        converter = ClientFactory.create_currency_converter(fx_client=custom_fx_client)
        
        assert isinstance(converter, CurrencyConverter)
        assert converter.fx_client is custom_fx_client
    
    def test_eodhd_client_only_fetches(self):
        """The EODHD adapter fetches and maps; FX and assembly are separate ports / core."""
        client = ClientFactory.create_eodhd_client("test_api_key_12345")
        
        assert not hasattr(client, 'fx_client')
        assert not hasattr(client, 'assembler')
    
    def test_default_fundamentals_provider_is_eodhd(self):
        provider = ClientFactory.fundamentals_provider()
        
        assert provider.name == "eodhd" and provider.required_env == ("EODHD_API_KEY",)
        assert provider.secret_env == ("EODHD_API_KEY",)
        assert ClientFactory.fundamentals_provider(" EODHD ") is provider
        assert isinstance(ClientFactory.create_fundamentals_source({"EODHD_API_KEY": "key"}, "eodhd"), EODHDClient)
    
    def test_unknown_fundamentals_provider_is_rejected(self):
        with pytest.raises(ValueError, match="registered: eodhd"):
            ClientFactory.fundamentals_provider("acme")
    
    def test_quote_and_rate_sources(self):
        assert isinstance(ClientFactory.create_quote_source(), YFinanceClient)
        assert isinstance(ClientFactory.create_rate_source(), FXClient)
    
    def test_debug_flag_propagates_to_eodhd_client(self):
        """Test that debug flag is properly propagated to EODHD client."""
        api_key = "test_api_key_12345"
        
        # Test with debug=False
        client_no_debug = ClientFactory.create_eodhd_client(api_key, debug=False)
        assert client_no_debug.debug is False
        
        # Test with debug=True
        client_with_debug = ClientFactory.create_eodhd_client(api_key, debug=True)
        assert client_with_debug.debug is True
    
    def test_debug_flag_propagates_to_yfinance_client(self):
        """Test that debug flag is properly propagated to yfinance client."""
        # Test with debug=False
        client_no_debug = ClientFactory.create_yfinance_client(debug=False)
        assert client_no_debug.debug is False
        
        # Test with debug=True
        client_with_debug = ClientFactory.create_yfinance_client(debug=True)
        assert client_with_debug.debug is True
    
    def test_multiple_client_creation_independence(self):
        """Test that multiple client creations are independent."""
        api_key = "test_api_key_12345"
        
        # Create two EODHD clients
        client1 = ClientFactory.create_eodhd_client(api_key, debug=False)
        client2 = ClientFactory.create_eodhd_client(api_key, debug=True)
        
        # Verify they are different instances
        assert client1 is not client2
        assert client1.debug != client2.debug
    
    def test_factory_methods_are_static(self):
        """Test that factory methods can be called without instantiation."""
        # Should be able to call without creating factory instance
        client = ClientFactory.create_fx_client()
        assert isinstance(client, FXClient)
        
        # Verify methods are static
        assert callable(ClientFactory.create_eodhd_client)
        assert callable(ClientFactory.create_yfinance_client)
        assert callable(ClientFactory.create_fx_client)
        assert callable(ClientFactory.create_currency_converter)
