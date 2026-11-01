"""
Risk Factors display bands.

Heuristic bands used to label figures in the dossier's Risk Factors section (e.g. "Low
volatility", "Tight coverage"). They do not affect any calculation, test or verdict, and
they are not Graham's criteria except where noted (current ratio bands reuse
investor_thresholds; see GRAHAM_METHODOLOGY §4.2 / §5.2).
"""

from typing import Final

# Market & liquidity
BETA_LOW: Final[float] = 0.5
BETA_MARKET: Final[float] = 1.0
BETA_HIGH: Final[float] = 1.5
LIQUIDITY_LOW_PCT: Final[float] = 0.1          # average daily volume as % of shares outstanding
LIQUIDITY_MODERATE_PCT: Final[float] = 0.5

# Financial strength (current ratio bands above "critical" come from investor_thresholds)
CURRENT_RATIO_CRITICAL: Final[float] = 1.0
LT_DEBT_TO_ASSETS_LOW_PCT: Final[float] = 10
LT_DEBT_TO_ASSETS_MODERATE_PCT: Final[float] = 30

# Operational stability
RISK_HISTORY_WINDOW_YEARS: Final[int] = 10     # years examined for margins, loss years, dividends
PROFIT_MARGIN_SANITY_LIMIT_PCT: Final[float] = 1e6
MARGIN_VOLATILITY_LOW_PCT: Final[float] = 5    # std dev of profit margin, percentage points
MARGIN_VOLATILITY_MODERATE_PCT: Final[float] = 10
ROE_STRONG: Final[float] = 0.15
ROE_ADEQUATE: Final[float] = 0.10

# Dividend sustainability
PAYOUT_CONSERVATIVE_PCT: Final[float] = 50
PAYOUT_MODERATE_PCT: Final[float] = 75
PAYOUT_MAX_PCT: Final[float] = 100
DIVIDEND_COVERAGE_STRONG: Final[float] = 2.0   # operating cash flow per share / dividend
DIVIDEND_COVERAGE_ADEQUATE: Final[float] = 1.5
DIVIDEND_COVERAGE_MIN: Final[float] = 1.0
DIVIDEND_MOSTLY_CONSISTENT_FRACTION: Final[float] = 0.8

# Graham's bargain margin: indicated value at least 50% above price, so a margin of safety of
# at least one-third of value (GRAHAM_METHODOLOGY §1.2, §3.3)
MOS_GRAHAM_BARGAIN_PCT: Final[float] = 100 / 3

# Data quality
INSTITUTIONAL_HIGH_PCT: Final[float] = 20
