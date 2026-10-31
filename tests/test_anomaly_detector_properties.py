"""
AnomalyDetector (F17): modified Z-score of EPS growth, 0.6745 × (x − median) / MAD (MAD floored
at ANOMALY_MIN_SPREAD_PP), flagged above 3.5; dividend-only years skipped; only table years.
"""

import statistics

from hypothesis import given, settings, strategies as st

from config.data_quality_config import ANOMALY_MIN_SPREAD_PP, FINANCIAL_HISTORY_YEARS
from core.anomaly_detector import AnomalyDetector


def _row(eps):
    return {'eps': eps, 'net_income': eps * 1e6, 'revenue': 1e7, 'total_equity': 1e6, 'shares_outstanding': 1e6}


def _history(eps_newest_first, start_year=2023):
    return {f"{start_year - i}-12-31": _row(eps) for i, eps in enumerate(eps_newest_first)}


def _scan(history):
    return AnomalyDetector({'history': history}).scan()


def _steady(n, growth_pct=8.0, base=1.0):
    """EPS growing by growth_pct a year, newest first."""
    return [base * (1 + growth_pct / 100) ** (n - 1 - i) for i in range(n)]


@settings(max_examples=150)
@given(n=st.integers(min_value=4, max_value=12), jump=st.floats(min_value=1.0, max_value=5.0),
       growth=st.floats(min_value=0.0, max_value=15.0))
def test_single_extreme_year_is_flagged_even_in_short_histories(n, jump, growth):
    """Steady growth plus one year whose EPS doubles to sextuples: that year alone is flagged.
    (The old mean/SD test could never flag anything with fewer than 6 growth rates.)"""
    eps = _steady(n, growth)
    eps[0] = eps[1] * (1 + jump)  # newest year jumps by 100-500%
    anomalies = _scan(_history(eps))
    assert len(anomalies) == 1
    assert anomalies[0].startswith("Year 2023-12-31: EPS growth modified Z-Score")


@settings(max_examples=150)
@given(eps=st.lists(st.floats(min_value=4.0, max_value=6.0, allow_nan=False), min_size=5, max_size=12))
def test_flags_match_the_modified_z_rule(eps):
    history = _history(eps)
    years = sorted(history, reverse=True)
    rates = [(history[a]['eps'] - history[b]['eps']) / history[b]['eps'] * 100 for a, b in zip(years, years[1:])]
    median = statistics.median(rates)
    mad = max(statistics.median(abs(r - median) for r in rates), ANOMALY_MIN_SPREAD_PP)
    expected = sum(1 for r in rates if abs(0.6745 * (r - median) / mad) > 3.5)
    assert len(_scan(history)) == expected


def test_steady_growth_has_no_anomalies():
    assert _scan(_history(_steady(10))) == []


def test_dividend_only_placeholder_year_is_not_a_minus_100_percent_outlier():
    history = _history(_steady(10), start_year=2023)
    history['2024-12-31'] = {'eps': 0.0, 'net_income': 0.0, 'revenue': 0.0, 'total_equity': 0.0, 'dividend': 0.5}
    assert _scan(history) == []


def test_only_years_in_the_financial_history_table_are_considered():
    eps = _steady(FINANCIAL_HISTORY_YEARS + 3)
    eps[-1] = eps[-2] / 6  # an extreme year older than the table (its successor's growth is +500%)
    assert _scan(_history(eps)) == []
