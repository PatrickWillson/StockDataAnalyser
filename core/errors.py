"""
Errors raised when no reliable dossier can be produced (data source failures, missing price).

Clients and core raise these instead of exiting; the CLI turns them into an error message
and exit code 1 ("no data is better than wrong data").
"""


class DataSourceError(Exception):
    """A required data source failed; analysis cannot continue."""


class EODHDAuthError(DataSourceError):
    """EODHD rejected the API key (HTTP 401)."""


class EODHDRateLimitError(DataSourceError):
    """EODHD rate limit exceeded (HTTP 429)."""


class EODHDRequestError(DataSourceError):
    """The EODHD request failed (network error or unexpected HTTP status)."""


class PriceUnavailableError(DataSourceError):
    """No current price from yfinance or EODHD."""
