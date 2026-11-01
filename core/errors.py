"""
Errors raised when no reliable dossier can be produced (data source failures, missing price).

Clients and core raise these instead of exiting; the CLI turns them into an error message
and exit code 1 ("no data is better than wrong data"). They are provider-neutral: an adapter
may subclass them with vendor-specific names (e.g. clients.eodhd_client.EODHDAuthError).
"""


class DataSourceError(Exception):
    """A required data source failed; analysis cannot continue."""


class SourceAuthError(DataSourceError):
    """The data source rejected the credentials (e.g. HTTP 401)."""


class SourceRateLimitError(DataSourceError):
    """The data source's rate limit was exceeded (e.g. HTTP 429)."""


class SourceRequestError(DataSourceError):
    """A data source request failed (network error, unexpected status or invalid response)."""


class PriceUnavailableError(DataSourceError):
    """No usable current price from the quote source."""
