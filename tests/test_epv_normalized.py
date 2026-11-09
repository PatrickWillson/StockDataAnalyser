"""
Unit tests for normalized EPV calculation.

Tests the full-cycle EPV methodology that includes loss years.
"""

import pytest
from core.graham_math import GrahamCalculator


def test_epv_normalized_with_10_years_all_profitable():
    """
    Test with 10 years all profitable (should calculate average).
    Requirements: 3.1, 3.2, 3.3, 3.7
    """
    # Arrange: Create 10 years of profitable data
    history = {}
    net_incomes = [100000, 110000, 120000, 115000, 125000, 130000, 135000, 140000, 145000, 150000]
    
    for i, net_income in enumerate(net_incomes):
        year = str(2024 - i)
        history[year] = {
            'net_income': net_income,
            'revenue': net_income * 10,
            'eps': net_income / 1000000,
            'shares_outstanding': 1000000,
            'total_equity': 1000000,
            'intangible_assets': 0,
            'goodwill': 0
        }
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 10.0,
        'currency': 'USD',
        'history': history
    }
    
    # Act: Calculate EPV
    calculator = GrahamCalculator(financial_data)
    result = calculator.compute_epv_normalized(history)
    
    # Assert: Should return dict with correct average
    assert isinstance(result, dict), "Should return dict for valid data"
    
    expected_avg = sum(net_incomes) / len(net_incomes)
    assert result['normalized_earnings'] == pytest.approx(expected_avg, rel=1e-6)
    assert result['years_used'] == 10
    assert result['years_included'] == [str(2024 - i) for i in range(10)]
    assert len(result['net_incomes']) == 10
    
    # EPV should be normalized_earnings / 0.10
    expected_epv = expected_avg / 0.10
    assert result['epv'] == pytest.approx(expected_epv, rel=1e-6)


def test_epv_normalized_with_7_years_mixed_profit_loss():
    """
    Test with 7 years mixed profit/loss (should include losses).
    Requirements: 3.1, 3.2, 3.3, 3.7
    """
    # Arrange: Create 7 years with mix of profit and loss
    history = {}
    net_incomes = [50000, 60000, -10000, 40000, -5000, 55000, 45000]
    
    for i, net_income in enumerate(net_incomes):
        year = str(2024 - i)
        history[year] = {
            'net_income': net_income,
            'revenue': abs(net_income) * 10,
            'eps': net_income / 1000000,
            'shares_outstanding': 1000000,
            'total_equity': 1000000,
            'intangible_assets': 0,
            'goodwill': 0
        }
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 10.0,
        'currency': 'USD',
        'history': history
    }
    
    # Act: Calculate EPV
    calculator = GrahamCalculator(financial_data)
    result = calculator.compute_epv_normalized(history)
    
    # Assert: Should include loss years in average
    assert isinstance(result, dict), "Should return dict for valid data"
    
    expected_avg = sum(net_incomes) / len(net_incomes)
    assert result['normalized_earnings'] == pytest.approx(expected_avg, rel=1e-6)
    assert result['years_used'] == 7
    
    # Verify loss years are included
    assert -10000 in result['net_incomes']
    assert -5000 in result['net_incomes']


def test_epv_normalized_with_6_years_insufficient_history():
    """
    Test with 6 years (should return "N/A - Insufficient history").
    Requirements: 3.1, 3.2, 3.3, 3.7
    """
    # Arrange: Create only 6 years of data
    history = {}
    net_incomes = [50000, 60000, 70000, 65000, 75000, 80000]
    
    for i, net_income in enumerate(net_incomes):
        year = str(2024 - i)
        history[year] = {
            'net_income': net_income,
            'revenue': net_income * 10,
            'eps': net_income / 1000000,
            'shares_outstanding': 1000000,
            'total_equity': 1000000,
            'intangible_assets': 0,
            'goodwill': 0
        }
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 10.0,
        'currency': 'USD',
        'history': history
    }
    
    # Act: Calculate EPV
    calculator = GrahamCalculator(financial_data)
    result = calculator.compute_epv_normalized(history)
    
    # Assert: Should return N/A message
    assert isinstance(result, str), "Should return string for insufficient data"
    assert "Insufficient history" in result
    assert "6 complete years" in result
    assert "minimum 7" in result


def test_epv_normalized_with_negative_average():
    """
    Test with negative average (should return "N/A - Negative normalized earnings").
    Requirements: 3.1, 3.2, 3.3, 3.7
    """
    # Arrange: Create 7 years with mostly losses
    history = {}
    net_incomes = [-50000, -60000, 10000, -40000, -30000, 5000, -20000]
    
    for i, net_income in enumerate(net_incomes):
        year = str(2024 - i)
        history[year] = {
            'net_income': net_income,
            'revenue': abs(net_income) * 10,
            'eps': net_income / 1000000,
            'shares_outstanding': 1000000,
            'total_equity': 1000000,
            'intangible_assets': 0,
            'goodwill': 0
        }
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 10.0,
        'currency': 'USD',
        'history': history
    }
    
    # Act: Calculate EPV
    calculator = GrahamCalculator(financial_data)
    result = calculator.compute_epv_normalized(history)
    
    # Assert: Should return N/A message for negative average
    assert isinstance(result, str), "Should return string for negative average"
    assert "Negative normalized earnings" in result
    assert "unprofitable over cycle" in result


