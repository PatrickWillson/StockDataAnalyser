"""
Client Factory: the composition root for data sources.

Chooses the adapter behind each port (core/ports.py). The fundamentals provider is selected by
name (the FUNDAMENTALS_PROVIDER environment variable, default "eodhd"); adding a vendor means
writing its adapter and registering it in FUNDAMENTALS_PROVIDERS below.
"""

from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Tuple
from clients.eodhd_client import EODHDClient
from clients.yfinance_client import YFinanceClient
from clients.fx_client import FXClient
from core.currency_converter import CurrencyConverter
from core.ports import FundamentalsSource, QuoteSource, RateSource


@dataclass(frozen=True)
class FundamentalsProvider:
    """A registered fundamentals vendor (or resolution path)."""
    name: str                                            # FUNDAMENTALS_PROVIDER value, e.g. "eodhd"
    required_env: Tuple[str, ...]                        # environment variables it needs (API keys, contacts)
    secret_env: Tuple[str, ...]                          # those whose values are redacted from logs
    create: Callable[[Mapping[str, str], bool], FundamentalsSource]  # (required_env values, debug) -> adapter


DEFAULT_FUNDAMENTALS_PROVIDER = "eodhd"


class ClientFactory:
    """Factory for creating API clients with proper dependency injection."""
    
    @staticmethod
    def fundamentals_provider(name: Optional[str] = None) -> FundamentalsProvider:
        """
        The registered fundamentals provider called `name` (default: DEFAULT_FUNDAMENTALS_PROVIDER).
        
        Raises:
            ValueError: no provider of that name is registered
        """
        key = (name or DEFAULT_FUNDAMENTALS_PROVIDER).strip().lower()
        if key not in FUNDAMENTALS_PROVIDERS:
            raise ValueError(f"Unknown fundamentals provider {name!r}; "
                             f"registered: {', '.join(sorted(FUNDAMENTALS_PROVIDERS))}")
        return FUNDAMENTALS_PROVIDERS[key]
    
    @staticmethod
    def create_fundamentals_source(env: Mapping[str, str], provider: Optional[str] = None,
                                   debug: bool = False) -> FundamentalsSource:
        """
        The fundamentals adapter for `provider` (default "eodhd").
        
        Args:
            env: values of the provider's required_env variables
        """
        return ClientFactory.fundamentals_provider(provider).create(env, debug)
    
    @staticmethod
    def create_quote_source(debug: bool = False) -> QuoteSource:
        """Current and historical prices (yfinance)."""
        return ClientFactory.create_yfinance_client(debug=debug)
    
    @staticmethod
    def create_rate_source() -> RateSource:
        """Current and historical FX rates (yfinance)."""
        return ClientFactory.create_fx_client()
    
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
        
        return EODHDClient(api_key=api_key, debug=debug)
    
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
        # The composition root supplies the real FX source; core never creates one
        return CurrencyConverter(fx_client=fx_client or FXClient())


# Registered fundamentals vendors. `create` looks the factory method up at call time, so tests
# can substitute it.
FUNDAMENTALS_PROVIDERS = {
    "eodhd": FundamentalsProvider(
        name="eodhd",
        required_env=("EODHD_API_KEY",),
        secret_env=("EODHD_API_KEY",),
        create=lambda env, debug: ClientFactory.create_eodhd_client(env["EODHD_API_KEY"], debug=debug),
    ),
}
