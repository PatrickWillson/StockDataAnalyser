"""Eulerpool history before the filed years, behind the overlap gate (clients/eulerpool_mapper.py). Synthetic data."""

import pytest

from clients.edgar_mapper import EdgarAnnualData
from clients.eulerpool_mapper import EulerpoolData, older_years, parse
from core.fundamentals import BalanceSheetRow, IncomeStatementRow

M = 1e6


def _balance(end, assets=1000 * M, equity=400 * M, shares=50 * M, ltd=100 * M):
    return BalanceSheetRow(period_end=end, total_equity=equity, intangible_assets=10 * M, goodwill=20 * M,
                           current_assets=300 * M, current_liabilities=150 * M, total_liabilities=assets - equity,
                           long_term_debt=ltd, short_term_debt=5 * M, total_debt_reported=None, total_assets=assets,
                           inventory=80 * M, noncontrolling_interest=None, shares_outstanding=shares)


FILED_YEARS = ("2025-12-31", "2024-12-31", "2023-12-31")
ANNUAL = EdgarAnnualData(
    balance_sheets=tuple(_balance(e) for e in FILED_YEARS),
    income_statements=tuple(IncomeStatementRow(e, 900 * M, 60 * M, 1.2) for e in FILED_YEARS),
    dividends_paid={e: 30 * M for e in FILED_YEARS}, operating_cash_flow={e: 90 * M for e in FILED_YEARS},
    shares_by_year={e[:4]: 50 * M for e in FILED_YEARS}, latest_cover_shares=0.0, notes=(), currency="EUR")


def _year(net_income=60.0, shares=50.0, assets=1000.0, ltd=140.0, revenue=900.0):
    return {"revenue": revenue * M, "net_income": net_income * M, "total_assets": assets * M, "total_equity": 400 * M,
            "current_assets": 300 * M, "current_liabilities": 150 * M, "total_liabilities": (assets - 400) * M,
            "inventory": 80 * M, "goodwill": 20 * M, "long_term_debt": ltd * M, "short_term_debt": 5 * M,
            "shares": shares * M, "operating_cash_flow": 90 * M, "dividends_paid": 30 * M}


def _data(years, currency="EUR"):
    return EulerpoolData("XX0000000000", "Example AG", currency, years)


OVERLAP = {e: _year() for e in FILED_YEARS}
OLDER = {"2022-12-31": _year(50.0, 52.0, 950.0), "2021-12-31": _year(-5.0, 53.0, 900.0)}


def test_older_years_take_the_fields_that_agreed_in_every_overlapping_year():
    older = older_years(ANNUAL, _data({**OVERLAP, **OLDER}), strict=False, filed_source="the ESEF reports")
    assert [r.period_end for r in older.income_statements] == ["2022-12-31", "2021-12-31"]
    assert older.income_statements[1] == IncomeStatementRow("2021-12-31", 900 * M, -5 * M, None)   # EPS never taken
    assert older.shares_by_year == {"2022": 52 * M, "2021": 53 * M}
    row = older.balance_sheets[0]
    assert (row.total_assets, row.total_equity, row.intangible_assets) == (950 * M, 400 * M, None)
    # Eulerpool's long-term debt (140M) disagreed with the filed 100M: unknown in the older years, not zero
    assert row.long_term_debt is None and row.long_term_debt_unknown
    assert older.dividends_paid == {"2022-12-31": 30 * M, "2021-12-31": 30 * M}
    assert older.notes[0].startswith("History before FY2023: Eulerpool (vendor data, not filings) for FY2021-FY2022")
    assert "in FY2023-FY2025 (within 1.0%" in older.notes[0] and "long-term debt" not in older.notes[0]
    assert "long-term debt" in older.notes[1] and "unknown in those years, not zero" in older.notes[1]


def test_net_income_that_disagreed_once_rules_out_every_older_year():
    """Tesco FY2021: filed 5,954M with the Asia sale, Eulerpool 690M."""
    overlap = {**OVERLAP, "2023-12-31": _year(net_income=6.9)}
    older = older_years(ANNUAL, _data({**overlap, **OLDER}), strict=False, filed_source="the ESEF reports")
    assert older.income_statements == () and older.balance_sheets == ()
    assert "not used: its net income did not agree" in older.notes[0]