def test_epv_normalized_all_years_included():
    """
    Test that all years are included in calculation (both profitable and unprofitable).
    Requirements: 3.1, 3.2, 3.3, 3.7
    """
    # Arrange: Create 8 years with specific pattern
    history = {}
    net_incomes = [100000, -20000, 80000, -10000, 90000, 70000, -5000, 85000]
    
    for i, net_income in enumerate(net_incomes):
        year = str(2024 - i)
        history[year] = {
            'net_income': net_income,
            'revenue': abs(net_income) * 10,
            'eps': net_income / 1000000,
            'shares_outstanding': 1000000,
            'total_equity': 1000000,
            'intangible_assets': 0,
            'goodwill': 0
        }
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 10.0,
        'currency': 'USD',
        'history': history
    }
    
    # Act: Calculate EPV
    calculator = GrahamCalculator(financial_data)
    result = calculator.compute_epv_normalized(history)
    
    # Assert: All years should be included
    assert isinstance(result, dict), "Should return dict for valid data"
    assert result['years_used'] == 8
    assert len(result['net_incomes']) == 8
    
    # Verify all net incomes are present (including negative ones)
    for net_income in net_incomes:
        assert net_income in result['net_incomes'], f"Net income {net_income} should be included"
    
    # Verify average includes all years
    expected_avg = sum(net_incomes) / len(net_incomes)
    assert result['normalized_earnings'] == pytest.approx(expected_avg, rel=1e-6)


# --- Per share: average of each year's EPS (GRAHAM_METHODOLOGY §2.4, F22) ------------------------

from hypothesis import given, settings, strategies as st  # noqa: E402

from config.graham_constants import COST_OF_CAPITAL  # noqa: E402


def _history(net_incomes, shares):
    return {f"{2024 - i}-12-31": {'net_income': ni, 'revenue': 1.0, 'total_equity': 1.0,
                                  'shares_outstanding': s, 'eps': ni / s}
            for i, (ni, s) in enumerate(zip(net_incomes, shares))}


@settings(max_examples=100, deadline=None)
@given(st.lists(st.tuples(st.floats(1e3, 1e9), st.floats(1e3, 1e8)), min_size=7, max_size=12))
def test_epv_per_share_is_average_eps_capitalized(years):
    """Each year's earnings on the present capitalization (ch. 39): over max(latest count, that year's count)."""
    net_incomes, shares = zip(*years)
    result = GrahamCalculator({'history': _history(net_incomes, shares)}).compute_epv_normalized(
        _history(net_incomes, shares), round_result=False)
    used = min(len(years), 10)
    latest = shares[0]
    expected = sum(ni / max(latest, s) for ni, s in years[:used]) / used / COST_OF_CAPITAL
    assert result['epv_per_share'] == pytest.approx(expected)
    assert result['epv'] == pytest.approx(sum(net_incomes[:used]) / used / COST_OF_CAPITAL)


def test_epv_per_share_is_not_company_value_over_todays_shares():
    """A buyback (1,000 -> 500 shares) must not raise past years' per-share earnings."""
    history = _history([100.0] * 10, [500.0] + [1000.0] * 9)    # latest year: 500 shares after buybacks
    result = GrahamCalculator({'history': history}).compute_epv()
    assert result['epv_per_share'] == pytest.approx((0.2 + 9 * 0.1) / 10 / COST_OF_CAPITAL)   # 1.10, not 2.00
    assert result['normalized_eps'] == pytest.approx(0.11)


def test_a_year_without_a_share_count_takes_the_nearest_later_count():
    """Vendor years carry no share count (§8.12): Graham needs none, the past record goes on today's shares."""
    history = _history([100.0] * 8, [1000.0] * 8)
    history["2020-12-31"].update(eps=0.0, shares_outstanding=0.0)
    result = GrahamCalculator({'history': history}).compute_epv()
    assert result['epv_per_share'] == pytest.approx(1.0) and result['epv'] == 1000.0


def test_shares_since_issued_count_in_full_and_are_noted():
    """Issuance (500 -> 1,000 shares): earlier earnings on today's 1,000 (ch. 39, no allowance for cheap stock)."""
    history = _history([100.0] * 10, [1000.0] + [500.0] * 9)
    result = GrahamCalculator({'history': history}).compute_epv()
    assert result['epv_per_share'] == pytest.approx(1.0)
    assert "shares rose over 10%" in result['share_basis']


def test_epv_per_share_na_without_any_share_count():
    history = _history([100.0] * 8, [1000.0] * 8)
    for row in history.values():
        row.update(eps=0.0, shares_outstanding=0.0)
    result = GrahamCalculator({'history': history}).compute_epv()
    assert result['epv_per_share'] == "N/A" and "no share count" in result['epv_per_share_reason']
