"""
Eulerpool figures -> statement rows for the years before a company's filed history, behind an overlap gate
(European route, step 5; GRAHAM_METHODOLOGY §8.11; claude-output/EU_XBRL_EULERPOOL_SCOPE.md).

Eulerpool is vendor data, checked here against the company's own filings wherever both have a year:
- its currency must be the filings' (its figures are never converted);
- its fiscal years must line up with the filed ones, by date and by value (Per Aarsleff's years are labelled one
  year late in Eulerpool): otherwise none of its years are used;
- each field is used for the older years only if it agreed with the filed figure in every overlapping year (at least
  EULERPOOL_MIN_OVERLAP_YEARS), never rescaled to fit (a ratio inferred from the overlap is an estimate, not the
  reported figure);
- net income and the year-end share count must both pass, or no older year is added (a year's balance sheet
  needs total assets, equity, current assets and current liabilities to have passed): per-share figures for those
  years are net income / that share count, never Eulerpool's EPS (on a non-standard count).
"""

import datetime as dt
import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from clients.edgar_mapper import EdgarAnnualData
from config.eulerpool_config import (EULERPOOL_DATE_TOLERANCE_DAYS, EULERPOOL_MATCH_ABS, EULERPOOL_MATCH_REL,
                                     EULERPOOL_MATCH_REL_STRICT, EULERPOOL_MIN_OVERLAP_YEARS, EULERPOOL_SHARES_REL)
from core.fundamentals import BalanceSheetRow, IncomeStatementRow
from core.history import fiscal_year

MILLION = 1e6
# Eulerpool field -> our field, per statement (all in millions)
INCOME_FIELDS = {"revenue": "revenue", "netIncome": "net_income"}
BALANCE_FIELDS = {"totalAssets": "total_assets", "totalEquity": "total_equity", "currentAssets": "current_assets",
                  "currentLiabilities": "current_liabilities", "totalLiabilities": "total_liabilities",
                  "inventory": "inventory", "goodwill": "goodwill", "longTermDebt": "long_term_debt",
                  "shortTermDebt": "short_term_debt", "sharesOutstanding": "shares"}
CASH_FLOW_FIELDS = {"netOperatingCashFlow": "operating_cash_flow", "cashDividendsPaid": "dividends_paid"}
LABELS = {"revenue": "revenue", "net_income": "net income", "total_assets": "total assets",
          "total_equity": "equity", "current_assets": "current assets", "current_liabilities": "current liabilities",
          "total_liabilities": "total liabilities", "inventory": "inventory", "goodwill": "goodwill",
          "long_term_debt": "long-term debt", "short_term_debt": "short-term debt", "shares": "year-end shares",
          "operating_cash_flow": "operating cash flow", "dividends_paid": "dividends paid"}
REQUIRED = ("net_income", "shares")
# spiked_share_years: a temporary jump in the vendor's share count
SPIKE_MAX_YEARS, RUN_TOLERANCE, SPIKE_RATIO, SIDES_AGREE = 3, 0.10, 1.5, 0.20
# A balance sheet for a year needs these (a missing one would show as zero: working capital of 0.00)
BALANCE_REQUIRED = ("total_assets", "total_equity", "current_assets", "current_liabilities")
SOURCE = "Eulerpool (vendor data, not filings)"


@dataclass(frozen=True)
class EulerpoolData:
    """A company's Eulerpool figures by fiscal year end: field -> value (in units, not millions)."""
    isin: str
    name: str
    currency: str
    years: Mapping[str, Mapping[str, float]]


@dataclass(frozen=True)
class OlderYears:
    """Rows for the years before the filed history (newest first), and the notes that explain them."""
    balance_sheets: Tuple[BalanceSheetRow, ...] = ()
    income_statements: Tuple[IncomeStatementRow, ...] = ()
    shares_by_year: Mapping[str, float] = field(default_factory=dict)
    dividends_paid: Mapping[str, float] = field(default_factory=dict)
    operating_cash_flow: Mapping[str, float] = field(default_factory=dict)
    notes: Tuple[str, ...] = ()
    accepted: Tuple[str, ...] = ()            # fields that passed the overlap gate


def _date(text: Any) -> Optional[str]:
    """'2024-12-31' -> itself; estimates ('2030-12-31e') and anything else -> None."""
    text = str(text or "")
    try:
        return dt.date.fromisoformat(text).isoformat()
    except ValueError:
        return None


def _days(a: str, b: str) -> int:
    return abs((dt.date.fromisoformat(a) - dt.date.fromisoformat(b)).days)


