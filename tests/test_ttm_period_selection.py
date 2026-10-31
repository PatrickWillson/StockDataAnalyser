"""
M4.5: TTM period selection — median-based frequency, gap check without a dead zone, and the
balance sheet aligned with the latest income period.
"""

from core.ttm_calculator import TTMCalculator


def _income(dates, net_income=25.0):
    return {d: {'revenue': 100.0, 'net_income': net_income} for d in dates}


def _balance(dates, equity=500.0):
    return {d: {'total_equity': equity, 'intangible_assets': 0.0, 'goodwill': 0.0, 'current_assets': 300.0,
                'total_liabilities': 200.0, 'shares_outstanding': 100.0} for d in dates}


def _calc(income_dates, balance_dates=None):
    balance_dates = balance_dates or income_dates[:1]
    return TTMCalculator({'income_statement': _income(income_dates), 'balance_sheet': _balance(balance_dates)},
                         price=10.0, currency='USD')


def test_old_missing_quarter_does_not_block_ttm():
    """Latest four quarters are consecutive; a quarter is missing only further back."""
    dates = ['2024-12-31', '2024-09-30', '2024-06-30', '2024-03-31', '2023-09-30']  # 2023-12-31 missing
    result = _calc(dates).compute_all()
    assert result['reporting_frequency'] == 'quarterly'
    assert result['ttm_net_income'] == 100.0


def test_interval_just_above_tolerance_is_a_gap():
    """125 days between two of the latest quarters: not consecutive quarters, so no TTM."""
    dates = ['2024-12-31', '2024-09-30', '2024-06-30', '2024-02-25', '2023-11-25', '2023-08-25']
    calc = _calc(dates)
    result = calc.compute_all()
    assert result['ttm_graham_number'] == "N/A"
    assert any('gaps' in w for w in result['warnings'])


def test_balance_sheet_matches_latest_income_period():
    income_dates = ['2024-09-30', '2024-06-30', '2024-03-31', '2023-12-31']
    calc = TTMCalculator({'income_statement': _income(income_dates),
                          'balance_sheet': {**_balance(['2024-12-31'], equity=900.0),
                                            **_balance(['2024-09-30'], equity=500.0)}},
                         price=10.0, currency='USD')
    assert calc.calculate_ttm_metrics()['total_equity'] == 500.0


def test_missing_aligned_balance_sheet_falls_back_with_warning():
    income_dates = ['2024-09-30', '2024-06-30', '2024-03-31', '2023-12-31']
    calc = _calc(income_dates, balance_dates=['2024-06-30'])
    assert calc.calculate_ttm_metrics()['total_equity'] == 500.0
    assert any('No balance sheet for 2024-09-30' in w for w in calc.warnings)
