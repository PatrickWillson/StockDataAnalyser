"""Companies with no SEC or ESEF filings: UnfiledCompanySource (Yahoo statements + Eulerpool). Synthetic data."""

import pytest

from clients.unfiled_company_source import VENDOR_ONLY_SOURCE_NAME as SOURCE_NAME, UnfiledCompanySource
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
                                       "sharesOutstanding": self.shares, "longTermDebt": 900.0,
                                       "currentAssets": 1500.0, "currentLiabilities": 1000.0} for e, _ in rows],
                "cashflow": []}


class FakeYahoo:
    def __init__(self, data=YAHOO, net_income=None):
        self.data, self.net_income = data, NET_INCOME if net_income is None else net_income

    def fetch_company_data(self, ticker):
        return self.data

    def fetch_annual_net_income(self, ticker):
        return self.net_income

    def fetch_annual_statements(self, ticker):
        return None                 # vendor-only path: no Yahoo statements


def source(eulerpool=None, yahoo=None):
    return UnfiledCompanySource(yahoo or FakeYahoo(), eulerpool or FakeEulerpool())


def test_a_company_with_no_filings_gets_eulerpools_figures_labelled_unverified():
    f = source().fetch_fundamentals("HBH.XETRA")
    assert_fundamentals_contract(f)
    assert f.source == SOURCE_NAME and f.statement_currency == "EUR"
    assert [r.period_end for r in f.annual_income_statements][:2] == ["2025-02-28", "2024-02-29"]
    assert all(r.eps is None for r in f.annual_income_statements)
    # Eulerpool's long-term debt (900M) is not used: non-current liabilities, an upper bound (2,500M - 0 current)
    assert f.annual_balance_sheets[0].long_term_debt is None and f.annual_balance_sheets[0].long_term_debt_unknown
    assert any("all non-current liabilities" in n for n in f.notes)
    assert f.shares_by_year["2022"] == 0.0   # no per-share figures (§8.12); the count was only checked
    assert "UNVERIFIED against the company's reports" in f.notes[0] and "net income within 2% (or 1.1M for whole millions, at most 25% of the figure) in FY2023-FY2025" in f.notes[0]
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


# --- Yahoo statements path ---

from clients.unfiled_company_source import SOURCE_NAME as YAHOO_SOURCE  # noqa: E402
from clients.yfinance_client import YahooStatements  # noqa: E402

ENDS = ("2026-02-28", "2025-02-28", "2024-02-29")


def _statements(missing_net_income=()):
    income = {"Total Revenue": {e: 6000e6 for e in ENDS},
              "Net Income Common Stockholders": {e: v for e, v in zip(ENDS, (140e6, 100e6, 160e6)) if e not in missing_net_income},
              "Basic EPS": {e: v / 16e6 for e, v in zip(ENDS, (140e6, 100e6, 160e6)) if e not in missing_net_income}}
    balance = {"Total Assets": {e: 4500e6 for e in ENDS}, "Stockholders Equity": {e: 2000e6 for e in ENDS},
               "Ordinary Shares Number": {e: 16.0e6 for e in ENDS},
               "Long Term Debt And Capital Lease Obligation": {e: 900e6 for e in ENDS},
               "Long Term Capital Lease Obligation": {e: 600e6 for e in ENDS}}
    return YahooStatements("HBH.DE", income, balance, {})


class StatementsYahoo(FakeYahoo):
    def __init__(self, statements):
        super().__init__()
        self.statements = statements

    def fetch_annual_statements(self, ticker):
        return self.statements


def test_yahoo_statements_alone_give_the_recent_years():
    f = UnfiledCompanySource(StatementsYahoo(_statements())).fetch_fundamentals("HBH.XETRA")
    assert f.source == YAHOO_SOURCE
    assert [r.period_end for r in f.annual_income_statements] == list(ENDS)
    assert f.annual_income_statements[0].eps == pytest.approx(140e6 / 16e6)
    assert f.annual_balance_sheets[0].long_term_debt == 900e6            # debt incl. the reported lease line
    assert f.notes[0].startswith("Statements: Yahoo Finance annual statements for FY2024-FY2026")


def test_eulerpool_fills_a_yahoo_year_without_net_income_when_its_net_income_passed_the_gate():
    """Yahoo FY2025 and FY2023 agree with Eulerpool (140M, 160M); Yahoo's FY2024 has no net income: Eulerpool's 100M."""
    ends = ("2025-02-28", "2024-02-29", "2023-02-28")
    income = {"Total Revenue": {e: 6000e6 for e in ends},
              "Net Income Common Stockholders": {"2025-02-28": 140e6, "2023-02-28": 160e6},
              "Basic EPS": {"2025-02-28": 140e6 / 16e6, "2023-02-28": 160e6 / 16e6}}
    balance = {"Total Assets": {e: 4500e6 for e in ends}, "Stockholders Equity": {e: 2000e6 for e in ends},
               "Ordinary Shares Number": {e: 15.98e6 for e in ends}}
    f = UnfiledCompanySource(StatementsYahoo(YahooStatements("HBH.DE", income, balance, {})),
                             FakeEulerpool()).fetch_fundamentals("HBH.XETRA")
    by_end = {r.period_end: r for r in f.annual_income_statements}
    assert by_end["2024-02-29"].net_income == 100e6 and by_end["2024-02-29"].eps is None
    assert any("Eulerpool: net income for FY2024" in n for n in f.notes)
    assert "2022-02-28" in by_end                      # an older Eulerpool year, through the gate


