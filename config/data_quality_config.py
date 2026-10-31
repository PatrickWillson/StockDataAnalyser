"""
Data-quality and source-validation settings.

Thresholds for checks on incoming data (currency heuristics, cross-checks against
EODHD's own figures, staleness, history gaps, anomaly detection). These are
engineering choices, not Graham's criteria.
"""

from typing import Final


# Cross-validation against EODHD pre-computed values: warn when our figure differs by more than X%
SHARE_COUNT_MAX_DIFF_PCT: Final[float] = 5
PE_MAX_DIFF_PCT: Final[float] = 20
BVPS_MAX_DIFF_PCT: Final[float] = 15
PROFITABILITY_MAX_DIFF_PCT: Final[float] = 20      # ROE, ROA and profit margin
DIVIDEND_SOURCE_MAX_DIFF_PCT: Final[float] = 10    # cash-flow dividend vs forward rate

# Staleness
API_DATA_MAX_AGE_DAYS: Final[int] = 7              # EODHD "UpdatedAt"
ANNUAL_REPORT_MAX_AGE_MONTHS: Final[float] = 9     # most recent annual report
DAYS_PER_MONTH: Final[float] = 30.44               # 365.25 / 12

# Matching daily prices/FX rates to fiscal year-ends: look back up to N days
FISCAL_YEAR_END_LOOKBACK_DAYS: Final[int] = 7

# History completeness
MIN_HISTORY_YEARS_RECOMMENDED: Final[int] = 10
MAX_MISSING_HISTORY_YEARS: Final[int] = 3          # warn when this many fiscal years are missing in the reported range

# Anomaly detection (EPS growth Z-scores)
ANOMALY_Z_SCORE_THRESHOLD: Final[float] = 2.0
ANOMALY_MIN_DATA_POINTS: Final[int] = 3            # minimum years and growth rates
