"""
End-to-end snapshots of the European route (FUNDAMENTALS_PROVIDER=free, European home listings, no SEC filer).

Runs the real stock_data_analyser.main() offline:
  - GAW.LSE: ESEF annual reports from tests/fixtures_esef/GAW.json.gz (public filings from filings.xbrl.org,
    trimmed to company-wide ifrs-full figures; net-assets layout, EPS tagged in pence as pounds), with Eulerpool
    history before them: SYNTHETIC Eulerpool figures (vendor data is never committed), equal to the filed figures
    in the overlapping years so the gate passes, invented for the older years
  - EXH.XETRA: a company with no SEC or ESEF filings, from SYNTHETIC Eulerpool figures alone
  - yfinance is served by FakeYFinanceModule with SYNTHETIC values; no US listing, so the SEC route finds no filer
  - the date is pinned to 2026-11-01
Snapshots live in tests/__snapshots__/test_european_path_snapshots/; refresh intended changes with --snapshot-update.
"""

import gzip
import json
import logging
import pathlib
import sys
from datetime import datetime, timezone

import pytest

import stock_data_analyser
from clients.esef_client import EsefClient, EsefFiling
from clients.eulerpool_client import EulerpoolClient
from snapshot_fakes import FakeYFinanceModule, closes_around
from test_dossier_snapshots import MarkdownSnapshotExtension

PINNED_NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
ESEF = json.loads(gzip.open(pathlib.Path(__file__).parent / "fixtures_esef" / "GAW.json.gz").read())

# Synthetic Eulerpool years (millions): the overlap equals the filed figures; FY2015-FY2021 are invented
GAW_YEAR_ENDS = {2025: "2025-06-01", 2024: "2024-06-02", 2023: "2023-05-28", 2022: "2022-05-29", 2021: "2021-05-30",
                 2020: "2020-05-31", 2019: "2019-06-02", 2018: "2018-06-03", 2017: "2017-05-28", 2016: "2016-05-29",
                 2015: "2015-05-31"}
GAW_FILED = {2025: (617.5, 196.1, 383.0, 280.8), 2024: (525.7, 151.1, 351.3, 251.4), 2023: (470.8, 134.7, 326.8, 235.1),
             2022: (414.8, 128.4, 321.1, 234.7)}
GAW_SHARES = {2025: 33.06, 2024: 32.93, 2023: 32.88, 2022: 32.81}


def _gaw_eulerpool():
    income, balance = [], []
    for year, end in GAW_YEAR_ENDS.items():
        if year in GAW_FILED:
            revenue, ni, assets, equity = GAW_FILED[year]
            shares = GAW_SHARES[year]
        else:
            step = 2022 - year
            revenue, ni, assets, equity, shares = 380 - 30 * step, 110 - 12 * step, 300 - 15 * step, 210 - 12 * step, 32.7
        income.append({"period": end, "revenue": revenue, "netIncome": ni})
        balance.append({"period": end, "totalAssets": assets, "totalEquity": equity, "sharesOutstanding": shares})
    return {"profile": {"isin": "GB0003718474", "name": "Games Workshop Group PLC", "currency": "GBP"},
            "income": income, "balance_quarterly": balance, "cashflow": []}


def _exh_eulerpool():
    income, balance, cash = [], [], []
    for year in range(2014, 2026):
        end, step = f"{year}-12-31", 2025 - year
        income.append({"period": end, "revenue": 900.0 - 20 * step, "netIncome": 60.0 - 2 * step})
        balance.append({"period": end, "totalAssets": 1000.0 - 25 * step, "totalEquity": 520.0 - 15 * step,
                        "currentAssets": 600.0, "currentLiabilities": 210.0, "totalLiabilities": 480.0 - 10 * step,
                        "longTermDebt": 120.0, "inventory": 250.0, "sharesOutstanding": 20.0})
        cash.append({"period": end, "netOperatingCashFlow": 80.0, "cashDividendsPaid": -18.0})
    return {"profile": {"isin": "DE0000000001", "name": "Example Holding AG", "currency": "EUR"},
            "income": income, "balance_quarterly": balance, "cashflow": cash}


