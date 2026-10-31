"""
A current price together with the currency its source quoted it in.

The quote currency identifies the listing: a yfinance price is only used when its currency
matches the trading currency EODHD reports for the ticker (F7), so a bare-symbol lookup that
lands on another company's listing elsewhere is rejected instead of silently used.
"""

from dataclasses import dataclass
from typing import Optional

# Minor-unit codes (case-sensitive: yfinance writes pence as "GBp", pounds as "GBP")
# mapped to their major currency. EODHD writes pence as "GBX".
_MINOR_UNITS = {
    "GBp": "GBP", "GBX": "GBP", "GBx": "GBP",
    "ZAc": "ZAR", "ZAC": "ZAR",
    "ILA": "ILS", "ILa": "ILS",
}


@dataclass(frozen=True)
class PriceQuote:
    price: float
    currency: Optional[str]  # as the source reported it, e.g. "USD", "GBp"; None if unreported


def major_currency(code: Optional[str]) -> Optional[str]:
    """ISO currency a code belongs to, treating minor units as their major currency."""
    if not code:
        return None
    return _MINOR_UNITS.get(code, code.upper())


def same_currency(a: Optional[str], b: Optional[str]) -> bool:
    """True when both codes are known and name the same currency (in any unit)."""
    major_a, major_b = major_currency(a), major_currency(b)
    return major_a is not None and major_a == major_b
