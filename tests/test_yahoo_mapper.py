"""Yahoo company data for the free path: fetch (fake yfinance) and mapping to neutral pieces."""

import sys

import pandas as pd
import pytest

from clients import yahoo_mapper
from clients.yfinance_client import YahooCompanyData, YFinanceClient
from core.fundamentals import DividendPayment

INFO = {
    "longName": "Southern Company (The)", "sector": "Utilities", "industry": "Utilities - Regulated Electric",
    "fullTimeEmployees": 29502, "currency": "USD", "financialCurrency": "USD",
    "companyOfficers": [{"name": "Mr. David  Poroch", "title": "Executive VP, CFO & Treasurer"},
                        {"name": "Mr. Christopher C. Womack", "title": "Chairman, President & CEO"}],
    "trailingAnnualDividendRate": 2.92, "trailingAnnualDividendYield": 0.0331, "dividendRate": 2.96,
    "trailingPE": 22.4, "bookValue": 30.2, "returnOnEquity": 0.124, "returnOnAssets": 0.031,
    "profitMargins": 0.149, "enterpriseValue": 168e9, "heldPercentInsiders": 0.0017,
    "heldPercentInstitutions": 0.6812, "beta": 0.45, "fiftyTwoWeekHigh": 96.4, "fiftyTwoWeekLow": 80.5,
}


def data(**overrides):
    fields = {"yahoo_symbol": "SO", "info": INFO,
              "dividends": (("1982-01-26", 0.405), ("2026-08-17", 0.74), ("2026-09-01", 0.0)),
              "splits": (("1994-03-01", 2.0),)}
    fields.update(overrides)
    return YahooCompanyData(**fields)


def test_profile_and_ceo():
    prof = yahoo_mapper.profile(data())
    assert (prof.name, prof.sector, prof.industry) == ("Southern Company (The)", "Utilities",
                                                      "Utilities - Regulated Electric")
    assert prof.employees == 29502 and prof.ceo_name == "Mr. Christopher C. Womack"
    assert (prof.quote_currency, prof.financial_currency) == ("USD", "USD")


def test_profile_without_officers_or_employees():
    prof = yahoo_mapper.profile(data(info={"shortName": "HORMEL", "companyOfficers": [{"name": "X", "title": "CFO"}]}))
    assert prof.name == "HORMEL" and prof.ceo_name == "N/A" and prof.employees is None


def test_dividend_payments_skip_zero_amounts():
    payments = yahoo_mapper.dividend_payments(data(), "USD")
    assert payments == (DividendPayment("1982-01-26", 0.405, "USD"), DividendPayment("2026-08-17", 0.74, "USD"))
    assert yahoo_mapper.dividend_payments(data(dividends=()), "USD") is None


def test_splits():
    assert yahoo_mapper.splits(data()) == (("1994-03-01", 2.0),)


def test_market_data_units():
    market = yahoo_mapper.market_data(data())
    assert market.insider_ownership == pytest.approx(0.17) and market.institutional_ownership == pytest.approx(68.12)
    assert market.dividend_yield == 0.0331 and market.roe == 0.124 and market.beta == 0.45
    assert (market.week_52_high, market.week_52_low) == (96.4, 80.5)
    assert market.per_share_currency == "USD"
    assert yahoo_mapper.forward_dividend_rate(data()) == 2.96
    assert yahoo_mapper.forward_dividend_rate(data(info={})) is None


def test_market_data_tolerates_missing_and_junk():
    market = yahoo_mapper.market_data(data(info={"beta": None, "trailingPE": "Infinity?", "bookValue": "NA"}))
    assert market.beta == 0.0 and market.pe_ratio == 0.0 and market.book_value_per_share == 0.0


class _FakeTicker:
    def __init__(self, symbol):
        if symbol == "BOOM":
            raise RuntimeError("network")
        self.info = dict(INFO)
        self.dividends = pd.Series([0.405, 0.74], index=pd.to_datetime(["1982-01-26", "2026-08-17"]))
        self.splits = pd.Series([2.0], index=pd.to_datetime(["1994-03-01"]))


class _FakeYF:
    Ticker = _FakeTicker


def test_client_fetches_company_data(monkeypatch):
    monkeypatch.setitem(sys.modules, "yfinance", _FakeYF)
    fetched = YFinanceClient().fetch_company_data("SO.US")
    assert fetched.yahoo_symbol == "SO" and fetched.info["industry"] == "Utilities - Regulated Electric"
    assert fetched.dividends == (("1982-01-26", 0.405), ("2026-08-17", 0.74))
    assert fetched.splits == (("1994-03-01", 2.0),)