COMPANIES = {
    "GAW.LSE": {"yahoo": "GAW.L", "eulerpool": _gaw_eulerpool(), "currency": "GBp", "last": 16000.0, "base": 1500.0,
                "dividend": 160.0, "net_income": {"2025-06-01": 196.1e6},
                "info": {"longName": "Games Workshop Group PLC", "sector": "Consumer Cyclical", "industry": "Leisure",
                         "fullTimeEmployees": 3000, "financialCurrency": "GBP", "sharesOutstanding": 33_000_000,
                         "companyOfficers": [{"name": "Test CEO Eight", "title": "CEO & Director"}]}},
    "EXH.XETRA": {"yahoo": "EXH.DE", "eulerpool": _exh_eulerpool(), "currency": "EUR", "last": 45.0, "base": 20.0,
                  "dividend": 0.9, "net_income": {"2025-12-31": 60.0e6, "2024-12-31": 58.0e6, "2023-12-31": 56.0e6},
                  "info": {"longName": "Example Holding AG", "sector": "Industrials", "industry": "Machinery",
                           "fullTimeEmployees": 4000, "financialCurrency": "EUR", "sharesOutstanding": 20_000_000,
                           "companyOfficers": [{"name": "Test CEO Nine", "title": "CEO"}]}},
}


def yahoo(home: str):
    spec = COMPANIES[home]
    ends = sorted(r["period"] for r in spec["eulerpool"]["income"])
    closes = closes_around(ends, lambda d: spec["base"] + (spec["last"] - spec["base"]) * ends.index(d) / len(ends))
    dividends = {f"{year}-01-15": round(spec["dividend"] * 1.05 ** (year - 2026), 4) for year in range(2008, 2027)}
    return FakeYFinanceModule({spec["yahoo"]: {"last": spec["last"], "currency": spec["currency"], "closes": closes,
                                               "info": {"currency": spec["currency"], **spec["info"]},
                                               "dividends": dividends, "net_income": spec["net_income"]}})


@pytest.fixture
def run_european_cli(monkeypatch, tmp_path):
    root = logging.getLogger()
    saved_filters = {handler: list(handler.filters) for handler in root.handlers}

    def run(home: str):
        spec = COMPANIES[home]
        monkeypatch.setitem(sys.modules, "yfinance", yahoo(home))
        esef = ESEF if home == "GAW.LSE" else {"entities": [], "filings": [], "reports": {}}
        monkeypatch.setattr(EsefClient, "search_entities", lambda self, pattern: [tuple(e) for e in esef["entities"]])
        monkeypatch.setattr(EsefClient, "fetch_filings", lambda self, lei: [EsefFiling(**f) for f in esef["filings"]])
        monkeypatch.setattr(EsefClient, "fetch_report", lambda self, filing: esef["reports"][filing.json_url])
        vendor = spec["eulerpool"]
        monkeypatch.setattr(EulerpoolClient, "find_profile", lambda self, symbol, name: vendor["profile"])
        monkeypatch.setattr(EulerpoolClient, "fetch_statements",
                            lambda self, isin: {k: vendor[k] for k in ("income", "balance_quarterly", "cashflow")})
        monkeypatch.setenv("FUNDAMENTALS_PROVIDER", "free")
        monkeypatch.setenv("SEC_USER_AGENT", "StockDataAnalyser tests no-reply@example.invalid")
        monkeypatch.setenv("EULERPOOL_API_KEY", "test-key-not-real")
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
def test_european_path_snapshot(home, run_european_cli, snapshot):
    dossier = run_european_cli(home)
    if home == "GAW.LSE":
        assert "ESEF annual reports (filings.xbrl.org) + Yahoo Finance" in dossier
        assert "History before FY2022: Eulerpool (vendor data, not filings) for FY2015-FY2021" in dossier
        assert "implies 1/100 of the listing's current share count" in dossier
    else:
        assert "Eulerpool (vendor data, unverified) + Yahoo Finance" in dossier and "UNVERIFIED" in dossier
    assert "test-key-not-real" not in dossier
    assert dossier == snapshot(extension_class=MarkdownSnapshotExtension)
