"""Free resolution path: FreeUSFundamentalsSource (EDGAR + Yahoo), the exchange router, the provider."""

import pytest

from clients.factory import ClientFactory
from clients.free_us_source import SOURCE_NAME, FreeUSFundamentalsSource
from clients.routing_source import RoutingFundamentalsSource
from clients.yfinance_client import YahooCompanyData
from core.errors import TickerNotCoveredError
from core.financial_data_assembler import load_financial_data
from core.ports import FundamentalsSource
from core.price_quote import PriceQuote
from tests.test_data_source_ports import _Quotes, _Rates, assert_fundamentals_contract
from tests.test_edgar_mapper import fixture

SO_YAHOO = YahooCompanyData(
    yahoo_symbol="SO",
    info={"longName": "Southern Company (The)", "sector": "Utilities", "industry": "Utilities - Regulated Electric",
          "fullTimeEmployees": 29502, "currency": "USD", "financialCurrency": "USD",
          "companyOfficers": [{"name": "Mr. Christopher C. Womack", "title": "Chairman, President & CEO"}],
          "dividendRate": 2.96, "beta": 0.45, "heldPercentInstitutions": 0.68},
    dividends=tuple((f"{year}-05-15", 0.5 + 0.02 * (year - 2000)) for year in range(2000, 2026)),
    splits=(),
)


class FakeEdgar:
    def __init__(self, ticker="SO"):
        self.data = fixture(ticker)
        self.calls = []

    def resolve_cik(self, ticker):
        self.calls.append(("cik", ticker))
        return "0000092122"

    def fetch_company_facts(self, cik):
        return self.data["companyfacts"]

    def fetch_submissions(self, cik):
        return self.data["submissions"]

    def predecessor_ciks(self, ticker):
        return ()

    def fetch_certifying_officer(self, cik, submissions):
        return self.officer if hasattr(self, "officer") else None


class FakeYahoo:
    def __init__(self, data=SO_YAHOO):
        self.data = data

    def fetch_company_data(self, ticker):
        return self.data


def source(yahoo=SO_YAHOO, edgar=None):
    return FreeUSFundamentalsSource(edgar or FakeEdgar(), FakeYahoo(yahoo))


def test_free_us_source_satisfies_the_port_and_the_contract():
    src = source()
    assert isinstance(src, FundamentalsSource)
    fundamentals = src.fetch_fundamentals("SO.US")
    assert_fundamentals_contract(fundamentals)
    assert fundamentals.source == SOURCE_NAME and fundamentals.symbol == "SO"
    assert fundamentals.statement_currency == fundamentals.trading_currency == "USD"


def test_statements_from_edgar_profile_and_dividends_from_yahoo():
    f = source().fetch_fundamentals("SO.US")
    assert f.annual_balance_sheets[0].period_end == "2025-12-31" and len(f.annual_income_statements) == 19
    assert f.quarterly_income_statements and f.quarterly_balance_sheets
    assert (f.industry, f.ceo_name, f.employees) == ("Utilities - Regulated Electric", "Mr. Christopher C. Womack", 29502)
    assert f.exchange == "NYSE" and f.name == "Southern Company (The)"
    assert len(f.dividend_payments) == 26 and f.dividend_payments[0].currency == "USD"
    assert f.annual_dividends_paid["2024-12-31"] == 2_954e6
    assert f.forward_dividend_rate == 2.96 and f.market.institutional_ownership == pytest.approx(68.0)
    assert f.updated_at is None                                 # no vendor refresh date for SEC filings
    assert any(n.startswith("Statements as filed with the SEC; latest 10-K/10-Q filed 2026-") for n in f.notes)
    assert f.shares_outstanding > 1_100e6                      # cover-page count of the latest 10-K


def test_notes_explain_derivations_and_dividend_dating():
    notes = source().fetch_fundamentals("SO.US").notes
    assert any("ex-dividend date" in n for n in notes)
    assert any("inventory: derived as the sum of" in n for n in notes)
    assert any("fourth quarter: derived" in n for n in notes)


def test_split_history_is_applied_and_noted():
    apple_yahoo = YahooCompanyData(yahoo_symbol="AAPL", info={"currency": "USD"},
                                   splits=(("2014-06-09", 7.0), ("2020-08-31", 4.0)))
    f = source(apple_yahoo, FakeEdgar("AAPL")).fetch_fundamentals("AAPL.US")
    eps = {r.period_end[:4]: r.eps for r in f.annual_income_statements}
    assert eps["2013"] == pytest.approx(40.03 / 28, abs=0.005)
    assert any("2014-06-09 7:1" in n for n in f.notes)


