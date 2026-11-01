"""
SEC EDGAR settings for the free resolution path (docs/CODEBASE_GUIDE.md §12).

SEC fair access (https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data):
at most 10 requests per second, and every request declares a User-Agent naming the requester with a
contact email (the SEC_USER_AGENT environment variable, e.g. "StockDataAnalyser Jane Doe jane@example.com").
"""

from typing import Final, Mapping

SEC_TICKER_INDEX_URL: Final[str] = "https://www.sec.gov/files/company_tickers.json"
SEC_COMPANY_FACTS_URL: Final[str] = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SEC_SUBMISSIONS_URL: Final[str] = "https://data.sec.gov/submissions/CIK{cik}.json"

# Seconds between requests: 0.11 s keeps a client under the SEC's 10 requests/second
SEC_MIN_REQUEST_INTERVAL: Final[float] = 0.11

# Tickers whose current CIK has no usable history because the listed company was reorganised; the
# filings with the history are under the predecessor's CIK (decision D-F6: static map + warning).
#   XOM: in 2026 the ticker moved to the new holding company ExxonMobil Holdings Corp (CIK 2115436,
#        no annual reports yet); Exxon Mobil Corp (CIK 34088) filed every 10-K up to FY2025.
SEC_CIK_OVERRIDES: Final[Mapping[str, str]] = {
    "XOM": "0000034088",
}
