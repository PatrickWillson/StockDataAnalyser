"""
Valuation method settings.

These are this project's choices for applying Graham's ideas (see
docs/GRAHAM_METHODOLOGY.md §2, §4.6, §7), not Graham's fixed constants
(those are in graham_constants.py and investor_thresholds.py).
"""

from typing import Final

# Normalized Graham Number and 3-year average P/E: average EPS of the most recent
# N reported years (GRAHAM_METHODOLOGY §4.6: "average earnings of the past three years")
NORMALIZED_EPS_YEARS: Final[int] = 3

# EPV (capitalised past earning power): average net income over at least MIN and at
# most MAX complete years (GRAHAM_METHODOLOGY §2.1: "five or seven or perhaps ten years")
EPV_MIN_YEARS: Final[int] = 7
EPV_MAX_YEARS: Final[int] = 10

# Flag a deep-value opportunity when price is more than this % below net-net value
DEEP_VALUE_MIN_DISCOUNT_PCT: Final[float] = 2.0
