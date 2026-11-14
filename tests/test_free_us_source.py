"""Free resolution path: FreeUSFundamentalsSource (EDGAR + Yahoo), the exchange router, the provider."""

import copy

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
from tests.test_edgar_mapper import _instance, fixture

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


def test_non_usd_filer_is_not_covered_by_the_us_route():
    class EuroEdgar(FakeEdgar):
        def fetch_company_facts(self, cik):
            return {"facts": {"us-gaap": {"NetIncomeLoss": {"units": {"EUR": [
                {"start": "2024-01-01", "end": "2024-12-31", "val": 10.0, "filed": "2025-03-01", "form": "10-K"}]}}}}}
    with pytest.raises(TickerNotCoveredError, match="reported in EUR; only USD"):
        source(edgar=EuroEdgar()).fetch_fundamentals("SO.US")


def test_us_ticker_of_a_foreign_filer_points_to_its_home_listing():
    class ForeignEdgar(FakeEdgar):
        def fetch_submissions(self, cik):
            subs = dict(super().fetch_submissions(cik))
            subs["name"] = "BP PLC"
            subs["filings"] = {"recent": {"form": ["6-K", "20-F"], "filingDate": ["2026-05-01", "2026-03-06"]}}
            return subs
    with pytest.raises(TickerNotCoveredError, match="BP PLC files 20-F as a foreign company and this US line is not "
                                                     "confirmed to trade its shares; use its home-exchange listing"):
        source(edgar=ForeignEdgar()).fetch_fundamentals("SO.US")


def _cover(*rows):
    """An XBRL instance cover: (Security12bTitle, TradingSymbol or None) per context."""
    body = "".join(f'<dei:Security12bTitle contextRef="c{i}">{title}</dei:Security12bTitle>'
                   + (f'<dei:TradingSymbol contextRef="c{i}">{symbol}</dei:TradingSymbol>' if symbol else "")
                   for i, (title, symbol) in enumerate(rows))
    return f'<xbrl xmlns:dei="http://xbrl.sec.gov/dei/2024">{body}</xbrl>'


def test_registered_line_basis_from_the_annual_report_cover():
    from clients.edgar_mapper import registered_line_basis
    assert registered_line_basis(_cover(("Ordinary Shares, Nominal Value $1.00 Per Share", "FRO")), "FRO") == "shares"
    assert registered_line_basis(_cover(("Common stock, par value Won 500 per share*", "GRVY"),
                                        ("American depositary shares, each representing one share of common stock", None)),
                                 "GRVY") == "one_to_one_ads"
    assert registered_line_basis(_cover(("American Depositary Shares", "BP"), ("Ordinary Shares of 25c each", None)), "BP") == "ads"
    assert registered_line_basis("<xbrl/>", "X") is None


class _ForeignEdgar(FakeEdgar):
    def __init__(self, cover):
        super().__init__()
        self.cover = cover

    def fetch_submissions(self, cik):
        return {**super().fetch_submissions(cik), "name": "FRONTLINE PLC",
                "filings": {"recent": {"form": ["20-F"], "filingDate": ["2026-03-27"], "accessionNumber": ["a1"]}}}

    def fetch_filing_instance(self, cik, accession):
        return self.cover


def test_us_line_trading_a_foreign_filers_ordinary_shares_goes_through_the_foreign_route():
    calls = []

    class Foreign:
        def fetch_for_filer(self, ticker, filer, note):
            calls.append((ticker, filer.cik, filer.annual_form, note))
            return "foreign dossier"
    src = FreeUSFundamentalsSource(_ForeignEdgar(_cover(("Ordinary Shares", "SO"))), FakeYahoo(), foreign=Foreign())
    assert src.fetch_fundamentals("SO.US") == "foreign dossier"
    assert calls[0][:3] == ("SO.US", "0000092122", "20-F") and "trades its ordinary shares" in calls[0][3]


