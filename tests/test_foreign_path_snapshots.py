"""
End-to-end snapshots of the SEC route for non-US companies (FUNDAMENTALS_PROVIDER=free, home listings).

Runs the real stock_data_analyser.main() offline for SAP.XETRA (IFRS 20-F, EUR) and RY.TO (40-F, CAD, a
bank):
  - SEC EDGAR is served by FakeSecSession from real, trimmed companyfacts / submissions in
    tests/fixtures_sec/ (US-government public data)
  - yfinance is served by FakeYFinanceModule with SYNTHETIC values (Yahoo data cannot be
    redistributed): prices, closes, dividends, profile, the US-listing search, and an annual net
    income equal to the filing's latest (so the same-company check passes, as it does live)
  - the date is pinned to 2026-11-01
Snapshots live in tests/__snapshots__/test_foreign_path_snapshots/; refresh intended changes with
--snapshot-update.
"""

import logging
import sys
from datetime import datetime, timezone

import pytest

import stock_data_analyser
from clients.edgar_client import EdgarClient
from clients.edgar_mapper import annual_data
from snapshot_fakes import FakeSecSession, FakeYFinanceModule, closes_around
from test_dossier_snapshots import MarkdownSnapshotExtension
from test_edgar_mapper import fixture

PINNED_NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)

# home ticker -> (US symbol, CIK, Yahoo home symbol, synthetic Yahoo values)
COMPANIES = {
    "SAP.XETRA": ("SAP", "0001000184", "SAP.DE",
                  {"last": 210.0, "base": 60.0, "dividend": 2.0, "currency": "EUR", "exchange": "NYQ",
                   "info": {"longName": "SAP SE", "sector": "Technology", "industry": "Software - Application",
                            "fullTimeEmployees": 110000, "financialCurrency": "EUR", "dividendRate": 2.5,
                            "companyOfficers": [{"name": "Test CEO Four", "title": "CEO & Member of Executive Board"}]}}),
    "RY.TO": ("RY", "0001000275", "RY.TO",
              {"last": 190.0, "base": 70.0, "dividend": 4.5, "currency": "CAD", "exchange": "NYQ",
               "info": {"longName": "Royal Bank of Canada", "sector": "Financial Services", "industry": "Banks - Diversified",
                        "fullTimeEmployees": 95000, "financialCurrency": "CAD", "dividendRate": 6.2,
                        "companyOfficers": [{"name": "Test CEO Five", "title": "President, CEO & Director"}]}}),
}


def yahoo(home: str):
    us_symbol, _, yahoo_symbol, spec = COMPANIES[home]
    annual = annual_data(fixture(us_symbol)["companyfacts"])
    ordered = sorted(r.period_end for r in annual.income_statements)
    closes = closes_around(ordered, lambda d: spec["base"] + (spec["last"] - spec["base"]) * ordered.index(d) / len(ordered))
    dividends = {f"{year}-05-15": round(spec["dividend"] * 1.04 ** (year - 2026), 4) for year in range(2008, 2027)}
    latest = annual.income_statements[0]
    symbols = {yahoo_symbol: {"last": spec["last"], "currency": spec["currency"], "closes": closes,
                              "info": {"currency": spec["currency"], **spec["info"]}, "dividends": dividends,
                              "net_income": {latest.period_end: latest.net_income}}}
    search = {spec["info"]["longName"]: [{"symbol": us_symbol, "exchange": spec["exchange"],
                                          "longname": spec["info"]["longName"]}]}
    return FakeYFinanceModule(symbols, search=search)


@pytest.fixture
def run_foreign_cli(monkeypatch, tmp_path):
    root = logging.getLogger()
    saved_filters = {handler: list(handler.filters) for handler in root.handlers}

    def run(home: str):
        us_symbol, cik, _, _ = COMPANIES[home]
        monkeypatch.setitem(sys.modules, "yfinance", yahoo(home))
        data = fixture(us_symbol)
        session = FakeSecSession({us_symbol: (cik, data["companyfacts"], data["submissions"])})
        real_init = EdgarClient.__init__

        def init(self, *args, **kwargs):
            real_init(self, *args, **kwargs)
            self.session = session

        monkeypatch.setattr(EdgarClient, "__init__", init)
        monkeypatch.setenv("FUNDAMENTALS_PROVIDER", "free")
        monkeypatch.setenv("SEC_USER_AGENT", "StockDataAnalyser tests no-reply@example.invalid")
        monkeypatch.setattr(sys, "argv", ["stock_data_analyser.py", home])
        monkeypatch.chdir(tmp_path)
        try:
            stock_data_analyser.main()
        except SystemExit as exc:
            pytest.fail(f"main() exited with code {exc.code} for {home}")
        return (tmp_path / "data" / f"{home.replace('.', '_')}_DOSSIER.md").read_text(encoding="utf-8")

    yield run
    for handler, filters in saved_filters.items():
        handler.filters[:] = filters


@pytest.mark.time_machine(PINNED_NOW, tick=False)
@pytest.mark.parametrize("home", sorted(COMPANIES))
def test_foreign_path_snapshot(home, run_foreign_cli, snapshot):
    dossier = run_foreign_cli(home)
    assert "SEC EDGAR (20-F/40-F) + Yahoo Finance" in dossier
    assert "per-share figures are per ordinary share" in dossier
    assert dossier == snapshot(extension_class=MarkdownSnapshotExtension)


def test_us_listing_of_a_foreign_filer_is_refused(monkeypatch, tmp_path, caplog):
    data = fixture("SAP")
    session = FakeSecSession({"SAP": ("0001000184", data["companyfacts"], data["submissions"])})
    real_init = EdgarClient.__init__

    def init(self, *args, **kwargs):
        real_init(self, *args, **kwargs)
        self.session = session

    monkeypatch.setattr(EdgarClient, "__init__", init)
    monkeypatch.setitem(sys.modules, "yfinance", FakeYFinanceModule({}))
    monkeypatch.setenv("FUNDAMENTALS_PROVIDER", "free")
    monkeypatch.setenv("SEC_USER_AGENT", "StockDataAnalyser tests no-reply@example.invalid")
    monkeypatch.setattr(sys, "argv", ["stock_data_analyser.py", "SAP.US"])
    monkeypatch.chdir(tmp_path)
    with caplog.at_level(logging.ERROR), pytest.raises(SystemExit) as exc:
        stock_data_analyser.main()
    assert exc.value.code == 1
    assert "files 20-F as a foreign company; use its home-exchange listing" in caplog.text
