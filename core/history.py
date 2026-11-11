"""
Predicates for rows of the per-year financial `history`.

merge_financial_data adds dividend-only years (dividend data but no statements) whose
statement fields are all 0.0, so code that needs "the latest real year" must skip them.
Each predicate below is one definition of "this year has real data"; the variants
differ on purpose and are kept distinct so existing behaviour is unchanged. Unifying
them is a behaviour change and must be done (and snapshot-reviewed) separately.
"""

import datetime as dt
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence, Union

from core.models import MISSING, HistoryRow, or_default

# A row as a HistoryRow, or its dict form (assembly works on dicts; each predicate normalises)
YearData = Union[HistoryRow, Mapping[str, Any]]


def has_statement_data(year_data: YearData) -> bool:
    """Revenue, net income (may be a loss) or equity reported."""
    row = HistoryRow.from_dict(year_data)
    return (
        or_default(row.revenue, 0.0) > 0
        or or_default(row.net_income, 0.0) != 0
        or or_default(row.total_equity, 0.0) > 0
    )


def net_income_known(year_data: YearData) -> bool:
    """
    Net income reported (a profit or a loss). The history stores an unreported figure as 0.0 (a year with
    only a balance sheet, or a vendor's 0 for a year it lacks), and filed net income is never exactly zero,
    so 0.0 is unknown, not a break-even year.
    """
    return or_default(HistoryRow.from_dict(year_data).net_income, 0.0) != 0


def eps_unknown(year_data: YearData) -> bool:
    """
    Net income reported but no EPS (0.0): the year has no share count to put it on (vendor history
    without per-share figures, GRAHAM_METHODOLOGY §8.12), so its EPS is unknown, not zero.
    """
    row = HistoryRow.from_dict(year_data)
    return not or_default(row.eps, 0.0) and or_default(row.net_income, 0.0) != 0


def has_statement_or_current_assets(year_data: YearData) -> bool:
    """has_statement_data, or current assets reported."""
    return has_statement_data(year_data) or or_default(HistoryRow.from_dict(year_data).current_assets, 0.0) > 0


def has_income_data(year_data: YearData) -> bool:
    """Revenue, net income (may be a loss) or EPS reported."""
    row = HistoryRow.from_dict(year_data)
    return (
        or_default(row.revenue, 0.0) > 0
        or or_default(row.net_income, 0.0) != 0
        or or_default(row.eps, 0.0) != 0
    )


def has_balance_sheet_data(year_data: YearData) -> bool:
    """Current assets or equity reported."""
    row = HistoryRow.from_dict(year_data)
    return or_default(row.current_assets, 0.0) > 0 or or_default(row.total_equity, 0.0) > 0


def is_dividend_only_year(year_data: YearData) -> bool:
    """
    True for rows merge_financial_data creates from dividend data alone: revenue, net income
    and equity all present and 0.0, and EPS 0/None. A break-even or loss year still has
    revenue or equity, so it is not dividend-only. Rows lacking those keys are not judged
    dividend-only (they are partial data, not placeholders).
    """
    row = HistoryRow.from_dict(year_data)
    statement_values = (row.revenue, row.net_income, row.total_equity)
    return (all(value is not MISSING and value in (0, 0.0) for value in statement_values)
            and or_default(row.eps, None) in (None, 0, 0.0))


def fiscal_year(period_end: str) -> str:
    """
    The fiscal year a period end belongs to, as 'YYYY'. A 52/53-week year that ends in the first
    week of January (Johnson & Johnson's FY2022 ended 2023-01-01) is the previous year's: the filer
    declares it so (dei:DocumentFiscalYearFocus, SEC EDGAR XBRL Guide §3.1.8), and labelling it by
    the calendar year of its last day would give two fiscal years the same label. Year-only keys
    ('2023') are returned as they are.
    """
    try:
        end = dt.date.fromisoformat(period_end)
    except (TypeError, ValueError):
        return str(period_end).split('-')[0]
    return str(end.year - 1) if end.month == 1 and end.day <= 7 else str(end.year)


def fiscal_year_of_date(date: str, period_ends: Sequence[str]) -> str:
    """
    The fiscal year a date falls in, as 'YYYY': the year of the first reported period end on or after it, and
    outside the reported years the company's usual year end decides. Without period ends, the calendar year.
    E.g. with a June year end, 2025-08-15 belongs to fiscal 2026.
    """
    day = str(date)[:10]
    if not period_ends:
        return day[:4]
    following = next((end for end in sorted(period_ends) if end >= day), None)
    if following is not None and day >= min(period_ends):
        return fiscal_year(following)
    usual_end = min(period_ends)[5:10] if following is not None else max(period_ends)[5:10]
    year = int(day[:4]) if day[5:10] <= usual_end else int(day[:4]) + 1
    return fiscal_year(f"{year}-{usual_end}")


def row_at(history: Mapping[str, YearData], year: str) -> HistoryRow:
    """history[year] as a HistoryRow (dict rows are converted, models pass through)."""
    return HistoryRow.from_dict(history[year])


def latest_year(history: Mapping[str, YearData], years: Iterable[str],
                predicate: Callable[[YearData], bool] = has_statement_data) -> Optional[str]:
    """
    First year in `years` (callers pass newest first) whose row satisfies `predicate`.

    Returns:
        The year key, or None if no year qualifies
    """
    for year in years:
        if predicate(history[year]):
            return year
    return None
