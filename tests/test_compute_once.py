"""
M4.3: GrahamCalculator.compute_all computes TBVPS, the normalized Graham Number and EPV once and
passes them on, so each warning appears once (it appeared 4 times for negative tangible equity).
"""

from collections import Counter
from unittest.mock import patch

from core.graham_math import GrahamCalculator


def _history(goodwill):
    rows = {}
    for i, year in enumerate(range(2014, 2024)):
        rows[f"{year}-12-31"] = {
            'revenue': 1000.0 + i, 'net_income': 100.0 + i, 'eps': 1.0 + i / 100,
            'dividend': 0.5, 'total_equity': 500.0, 'intangible_assets': 0.0, 'goodwill': goodwill,
            'current_assets': 400.0, 'current_liabilities': 100.0, 'total_liabilities': 300.0,
            'long_term_debt': 50.0, 'total_assets': 800.0, 'shares_outstanding': 100.0,
        }
    return rows


def _calculator(goodwill=0.0):
    return GrahamCalculator({'history': _history(goodwill), 'price': 10.0, 'sector': 'Industrials'})


def test_each_shared_input_is_computed_once():
    calc = _calculator()
    with patch.object(calc, 'compute_tbvps', wraps=calc.compute_tbvps) as tbvps, \
         patch.object(calc, 'compute_epv', wraps=calc.compute_epv) as epv, \
         patch.object(calc, 'compute_normalized_graham_number',
                      wraps=calc.compute_normalized_graham_number) as ngn:
        calc.compute_all()
    assert tbvps.call_count == 1
    assert epv.call_count == 1
    assert ngn.call_count == 1


def test_negative_tangible_equity_warning_appears_once():
    warnings = _calculator(goodwill=900.0).compute_all()['warnings']
    assert Counter(warnings)["Negative Tangible Book Value - Company has negative equity"] == 1


def test_compute_all_matches_individual_methods():
    calc = _calculator()
    metrics = calc.compute_all()
    fresh = _calculator()
    assert metrics['graham_number'] == fresh.compute_graham_number()
    assert metrics['normalized_graham_number'] == fresh.compute_normalized_graham_number()
    assert metrics['margin_of_safety_details'] == fresh.compute_margin_of_safety(10.0)
    assert metrics['enterprising_tests'] == fresh.run_investor_tests("enterprising")
