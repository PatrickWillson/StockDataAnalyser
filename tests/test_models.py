"""
core.models (M7, decision D2): typed models whose to_dict() is exactly today's dict shape.
Round-trips every snapshot scenario's financial_data, metrics and ttm_metrics.
"""

import glob
import json
import os

import pytest

from core.models import MISSING, FinancialData, GrahamResult, HistoryRow, TTMResult, or_default

SNAPSHOTS = sorted(glob.glob(os.path.join(os.path.dirname(__file__), "__snapshots__", "test_dossier_snapshots",
                                          "*[[]data[]].json")))


@pytest.mark.parametrize("path", SNAPSHOTS, ids=lambda p: os.path.basename(p).split('[')[1].split(']')[0])
def test_snapshot_data_round_trips_exactly(path):
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    assert FinancialData.from_dict(data['financial_data']).to_dict() == data['financial_data']
    assert GrahamResult.from_dict(data['metrics']).to_dict() == data['metrics']
    if data.get('ttm_metrics'):
        assert TTMResult.from_dict(data['ttm_metrics']).to_dict() == data['ttm_metrics']


def test_models_are_typed_and_nested():
    with open(SNAPSHOTS[0], encoding="utf-8") as handle:
        data = json.load(handle)
    result = GrahamResult.from_dict(data['metrics'])
    assert result.epv_details.cost_of_capital == 0.10
    assert isinstance(result.warnings, tuple)
    fd = FinancialData.from_dict(data['financial_data'])
    assert all(isinstance(row, HistoryRow) for row in fd.history.values())


def test_absent_keys_stay_absent_and_unknown_keys_are_kept():
    row = HistoryRow.from_dict({'dividend': 0.5, 'operating_cash_flow': 9.0})
    assert row.revenue is MISSING
    assert row.to_dict() == {'dividend': 0.5, 'operating_cash_flow': 9.0}
    assert row.get('revenue', 0.0) == 0.0 and row.get('operating_cash_flow') == 9.0


def test_or_default_replaces_only_missing():
    assert or_default(MISSING, 'N/A') == 'N/A'
    assert or_default(0.0, 'N/A') == 0.0
    assert or_default(None, 'N/A') is None
    assert or_default('', 'N/A') == ''


def test_from_dict_passes_models_and_none_through():
    result = GrahamResult.from_dict({'verdict': 'OVERVALUED'})
    assert GrahamResult.from_dict(result) is result
    assert GrahamResult.from_dict(None) is None
