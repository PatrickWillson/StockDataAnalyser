"""
End-to-end snapshots of the free resolution path (FUNDAMENTALS_PROVIDER=free).

Runs the real stock_data_analyser.main() offline:
  - SEC EDGAR is served by FakeSecSession from the real, trimmed companyfacts / submissions in
    tests/fixtures_sec/ (US-government public data)
  - yfinance (price, closes, profile, dividends, splits) is served by FakeYFinanceModule; these Yahoo
    values are SYNTHETIC (Yahoo data cannot be redistributed), except the splits, which are the
    companies' published stock splits
  - the date is pinned to 2026-11-01, after the fixtures' latest filings
Snapshots (dossier .md and the [data].json passed to DossierGenerator) live in
tests/__snapshots__/test_free_path_snapshots/; refresh intended changes with --snapshot-update.
"""

import copy
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict

import pytest
from syrupy.extensions.json import JSONSnapshotExtension

import stock_data_analyser
from clients.edgar_client import EdgarClient
from clients.edgar_mapper import annual_data
from output.dossier_generator import DossierGenerator
from snapshot_fakes import FakeSecSession, FakeYFinanceModule, closes_around
from test_dossier_snapshots import MarkdownSnapshotExtension
from test_edgar_mapper import fixture

PINNED_NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
CIKS = {"SO": "0000092122", "AAPL": "0000320193", "JPM": "0000019617"}

# Synthetic Yahoo data (see module docstring)
YAHOO = {
    "SO": {"last": 88.0, "base": 40.0, "dividend": 0.35,
           "info": {"longName": "Southern Company (The)", "sector": "Utilities",
                    "industry": "Utilities - Regulated Electric", "fullTimeEmployees": 28000,
                    "companyOfficers": [{"name": "Test CEO One", "title": "Chairman, President & CEO"}],
                    "beta": 0.45, "heldPercentInstitutions": 0.68, "dividendRate": 2.96}},
    "AAPL": {"last": 230.0, "base": 20.0, "dividend": 0.05, "splits": {"2014-06-09": 7.0, "2020-08-31": 4.0},
             "info": {"longName": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics",
                      "fullTimeEmployees": 150000,
                      "companyOfficers": [{"name": "Test CEO Two", "title": "CEO & Director"}],
                      "beta": 1.2, "heldPercentInsiders": 0.017, "dividendRate": 1.04}},
    "JPM": {"last": 300.0, "base": 40.0, "dividend": 0.40,
            "info": {"longName": "JPMorgan Chase & Co.", "sector": "Financial Services",
                     "industry": "Banks - Diversified", "fullTimeEmployees": 317000,
                     "companyOfficers": [{"name": "Test CEO Three", "title": "Chairman & CEO"}],
                     "beta": 1.1, "dividendRate": 6.0}},
}


def yahoo_symbols(ticker: str) -> Dict[str, Any]:
    spec = YAHOO[ticker]
    data = fixture(ticker)
    year_ends = [r.period_end for r in annual_data(data["companyfacts"]).income_statements]
    # Closes rise steadily to the current price; quarterly dividends since 2003, growing 3% a year
    ordered = sorted(year_ends)
    closes = closes_around(ordered, lambda d: spec["base"] + (spec["last"] - spec["base"]) * ordered.index(d) / len(ordered))
    dividends = {f"{year}-{month:02d}-15": round(spec["dividend"] * 1.03 ** (year - 2003), 4)
                 for year in range(2003, 2027) for month in (2, 5, 8, 11) if f"{year}-{month:02d}-15" <= "2026-10-31"}
    return {ticker: {"last": spec["last"], "currency": "USD", "closes": closes,
                     "info": {"currency": "USD", "financialCurrency": "USD", **spec["info"]},
                     "dividends": dividends, "splits": spec.get("splits", {})}}


@pytest.fixture
def run_free_cli(monkeypatch, tmp_path):
    root = logging.getLogger()
    saved_filters = {handler: list(handler.filters) for handler in root.handlers}

    def run(ticker: str):
        monkeypatch.setitem(sys.modules, "yfinance", FakeYFinanceModule(yahoo_symbols(ticker)))
        data = fixture(ticker)
        session = FakeSecSession({ticker: (CIKS[ticker], data["companyfacts"], data["submissions"])})
        real_init = EdgarClient.__init__

        def init(self, *args, **kwargs):
            real_init(self, *args, **kwargs)
            self.session = session

        monkeypatch.setattr(EdgarClient, "__init__", init)
        captured: Dict[str, Any] = {}

        class RecordingDossierGenerator(DossierGenerator):
            def __init__(self, ticker, financial_data, metrics, anomalies, ttm_metrics=None):
                def plain(value):
                    return value.to_dict() if hasattr(value, "to_dict") else value
                captured.update(copy.deepcopy({"financial_data": plain(financial_data), "metrics": plain(metrics),
                                               "ttm_metrics": plain(ttm_metrics), "anomalies": anomalies}))
                super().__init__(ticker, financial_data, metrics, anomalies, ttm_metrics=ttm_metrics)

        monkeypatch.setattr(stock_data_analyser, "DossierGenerator", RecordingDossierGenerator)
        monkeypatch.setenv("FUNDAMENTALS_PROVIDER", "free")
        monkeypatch.setenv("SEC_USER_AGENT", "StockDataAnalyser tests no-reply@example.invalid")
        monkeypatch.setattr(sys, "argv", ["stock_data_analyser.py", f"{ticker}.US"])
        monkeypatch.chdir(tmp_path)
        try:
            stock_data_analyser.main()
        except SystemExit as exc:
            pytest.fail(f"main() exited with code {exc.code} for {ticker}")
        dossier = (tmp_path / "data" / f"{ticker}_US_DOSSIER.md").read_text(encoding="utf-8")
        return dossier, captured, session

    yield run
    for handler, filters in saved_filters.items():
        handler.filters[:] = filters


@pytest.mark.time_machine(PINNED_NOW, tick=False)
@pytest.mark.parametrize("ticker", sorted(CIKS))
def test_free_path_snapshot(ticker, run_free_cli, snapshot):
    dossier, data, session = run_free_cli(ticker)

    assert "# SOURCE: SEC EDGAR + Yahoo Finance (Tier 1 Data)" in dossier
    assert all(agent == "StockDataAnalyser tests no-reply@example.invalid" for _, agent in session.requests)
    assert dossier == snapshot(extension_class=MarkdownSnapshotExtension)
    assert data == snapshot(extension_class=JSONSnapshotExtension, name="data")
