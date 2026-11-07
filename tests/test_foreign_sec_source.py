"""SEC route for non-US companies: ForeignSECFundamentalsSource (clients/foreign_sec_source.py). Synthetic data."""

import pytest

from clients.foreign_sec_source import SOURCE_NAME, ForeignSECFundamentalsSource
from clients.sec_filer_lookup import SecFiler
from clients.yfinance_client import YahooCompanyData
from core.errors import TickerNotCoveredError
from core.ports import FundamentalsSource
from tests.test_data_source_ports import assert_fundamentals_contract
from tests.test_edgar_mapper import FILED, Y23, Y24, _ifrs

FACTS = _ifrs({
    "Revenue": [(*Y24, 1000.0e6, FILED, "EUR"), (*Y23, 900.0e6, FILED, "EUR")],
    "ProfitLossAttributableToOwnersOfParent": [(*Y24, 110.0e6, FILED, "EUR"), (*Y23, 95.0e6, FILED, "EUR")],
    "BasicEarningsLossPerShare": [(*Y24, 1.10, FILED, "EUR/shares"), (*Y23, 0.95, FILED, "EUR/shares")],
    "WeightedAverageShares": [(*Y24, 100.0e6, FILED, "shares"), (*Y23, 100.0e6, FILED, "shares")],
    "Assets": [(None, "2024-12-31", 2000.0e6, FILED, "EUR"), (None, "2023-12-31", 1900.0e6, FILED, "EUR")],
    "EquityAttributableToOwnersOfParent": [(None, "2024-12-31", 800.0e6, FILED, "EUR")],
    "CashFlowsFromUsedInOperatingActivities": [(*Y24, 210.0e6, FILED, "EUR")],
})
YAHOO = YahooCompanyData(
    yahoo_symbol="ULVR.L",
    info={"longName": "Example plc", "currency": "GBp", "financialCurrency": "EUR", "sector": "Consumer Defensive",
          "companyOfficers": [{"name": "Jane Roe", "title": "CEO"}]},
    dividends=(("2024-05-01", 40.0), ("2024-11-01", 42.0)),
    splits=(),
)
FILER = SecFiler("0000000099", "EXAMPLE PLC", ("EXPL",), "20-F", "2025-03-10")


class FakeEdgar:
    def fetch_company_facts(self, cik):
        return FACTS

    def fetch_submissions(self, cik):
        return {"name": "EXAMPLE PLC", "sic": "2840"}


class FakeYahoo:
    def __init__(self, data=YAHOO, net_income=None):
        self.data = data
        self.net_income = {"2024-12-31": [110.0e6]} if net_income is None else net_income

    def fetch_company_data(self, ticker):
        return self.data

    def fetch_annual_net_income(self, ticker):
        return self.net_income


class FakeLookup:
    def __init__(self):
        self.calls = []

    def resolve(self, ticker, home_name):
        self.calls.append((ticker, home_name))
        return FILER


def source(yahoo=None, lookup=None):
    return ForeignSECFundamentalsSource(FakeEdgar(), yahoo or FakeYahoo(), lookup or FakeLookup())


def test_home_listing_gets_the_filers_statements_with_the_listings_market_data():
    lookup = FakeLookup()
    f = source(lookup=lookup).fetch_fundamentals("ULVR.LSE")
    assert isinstance(source(), FundamentalsSource)
    assert_fundamentals_contract(f)
    assert lookup.calls == [("ULVR.LSE", "Example plc")]                 # looked up by the home listing's name
    assert (f.source, f.symbol, f.exchange) == (SOURCE_NAME, "ULVR", "LSE")
    assert (f.statement_currency, f.trading_currency, f.cash_flow_currency) == ("EUR", "GBp", "EUR")
    assert f.annual_income_statements[0].net_income == 110.0e6
    assert f.annual_balance_sheets[0].total_equity == 800.0e6
    assert f.quarterly_income_statements == () and f.quarterly_balance_sheets == ()
    assert [(p.amount, p.currency) for p in f.dividend_payments] == [(0.40, "GBP"), (0.42, "GBP")]   # pence -> pounds
    assert any("quotes them in GBp; converted to GBP" in n for n in f.notes)
    assert f.ceo_name == "Jane Roe"
    assert any("EXAMPLE PLC (CIK 0000000099) (US listing EXPL)" in n for n in f.notes)
    assert any("covers 2 fiscal years (from FY2023)" in n and "data limit" in n for n in f.notes)


def test_statement_currency_disagreeing_with_yahoo_gives_no_dossier():
    yahoo = YahooCompanyData(yahoo_symbol="X.L", info={**YAHOO.info, "financialCurrency": "GBP"})
    with pytest.raises(TickerNotCoveredError, match="Yahoo reports this company's statements in GBP"):
        source(yahoo=FakeYahoo(yahoo)).fetch_fundamentals("X.LSE")


def test_net_income_disagreeing_with_yahoo_gives_no_dossier():
    with pytest.raises(TickerNotCoveredError, match="net income differs from the SEC filing of EXAMPLE PLC"):
        source(yahoo=FakeYahoo(net_income={"2024-12-31": [150.0e6, 160.0e6]})).fetch_fundamentals("X.LSE")


def test_without_an_overlapping_yahoo_year_the_match_is_noted():
    f = source(yahoo=FakeYahoo(net_income={})).fetch_fundamentals("X.LSE")
    assert any("Yahoo Finance has no overlapping year of net income" in n for n in f.notes)


def test_no_yahoo_data_for_the_listing_gives_no_dossier():
    class NoYahoo(FakeYahoo):
        def fetch_company_data(self, ticker):
            return None
    with pytest.raises(TickerNotCoveredError, match="no Yahoo Finance data"):
        source(yahoo=NoYahoo()).fetch_fundamentals("X.LSE")
