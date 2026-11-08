"""
A FundamentalsSource that picks a source per exchange from the ticker's suffix (AAPL.US -> "US").

The free resolution path routes `.US` to SEC EDGAR + Yahoo; adapters for other markets are added as
routes. A ticker whose exchange has no route is not covered (no dossier rather than a guess).
"""

from typing import Mapping, Sequence

from core.errors import TickerNotCoveredError
from core.fundamentals import CompanyFundamentals
from core.ports import FundamentalsSource


class RoutingFundamentalsSource:
    """core.ports.FundamentalsSource delegating to one source per exchange code."""

    def __init__(self, routes: Mapping[str, FundamentalsSource], name: str):
        self.routes = {exchange.upper(): source for exchange, source in routes.items()}
        self.name = name

    def source_for(self, ticker: str) -> FundamentalsSource:
        exchange = ticker.rsplit('.', 1)[1].upper() if '.' in ticker else ''
        if exchange not in self.routes:
            supported = ", ".join(sorted(self.routes))
            raise TickerNotCoveredError(
                f"{ticker}: no {self.name} fundamentals source for exchange {exchange or '(none)'!r} yet "
                f"(supported: {supported}); use SYMBOL.EXCHANGE, or FUNDAMENTALS_PROVIDER=eodhd")
        return self.routes[exchange]

    def fetch_fundamentals(self, ticker: str) -> CompanyFundamentals:
        return self.source_for(ticker).fetch_fundamentals(ticker)


class FallbackFundamentalsSource:
    """
    core.ports.FundamentalsSource trying sources in order: the first that covers the ticker is used (the SEC route,
    then the European route). A source's other failures (rate limits, network) are raised, not passed over.
    """

    def __init__(self, sources: Sequence[FundamentalsSource], name: str):
        self.sources = tuple(sources)
        self.name = name

    def fetch_fundamentals(self, ticker: str) -> CompanyFundamentals:
        reasons = []
        for source in self.sources:
            try:
                return source.fetch_fundamentals(ticker)
            except TickerNotCoveredError as e:
                reasons.append(f"{getattr(source, 'name', type(source).__name__)}: {e}")
        raise TickerNotCoveredError(f"{ticker}: not covered by any source. " + " | ".join(reasons))
