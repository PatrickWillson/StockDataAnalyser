"""
SEC EDGAR settings for the free resolution path (docs/CODEBASE_GUIDE.md §12).

SEC fair access (https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data):
at most 10 requests per second, and every request declares a User-Agent naming the requester with a
contact email (the SEC_USER_AGENT environment variable, e.g. "StockDataAnalyser Jane Doe jane@example.com").
"""

from typing import Final, Mapping, Tuple

SEC_TICKER_INDEX_URL: Final[str] = "https://www.sec.gov/files/company_tickers.json"
SEC_COMPANY_FACTS_URL: Final[str] = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SEC_SUBMISSIONS_URL: Final[str] = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_ARCHIVES_URL: Final[str] = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}"   # a filing's folder

# Seconds between requests: 0.11 s keeps a client under the SEC's 10 requests/second
SEC_MIN_REQUEST_INTERVAL: Final[float] = 0.11

# Predecessor filers of companies reorganised under a new holding company (decision D-F6, revised
# 2026-11-01: merge the predecessor's filings). The SEC has no structured predecessor/successor link:
# each keeps its own CIK, and the successor files a Form 8-K12B under the predecessor's file number.
# The successor's figures win where years overlap; the predecessor's fill the earlier years. Only list
# reorganisations that exchanged shares one for one (per-share history continues unchanged).
#   GOOGL, GOOG: Alphabet Inc. (CIK 1652044, from Oct 2015; 8-K12B 2015-10-02) succeeded Google Inc.
#                (CIK 1288776, FY2004-FY2014 filings), one Alphabet share per Google share.
#   DINO: HF Sinclair Corp (CIK 1915657, from Mar 2022; 8-K12B 2022-03-14) succeeded HollyFrontier Corp
#         (CIK 48039), each share "automatically converted into one" HF Sinclair share.
#   XOM: ExxonMobil Holdings Corp (CIK 2115436, 2026) succeeded Exxon Mobil Corp (CIK 34088, every
#        10-K to FY2025), one for one.
SEC_PREDECESSOR_CIKS: Final[Mapping[str, Tuple[str, ...]]] = {
    "GOOGL": ("0001288776",),
    "GOOG": ("0001288776",),
    "XOM": ("0000034088",),
    "DINO": ("0000048039",),
}

# Non-US companies with more than one SEC filer, settled by hand (SEC route for non-US companies, decision of
# 2026-11-07: an ambiguous lookup gives no dossier unless listed here). Keys are EODHD tickers.
#   Rio Tinto: a dual-listed company with two SEC filers, Rio Tinto plc (CIK 863064, London) and Rio Tinto Ltd
#              (CIK 887028, Sydney). The group files one 20-F, whose XBRL is under the plc's CIK (the Ltd's has
#              none); its statements and EPS are the whole group's, on plc + Ltd shares (equalised one for one),
#              so both home listings take the plc's facts.
SEC_FOREIGN_FILER_CIKS: Final[Mapping[str, str]] = {
    "RIO.LSE": "0000863064",
    "RIO.AU": "0000863064",
}