def _number(value: Any) -> Optional[float]:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def parse(profile: Mapping[str, Any], statements: Mapping[str, Sequence[Mapping[str, Any]]]) -> EulerpoolData:
    """Eulerpool's annual income and cash-flow rows and the balance sheet of the quarter ending each fiscal year."""
    years: Dict[str, Dict[str, float]] = {}
    for row in statements.get("income") or []:
        end = _date(row.get("period"))
        if end is None:
            continue
        values = years.setdefault(end, {})
        for theirs, ours in INCOME_FIELDS.items():
            if _number(row.get(theirs)) is not None:
                values[ours] = _number(row.get(theirs)) * MILLION
    for row in statements.get("cashflow") or []:
        end = _date(row.get("period"))
        target = next((e for e in years if end and _days(e, end) <= EULERPOOL_DATE_TOLERANCE_DAYS), None)
        if target is None:
            continue
        for theirs, ours in CASH_FLOW_FIELDS.items():
            if _number(row.get(theirs)) is not None:
                value = _number(row.get(theirs)) * MILLION
                years[target][ours] = abs(value) if ours == "dividends_paid" else value
    quarters = [(end, row) for row in statements.get("balance_quarterly") or [] if (end := _date(row.get("period")))]
    for end, values in years.items():
        quarter = next((row for q_end, row in quarters if _days(q_end, end) <= EULERPOOL_DATE_TOLERANCE_DAYS), None)
        for theirs, ours in BALANCE_FIELDS.items():
            if quarter is not None and _number(quarter.get(theirs)) is not None:
                values[ours] = _number(quarter.get(theirs)) * MILLION
    return EulerpoolData(str(profile.get("isin") or ""), str(profile.get("name") or ""),
                         str(profile.get("currency") or ""), years)


def spiked_share_years(counts: Mapping[str, float]) -> List[str]:
    """
    Fiscal year ends whose share count is a temporary jump: a run of up to SPIKE_MAX_YEARS years (counts within
    RUN_TOLERANCE of each other) over SPIKE_RATIO from the company's median count across all years, with the years on
    both sides within SIDES_AGREE of that median. Eulerpool's Games Workshop counts are 62M for FY2007-09 and FY2012 between years of about 31M, against
    about 31M printed in every report; Eulerpool's counts are already restated for splits, so a jump that reverts is
    not a share change. A lasting step (a share issue) is not flagged.
    """
    ends = sorted(end for end, count in counts.items() if count)
    runs: List[List[str]] = []
    for end in ends:
        if runs and abs(counts[end] / counts[runs[-1][0]] - 1) <= RUN_TOLERANCE:
            runs[-1].append(end)
        else:
            runs.append([end])
    if len(ends) < 3:
        return []
    typical = statistics.median(counts[end] for end in ends)    # the company's usual level across all years
    near = lambda level: abs(level / typical - 1) <= SIDES_AGREE   # noqa: E731
    spiked = []
    for i in range(1, len(runs) - 1):
        level = counts[runs[i][0]]
        if len(runs[i]) <= SPIKE_MAX_YEARS and max(level / typical, typical / level) > SPIKE_RATIO \
                and near(counts[runs[i - 1][-1]]) and near(counts[runs[i + 1][0]]):
            spiked.extend(runs[i])
    return spiked


def filed_values(annual: EdgarAnnualData) -> Dict[str, Dict[str, float]]:
    """The filed figures per fiscal year end, in the gate's fields."""
    out: Dict[str, Dict[str, float]] = {}
    for row in annual.income_statements:
        values = out.setdefault(row.period_end, {})
        for name in ("revenue", "net_income"):
            if getattr(row, name) is not None:
                values[name] = getattr(row, name)
    for row in annual.balance_sheets:
        values = out.setdefault(row.period_end, {})
        for name in ("total_assets", "total_equity", "current_assets", "current_liabilities", "total_liabilities",
                     "inventory", "goodwill", "long_term_debt", "short_term_debt"):
            if getattr(row, name) is not None:
                values[name] = getattr(row, name)
    for end, values in out.items():
        year = fiscal_year(end)
        if annual.shares_by_year.get(year):
            values["shares"] = annual.shares_by_year[year]
        if end in annual.operating_cash_flow:
            values["operating_cash_flow"] = annual.operating_cash_flow[end]
        if end in annual.dividends_paid:
            values["dividends_paid"] = annual.dividends_paid[end]
    return out


def _agrees(name: str, theirs: float, filed: float, relative: float) -> bool:
    if name == "shares":
        return filed > 0 and abs(theirs / filed - 1) <= EULERPOOL_SHARES_REL
    return abs(theirs - filed) <= max(relative * abs(filed), EULERPOOL_MATCH_ABS)


