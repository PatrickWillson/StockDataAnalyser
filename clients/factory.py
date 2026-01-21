"""
Client Factory

Factory for creating API clients with proper dependency injection.
Centralizes client instantiation for maintainability and testability.
"""

from typing import Optional
from clients.eodhd_client import EODHDClient
from clients.yfinance_client import YFinanceClient
from clients.fx_client import FXClient
from core.currency_converter import CurrencyConverter


class ClientFactory:
    """Factory for creating API clients with proper dependency injection."""
    
    @staticmethod
    def create_eodhd_client(api_key: str, debug: bool = False) -> EODHDClient:
        """
        Create EODHD client with all dependencies.
        
        Args:
            api_key: EODHD API key
            debug: Enable debug logging
            
        Returns:
            Configured EODHDClient instance
            
        Raises:
            ValueError: If api_key is empty or None
            
        Example:
            >>> factory = ClientFactory()
            >>> client = factory.create_eodhd_client("your_api_key", debug=True)
        """
        if not api_key or not api_key.strip():
            raise ValueError("EODHD API key is required")
        
        fx_client = FXClient()
        
        return EODHDClient(
            api_key=api_key,
            fx_client=fx_client,
            debug=debug
        )
    
    @staticmethod
    def create_yfinance_client(debug: bool = False) -> YFinanceClient:
        """
        Create yfinance client.
        
        Args:
            debug: Enable debug logging
            
        Returns:
            Configured YFinanceClient instance
            
        Example:
            >>> factory = ClientFactory()
            >>> client = factory.create_yfinance_client(debug=True)
        """
        return YFinanceClient(debug=debug)
    
    @staticmethod
    def create_fx_client() -> FXClient:
        """
        Create FX rate client.
        
        Returns:
            Configured FXClient instance
            
        Example:
            >>> factory = ClientFactory()
            >>> client = factory.create_fx_client()
        """
        return FXClient()
    
    @staticmethod
    def create_currency_converter(fx_client: Optional[FXClient] = None) -> CurrencyConverter:
        """
        Create currency converter with optional FX client.
        
        Args:
            fx_client: Optional FX client for dependency injection (creates one if not provided)
            
        Returns:
            Configured CurrencyConverter instance
            
        Example:
            >>> factory = ClientFactory()
            >>> converter = factory.create_currency_converter()
            >>> # Or with custom FX client:
            >>> fx_client = factory.create_fx_client()
            >>> converter = factory.create_currency_converter(fx_client=fx_client)
        """
        return CurrencyConverter(fx_client=fx_client)
