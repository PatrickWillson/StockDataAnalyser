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
    'NORMALIZED_EPS_YEARS',
    'EPV_MIN_YEARS',
    'EPV_MAX_YEARS',
    'DEEP_VALUE_MIN_DISCOUNT_PCT',
    'STRONG_BUY_MIN_MOS_PCT',
]
