"""
Predicates for rows of the per-year financial `history`.

merge_financial_data adds dividend-only years (dividend data but no statements) whose
statement fields are all 0.0, so code that needs "the latest real year" must skip them.
Each predicate below is one definition of "this year has real data"; the variants
differ on purpose and are kept distinct so existing behaviour is unchanged. Unifying
them is a behaviour change and must be done (and snapshot-reviewed) separately.
"""

from typing import Any, Callable, Iterable, Mapping, Optional, Union

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
