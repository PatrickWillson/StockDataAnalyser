"""
Investor Test Thresholds.

This module defines the thresholds for Graham's Defensive and Enterprising
Investor tests. These thresholds are based on Benjamin Graham's criteria
for evaluating stocks according to different investor profiles.

The thresholds are immutable (frozen dataclasses) to ensure consistency
across all analyses.
"""

from typing import Final
from dataclasses import dataclass


@dataclass(frozen=True)
class DefensiveThresholds:
    """
    Thresholds for Graham's Defensive Investor tests.
    
    The Defensive Investor seeks safety and stability, requiring stricter
    criteria for financial strength and valuation. These tests are designed
    for investors who want minimal risk and are willing to accept lower returns.
    
    Attributes:
        MIN_CURRENT_RATIO: Minimum current assets to current liabilities ratio (2.0)
        MIN_EARNINGS_YEARS: Minimum years of positive earnings required (10 years - strict Graham)
        MAX_PE_RATIO: Maximum acceptable Price-to-Earnings ratio (15.0)
        MAX_PB_RATIO: Maximum acceptable Price-to-Book ratio (1.5)
        MIN_EARNINGS_GROWTH: Minimum earnings growth over 10 years (1.33 = 33%)
    """
    MIN_CURRENT_RATIO: float = 2.0
    MIN_EARNINGS_YEARS: int = 10  # Graham: "Some earnings in EACH of the past 10 years"
    MAX_PE_RATIO: float = 15.0
    MAX_PB_RATIO: float = 1.5
    MIN_EARNINGS_GROWTH: float = 1.33  # 33% over 10 years


@dataclass(frozen=True)
class EnterprisingThresholds:
    """
    Thresholds for Graham's Enterprising Investor tests.
    
    The Enterprising Investor is willing to devote more time and effort to
    stock selection and accepts somewhat relaxed criteria compared to the
    Defensive Investor. These tests allow for more flexibility while still
    maintaining Graham's value investing principles.
    
    Attributes:
        MIN_CURRENT_RATIO: Minimum current assets to current liabilities ratio (1.5)
        MAX_DEBT_ASSETS: Maximum debt relative to net current assets (1.10 = 110%)
        MIN_EARNINGS_YEARS: Minimum years of positive earnings required (5 years)
        MAX_PE_RATIO: Maximum acceptable Price-to-Earnings ratio (10.0)
        MAX_PB_RATIO: Maximum acceptable Price-to-Book ratio (1.2)
    """
    MIN_CURRENT_RATIO: float = 1.5
    MAX_DEBT_ASSETS: float = 1.10  # Debt < 110% of Net Current Assets
    MIN_EARNINGS_YEARS: int = 5
    MAX_PE_RATIO: float = 10.0
    MAX_PB_RATIO: float = 1.2


# Singleton instances for use throughout the application
DEFENSIVE: Final[DefensiveThresholds] = DefensiveThresholds()
ENTERPRISING: Final[EnterprisingThresholds] = EnterprisingThresholds()
