"""
RNS results announcements: history before a London-listed company's Yahoo Finance years (UK route; claude-output/
UK_HISTORY_SOURCES_2026-11-11.md; docs/CODEBASE_GUIDE.md §12.1; GRAHAM_METHODOLOGY §8.12).

A UK-listed company (main market or AIM) must publish its annual results through a Regulatory Information Service;
the final-results announcement carries the consolidated income statement for the year and the year before, in the
company's own figures. The announcements are read from the Investegate archive (https://www.investegate.co.uk, back
to 2000), whose terms allow use as a private investor, not commercially, with no redistribution: the pages are cached
under data/ (gitignored) and never committed. robots.txt allows company and announcement pages.
"""

from typing import Final

RNS_BASE_URL: Final[str] = "https://www.investegate.co.uk"
RNS_USER_AGENT: Final[str] = "StockDataAnalyser research (no-reply@example.invalid)"
RNS_MIN_REQUEST_INTERVAL: Final[float] = 2.0           # seconds between requests (a polite rate for a free archive)
RNS_MAX_LISTING_PAGES: Final[int] = 40                  # a company's announcement list, newest first, about 20 a page
RNS_LISTING_CACHE_DAYS: Final[int] = 7                  # a listing page is re-read after this; announcements never change
RNS_CACHE_DIR: Final[str] = "data/cache/rns"            # relative to the repository root

# Overlap gate: the announced net income must agree with Yahoo Finance's in every overlapping year (at least
# RNS_MIN_OVERLAP_YEARS): within RNS_MATCH_REL, or RNS_MATCH_UNITS of the statement's rounding unit (£'000: 1.5 x
# 1,000), whichever is larger. Exact company figures, so no whole-million allowance (unlike Eulerpool).
RNS_MIN_OVERLAP_YEARS: Final[int] = 2
RNS_MATCH_REL: Final[float] = 0.01
RNS_MATCH_UNITS: Final[float] = 1.5
# A statement's year end matches a Yahoo year end within this many days (52/53-week years end on different dates)
RNS_DATE_TOLERANCE_DAYS: Final[int] = 10
# Chain: the history uses only announcements linked year by year from the newest: each one's year end is the later
# one's prior year end, and its net income is within RNS_CHAIN_REL of the later one's comparative (a restatement can
# move it a little). An announcement that does not link (a TIDM reused by another company: Quadrise's QED page also
# carries an earlier QED's March-year results in £m) ends the history there.
RNS_CHAIN_REL: Final[float] = 0.05
