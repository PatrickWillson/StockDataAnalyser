"""
F13: the TTM section compares TBVPS, P/E and P/B with the latest annual figures, and states the
basis of the TTM margin of safety instead of diffing it against a differently-defined annual one.
"""

from output.sections.ttm_analysis import TTMAnalysisSection

TTM = {'ttm_graham_number': 30.0, 'ttm_tbvps': 11.0, 'ttm_net_net': 2.0, 'ttm_margin_of_safety': 25.0,
       'ttm_pe_ratio': 12.0, 'ttm_pb_ratio': 2.0, 'currency': 'USD', 'reporting_frequency': 'quarterly',
       'date_range': 'Q1 2024 through Q4 2024', 'warnings': []}


def _lines(annual_metrics, financial_data):
    return TTMAnalysisSection(TTM, annual_metrics, {'currency': 'USD', 'price': 22.0, **financial_data}).generate()


def test_tbvps_pe_pb_compared_with_latest_annual():
    lines = _lines({'graham_number': 28.0, 'tbvps': 10.0, 'net_net_value': 2.0, 'margin_of_safety': 10.0},
                   {'pe_ratio': 10.0, 'price_to_book': 2.5})
    assert "- TTM Tangible Book Value Per Share: 11.00 USD (Annual: 10.00 USD, Diff: +10.0%)" in lines
    assert "- TTM P/E Ratio: 12.00 (Annual: 10.00, Diff: +20.0%)" in lines
    assert "- TTM P/B Ratio: 2.00 (Annual: 2.50, Diff: -20.0%)" in lines


def test_margin_of_safety_states_its_basis_without_a_diff():
    lines = _lines({'margin_of_safety': 10.0}, {})
    mos = [line for line in lines if line.startswith("- TTM Margin of Safety")]
    assert mos == ["- TTM Margin of Safety: 25.0% (vs the TTM Graham Number; the annual margin of safety "
                   "uses the lower of the normalized Graham Number and EPV)"]


def test_missing_annual_ratio_shows_ttm_only():
    lines = _lines({}, {'pe_ratio': 0.0})
    assert "- TTM P/E Ratio: 12.00" in lines