def test_us_line_that_is_an_adr_is_refused():
    class Foreign:
        def fetch_for_filer(self, *args):
            raise AssertionError("an ADR must not reach the foreign route")
    src = FreeUSFundamentalsSource(_ForeignEdgar(_cover(("American Depositary Shares", "SO"))), FakeYahoo(), foreign=Foreign())
    with pytest.raises(TickerNotCoveredError, match="is an ADR"):
        src.fetch_fundamentals("SO.US")


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
    assert provider.required_env == ("SEC_USER_AGENT",)
    # optional, redacted from logs
    assert provider.optional_env == provider.secret_env == ("EULERPOOL_API_KEY", "COMPANIES_HOUSE_API_KEY")
    router = ClientFactory.create_fundamentals_source({"SEC_USER_AGENT": "Test t@example.invalid"}, "free")
    assert isinstance(router, RoutingFundamentalsSource)
    assert {e for e, src in router.routes.items() if isinstance(src, FreeUSFundamentalsSource)} == {"US", "NYSE", "NASDAQ", "AMEX"}
    for exchange in ("TSE", "SW", "AU", "TO"):          # no ESEF: the SEC route, then Yahoo statements (+ Eulerpool)
        assert [type(s).__name__ for s in router.routes[exchange].sources] == ["ForeignSECFundamentalsSource",
                                                                               "UnfiledCompanySource"]
    european = router.routes["LSE"]                     # SEC route first, then the ESEF reports
    assert [type(s).__name__ for s in european.sources] == ["ForeignSECFundamentalsSource", "EuropeanFilingsSource",
                                                            "UnfiledCompanySource"]
    assert european.sources[1].history is None                                      # no Eulerpool key
    with_key = ClientFactory.create_fundamentals_source(
        {"SEC_USER_AGENT": "Test t@example.invalid", "EULERPOOL_API_KEY": "k"}, "free")
    assert type(with_key.routes["LSE"].sources[1].history).__name__ == "EulerpoolClient"
    assert type(with_key.routes["LSE"].sources[2]).__name__ == "UnfiledCompanySource"   # no filings at all
    assert with_key.routes["LSE"].sources[2].eulerpool is not None
    assert with_key.routes["SW"].sources[1].eulerpool is not None and router.routes["SW"].sources[1].eulerpool is None
    assert type(european.sources[2]).__name__ == "UnfiledCompanySource" and european.sources[2].eulerpool is None
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


# --- Share counts reported per class ---------------------------------------------------------------

def _no_shares(fixture_data):
    """The fixture's filer with its share tags removed: what a dual-class company looks like in companyfacts."""
    facts = copy.deepcopy(fixture_data)
    for taxonomy in facts["companyfacts"]["facts"].values():
        for tag in ("CommonStockSharesOutstanding", "CommonStockSharesIssued", "EntityCommonStockSharesOutstanding",
                    "WeightedAverageNumberOfSharesOutstandingBasic", "TreasuryStockCommonShares", "TreasuryStockShares"):
            taxonomy.pop(tag, None)
    return facts


class DualClassEdgar(FakeEdgar):
    def __init__(self, a, b, cover=None):
        super().__init__()
        self.data = _no_shares(self.data)
        self.a, self.b = a, b
        self.requests = []
        self.data["submissions"]["filings"]["recent"] = {
            "form": ["10-K", "10-K"], "reportDate": ["2025-12-31", "2024-12-31"], "filingDate": ["2026-02-20", "2025-02-20"],
            "accessionNumber": ["a-1", "a-2"], "primaryDocument": ["a.htm", "b.htm"], "isXBRL": [1, 1]}

    def fetch_filing_instance(self, cik, accession):
        self.requests.append(accession)
        filing = dict(zip(self.data["submissions"]["filings"]["recent"]["accessionNumber"],
                          self.data["submissions"]["filings"]["recent"]["reportDate"]))
        end = filing[accession]
        return _instance(("CommonStockSharesOutstanding", end, "us-gaap:CommonClassAMember", self.a),
                         ("CommonStockSharesOutstanding", end, "us-gaap:CommonClassBMember", self.b))


def _yahoo_total(total):
    return YahooCompanyData(yahoo_symbol="SO", info={"currency": "USD", "impliedSharesOutstanding": total})


def test_dual_class_share_counts_come_from_the_filings():
    f = source(_yahoo_total(1_100e6), DualClassEdgar(100e6, 1_000e6)).fetch_fundamentals("SO.US")
    assert f.annual_balance_sheets[0].shares_outstanding == 1_100e6
    assert f.shares_by_year["2025"] == 1_100e6
    assert f.quarterly_balance_sheets[0].shares_outstanding == 1_100e6   # for the TTM per-share figures
    assert any("all classes added one for one" in n for n in f.notes)


