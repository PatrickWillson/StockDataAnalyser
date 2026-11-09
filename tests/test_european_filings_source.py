"""European route: EuropeanFilingsSource (ESEF reports + Yahoo) and the SEC-then-ESEF fallback. Synthetic data."""

import pytest

from clients.esef_client import EsefFiling
from clients.esef_entity_lookup import EsefEntity
from clients.european_filings_source import SOURCE_NAME, EuropeanFilingsSource
from clients.routing_source import FallbackFundamentalsSource
from clients.yfinance_client import YahooCompanyData
from core.errors import SourceRateLimitError, SourceRequestError, TickerNotCoveredError
from core.ports import FundamentalsSource
from tests.test_data_source_ports import assert_fundamentals_contract

LEI = "213800RP9QJQYGWHNT41"


def _fact(concept, period, value, unit="iso4217:GBP"):
    return {"value": str(value), "dimensions": {"concept": f"ifrs-full:{concept}", "entity": f"scheme:{LEI}",
                                                "period": period, "unit": unit}}


def _year(y):
    return f"{y}-06-01T00:00:00/{y + 1}-06-01T00:00:00"


def _report(y, eps_scale=100.0):
    """A June-year annual report for FY(y+1) with its comparative, EPS tagged in pence as pounds."""
    facts = []
    for year, ni in ((y, 150e6), (y - 1, 130e6)):
        facts += [_fact("Revenue", _year(year), 500e6), _fact("ProfitLossAttributableToOwnersOfParent", _year(year), ni),
                  _fact("BasicEarningsLossPerShare", _year(year), ni / 33e6 * eps_scale, "iso4217:GBP/xbrli:shares"),
                  _fact("NoncurrentAssets", f"{year + 1}-06-01T00:00:00", 150e6),
                  _fact("CurrentAssets", f"{year + 1}-06-01T00:00:00", 230e6),
                  _fact("Equity", f"{year + 1}-06-01T00:00:00", 280e6)]
    return {"facts": {f"f{i}": f for i, f in enumerate(facts)}}


FILINGS = (EsefFiling(f"{LEI}-2024-05-31-ESEF-GB-0", "2024-05-31", "GB", "https://x/24.json", "2024-09-20 00:00:00", 0),
           EsefFiling(f"{LEI}-2025-05-31-ESEF-GB-0", "2025-05-31", "GB", "https://x/25.json", "2025-09-24 00:00:00", 0))
REPORTS = {"https://x/24.json": _report(2023), "https://x/25.json": _report(2024)}
YAHOO = YahooCompanyData(
    yahoo_symbol="GAW.L",
    info={"longName": "Games Workshop Group PLC", "currency": "GBp", "financialCurrency": "GBP",
          "sharesOutstanding": 33_000_000, "companyOfficers": [{"name": "Kevin Rountree", "title": "CEO"}]},
    dividends=(("2025-01-10", 165.0),),
    splits=(),
)


class FakeClient:
    def __init__(self, reports=None, fail=()):
        self.reports, self.fail = reports or REPORTS, fail

    def fetch_report(self, filing):
        if filing.json_url in self.fail:
            raise SourceRequestError("boom")
        return self.reports[filing.json_url]


class FakeYahoo:
    def __init__(self, data=YAHOO, net_income=None):
        self.data = data
        self.net_income = {"2025-05-31": [150e6]} if net_income is None else net_income

    def fetch_company_data(self, ticker):
        return self.data

    def fetch_annual_net_income(self, ticker):
        return self.net_income


class FakeLookup:
    def resolve(self, ticker, home_name):
        assert home_name == "Games Workshop Group PLC"
        return EsefEntity(LEI, "GAMES WORKSHOP GROUP PLC", FILINGS)


def source(client=None, yahoo=None):
    return EuropeanFilingsSource(client or FakeClient(), yahoo or FakeYahoo(), FakeLookup())


def test_home_listing_gets_the_esef_statements_with_the_listings_market_data():
    f = source().fetch_fundamentals("GAW.LSE")
    assert isinstance(source(), FundamentalsSource)
    assert_fundamentals_contract(f)
    assert (f.source, f.symbol, f.exchange, f.statement_currency, f.trading_currency) == (SOURCE_NAME, "GAW", "LSE", "GBP", "GBp")
    assert [r.period_end for r in f.annual_income_statements] == ["2025-05-31", "2024-05-31", "2023-05-31"]
    latest = f.annual_income_statements[0]
    assert latest.eps == pytest.approx(150e6 / 33e6)                 # pence tagged as pounds, divided back
    assert f.annual_balance_sheets[0].total_assets == 380e6          # net-assets layout
    assert f.shares_by_year["2025"] == pytest.approx(33e6)
    assert [(p.amount, p.currency) for p in f.dividend_payments] == [(1.65, "GBP")]
    assert f.quarterly_income_statements == ()
    assert f.notes[0].startswith(f"Statements: ESEF annual reports of GAMES WORKSHOP GROUP PLC (LEI {LEI})")
    assert any("History: 3 fiscal years (the ESEF reports cover 3, from FY2023" in n for n in f.notes)
    assert any(n.startswith("ESEF: EPS: implies 1/100 of the listing's current share count") for n in f.notes)


