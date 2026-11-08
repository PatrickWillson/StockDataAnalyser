"""
filings.xbrl.org settings for the European route (ESEF annual reports; docs/CODEBASE_GUIDE.md §12).

filings.xbrl.org is run by XBRL International and publishes the ESEF reports that EU and UK regulated-market
issuers file with their national storage mechanisms, as xBRL-JSON. It needs no key, and its terms say: "At present,
there are no restrictions on the ways that the data can be used" (https://filings.xbrl.org/about.html). It is not
an official regulator service, and it is incomplete: Germany and Ireland are absent, as is AIM (not a regulated
market). Its rate limit is undocumented; it answers HTTP 429 when exceeded.
"""

from typing import Final, Mapping

ESEF_BASE_URL: Final[str] = "https://filings.xbrl.org"
ESEF_FILINGS_URL: Final[str] = ESEF_BASE_URL + "/api/filings"
ESEF_ENTITIES_URL: Final[str] = ESEF_BASE_URL + "/api/entities"

# Sent with every request. Neutral contact: the user's own address must never be sent.
ESEF_USER_AGENT: Final[str] = "StockDataAnalyser research (no-reply@example.invalid)"

# Seconds between requests (the limit is undocumented; a report's JSON can be several MB)
ESEF_MIN_REQUEST_INTERVAL: Final[float] = 1.0

# On HTTP 429: wait the server's Retry-After (capped), this many times, before giving up
ESEF_RATE_LIMIT_RETRIES: Final[int] = 2
ESEF_MAX_RETRY_WAIT: Final[float] = 60.0

ESEF_PAGE_SIZE: Final[int] = 100

# Companies whose ESEF filer the name lookup cannot settle (more than one entity matches), by EODHD ticker -> LEI
# (European route decision of 2026-11-08, as SEC_FOREIGN_FILER_CIKS: an ambiguous lookup gives no dossier unless
# listed here)
ESEF_ENTITY_LEIS: Final[Mapping[str, str]] = {}