def test_a_share_count_that_disagreed_rules_out_every_older_year():
    """Bonduelle FY2023: Eulerpool 63.5M shares against 32.6M."""
    overlap = {**OVERLAP, "2024-12-31": _year(shares=97.0)}
    older = older_years(ANNUAL, _data({**overlap, **OLDER}), strict=False, filed_source="the ESEF reports")
    assert older.income_statements == () and "year-end shares did not agree" in older.notes[0]


def test_another_currency_is_never_converted():
    older = older_years(ANNUAL, _data({**OVERLAP, **OLDER}, currency="USD"), strict=False, filed_source="x")
    assert older.income_statements == () and "never converted" in older.notes[0]


def _annual_with_net_income(values):
    return EdgarAnnualData(
        balance_sheets=ANNUAL.balance_sheets,
        income_statements=tuple(IncomeStatementRow(e, 900 * M, ni * M, 1.2) for e, ni in zip(FILED_YEARS, values)),
        dividends_paid={}, operating_cash_flow={}, shares_by_year=ANNUAL.shares_by_year, latest_cover_shares=0.0,
        notes=(), currency="EUR")


def test_years_labelled_a_year_late_rule_out_every_year():
    """Per Aarsleff: FY2016/17 under September 2018. The filed FY2023 figure sits under Eulerpool's 2024."""
    filed = _annual_with_net_income((100, 200, 300))
    shifted = {"2026-12-31": _year(100.0), "2025-12-31": _year(200.0), "2024-12-31": _year(300.0),
               "2023-12-31": _year(400.0), **OLDER}
    older = older_years(filed, _data(shifted), strict=False, filed_source="the ESEF reports")
    assert older.income_statements == () and "labelled one year late" in older.notes[0]


def test_strict_tolerance_when_the_reporting_currency_is_not_the_listings():
    """0.8% off passes at 1%, not at 0.5%."""
    filed = _annual_with_net_income((600, 600, 600))
    overlap = {e: _year(net_income=604.8) for e in FILED_YEARS}
    assert older_years(filed, _data({**overlap, **OLDER}), strict=False, filed_source="x").income_statements
    strict = older_years(filed, _data({**overlap, **OLDER}), strict=True, filed_source="x")
    assert strict.income_statements == () and "stricter" in strict.notes[0]


def test_too_few_overlapping_years_is_not_enough():
    older = older_years(ANNUAL, _data({"2025-12-31": _year(), **OLDER}), strict=False, filed_source="the ESEF reports")
    assert older.income_statements == () and "do not line up" in older.notes[0]


def test_no_older_year_is_noted():
    older = older_years(ANNUAL, _data(OVERLAP), strict=False, filed_source="the ESEF reports")
    assert older.income_statements == () and "no complete year before FY2023" in older.notes[0]


def test_parse_reads_annual_rows_and_the_year_end_quarter_in_millions():
    profile = {"isin": "GB0003718474", "name": "Games Workshop Group PLC", "currency": "GBP"}
    statements = {
        "income": [{"period": "2021-05-30", "revenue": 353.2, "netIncome": 124.5, "diluted_eps": 3.8},
                   {"period": "2030-05-31e", "revenue": 900, "netIncome": 300}],
        "balance_quarterly": [{"period": "2021-02-28", "totalAssets": 1.0},
                              {"period": "2021-05-30", "totalAssets": 304.6, "totalEquity": 196.3,
                               "sharesOutstanding": 32.76, "longTermDebt": None}],
        "cashflow": [{"period": "2021-05-30", "netOperatingCashFlow": 170.8, "cashDividendsPaid": -88.4}],
    }
    data = parse(profile, statements)
    assert (data.isin, data.currency) == ("GB0003718474", "GBP")
    assert list(data.years) == ["2021-05-30"]                              # estimates left out
    year = data.years["2021-05-30"]
    assert year["net_income"] == pytest.approx(124.5e6) and year["total_assets"] == pytest.approx(304.6e6)
    assert year["shares"] == pytest.approx(32.76e6) and year["dividends_paid"] == pytest.approx(88.4e6)
    assert "long_term_debt" not in year and "eps" not in year
