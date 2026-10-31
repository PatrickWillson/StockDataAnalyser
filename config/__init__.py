"""
Configuration module for Stock Data Analyser.

This module centralizes all configuration constants, thresholds, and settings
used throughout the application. All configuration values are immutable to
ensure consistency and prevent accidental modifications.
"""

from config.graham_constants import GRAHAM_MULTIPLIER, COST_OF_CAPITAL
from config.investor_thresholds import (
    DefensiveThresholds,
    EnterprisingThresholds,
    DEFENSIVE,
    ENTERPRISING
)
from config.api_config import APIConfig, EODHD_CONFIG, FX_CONFIG
from config.output_config import OutputConfig
from config.data_quality_config import (
    LONDON_FIX_PE_THRESHOLD,
    SHARE_COUNT_MAX_DIFF_PCT,
    PE_MAX_DIFF_PCT,
    BVPS_MAX_DIFF_PCT,
    PROFITABILITY_MAX_DIFF_PCT,
    DIVIDEND_SOURCE_MAX_DIFF_PCT,
    API_DATA_MAX_AGE_DAYS,
    ANNUAL_REPORT_MAX_AGE_MONTHS,
    DAYS_PER_MONTH,
    FISCAL_YEAR_END_LOOKBACK_DAYS,
    MIN_HISTORY_YEARS_RECOMMENDED,
    MAX_CONSECUTIVE_YEAR_GAPS,
    ANOMALY_Z_SCORE_THRESHOLD,
    ANOMALY_MIN_DATA_POINTS,
)
from config.valuation_config import (
    NORMALIZED_EPS_YEARS,
    EPV_MIN_YEARS,
    EPV_MAX_YEARS,
    DEEP_VALUE_MIN_DISCOUNT_PCT,
    STRONG_BUY_MIN_MOS_PCT,
)

__all__ = [
    'GRAHAM_MULTIPLIER',
    'COST_OF_CAPITAL',
    'DefensiveThresholds',
    'EnterprisingThresholds',
    'DEFENSIVE',
    'ENTERPRISING',
    'APIConfig',
    'EODHD_CONFIG',
    'FX_CONFIG',
    'OutputConfig',
    'LONDON_FIX_PE_THRESHOLD',
    'SHARE_COUNT_MAX_DIFF_PCT',
    'PE_MAX_DIFF_PCT',
    'BVPS_MAX_DIFF_PCT',
    'PROFITABILITY_MAX_DIFF_PCT',
    'DIVIDEND_SOURCE_MAX_DIFF_PCT',
    'API_DATA_MAX_AGE_DAYS',
    'ANNUAL_REPORT_MAX_AGE_MONTHS',
    'DAYS_PER_MONTH',
    'FISCAL_YEAR_END_LOOKBACK_DAYS',
    'MIN_HISTORY_YEARS_RECOMMENDED',
    'MAX_CONSECUTIVE_YEAR_GAPS',
    'ANOMALY_Z_SCORE_THRESHOLD',
    'ANOMALY_MIN_DATA_POINTS',
    'NORMALIZED_EPS_YEARS',
    'EPV_MIN_YEARS',
    'EPV_MAX_YEARS',
    'DEEP_VALUE_MIN_DISCOUNT_PCT',
    'STRONG_BUY_MIN_MOS_PCT',
]
