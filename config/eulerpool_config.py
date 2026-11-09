"""
Eulerpool settings: history before a European company's first ESEF report (European route, step 5;
claude-output/EU_XBRL_EULERPOOL_SCOPE.md; docs/CODEBASE_GUIDE.md §12.1).

Eulerpool (https://eulerpool.com) is a commercial data vendor. Its key is optional (EULERPOOL_API_KEY in .env, sent
only as a header; the free plan is for non-commercial use). Its figures are vendor data, not filings: they are used
only for years before the filed (ESEF) history, and only field by field where they agreed with the filed figures in
every overlapping year (GRAHAM_METHODOLOGY §8.11).
"""

from typing import Final

EULERPOOL_BASE_URL: Final[str] = "https://api.eulerpool.com/api/1"
EULERPOOL_USER_AGENT: Final[str] = "StockDataAnalyser (no-reply@example.invalid)"
EULERPOOL_MIN_REQUEST_INTERVAL: Final[float] = 0.3          # seconds between requests

# Overlap gate: an Eulerpool field is used for the older years only if, in every year it overlaps the filings (at
# least EULERPOOL_MIN_OVERLAP_YEARS), it is within EULERPOOL_MATCH_REL of the filed figure (EULERPOOL_MATCH_REL_STRICT
# when the reporting currency differs from the listing's, where its errors clustered: silent conversions of
# TotalEnergies, Pharming, Cellectis, and per-year differences for AstraZeneca and BP), or within
# EULERPOOL_MATCH_ABS (Eulerpool reports whole millions). Share counts: within EULERPOOL_SHARES_REL (a year-end count
# against the filings' count, often a weighted average).
EULERPOOL_MIN_OVERLAP_YEARS: Final[int] = 2
EULERPOOL_MATCH_REL: Final[float] = 0.01
EULERPOOL_MATCH_REL_STRICT: Final[float] = 0.005
EULERPOOL_MATCH_ABS: Final[float] = 1.1e6
EULERPOOL_SHARES_REL: Final[float] = 0.05
# A fiscal year end in Eulerpool matches the filed one within this many days
EULERPOOL_DATE_TOLERANCE_DAYS: Final[int] = 10
