"""
Criterion checks shared by the defensive and enterprising investor tests
(GRAHAM_METHODOLOGY §4, §5). Each returns 'PASS', 'FAIL' or an 'N/A ...' string.

Moved verbatim from GrahamCalculator (M4.4); the Graham alignment of each criterion is F20.
"""

from typing import Optional, Tuple

from core.history import (has_balance_sheet_data, has_statement_data, has_statement_or_current_assets,
                          net_income_known, row_at)
from core.models import or_default


def latest_financial_year(history: dict, years: list) -> Optional[str]:
    """
    Most recent year with actual financial data (statement data or current assets), skipping
    dividend-only years. years: newest first.
    """
    for year in years:
        if has_statement_or_current_assets(history[year]):
            return year
    return None


def earnings_stability(history: dict, years: list, min_years: int = 8, period: int = 10) -> str:
    """
    Positive net income in at least min_years of the latest `period` complete years.

    Graham's Earnings Stability Criteria:
    - Defensive Investor: Positive earnings in each of the past 10 years
    - Enterprising Investor: no deficit in the last five years

    Incomplete years (dividend data only, no statements) are skipped. A year with statement data but
    no net income (core.history.net_income_known) is unknown, not a deficit: the test FAILs when the
    known years alone settle it (too many deficits), else it is "N/A (Net income unknown)", never a pass.
    """
    complete_years = [year for year in years if has_statement_data(history[year])]
    test_years = complete_years[:period]
    if len(test_years) < min_years:
        return 'FAIL'
    known = [year for year in test_years if net_income_known(history[year])]
    positive_years = sum(1 for year in known if row_at(history, year).net_income > 0)
    deficits = len(known) - positive_years
    if positive_years >= min_years:
        return 'PASS'
    if len(test_years) - deficits < min_years:
        return 'FAIL'
    return 'N/A (Net income unknown)'


def latest_current_ratio(history: dict, years: list) -> Tuple[Optional[str], Optional[float]]:
    """
    Current ratio (current assets / current liabilities) for the most recent year with
    balance sheet data (current assets or equity > 0, so dividend-only years are skipped).

    Returns:
        (fiscal_year_end or None, ratio or None) — ratio is None when there is no such
        year or current liabilities are zero
    """
    for year in years:
        if has_balance_sheet_data(history[year]):
            current_liabilities = or_default(row_at(history, year).current_liabilities, 0.0)
            if current_liabilities == 0:
                return year, None
            return year, or_default(row_at(history, year).current_assets, 0.0) / current_liabilities
    return None, None


def current_ratio_test(history: dict, years: list, min_ratio: float = 2.0) -> str:
    """Current ratio at least min_ratio."""
    _, current_ratio = latest_current_ratio(history, years)
    if current_ratio is None:
        return 'FAIL'
    return 'PASS' if current_ratio >= min_ratio else 'FAIL'
