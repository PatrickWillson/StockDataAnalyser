"""
Provider-neutral company fundamentals: the input contract of the core.

A fundamentals source (see core/ports.py; clients/eodhd_mapper.py for EODHD) maps its vendor's
payloads into CompanyFundamentals. Nothing in core reads a vendor format, so replacing the data
vendor means writing one new adapter that fills this model.

Conventions:
- Values are as the source reported them: no currency conversion, per-share amounts in the
  currency stated next to them. Every currency here is the *true* currency of the values (an
  adapter corrects vendor labelling quirks, e.g. EODHD's GBX label on pound-scale LSE amounts).
- Statement rows use Optional[float]: None = not reported (as opposed to a reported 0.0).
- Market figures are the vendor's own pre-computed values: display or labelled comparison only,
  never inputs to a calculation (CLAUDE.md "raw data in, our own calculations out"); 0.0 = missing.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

_MISSING_MARKERS = (None, "", "NA", "N/A")


def optional_float(value: Any) -> Optional[float]:
    """Parse a raw vendor value: None when missing or not numeric, else a float."""
    if value in _MISSING_MARKERS:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def number_or_zero(value: Any) -> float:
    """Parse a raw vendor value: 0.0 when missing or not numeric, else a float."""
    if value is None or value == "" or value == "NA" or value == "N/A":
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _zero_if_missing(value: Optional[float]) -> float:
    return 0.0 if value is None else value


@dataclass(frozen=True)
class BalanceSheetRow:
    period_end: str
    total_equity: Optional[float]                # common stockholders' equity, excluding minority interest
    intangible_assets: Optional[float]           # excluding goodwill
    goodwill: Optional[float]
    current_assets: Optional[float]
    current_liabilities: Optional[float]
    total_liabilities: Optional[float]
    long_term_debt: Optional[float]
    short_term_debt: Optional[float]
    total_debt_reported: Optional[float]         # short- and long-term debt incl. leases, when reported as a total
    total_assets: Optional[float]
    inventory: Optional[float]
    noncontrolling_interest: Optional[float]
    shares_outstanding: Optional[float]          # common shares at the period end
    preferred_stock: Optional[float] = None      # preferred inside equity, at Graham's valuation (§3.5)

    @property
    def total_debt(self) -> float:
        """
        The reported total (short- and long-term debt including lease obligations) when present;
        otherwise the sum of the reported components. Graham counted every obligation ranking
        ahead of the stock, and the conservative figure is the fuller one (GRAHAM_METHODOLOGY §8.4).
        """
        reported = _zero_if_missing(self.total_debt_reported)
        if reported > 0:
            return reported
        return _zero_if_missing(self.long_term_debt) + _zero_if_missing(self.short_term_debt)

    @property
    def claims_outside_common_equity(self) -> float:
        """
        Claims on the consolidated assets that rank ahead of the common but sit in neither
        liabilities nor equity: minority (noncontrolling) interests, redeemable / temporary equity.
        The explicit minority-interest figure when reported; otherwise the balance-sheet gap
        total assets − total liabilities − equity (WLKP 2024: field null, gap 310.6M = its
        minority interest). Never negative; 0 when any of the three is not reported.
        """
        explicit = _zero_if_missing(self.noncontrolling_interest)
        if explicit > 0:
            return explicit
        if None in (self.total_assets, self.total_liabilities, self.total_equity):
            return 0.0
        return max(0.0, self.total_assets - self.total_liabilities - self.total_equity)

    def as_history_fields(self) -> Dict[str, Optional[float]]:
        """
        Balance-sheet fields of a history row (missing values as 0.0, except inventory: None when
        not reported, so the quick ratio can tell "not reported" from "no inventory").
        """
        return {
            'total_equity': _zero_if_missing(self.total_equity),
            'intangible_assets': _zero_if_missing(self.intangible_assets),
            'goodwill': _zero_if_missing(self.goodwill),
            'current_assets': _zero_if_missing(self.current_assets),
            'current_liabilities': _zero_if_missing(self.current_liabilities),
            'total_liabilities': _zero_if_missing(self.total_liabilities),
            'long_term_debt': _zero_if_missing(self.long_term_debt),
            'total_assets': _zero_if_missing(self.total_assets),
            'total_debt': self.total_debt,
            'inventory': self.inventory,
            'claims_outside_equity': self.claims_outside_common_equity,
            'shares_outstanding': _zero_if_missing(self.shares_outstanding),
            'preferred_stock': _zero_if_missing(self.preferred_stock),
        }


@dataclass(frozen=True)
class IncomeStatementRow:
    period_end: str
    revenue: Optional[float]
    net_income: Optional[float]                  # for the common, special items included (GRAHAM_METHODOLOGY §2.3)
    eps: Optional[float]                         # reported EPS, when the source has one

    def as_history_fields(self) -> Dict[str, float]:
        """Income-statement fields of a history row (missing values as 0.0)."""
        return {
            'revenue': _zero_if_missing(self.revenue),
            'net_income': _zero_if_missing(self.net_income),
            'eps': _zero_if_missing(self.eps),
        }


@dataclass(frozen=True)
class DividendPayment:
    """One declared dividend (per share, split-adjusted to today's shares)."""
    date: Optional[str]                          # payment date (YYYY-MM-DD), else the ex-dividend date
    amount: float                                # 0.0 when missing or not numeric
    currency: str


@dataclass(frozen=True)
class DatedDividend:
    """A dividend amount without a stated currency (assumed the trading currency)."""
    date: str
    amount: float


@dataclass(frozen=True)
class MarketData:
    """The vendor's pre-computed figures: display / labelled comparison only. 0.0 = missing."""
    dividend_per_share: float = 0.0
    dividend_yield: float = 0.0
    pe_ratio: float = 0.0
    book_value_per_share: float = 0.0
    roe: float = 0.0                             # trailing twelve months
    roa: float = 0.0                             # trailing twelve months
    profit_margin: float = 0.0
    enterprise_value: float = 0.0
    insider_ownership: float = 0.0
    institutional_ownership: float = 0.0
    beta: float = 0.0
    week_52_high: float = 0.0                    # in the exchange quoting unit, like the price
    week_52_low: float = 0.0
    per_share_currency: str = "USD"              # currency of dividend_per_share and book_value_per_share


@dataclass(frozen=True)
class CompanyFundamentals:
    source: str                                  # vendor name for labels and messages, e.g. "EODHD"
    symbol: str
    exchange: str
    trading_currency: str                        # the vendor's trading currency code (may be a minor unit, GBX)
    statement_currency: str                      # currency of the financial statements
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    employees: Optional[int] = None
    ceo_name: str = 'N/A'
    is_delisted: bool = False
    updated_at: Optional[str] = None             # when the vendor last updated the data (ISO date/time)
    annual_balance_sheets: Tuple[BalanceSheetRow, ...] = ()       # newest first
    annual_income_statements: Tuple[IncomeStatementRow, ...] = ()
    quarterly_balance_sheets: Tuple[BalanceSheetRow, ...] = ()    # periodic (quarterly or semi-annual)
    quarterly_income_statements: Tuple[IncomeStatementRow, ...] = ()
    shares_outstanding: float = 0.0              # current count (market data); fallback for per-year counts
    shares_by_year: Mapping[str, float] = field(default_factory=dict)  # 'YYYY' -> reported shares
    latest_statement_shares: float = 0.0         # most recent reported annual share count (cross-check)
    dividend_payments: Optional[Tuple[DividendPayment, ...]] = None    # None: no payment-level data
    annual_dividends_paid: Mapping[str, float] = field(default_factory=dict)  # period end -> total cash paid (>= 0)
    cash_flow_currency: str = "USD"
    dividend_amounts: Tuple[DatedDividend, ...] = ()              # amounts without currency (fallback)
    dividend_counts_by_year: Mapping[str, float] = field(default_factory=dict)  # 'YYYY' -> payments (last resort)
    forward_dividend_rate: Optional[float] = None  # vendor estimate: labelled display only (F21)
    forward_dividend_currency: str = "USD"
    market: MarketData = field(default_factory=MarketData)
    notes: Tuple[str, ...] = ()                  # the adapter's data-quality notes (derived values, restatements)
