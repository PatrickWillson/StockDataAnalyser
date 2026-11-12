"""Eulerpool history before the filed years, behind the overlap gate (clients/eulerpool_mapper.py). Synthetic data."""

import pytest

from clients.edgar_mapper import EdgarAnnualData
from clients.eulerpool_mapper import EulerpoolData, allowed_gap, older_years, parse
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
    assert older.shares_by_year == {"2022": 0.0, "2021": 0.0}   # no per-share figures (§8.12)
    assert all(row.shares_outstanding is None for row in older.balance_sheets)
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


def test_a_share_count_that_disagreed_rules_out_no_year():
    """Bonduelle FY2023: Eulerpool 63.5M shares against 32.6M. The count is never used (§8.12), so net income decides."""
    overlap = {**OVERLAP, "2024-12-31": _year(shares=97.0)}
    older = older_years(ANNUAL, _data({**overlap, **OLDER}), strict=False, filed_source="the ESEF reports")
    assert [r.period_end for r in older.income_statements] == ["2022-12-31", "2021-12-31"]
    assert "shares" not in older.accepted and any("year-end shares" in n for n in older.notes)


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


def test_vendor_only_long_term_debt_is_non_current_liabilities_an_upper_bound():
    """Eulerpool's own long-term debt includes leases for some companies and not others: not used."""
    from clients.eulerpool_mapper import vendor_annual
    year = _year()            # total liabilities 600M, current 150M, Eulerpool long-term debt 140M
    annual = vendor_annual(_data({"2025-12-31": year, "2024-12-31": {k: v for k, v in year.items() if k != "total_liabilities"}}))
    latest, older = annual.balance_sheets
    assert latest.long_term_debt == 450 * M and not latest.long_term_debt_unknown
    assert older.long_term_debt is None and older.long_term_debt_unknown
    assert annual.income_statements[0].eps is None


def test_a_share_count_that_jumps_and_returns_is_a_vendor_error():
    """Games Workshop: Eulerpool 62M for FY2007-09 and FY2012 between years of about 31M (31M printed throughout)."""
    from clients.eulerpool_mapper import spiked_share_years
    counts = {"2006-05-31": 31.1, "2007-05-31": 62.2, "2008-05-31": 62.3, "2009-05-31": 62.3, "2010-05-31": 31.1,
              "2011-05-31": 31.2, "2012-05-31": 63.2, "2013-05-31": 31.9, "2014-05-31": 32.0}
    assert spiked_share_years(counts) == ["2007-05-31", "2008-05-31", "2009-05-31", "2012-05-31"]


def test_a_lasting_step_in_the_share_count_is_kept():
    from clients.eulerpool_mapper import spiked_share_years
    assert spiked_share_years({"2018-12-31": 30.0, "2019-12-31": 30.0, "2020-12-31": 60.0, "2021-12-31": 61.0}) == []
    assert spiked_share_years({"2018-12-31": 60.0, "2019-12-31": 30.0, "2020-12-31": 30.0}) == []   # oldest year: no side


def test_spiked_years_are_left_out_of_the_older_history_and_noted():
    older = {"2022-12-31": _year(50.0, 52.0), "2021-12-31": _year(45.0, 104.0), "2020-12-31": _year(40.0, 53.0)}
    result = older_years(ANNUAL, _data({**OVERLAP, **older}), strict=False, filed_source="the ESEF reports")
    assert [r.period_end for r in result.income_statements] == ["2022-12-31", "2020-12-31"]
    assert any("FY2021 not used: the year-end share count jumps" in n for n in result.notes)


def test_vendor_only_history_leaves_out_spiked_years():
    from clients.eulerpool_mapper import vendor_annual
    years = {"2022-12-31": _year(50.0, 52.0), "2021-12-31": _year(45.0, 104.0), "2020-12-31": _year(40.0, 53.0)}
    annual = vendor_annual(_data(years))
    assert [r.period_end for r in annual.income_statements] == ["2022-12-31", "2020-12-31"]
    assert any("FY2021 not used" in n for n in annual.notes)


def test_the_whole_million_allowance_is_at_most_a_quarter_of_the_figure():
    """Braime: Eulerpool's 2 (whole millions, truncated) against a filed 2.71M is 26% off, so it does not agree."""
    assert allowed_gap(2.71e6, 0.01) == pytest.approx(0.6775e6)
    assert abs(2e6 - 2.71e6) > allowed_gap(2.71e6, 0.01)
    assert allowed_gap(48.29e6, 0.01) == pytest.approx(1.1e6)      # Guillin: whole millions still agree
    assert allowed_gap(5_000e6, 0.01) == pytest.approx(50e6)       # large figures: the relative band


def test_a_field_is_cut_where_the_vendor_series_breaks_tenfold():
    """Braime: equity 15.9M in FY2021, then 0.15M; the overlap vouches only for the years connected to it."""
    broken = {"2022-12-31": _year(50.0), "2021-12-31": {**_year(40.0), "total_equity": 0.04 * M},
              "2020-12-31": _year(30.0)}
    older = older_years(ANNUAL, _data({**OVERLAP, **broken}), strict=False, filed_source="the ESEF reports")
    assert [r.period_end for r in older.income_statements] == ["2022-12-31", "2021-12-31", "2020-12-31"]
    assert [r.period_end for r in older.balance_sheets] == ["2022-12-31"]   # equity cut from FY2021 back
    assert any("equity FY2021 and earlier" in note for note in older.notes)


def test_a_net_income_moving_tenfold_is_not_a_break():
    swing = {"2022-12-31": _year(5.0), "2021-12-31": _year(80.0)}
    older = older_years(ANNUAL, _data({**OVERLAP, **swing}), strict=False, filed_source="the ESEF reports")
    assert [r.net_income for r in older.income_statements] == [5 * M, 80 * M]
    assert not any("jumps over" in note for note in older.notes)


def test_older_years_carry_the_overlap_error_as_their_allowance():
    """Eulerpool's FY2024 net income is 61M against a filed 60M (1.7% off, within the whole-million allowance): the
    older years carry that error as their allowance."""
    off = {**OVERLAP, "2024-12-31": _year(net_income=61.0)}
    older = older_years(ANNUAL, _data({**off, **OLDER}, currency="EUR"), strict=False, filed_source="the ESEF reports")
    assert [r.net_income_allowance for r in older.income_statements] == [pytest.approx(1 / 60)] * 2
    assert older.net_income_error == pytest.approx(1 / 60) and "low end of that range" in older.notes[0]
    exact = older_years(ANNUAL, _data({**OVERLAP, **OLDER}), strict=False, filed_source="the ESEF reports")
    assert all(r.net_income_allowance is None for r in exact.income_statements)
