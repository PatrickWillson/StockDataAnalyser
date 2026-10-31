"""
Typed parsing of EODHD financial statements at the boundary.

Raw `Financials.Balance_Sheet` / `Financials.Income_Statement` entries (yearly or quarterly)
become frozen rows whose fields are Optional[float]: None means EODHD did not report a
usable value (null, "", "NA", "N/A" or junk), as opposed to a reported 0.0.

`as_history_fields()` produces the dict shape the rest of the pipeline uses today, where
missing values are 0.0 (docs/CODEBASE_GUIDE.md §4.2). The raw EODHD key names live only here.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

STATEMENT_PERIODS = ("yearly", "quarterly")
_MISSING_MARKERS = (None, "", "NA", "N/A")


def optional_float(value: Any) -> Optional[float]:
    """Parse a raw EODHD value: None when missing or not numeric, else a float."""
    if value in _MISSING_MARKERS:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _zero_if_missing(value: Optional[float]) -> float:
    return 0.0 if value is None else value


@dataclass(frozen=True)
class BalanceSheetRow:
    period_end: str
    total_equity: Optional[float]
    intangible_assets: Optional[float]
    goodwill: Optional[float]
    current_assets: Optional[float]
    current_liabilities: Optional[float]
    total_liabilities: Optional[float]
    long_term_debt: Optional[float]
    short_term_debt: Optional[float]
    total_debt_reported: Optional[float]
    total_assets: Optional[float]
    inventory: Optional[float]
    noncontrolling_interest: Optional[float]
    shares_outstanding: Optional[float]

    @classmethod
    def from_eodhd(cls, period_end: str, raw: Mapping[str, Any]) -> "BalanceSheetRow":
        # EODHD uses several field names for the share count; the first truthy raw value wins
        shares_raw = (raw.get('commonStockSharesOutstanding') or raw.get('weightedAverageShsOut')
                      or raw.get('weightedAverageShsOutDil') or 0)
        return cls(
            period_end=period_end,
            total_equity=optional_float(raw.get('totalStockholderEquity')),
            intangible_assets=optional_float(raw.get('intangibleAssets')),
            goodwill=optional_float(raw.get('goodWill')),
            current_assets=optional_float(raw.get('totalCurrentAssets')),
            current_liabilities=optional_float(raw.get('totalCurrentLiabilities')),
            total_liabilities=optional_float(raw.get('totalLiab')),
            long_term_debt=optional_float(raw.get('longTermDebt', 0)),
            short_term_debt=optional_float(raw.get('shortTermDebt', 0)),
            total_debt_reported=optional_float(raw.get('shortLongTermDebtTotal', 0)),
            total_assets=optional_float(raw.get('totalAssets')),
            inventory=optional_float(raw.get('inventory')),
            noncontrolling_interest=optional_float(raw.get('noncontrollingInterestInConsolidatedEntity')),
            shares_outstanding=optional_float(shares_raw),
        )

    @property
    def total_debt(self) -> float:
        """
        The reported total (shortLongTermDebtTotal: short- and long-term debt including lease
        obligations) when present; otherwise the sum of the reported components. Graham counted
        every obligation ranking ahead of the stock, and the conservative figure is the fuller
        one (GRAHAM_METHODOLOGY §8.4).
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
        EODHD's explicit minority-interest field when reported; otherwise the balance-sheet gap
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
        }


@dataclass(frozen=True)
class IncomeStatementRow:
    period_end: str
    revenue: Optional[float]
    net_income: Optional[float]
    eps: Optional[float]

    @classmethod
    def from_eodhd(cls, period_end: str, raw: Mapping[str, Any]) -> "IncomeStatementRow":
        eps_raw = raw.get('eps')
        if eps_raw in _MISSING_MARKERS[:3]:
            eps_raw = raw.get('basicEPS') or raw.get('epsBasic')
        # Earnings for the common stock, special items included (GRAHAM_METHODOLOGY §2.3: special
        # charges and credits "should be included in the average earnings"). Never
        # netIncomeFromContinuingOps: it drops those items and EODHD reports it before minority
        # interest (WLKP 2024: 369.2M vs 62.4M attributable, ~6x the real EPS)
        net_income_raw = raw.get('netIncomeApplicableToCommonShares')
        if net_income_raw in _MISSING_MARKERS[:3]:
            net_income_raw = raw.get('netIncome')
        return cls(
            period_end=period_end,
            revenue=optional_float(raw.get('totalRevenue')),
            net_income=optional_float(net_income_raw),
            eps=optional_float(eps_raw),
        )

    def as_history_fields(self) -> Dict[str, float]:
        """Income-statement fields of a history row (missing values as 0.0)."""
        return {
            'revenue': _zero_if_missing(self.revenue),
            'net_income': _zero_if_missing(self.net_income),
            'eps': _zero_if_missing(self.eps),
        }


def _parse_rows(data: Mapping[str, Any], statement: str, period: str, row_type) -> List[Any]:
    if period not in STATEMENT_PERIODS:
        raise ValueError(f"period must be one of {STATEMENT_PERIODS}, got {period!r}")
    rows: List[Any] = []
    try:
        section = data.get('Financials', {}).get(statement, {}).get(period, {})
        if not section:
            return rows
        for period_end in sorted(section.keys(), reverse=True):
            rows.append(row_type.from_eodhd(period_end, section[period_end]))
    except (KeyError, TypeError, AttributeError):
        # Malformed section or row: keep the rows parsed so far
        pass
    return rows


def parse_balance_sheet_rows(data: Mapping[str, Any], period: str = "yearly") -> List[BalanceSheetRow]:
    """Balance sheet rows for `period` ("yearly" or "quarterly"), newest first."""
    return _parse_rows(data, 'Balance_Sheet', period, BalanceSheetRow)


def parse_income_statement_rows(data: Mapping[str, Any], period: str = "yearly") -> List[IncomeStatementRow]:
    """Income statement rows for `period` ("yearly" or "quarterly"), newest first."""
    return _parse_rows(data, 'Income_Statement', period, IncomeStatementRow)
