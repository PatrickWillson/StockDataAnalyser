"""
Graham Methodology Constants.

These constants are based on Benjamin Graham's "The Intelligent Investor"
and represent the core parameters of his value investing methodology.

CRITICAL: These values are IMMUTABLE and must never be modified.
They represent Graham's original formulas and should remain unchanged
to preserve the integrity of the methodology.
"""

from typing import Final

# Graham Number multiplier used in intrinsic value calculation
# Formula: Graham Number = sqrt(GRAHAM_MULTIPLIER × EPS × TBVPS)
# This value of 22.5 comes directly from Graham's work
GRAHAM_MULTIPLIER: Final[float] = 22.5

# Cost of Capital (discount rate) for Earnings Power Value (EPV) calculation
# Graham used 10% as the standard required return for equity investments
# Formula: EPV = Normalized Earnings / COST_OF_CAPITAL
COST_OF_CAPITAL: Final[float] = 0.10  # 10%
