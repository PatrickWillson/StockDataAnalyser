"""
Ports: the interfaces through which the core gets its data (hexagonal "ports and adapters").

Python's equivalent of a Java interface here is typing.Protocol (PEP 544, structural typing):
an adapter satisfies a port by having the right methods, with no inheritance from core. Each
port is @runtime_checkable so tests can assert that an adapter conforms
(tests/test_data_source_ports.py). Adapters live in clients/ and are chosen in clients/factory.py;
nothing outside the factory and the CLI names a vendor.

To replace a vendor, write an adapter that satisfies the port (for fundamentals: map the
vendor's payloads into core.fundamentals.CompanyFundamentals, as clients/eodhd_mapper.py does for
EODHD), register it in clients/factory.py and run the adapter contract tests.
"""

from typing import Dict, List, Optional, Protocol, runtime_checkable

from core.fundamentals import CompanyFundamentals
from core.price_quote import PriceQuote


@runtime_checkable
class FundamentalsSource(Protocol):
    """Annual and periodic financial statements, dividends and company data (today: EODHD)."""

    name: str  # vendor name for labels and messages, e.g. "EODHD"

    def fetch_fundamentals(self, ticker: str) -> CompanyFundamentals:
        """
        Fundamentals for a ticker in SYMBOL.EXCHANGE form (e.g. AAPL.US, VOD.LSE).

        Raises:
            core.errors.DataSourceError (or a subclass): the source could not supply them
        """
        ...


@runtime_checkable
class QuoteSource(Protocol):
    """Current and historical market prices (today: yfinance)."""

    def get_quote(self, ticker: str) -> Optional[PriceQuote]:
        """Current price with its quote currency (e.g. GBp for LSE), or None."""
        ...

    def fetch_historical_prices(self, ticker: str, start_date: str, end_date: str) -> Optional[Dict[str, float]]:
        """Daily closes {'YYYY-MM-DD': price}, split-adjusted but not dividend-adjusted, or None."""
        ...

    def match_fiscal_year_end_prices(self, price_data: Dict[str, float],
                                     fiscal_year_ends: List[str]) -> Dict[str, Optional[float]]:
        """The close on (or shortly before) each fiscal year end."""
        ...


@runtime_checkable
class RateSource(Protocol):
    """Current and historical FX rates (today: yfinance via clients.fx_client.FXClient)."""

    def get_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Units of to_currency per unit of from_currency, or None."""
        ...

    def fetch_historical_rates(self, from_currency: str, to_currency: str,
                               start_date: str, end_date: str) -> Optional[Dict[str, float]]:
        """Daily rates {'YYYY-MM-DD': rate}, or None."""
        ...

    def match_fiscal_year_end_rates(self, rate_data: Dict[str, float],
                                    fiscal_year_ends: List[str]) -> Dict[str, Optional[float]]:
        """The rate on (or shortly before) each fiscal year end."""
        ...
