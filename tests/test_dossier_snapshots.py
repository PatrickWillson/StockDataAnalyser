"""
End-to-end snapshot (characterisation) tests.

Each scenario runs the real CLI entry point, stock_data_analyser.main(), offline:
  - EODHD HTTP is served by FakeEODHDSession (swapped into the real EODHDClient)
  - yfinance (prices and FX) is served by FakeYFinanceModule
  - the date is pinned with time-machine
Two snapshots are stored per scenario in tests/__snapshots__/test_dossier_snapshots/:
  - <test>.md    the dossier exactly as written to disk
  - <test>[data].json   financial_data, metrics, ttm_metrics and anomalies as passed
                 to DossierGenerator, so number changes hidden by formatting are caught

Snapshots record CURRENT behaviour, including known bugs. When a change is meant to alter
output, review the diff and refresh with:  pytest tests/test_dossier_snapshots.py --snapshot-update
"""

import copy
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

import pytest
from syrupy.extensions.json import JSONSnapshotExtension
from syrupy.extensions.single_file import SingleFileSnapshotExtension, WriteMode

import stock_data_analyser
from clients.factory import ClientFactory
from output.dossier_generator import DossierGenerator
from snapshot_fakes import FakeEODHDSession, FakeYFinanceModule
from snapshot_scenarios import ALL_SCENARIOS, Scenario

PINNED_NOW = datetime(2024, 3, 1, 12, 0, tzinfo=timezone.utc)


class MarkdownSnapshotExtension(SingleFileSnapshotExtension):
    file_extension = "md"
    _write_mode = WriteMode.TEXT


@dataclass
class CliRun:
    dossier: str
    data: Dict[str, Any]


@pytest.fixture
def run_cli(monkeypatch, tmp_path):
    """Run stock_data_analyser.main() for a scenario with fake external services."""
    root = logging.getLogger()
    saved_filters = {handler: list(handler.filters) for handler in root.handlers}

    def run(scenario: Scenario) -> CliRun:
        monkeypatch.setitem(sys.modules, "yfinance", FakeYFinanceModule(scenario.yahoo))

        dividends = {scenario.ticker: scenario.dividends} if scenario.dividends is not None else None
        session = FakeEODHDSession({scenario.ticker: scenario.fundamentals}, dividends)
        real_create_eodhd_client = ClientFactory.create_eodhd_client

        def create_eodhd_client(api_key, debug=False):
            client = real_create_eodhd_client(api_key, debug=debug)
            client.session = session
            return client

        monkeypatch.setattr(ClientFactory, "create_eodhd_client", staticmethod(create_eodhd_client))

        captured: Dict[str, Any] = {}

        class RecordingDossierGenerator(DossierGenerator):
            def __init__(self, ticker, financial_data, metrics, anomalies, ttm_metrics=None):
                captured.update(copy.deepcopy({
                    "financial_data": financial_data,
                    "metrics": metrics,
                    "ttm_metrics": ttm_metrics,
                    "anomalies": anomalies,
                }))
                super().__init__(ticker, financial_data, metrics, anomalies, ttm_metrics=ttm_metrics)

        monkeypatch.setattr(stock_data_analyser, "DossierGenerator", RecordingDossierGenerator)
        monkeypatch.setattr(stock_data_analyser, "API_KEY", "fake-api-key")
        monkeypatch.setattr(sys, "argv", ["stock_data_analyser.py", scenario.ticker])
        monkeypatch.chdir(tmp_path)

        try:
            stock_data_analyser.main()
        except SystemExit as exc:
            pytest.fail(f"main() exited with code {exc.code} for scenario {scenario.name}")

        dossier_path = tmp_path / "data" / f"{scenario.ticker.replace('.', '_')}_DOSSIER.md"
        return CliRun(dossier=dossier_path.read_text(encoding="utf-8"), data=captured)

    yield run

    for handler, filters in saved_filters.items():
        handler.filters[:] = filters


@pytest.mark.time_machine(PINNED_NOW, tick=False)
@pytest.mark.parametrize("build_scenario", ALL_SCENARIOS, ids=lambda f: f.__name__)
def test_dossier_snapshot(build_scenario, run_cli, snapshot):
    result = run_cli(build_scenario())

    assert result.dossier == snapshot(extension_class=MarkdownSnapshotExtension)
    assert result.data == snapshot(extension_class=JSONSnapshotExtension, name="data")