def test_a_filled_year_keeps_yahoos_own_basic_eps():
    """James Halstead FY2025: Yahoo has basic EPS (9.7p) but no net income; the EPS is Yahoo's, never Eulerpool's."""
    ends = ("2025-02-28", "2023-02-28")
    income = {"Total Revenue": {e: 6000e6 for e in ends},
              "Net Income Common Stockholders": {"2025-02-28": 140e6, "2023-02-28": 160e6},
              "Basic EPS": {"2025-02-28": 140e6 / 16e6, "2024-02-29": 6.25, "2023-02-28": 160e6 / 16e6}}
    balance = {"Total Assets": {e: 4500e6 for e in ends}, "Stockholders Equity": {e: 2000e6 for e in ends},
               "Ordinary Shares Number": {e: 15.98e6 for e in ends}}
    f = UnfiledCompanySource(StatementsYahoo(YahooStatements("HBH.DE", income, balance, {})),
                             FakeEulerpool()).fetch_fundamentals("HBH.XETRA")
    by_end = {r.period_end: r for r in f.annual_income_statements}
    assert by_end["2024-02-29"].net_income == 100e6 and by_end["2024-02-29"].eps == 6.25
    assert f.shares_by_year["2024"] == 0.0                        # no Eulerpool share count
    assert any("EPS for FY2024 is Yahoo Finance's own basic EPS" in n for n in f.notes)


def test_without_yahoo_statements_or_eulerpool_there_is_no_dossier():
    with pytest.raises(TickerNotCoveredError, match="no Yahoo Finance statements"):
        UnfiledCompanySource(StatementsYahoo(None)).fetch_fundamentals("HBH.XETRA")


def test_a_filled_latest_year_gets_eulerpools_gated_balance_sheet_on_todays_shares():
    """Fevertree FY2025: Yahoo's column is empty but for EPS; Eulerpool's balance fields passed the gate."""
    ends = ("2024-02-29", "2023-02-28")
    income = {"Total Revenue": {e: 6000e6 for e in ends},
              "Net Income Common Stockholders": {"2024-02-29": 100e6, "2023-02-28": 160e6},
              "Basic EPS": {"2025-02-28": 8.75, "2024-02-29": 100e6 / 16e6, "2023-02-28": 160e6 / 16e6}}
    balance = {"Total Assets": {e: 4500e6 for e in ends}, "Stockholders Equity": {e: 2000e6 for e in ends},
               "Current Assets": {e: 1500e6 for e in ends}, "Current Liabilities": {e: 1000e6 for e in ends},
               "Ordinary Shares Number": {e: 15.98e6 for e in ends}}
    f = UnfiledCompanySource(StatementsYahoo(YahooStatements("HBH.DE", income, balance, {})),
                             FakeEulerpool()).fetch_fundamentals("HBH.XETRA")
    latest = f.annual_balance_sheets[0]
    assert latest.period_end == "2025-02-28" and latest.total_equity == 2000e6 and latest.current_assets == 1500e6
    assert latest.shares_outstanding == 16e6 and f.shares_by_year["2025"] == 16e6      # today's count, Yahoo
    assert f.annual_income_statements[0].eps == 8.75                                    # Yahoo's own EPS
    assert any("Eulerpool: balance sheet for FY2025" in n for n in f.notes)


# London listings: the company's RNS results announcements before Eulerpool (synthetic announcements)
from dataclasses import replace as _replace  # noqa: E402

from clients.rns_client import RnsAnnouncement  # noqa: E402
from core.fundamentals import IncomeStatementRow  # noqa: E402

LONDON = _replace(YAHOO, yahoo_symbol="HBH.L", info={**YAHOO.info, "currency": "GBp", "financialCurrency": "EUR"})


def _announcement(year_end, ni, prior):
    rows = [["", "€'000", "€'000"], ["Revenue", "6,000,000", "6,000,000"], ["Cost of sales", "(1)", "(1)"],
            ["Profit before tax", "1", "1"], ["Profit for the year attributable to owners of the parent",
                                              f"{ni:,.0f}", f"{prior:,.0f}"]]
    cells = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<p>Consolidated income statement for the year ended {year_end}</p><table>{cells}</table>"


