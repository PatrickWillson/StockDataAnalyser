"""Dividends belong to the fiscal year they fall in, like the statements beside them."""

import datetime as dt

import pytest
from hypothesis import given, settings, strategies as st

from core.fundamentals import CompanyFundamentals, DividendPayment, IncomeStatementRow
from core.financial_data_processor import FinancialDataProcessor
from core.history import fiscal_year_of_date

JUNE_YEARS = ["2023-06-30", "2024-06-30", "2025-06-30"]


@pytest.mark.parametrize("date, ends, expected", [
    ("2024-06-30", JUNE_YEARS, "2024"),      # the last day is in the year
    ("2024-07-01", JUNE_YEARS, "2025"),      # the next day is not
    ("2025-08-15", JUNE_YEARS, "2026"),      # after the reports: the usual year end decides
    ("2010-08-15", JUNE_YEARS, "2011"),      # before them
    ("2010-03-15", JUNE_YEARS, "2010"),
    ("2024-08-15", [], "2024"),              # nothing reported: the calendar year
    ("2024-12-29", ["2024-12-27", "2025-12-28"], "2025"),   # a 52-week year has already ended
    ("2022-12-30", ["2023-01-01", "2023-12-31"], "2022"),   # a year ending in early January is the previous year's
])
def test_fiscal_year_of_date(date, ends, expected):
    assert fiscal_year_of_date(date, ends) == expected


@settings(max_examples=200, deadline=None)
@given(st.dates(dt.date(2001, 1, 1), dt.date(2020, 12, 31)), st.integers(1, 12))
def test_a_date_in_a_reported_year_gets_that_years_label(date, month):
    """Every date from the day after one month-end year end to the next belongs to the later year."""
    day = 28                                     # valid in every month
    ends = [dt.date(year, month, day).isoformat() for year in range(1999, 2024)]
    label = fiscal_year_of_date(date.isoformat(), ends)
    end = next(e for e in ends if e >= date.isoformat())
    assert label == end[:4]
    assert dt.date.fromisoformat(end) - date < dt.timedelta(days=367)


def _dividends(ends, payments):
    fundamentals = CompanyFundamentals(
        source="test", symbol="T", exchange="US", trading_currency="USD", statement_currency="USD",
        annual_income_statements=tuple(IncomeStatementRow(end, 1.0, 1.0, None) for end in ends),
        dividend_payments=tuple(DividendPayment(date, amount, "USD") for date, amount in payments))
    return FinancialDataProcessor().parse_dividend_history(fundamentals)[0]


def test_a_june_year_gets_the_dividends_paid_in_it():
    """Standex: fiscal 2025 runs July 2024 to June 2025, whichever calendar years the payments fall in."""
    payments = [("2024-08-08", 0.32), ("2024-11-07", 0.32), ("2025-02-06", 0.32), ("2025-05-08", 0.32), ("2025-08-07", 0.34)]
    assert _dividends(JUNE_YEARS, payments) == pytest.approx({"2025": 1.28, "2026": 0.34})


def test_a_december_year_is_unchanged():
    payments = [("2024-03-08", 0.5), ("2024-09-08", 0.5), ("2025-03-08", 0.6)]
    assert _dividends(["2023-12-31", "2024-12-31"], payments) == pytest.approx({"2024": 1.0, "2025": 0.6})