def test_classes_that_do_not_add_up_to_yahoos_total_are_not_used():
    """Berkshire: one Class A is 1,500 Class B, so adding the counts is wrong. Yahoo's total stands for today."""
    f = source(_yahoo_total(2_160e6), DualClassEdgar(600_000.0, 1_300e6)).fetch_fundamentals("SO.US")
    assert not f.annual_balance_sheets[0].shares_outstanding
    assert f.shares_outstanding == 2_160e6 and f.quarterly_balance_sheets[0].shares_outstanding == 2_160e6
    assert any("today's total from Yahoo Finance" in n for n in f.notes)


def test_filings_without_instances_leave_yahoos_total():
    class NoInstances(DualClassEdgar):
        def fetch_filing_instance(self, cik, accession):
            return None
    f = source(_yahoo_total(1_100e6), NoInstances(1, 1)).fetch_fundamentals("SO.US")
    assert f.shares_outstanding == 1_100e6


def test_single_class_companies_fetch_no_instances():
    edgar = DualClassEdgar(1, 1)
    edgar.data = fixture("SO")
    assert source(edgar=edgar).fetch_fundamentals("SO.US").annual_balance_sheets[0].shares_outstanding
    assert edgar.requests == []


def test_a_10k_missing_from_company_facts_is_read_from_its_own_file():
    class LateFiling(FakeEdgar):
        def __init__(self):
            super().__init__()
            self.data = dict(self.data, submissions=dict(self.data["submissions"], filings={"recent": {
                "form": ["10-K"], "reportDate": ["2026-12-31"], "filingDate": ["2027-02-20"], "accessionNumber": ["late"],
                "primaryDocument": ["a.htm"], "isXBRL": [1]}}))

        def fetch_filing_instance(self, cik, accession):
            assert accession == "late"
            return _instance(("Assets", "2026-12-31", None, 1)).replace(
                "<us-gaap:Assets contextRef=\"c0\">1</us-gaap:Assets>",
                "<unit id=\"U\"><measure>iso4217:USD</measure></unit>"
                "<context id=\"d\"><period><startDate>2026-01-01</startDate><endDate>2026-12-31</endDate></period></context>"
                "<us-gaap:Assets contextRef=\"c0\" unitRef=\"U\">900</us-gaap:Assets>"
                "<us-gaap:NetIncomeLoss contextRef=\"d\" unitRef=\"U\">77</us-gaap:NetIncomeLoss>")
    f = source(edgar=LateFiling()).fetch_fundamentals("SO.US")
    assert f.annual_income_statements[0].period_end == "2026-12-31" and f.annual_income_statements[0].net_income == 77.0
    assert any("10-K for 2026-12-31 read from the filing's own XBRL file" in n for n in f.notes)


def test_a_latest_count_that_is_only_an_average_uses_the_classes():
    """UHS: four classes, so only the year's average is tagged: 63.6M against 61.1M at the year end."""
    edgar = DualClassEdgar(10e6, 51.1e6)
    edgar.data["companyfacts"]["facts"]["us-gaap"]["WeightedAverageNumberOfSharesOutstandingBasic"] = {"units": {"shares": [
        {"start": "2025-01-01", "end": "2025-12-31", "val": 63.6e6, "filed": "2026-02-20", "form": "10-K", "fy": 2025, "fp": "FY"}]}}
    f = source(_yahoo_total(61.1e6), edgar).fetch_fundamentals("SO.US")
    assert f.annual_balance_sheets[0].shares_outstanding == 61.1e6


def test_the_filed_accounts_route_is_wired_for_london_only_with_a_companies_house_key():
    def unfiled(env):
        router = ClientFactory.create_fundamentals_source({"SEC_USER_AGENT": "Test t@example.invalid", **env}, "free")
        return next(s for s in router.routes["LSE"].sources if type(s).__name__ == "UnfiledCompanySource")
    assert unfiled({}).companies_house is None
    assert type(unfiled({"COMPANIES_HOUSE_API_KEY": "test-key"}).companies_house).__name__ == "CompaniesHouseHistorySource"
