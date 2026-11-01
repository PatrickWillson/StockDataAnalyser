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