def test_without_yahoo_data_statements_still_resolve():
    class NoYahoo:
        def fetch_company_data(self, ticker):
            return None
    f = FreeUSFundamentalsSource(FakeEdgar(), NoYahoo()).fetch_fundamentals("SO.US")
    assert f.dividend_payments is None and f.annual_income_statements
    assert f.ceo_name == "N/A" and f.name                       # name from SEC submissions
    assert any("Yahoo Finance company data unavailable" in n for n in f.notes)


def test_filer_without_xbrl_statements_is_not_covered():
    class EmptyEdgar(FakeEdgar):
        def fetch_company_facts(self, cik):
            return {"facts": {}}
    with pytest.raises(TickerNotCoveredError, match="no annual reports"):
        source(edgar=EmptyEdgar()).fetch_fundamentals("SO.US")


def test_router_sends_us_tickers_and_rejects_other_markets():
    src = source()
    router = RoutingFundamentalsSource({"us": src}, name="free")
    assert isinstance(router, FundamentalsSource)
    assert router.fetch_fundamentals("SO.US").source == SOURCE_NAME
    with pytest.raises(TickerNotCoveredError, match="exchange 'LSE'"):
        router.fetch_fundamentals("VOD.LSE")
    with pytest.raises(TickerNotCoveredError):
        router.fetch_fundamentals("SO")


def test_free_provider_is_registered():
    provider = ClientFactory.fundamentals_provider("free")
    assert provider.required_env == ("SEC_USER_AGENT",) and provider.secret_env == ()
    router = ClientFactory.create_fundamentals_source({"SEC_USER_AGENT": "Test t@example.invalid"}, "free")
    assert isinstance(router, RoutingFundamentalsSource) and set(router.routes) == {"US"}
    with pytest.raises(ValueError, match="contact email"):
        ClientFactory.create_fundamentals_source({"SEC_USER_AGENT": "no contact"}, "free")


def test_free_path_assembles_financial_data():
    class Quotes(_Quotes):
        def get_quote(self, ticker):
            return PriceQuote(88.0, "USD")
    data = load_financial_data("SO.US", source(), Quotes(), _Rates())
    assert data["data_source"] == SOURCE_NAME and data["price"] == 88.0
    assert data["history"]["2024-12-31"]["total_equity"] == 33_208e6
    assert data["history"]["2024-12-31"]["dividend"] == pytest.approx(0.98)   # Yahoo payments, 2024
    assert data["industry"] == "Utilities - Regulated Electric"
    assert data["warnings"][0].startswith("Dividends per year bucketed by ex-dividend date")


class PredecessorEdgar(FakeEdgar):
    def __init__(self):
        super().__init__("GOOGL")
        self.predecessor = fixture("GOOGL_PREDECESSOR")

    def resolve_cik(self, ticker):
        return "0001652044"

    def predecessor_ciks(self, ticker):
        return ("0001288776",)

    def fetch_company_facts(self, cik):
        return self.predecessor["companyfacts"] if cik == "0001288776" else self.data["companyfacts"]


def test_predecessor_history_is_merged_and_noted():
    yahoo = YahooCompanyData(yahoo_symbol="GOOGL", info={"currency": "USD"},
                             splits=(("2014-03-27", 2.002), ("2022-07-18", 20.0)))
    f = FreeUSFundamentalsSource(PredecessorEdgar(), FakeYahoo(yahoo)).fetch_fundamentals("GOOGL.US")
    assert f.annual_income_statements[-1].period_end == "2007-12-31"
    assert any("EARLIER YEARS FROM THE PREDECESSOR FILER GOOGLE INC." in n.upper() and "CIK 0001288776" in n
               for n in f.notes)


def test_successor_issuer_without_mapped_predecessor_is_noted():
    edgar = FakeEdgar()
    edgar.data = dict(edgar.data, submissions=dict(edgar.data["submissions"], filings={"recent": {
        "form": ["10-K", "8-K12B"], "filingDate": ["2026-02-20", "2016-07-01"],
        "accessionNumber": ["a", "b"], "reportDate": ["2025-12-31", ""]}}))
    f = FreeUSFundamentalsSource(edgar, FakeYahoo()).fetch_fundamentals("SO.US")
    assert any("filed a Form 8-K12B (successor issuer) on 2016-07-01" in n for n in f.notes)


def test_ceo_from_the_10k_certification_when_yahoo_has_none():
    edgar = FakeEdgar()
    edgar.officer = "Jane Q. Doe"
    no_ceo = YahooCompanyData(yahoo_symbol="SO", info={"currency": "USD", "companyOfficers": []})
    f = FreeUSFundamentalsSource(edgar, FakeYahoo(no_ceo)).fetch_fundamentals("SO.US")
    assert f.ceo_name == "Jane Q. Doe"
    assert any("Exhibit 31.1 certification" in n for n in f.notes)
    # Yahoo's CEO is preferred; the certification is not fetched then
    assert source().fetch_fundamentals("SO.US").ceo_name == "Mr. Christopher C. Womack"