def test_currency_disagreeing_with_yahoo_gives_no_dossier():
    yahoo = YahooCompanyData(yahoo_symbol="GAW.L", info={**YAHOO.info, "financialCurrency": "EUR"})
    with pytest.raises(TickerNotCoveredError, match="Yahoo reports this company's statements in EUR"):
        source(yahoo=FakeYahoo(yahoo)).fetch_fundamentals("GAW.LSE")


def test_net_income_disagreeing_with_yahoo_gives_no_dossier():
    with pytest.raises(TickerNotCoveredError, match="net income differs from the ESEF reports"):
        source(yahoo=FakeYahoo(net_income={"2025-05-31": [90e6]})).fetch_fundamentals("GAW.LSE")


def test_a_report_that_cannot_be_downloaded_is_left_out_and_noted():
    f = source(client=FakeClient(fail=("https://x/24.json",))).fetch_fundamentals("GAW.LSE")
    assert [r.period_end for r in f.annual_income_statements] == ["2025-05-31", "2024-05-31"]
    assert any("could not be downloaded" in n and "2024-05-31" in n for n in f.notes)


def test_no_annual_figures_gives_no_dossier():
    empty = {url: {"facts": {}} for url in REPORTS}
    with pytest.raises(TickerNotCoveredError, match="no annual ESEF report with figures"):
        source(client=FakeClient(reports=empty)).fetch_fundamentals("GAW.LSE")


class Named:
    def __init__(self, name, result):
        self.name, self.result, self.calls = name, result, 0

    def fetch_fundamentals(self, ticker):
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_the_first_source_that_covers_a_ticker_is_used():
    sec, esef = Named("SEC", TickerNotCoveredError("no SEC filer")), Named("ESEF", "fundamentals")
    assert FallbackFundamentalsSource((sec, esef), "SEC, then ESEF").fetch_fundamentals("X.LSE") == "fundamentals"
    covered, unused = Named("SEC", "sec fundamentals"), Named("ESEF", "x")
    assert FallbackFundamentalsSource((covered, unused), "n").fetch_fundamentals("X.LSE") == "sec fundamentals"
    assert unused.calls == 0


def test_no_source_covering_the_ticker_names_every_reason():
    sources = (Named("SEC", TickerNotCoveredError("no SEC filer")), Named("ESEF", TickerNotCoveredError("no ESEF filer")))
    with pytest.raises(TickerNotCoveredError, match="SEC: no SEC filer | ESEF: no ESEF filer"):
        FallbackFundamentalsSource(sources, "n").fetch_fundamentals("X.LSE")


def test_other_failures_are_not_passed_over():
    sources = (Named("SEC", SourceRateLimitError("429")), Named("ESEF", "fundamentals"))
    with pytest.raises(SourceRateLimitError):
        FallbackFundamentalsSource(sources, "n").fetch_fundamentals("X.LSE")


class FakeHistory:
    """Eulerpool: the two filed years plus FY2022 and FY2021 before them (synthetic, in millions)."""

    def __init__(self, fail=None, profile=True):
        self.fail, self.profile = fail, profile

    def find_profile(self, symbol, name):
        if self.fail:
            raise self.fail
        return {"isin": "GB0003718474", "name": name, "currency": "GBP"} if self.profile else None

    def fetch_statements(self, isin):
        income, balance = [], []
        for year, ni in ((2024, 150.0), (2023, 130.0), (2022, 130.0), (2021, 110.0), (2020, 90.0)):
            end = f"{year + 1}-05-31"
            income.append({"period": end, "revenue": 500.0, "netIncome": ni})
            balance.append({"period": end, "totalAssets": 380.0, "totalEquity": 280.0, "sharesOutstanding": 33.0})
        return {"income": income, "balance_quarterly": balance, "cashflow": []}


def test_eulerpool_adds_the_years_before_the_first_report_when_they_agree():
    f = EuropeanFilingsSource(FakeClient(), FakeYahoo(), FakeLookup(), history=FakeHistory()).fetch_fundamentals("GAW.LSE")
    assert [r.period_end for r in f.annual_income_statements] == ["2025-05-31", "2024-05-31", "2023-05-31",
                                                                 "2022-05-31", "2021-05-31"]
    assert f.annual_income_statements[-1].eps is None and f.shares_by_year["2021"] == pytest.approx(33e6)
    assert any(n.startswith("History before FY2023: Eulerpool (vendor data, not filings) for FY2021-FY2022") for n in f.notes)
    assert any("History: 5 fiscal years (the ESEF reports cover 3, from FY2023; ESEF tagging began with FY2020; "
               "2 earlier from Eulerpool)" in n for n in f.notes)


@pytest.mark.parametrize("history, note", [
    (FakeHistory(fail=SourceRateLimitError("Eulerpool request limit reached (HTTP 429)")), "Eulerpool unavailable"),
    (FakeHistory(profile=False), "Eulerpool has no listing GAW.L"),
])
def test_without_eulerpool_the_dossier_keeps_the_esef_years(history, note):
    f = EuropeanFilingsSource(FakeClient(), FakeYahoo(), FakeLookup(), history=history).fetch_fundamentals("GAW.LSE")
    assert len(f.annual_income_statements) == 3 and any(note in n for n in f.notes)