def _pairs(filed: Mapping[str, Any], data: EulerpoolData, shift_years: int = 0) -> List[Tuple[str, str]]:
    """(filed year end, Eulerpool year end) pairs, the Eulerpool end `shift_years` later than the filed one."""
    pairs = []
    for end in filed:
        target = (dt.date.fromisoformat(end) + dt.timedelta(days=round(365.25 * shift_years))).isoformat()
        match = next((e for e in data.years if _days(e, target) <= EULERPOOL_DATE_TOLERANCE_DAYS), None)
        if match is not None:
            pairs.append((end, match))
    return pairs


def _matches(name: str, pairs: Sequence[Tuple[str, str]], filed, data: EulerpoolData, relative: float) -> int:
    return sum(1 for end, theirs in pairs if name in filed[end] and name in data.years[theirs]
               and _agrees(name, data.years[theirs][name], filed[end][name], relative))


def older_years(annual: EdgarAnnualData, data: EulerpoolData, strict: bool, filed_source: str) -> OlderYears:
    """
    Eulerpool's years before the filed history, with only the fields that passed the overlap gate.

    Args:
        strict: the reporting currency differs from the listing's (EULERPOOL_MATCH_REL_STRICT)
        filed_source: names the filings in notes ("the ESEF reports")
    """
    def not_used(reason: str) -> OlderYears:
        return OlderYears(notes=(f"History before the filed years: {SOURCE} not used: {reason}",))

    if data.currency != annual.currency:
        return not_used(f"its figures are in {data.currency or 'an unstated currency'}, the filings' in "
                        f"{annual.currency} (vendor figures are never converted)")
    filed = filed_values(annual)
    if not filed:
        return not_used("no filed years to check it against")
    relative = EULERPOOL_MATCH_REL_STRICT if strict else EULERPOOL_MATCH_REL
    pairs = _pairs(filed, data)
    if len(pairs) < EULERPOOL_MIN_OVERLAP_YEARS:
        return not_used(f"its fiscal years do not line up with {filed_source}' in at least "
                        f"{EULERPOOL_MIN_OVERLAP_YEARS} years")
    aligned = _matches("net_income", pairs, filed, data, relative)
    for shift in (1, -1):
        shifted = _matches("net_income", _pairs(filed, data, shift), filed, data, relative)
        if shifted > aligned:
            return not_used(f"its years are labelled one year {'late' if shift == 1 else 'early'} against "
                            f"{filed_source} (its net income matches the filed figure of another year)")
    accepted, rejected = [], []
    for name in LABELS:
        overlap = [(end, theirs) for end, theirs in pairs if name in filed[end] and name in data.years[theirs]]
        if len(overlap) >= EULERPOOL_MIN_OVERLAP_YEARS and _matches(name, overlap, filed, data, relative) == len(overlap):
            accepted.append(name)
        else:
            rejected.append(name)
    overlap_years = sorted(fiscal_year(end) for end, _ in pairs)
    stricter = "; stricter, as the reporting currency is not the listing's" if strict else ""
    checked = (f"against {filed_source} in FY{overlap_years[0]}-FY{overlap_years[-1]} (within {relative:.1%}, or 1.1M "
               f"for whole millions{stricter})")
    missing = [LABELS[name] for name in REQUIRED if name not in accepted]
    if missing:
        return not_used(f"its {' and '.join(missing)} did not agree {checked} in every overlapping year, so its "
                        "earlier years could not be put on the same basis")

    first_filed = min(filed)
    used = {theirs for _, theirs in pairs}
    older = sorted((end for end in data.years if end < first_filed and end not in used
                    and _days(end, first_filed) > EULERPOOL_DATE_TOLERANCE_DAYS), reverse=True)
    spiked = set(spiked_share_years({end: data.years[end].get("shares") for end in data.years}))
    income, balance, shares, dividends, cash = [], [], {}, {}, {}
    for end in older:
        if end in spiked:
            continue
        values = {name: value for name, value in data.years[end].items() if name in accepted}
        if values.get("net_income") is None or not values.get("shares"):
            continue
        income.append(IncomeStatementRow(end, values.get("revenue"), values["net_income"], None))
        shares[fiscal_year(end)] = values["shares"]
        if "dividends_paid" in values:
            dividends[end] = values["dividends_paid"]
        if "operating_cash_flow" in values:
            cash[end] = values["operating_cash_flow"]
        if all(values.get(name) is not None for name in BALANCE_REQUIRED):
            balance.append(BalanceSheetRow(
                period_end=end, total_equity=values["total_equity"], intangible_assets=None,
                goodwill=values.get("goodwill"), current_assets=values.get("current_assets"),
                current_liabilities=values.get("current_liabilities"),
                total_liabilities=values.get("total_liabilities"), long_term_debt=values.get("long_term_debt"),
                short_term_debt=values.get("short_term_debt"), total_debt_reported=None,
                total_assets=values["total_assets"], inventory=values.get("inventory"), noncontrolling_interest=None,
                shares_outstanding=values["shares"], long_term_debt_unknown="long_term_debt" not in accepted))
    if not income:
        return not_used(f"it has no complete year before FY{fiscal_year(first_filed)}")
    years = sorted(fiscal_year(row.period_end) for row in income)
    notes = [f"History before FY{fiscal_year(first_filed)}: {SOURCE} for FY{years[0]}-FY{years[-1]} ({len(years)} "
             f"years), unverified against the company's reports. Used field by field, only where it agreed {checked} "
             f"in every overlapping year: {', '.join(LABELS[n] for n in accepted)}. Never rescaled to fit; EPS for "
             "those years is net income / Eulerpool's year-end share count (its own EPS is not used); no intangibles "
             "(tangible book overstated); whole millions"]
    dropped = sorted(fiscal_year(end) for end in spiked if end in older)
    if dropped:
        notes.append(f"{SOURCE}: FY{', FY'.join(dropped)} not used: the year-end share count jumps over {SPIKE_RATIO:g}x "
                     "from the years on both sides and back (a vendor error, not a share change), so per-share figures "
                     "for those years cannot be put on the same basis")
    if rejected:
        notes.append(f"{SOURCE}: not used for the earlier years (disagreed with {filed_source} in an overlapping year, "
                     f"or too few years to check): {', '.join(LABELS[n] for n in rejected)}"
                     + ("; long-term debt is then unknown in those years, not zero" if "long_term_debt" in rejected else ""))
    return OlderYears(tuple(balance), tuple(income), shares, dividends, cash, tuple(notes), tuple(accepted))