def test_client_returns_none_on_failure(monkeypatch):
    monkeypatch.setitem(sys.modules, "yfinance", _FakeYF)
    assert YFinanceClient().fetch_company_data("BOOM.US") is None
    assert YFinanceClient().fetch_company_data("NOSUFFIX") is None


def test_search_us_listings_keeps_us_exchanges_only(monkeypatch):
    class _Search:
        def __init__(self, query, max_results=10, news_count=0):
            self.quotes = [{"symbol": "BP", "exchange": "NYQ", "longname": "BP p.l.c."},
                           {"symbol": "BPAQF", "exchange": "PNK", "shortname": "BP p.l.c."},
                           {"symbol": "BP.L", "exchange": "LSE", "longname": "BP p.l.c."}]

    class _YF:
        Search = _Search

    monkeypatch.setitem(sys.modules, "yfinance", _YF)
    assert YFinanceClient().search_us_listings("BP p.l.c.") == [("BP", "NYQ", "BP p.l.c."), ("BPAQF", "PNK", "BP p.l.c.")]


def test_search_us_listings_retries_then_reports_a_failed_search_as_none(monkeypatch):
    calls = []

    class _YF:
        def Search(*args, **kwargs):
            calls.append(1)
            raise RuntimeError("rate limited")

    monkeypatch.setitem(sys.modules, "yfinance", _YF)
    monkeypatch.setattr(YFinanceClient, "SEARCH_RETRY_SECONDS", 0.0)
    assert YFinanceClient().search_us_listings("BP p.l.c.") is None
    assert len(calls) == 2


def test_search_us_listings_is_empty_when_nothing_is_listed_in_the_us(monkeypatch):
    class _Search:
        def __init__(self, query, max_results=10, news_count=0):
            self.quotes = [{"symbol": "YU.L", "exchange": "LSE", "longname": "Yü Group PLC"}]

    class _YF:
        Search = _Search

    monkeypatch.setitem(sys.modules, "yfinance", _YF)
    assert YFinanceClient().search_us_listings("Yü Group PLC") == []


# --- Annual statements (companies with no XBRL) ---

from clients.yahoo_mapper import annual_statements  # noqa: E402
from clients.yfinance_client import YahooStatements  # noqa: E402
from core.fundamentals import IncomeStatementRow  # noqa: E402

E26, E25 = "2026-02-28", "2025-02-28"
STATEMENTS = YahooStatements(
    "HBH.DE",
    income={"Total Revenue": {E26: 6433.9e6, E25: 6200e6}, "Net Income Common Stockholders": {E26: 138.4e6, E25: 140.7e6},
            "Basic EPS": {E26: 8.66, E25: 8.80}},
    balance={"Stockholders Equity": {E26: 2070e6, E25: 1990e6}, "Total Assets": {E26: 4800e6, E25: 4700e6},
             "Current Assets": {E26: 1900e6, E25: 1850e6}, "Current Liabilities": {E26: 1332e6, E25: 1300e6},
             "Long Term Debt And Capital Lease Obligation": {E26: 1264.6e6, E25: 1300e6},
             "Long Term Capital Lease Obligation": {E26: 913.9e6},                      # no lease line for FY2025
             "Total Non Current Liabilities Net Minority Interest": {E26: 1346.7e6, E25: 1400e6},
             "Ordinary Shares Number": {E26: 15.997e6, E25: 15.991e6}},
    cashflow={"Operating Cash Flow": {E26: 400e6}, "Cash Dividends Paid": {E26: -38.4e6}})


def test_yahoo_statements_become_annual_rows():
    annual = annual_statements(STATEMENTS, "EUR")
    assert [r.period_end for r in annual.income_statements] == [E26, E25]
    assert annual.income_statements[0] == IncomeStatementRow(E26, 6433.9e6, 138.4e6, 8.66)
    latest, older = annual.balance_sheets
    assert latest.long_term_debt == 1264.6e6            # debt incl. the reported IFRS 16 lease line
    assert older.long_term_debt == 1400e6               # no lease line: all non-current liabilities, the upper bound
    assert annual.shares_by_year == {"2026": 15.997e6, "2025": 15.991e6}
    assert annual.dividends_paid == {E26: 38.4e6} and annual.operating_cash_flow == {E26: 400e6}
    assert annual.currency == "EUR"
    assert any("FY2025 is all non-current liabilities" in n for n in annual.notes)


def test_empty_yahoo_cells_stay_missing():
    sparse = YahooStatements("X.L", income={"Net Income": {E26: 10e6}}, balance={})
    annual = annual_statements(sparse, "GBP")
    assert annual.income_statements[0] == IncomeStatementRow(E26, None, 10e6, None) and annual.balance_sheets == ()
