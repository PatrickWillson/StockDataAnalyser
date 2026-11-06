"""An unclassified balance sheet reports no working capital: 0 debt <= 0 is not a pass (GRAHAM_METHODOLOGY §7)."""

import pytest

from core.investor_tests import defensive, enterprising

YEAR = "2025-12-31"


def _history(**row):
    return {YEAR: {"revenue": 100.0, "net_income": 10.0, "total_equity": 50.0, **row}}


@pytest.mark.parametrize("test", [defensive.debt_to_net_current_assets, enterprising.debt_to_net_current_assets])
def test_no_working_capital_is_not_a_pass(test):
    assert test(_history(current_assets=0.0, current_liabilities=0.0, long_term_debt=0.0), [YEAR]) == "FAIL"
    assert test(_history(long_term_debt=0.0), [YEAR]) == "FAIL"


@pytest.mark.parametrize("test", [defensive.debt_to_net_current_assets, enterprising.debt_to_net_current_assets])
def test_a_debt_free_company_with_working_capital_passes(test):
    assert test(_history(current_assets=80.0, current_liabilities=30.0, long_term_debt=0.0), [YEAR]) == "PASS"
    assert test(_history(current_assets=80.0, current_liabilities=30.0, long_term_debt=50.0), [YEAR]) == "PASS"
    assert test(_history(current_assets=80.0, current_liabilities=30.0, long_term_debt=60.0), [YEAR]) == "FAIL"