class FakeRns:
    def __init__(self, fy2024=160_000):
        self.pages = {3: _announcement("28 February 2026", 140_000, 100_000),
                      2: _announcement("28 February 2025", 100_000, fy2024),
                      1: _announcement("29 February 2024", 160_000, 90_000)}
        self.asked = []

    def results_announcements(self, tidm):
        self.asked.append(tidm)
        return [RnsAnnouncement(i, f"https://example.invalid/{i}") for i in sorted(self.pages, reverse=True)]

    def fetch_announcement(self, announcement):
        return self.pages[announcement.announcement_id]


def _london_statements():
    statements = _statements()
    return YahooStatements("HBH.L", statements.income, statements.balance, {})


class LondonYahoo(StatementsYahoo):
    def __init__(self):
        super().__init__(_london_statements())
        self.data = LONDON


def test_a_london_listing_takes_the_announced_years_before_eulerpool():
    """The announced FY2026-FY2024 agree with Yahoo (140M, 100M, 160M): FY2023 (90M) is added; Eulerpool is only the
    second source (its own FY2022 is not added)."""
    rns, eulerpool = FakeRns(), FakeEulerpool()
    f = UnfiledCompanySource(LondonYahoo(), eulerpool, rns).fetch_fundamentals("HBH.LSE")
    assert rns.asked == ["HBH"]
    by_end = {r.period_end: r for r in f.annual_income_statements}
    assert "2022-02-28" not in by_end
    assert by_end["2023-02-28"].net_income == 90e6 and by_end["2023-02-28"].eps is None
    assert any(n.startswith("History before FY2024: RNS results announcements") for n in f.notes)


def test_announcements_that_disagree_with_yahoo_leave_eulerpool_to_try():
    rns = FakeRns(fy2024=150_000)        # FY2024 announced 150M against Yahoo's 160M (as first reported 160M agrees)
    rns.pages[1] = _announcement("29 February 2024", 150_000, 90_000)
    f = UnfiledCompanySource(LondonYahoo(), None, rns).fetch_fundamentals("HBH.LSE")
    assert "2023-02-28" not in {r.period_end for r in f.annual_income_statements}
    assert any("did not agree" in n for n in f.notes)


def test_other_exchanges_never_ask_for_announcements():
    rns = FakeRns()
    UnfiledCompanySource(StatementsYahoo(_statements()), None, rns).fetch_fundamentals("HBH.XETRA")
    assert rns.asked == []


class FakeCompaniesHouse:
    """CompaniesHouseHistorySource stand-in: FY2022 and FY2021 before the held years, and what it was asked."""
    def __init__(self, rows=None):
        from clients.companies_house_history import CompaniesHouseHistory
        self.rows = rows if rows is not None else (IncomeStatementRow("2022-02-28", None, 80e6, None),
                                                   IncomeStatementRow("2021-02-28", None, 70e6, None))
        self.asked, self._history = [], CompaniesHouseHistory

    def history(self, name, known, currency, wanted_years, held_source=""):
        self.asked.append((name, sorted(known), currency, wanted_years, held_source))
        notes = ("History before FY2023: Companies House filed accounts ... for FY2021-FY2022 (2 years)",) if self.rows \
            else ("History before the held years: Companies House filed accounts not used: no single active plc",)
        return self._history(tuple(self.rows), {r.period_end[:4]: 0.0 for r in self.rows}, notes)


def test_a_london_listing_takes_the_filed_accounts_after_the_announcements():
    rns, ch, eulerpool = FakeRns(), FakeCompaniesHouse(), FakeEulerpool()
    f = UnfiledCompanySource(LondonYahoo(), eulerpool, rns, ch).fetch_fundamentals("HBH.LSE")
    name, known, currency, wanted, held = ch.asked[0]
    assert "2023-02-28" in known and currency == "EUR" and wanted == 10 - len(known)
    assert held == "Yahoo Finance's statements and the RNS results announcements"
    by_end = {r.period_end: r for r in f.annual_income_statements}
    assert by_end["2022-02-28"].net_income == 80e6 and by_end["2021-02-28"].net_income == 70e6
    assert f.shares_by_year["2021"] == 0.0
    assert any("from RNS results announcements; 2 from Companies House filed accounts" in n for n in f.notes)


def test_without_filed_accounts_eulerpool_is_still_tried_and_other_exchanges_never_ask():
    ch = FakeCompaniesHouse(rows=())
    f = UnfiledCompanySource(LondonYahoo(), FakeEulerpool(), None, ch).fetch_fundamentals("HBH.LSE")
    assert ch.asked and any("Companies House filed accounts not used" in n for n in f.notes)
    assert any("Eulerpool" in n for n in f.notes)
    other = FakeCompaniesHouse()
    UnfiledCompanySource(StatementsYahoo(_statements()), None, None, other).fetch_fundamentals("HBH.XETRA")
    assert other.asked == []