def vendor_annual(data: EulerpoolData) -> EdgarAnnualData:
    """
    Every Eulerpool year as statement rows, unchecked against filings (companies with no filings on any route:
    Germany, Ireland, AIM; the source checks them against Yahoo). EPS None (net income / the year's count
    downstream); no intangibles. Long-term debt is non-current liabilities (total - current), an upper bound
    (GRAHAM_METHODOLOGY §8.11): Eulerpool's own figure includes lease liabilities for some companies and not for others
    (Hunting, Clas Ohlson with; Tesco, Renishaw, Manitou without) and is 0 for some with debt (Games Workshop), so it
    cannot show the debt Graham counts (§8.10); without both totals it is unknown, not zero (§8.9).
    """
    balance, income, shares, dividends, cash = [], [], {}, {}, {}
    spiked = set(spiked_share_years({end: data.years[end].get("shares") for end in data.years}))
    for end in sorted(data.years, reverse=True):
        values = data.years[end]
        if values.get("net_income") is None or end in spiked:
            continue
        income.append(IncomeStatementRow(end, values.get("revenue"), values["net_income"], None))
        if values.get("shares"):
            shares[fiscal_year(end)] = values["shares"]
        if "dividends_paid" in values:
            dividends[end] = values["dividends_paid"]
        if "operating_cash_flow" in values:
            cash[end] = values["operating_cash_flow"]
        if values.get("total_assets") is not None and values.get("total_equity") is not None:
            total, current = values.get("total_liabilities"), values.get("current_liabilities")
            noncurrent = total - current if total is not None and current is not None else None
            balance.append(BalanceSheetRow(
                period_end=end, total_equity=values["total_equity"], intangible_assets=None,
                goodwill=values.get("goodwill"), current_assets=values.get("current_assets"),
                current_liabilities=current, total_liabilities=total, long_term_debt=noncurrent,
                short_term_debt=values.get("short_term_debt"), total_debt_reported=None,
                total_assets=values["total_assets"], inventory=values.get("inventory"), noncontrolling_interest=None,
                shares_outstanding=values.get("shares"), long_term_debt_unknown=noncurrent is None))
    notes = ((f"{SOURCE}: FY{', FY'.join(sorted(fiscal_year(e) for e in spiked))} not used: the year-end share count jumps "
              f"over {SPIKE_RATIO:g}x from the years on both sides and back (a vendor error, not a share change)",)
             if spiked else ())
    return EdgarAnnualData(tuple(balance), tuple(income), dividends, cash, shares, 0.0, notes, data.currency)
