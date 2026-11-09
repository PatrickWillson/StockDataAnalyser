"""Eulerpool-only companies (no SEC or ESEF filings): EulerpoolOnlySource, checked against Yahoo. Synthetic data."""

import pytest

from clients.eulerpool_source import SOURCE_NAME, EulerpoolOnlySource
from clients.yfinance_client import YahooCompanyData
from core.errors import TickerNotCoveredError
from tests.test_data_source_ports import assert_fundamentals_contract

YAHOO = YahooCompanyData(
    yahoo_symbol="HBH.DE",
    info={"longName": "HORNBACH Holding AG & Co. KGaA", "currency": "EUR", "financialCurrency": "EUR",
          "sharesOutstanding": 16_000_000},
    dividends=(("2025-07-10", 2.4),), splits=())
NET_INCOME = {"2025-02-28": [140e6], "2024-02-29": [100e6], "2023-02-28": [160e6]}


class FakeEulerpool:
    def __init__(self, currency="EUR", shares=15.98, net_income_2024=100.0, profile=True):
        self.currency, self.shares, self.ni, self.profile = currency, shares, net_income_2024, profile

    def find_profile(self, symbol, name):
        return {"isin": "DE0006083405", "name": "HORNBACH Holding AG & Co KgaA", "currency": self.currency} \
            if self.profile else None

    def fetch_statements(self, isin):
        rows = [("2025-02-28", 140.0), ("2024-02-29", self.ni), ("2023-02-28", 160.0), ("2022-02-28", 250.0)]
        return {"income": [{"period": e, "revenue": 6000.0, "netIncome": ni} for e, ni in rows],
                "balance_quarterly": [{"period": e, "totalAssets": 4500.0, "totalEquity": 2000.0,
                                       "sharesOutstanding": self.shares, "longTermDebt": 900.0} for e, _ in rows],
                "cashflow": []}


class FakeYahoo:
    def __init__(self, data=YAHOO, net_income=None):
        self.data, self.net_income = data, NET_INCOME if net_income is None else net_income

    def fetch_company_data(self, ticker):
        return self.data

    def fetch_annual_net_income(self, ticker):
        return self.net_income


def source(eulerpool=None, yahoo=None):
    return EulerpoolOnlySource(eulerpool or FakeEulerpool(), yahoo or FakeYahoo())


def test_a_company_with_no_filings_gets_eulerpools_figures_labelled_unverified():
    f = source().fetch_fundamentals("HBH.XETRA")
    assert_fundamentals_contract(f)
    assert f.source == SOURCE_NAME and f.statement_currency == "EUR"
    assert [r.period_end for r in f.annual_income_statements][:2] == ["2025-02-28", "2024-02-29"]
    assert all(r.eps is None for r in f.annual_income_statements)
    assert f.annual_balance_sheets[0].long_term_debt == pytest.approx(900e6)
    assert f.shares_by_year["2022"] == pytest.approx(15.98e6)
    assert "UNVERIFIED against the company's reports" in f.notes[0] and "net income within 2% (or 1.1M) in FY2023-FY2025" in f.notes[0]
    assert any("History: Eulerpool has 4 fiscal years" in n for n in f.notes)


def test_whole_millions_are_allowed_for():
    """Fevertree FY2023: Eulerpool 15.0M against 15.3M reported."""
    yahoo = FakeYahoo(net_income={**NET_INCOME, "2024-02-29": [100.9e6]})
    assert source(yahoo=yahoo).fetch_fundamentals("HBH.XETRA").annual_income_statements


@pytest.mark.parametrize("eulerpool, yahoo, message", [
    (FakeEulerpool(currency="USD"), None, "never converted"),
    (FakeEulerpool(net_income_2024=120.0), None, "FY2024 net income .* differs from Yahoo"),
    (FakeEulerpool(shares=32.0), None, "not within 10% of Yahoo's"),            # Bonduelle-like count
    (FakeEulerpool(profile=False), None, "Eulerpool has no listing HBH.DE"),
    (None, FakeYahoo(net_income={"2025-02-28": [140e6]}), "fewer than 2 years"),
])
def test_disagreement_with_yahoo_gives_no_dossier(eulerpool, yahoo, message):
    with pytest.raises(TickerNotCoveredError, match=message):
        source(eulerpool, yahoo).fetch_fundamentals("HBH.XETRA")
