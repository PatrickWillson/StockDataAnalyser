"""
core.history predicates must behave exactly like the inline expressions they replaced.

Each property compares a helper against the original expression (copied verbatim)
for arbitrary rows: zero, negative and positive values, and missing keys.
"""

from hypothesis import given, settings, strategies as st

from core.history import (
    has_balance_sheet_data, has_income_data, has_statement_data,
    has_statement_or_current_assets, latest_year,
)

FIELDS = ("revenue", "net_income", "total_equity", "current_assets", "eps")
values = st.sampled_from([0.0, -1.5, 2.0]) | st.floats(-1e6, 1e6, allow_nan=False)
rows = st.dictionaries(st.sampled_from(FIELDS), values)


@settings(max_examples=300)
@given(year_data=rows)
def test_has_statement_data_matches_original(year_data):
    original = (year_data.get('revenue', 0.0) > 0 or year_data.get('net_income', 0.0) != 0
                or year_data.get('total_equity', 0.0) > 0)
    assert has_statement_data(year_data) == original


@settings(max_examples=300)
@given(year_data=rows)
def test_has_statement_or_current_assets_matches_original(year_data):
    original = (year_data.get('revenue', 0.0) > 0 or year_data.get('net_income', 0.0) != 0
                or year_data.get('total_equity', 0.0) > 0 or year_data.get('current_assets', 0.0) > 0)
    assert has_statement_or_current_assets(year_data) == original


@settings(max_examples=300)
@given(year_data=rows)
def test_has_income_data_matches_original(year_data):
    revenue = year_data.get('revenue', 0.0)
    net_income = year_data.get('net_income', 0.0)
    eps = year_data.get('eps', 0.0)
    assert has_income_data(year_data) == (revenue > 0 or net_income != 0 or eps != 0)


@settings(max_examples=300)
@given(year_data=rows)
def test_has_balance_sheet_data_matches_original(year_data):
    original = year_data.get('current_assets', 0.0) > 0 or year_data.get('total_equity', 0.0) > 0
    assert has_balance_sheet_data(year_data) == original


DIVIDEND_ONLY = {"revenue": 0.0, "net_income": 0.0, "total_equity": 0.0, "eps": 0.0, "dividend": 0.9}


def test_dividend_only_year_has_no_data_under_any_predicate():
    for predicate in (has_statement_data, has_statement_or_current_assets, has_income_data,
                      has_balance_sheet_data):
        assert predicate(DIVIDEND_ONLY) is False


def test_loss_year_counts_as_statement_data():
    assert has_statement_data({"revenue": 0.0, "net_income": -5.0, "total_equity": 0.0})


def test_latest_year_skips_years_without_data():
    history = {"2024-12-31": DIVIDEND_ONLY, "2023-12-31": {"revenue": 10.0}, "2022-12-31": {"revenue": 9.0}}
    assert latest_year(history, sorted(history, reverse=True)) == "2023-12-31"


def test_latest_year_uses_given_predicate_and_returns_none_when_nothing_qualifies():
    history = {"2023-12-31": {"revenue": 10.0}}
    assert latest_year(history, ["2023-12-31"], has_balance_sheet_data) is None
    assert latest_year({}, []) is None
