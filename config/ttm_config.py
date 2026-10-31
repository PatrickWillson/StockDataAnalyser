"""
TTM (trailing twelve months) analysis settings.

Reporting-frequency detection, gap and span checks for selecting periodic statements.
Engineering choices, not Graham's criteria (Graham tests use annual audited data only — see GRAHAM_METHODOLOGY §8).
"""

from typing import Final, Tuple

# Frequency detection: mean interval between the most recent periodic statements
FREQUENCY_DETECTION_MAX_PERIODS: Final[int] = 5                      # 5 dates -> 4 intervals
QUARTERLY_INTERVAL_DAYS: Final[Tuple[int, int]] = (75, 105)          # inclusive range
SEMI_ANNUAL_INTERVAL_DAYS: Final[Tuple[int, int]] = (150, 210)       # inclusive range

# Periods summed for TTM
QUARTERLY_PERIODS: Final[int] = 4
SEMI_ANNUAL_PERIODS: Final[int] = 2

# Gap detection: an interval above expected + tolerance counts as missing period(s)
QUARTERLY_EXPECTED_INTERVAL_DAYS: Final[int] = 90
QUARTERLY_GAP_TOLERANCE_DAYS: Final[int] = 30
SEMI_ANNUAL_EXPECTED_INTERVAL_DAYS: Final[int] = 180
SEMI_ANNUAL_GAP_TOLERANCE_DAYS: Final[int] = 45

# Span check: first-to-last selected period must fall in this range (days, inclusive)
QUARTERLY_SPAN_DAYS: Final[Tuple[int, int]] = (225, 315)             # 3 intervals x 90 +/- 45
SEMI_ANNUAL_SPAN_DAYS: Final[Tuple[int, int]] = (150, 210)           # 1 interval x 180 +/- 30

# Period dates outside these limits are flagged as invalid
EARLIEST_PERIOD_YEAR: Final[int] = 1950
MAX_FUTURE_YEARS: Final[int] = 1                                     # up to Dec 31 of next year

