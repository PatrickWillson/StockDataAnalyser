"""
core.formulas: Graham's balance-sheet values, shared by annual, TTM and the dossier's worked
calculations (M4.1).
"""

from decimal import Decimal

from hypothesis import given, settings, strategies as st

from core.formulas import net_current_asset_value, tangible_equity

amounts = st.floats(min_value=-1e12, max_value=1e12, allow_nan=False, allow_infinity=False)


@settings(max_examples=200)
@given(equity=amounts, intangibles=amounts, goodwill=amounts)
def test_tangible_equity_removes_intangibles_and_goodwill_as_magnitudes(equity, intangibles, goodwill):
    assert tangible_equity(equity, intangibles, goodwill) == equity - abs(intangibles) - abs(goodwill)
    assert tangible_equity(equity, intangibles, goodwill) <= equity


@settings(max_examples=200)
@given(current_assets=amounts, total_liabilities=amounts)
def test_ncav_is_current_assets_less_all_liabilities(current_assets, total_liabilities):
    assert net_current_asset_value(current_assets, total_liabilities) == current_assets - total_liabilities


def test_formulas_accept_decimals():
    assert tangible_equity(Decimal("100"), Decimal("-10"), Decimal("5")) == Decimal("85")
    assert net_current_asset_value(Decimal("50"), Decimal("20")) == Decimal("30")


@settings(max_examples=200)
@given(current_assets=amounts, total_liabilities=amounts,
       claims=st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False))
def test_ncav_deducts_claims_ahead_of_the_common(current_assets, total_liabilities, claims):
    ncav = net_current_asset_value(current_assets, total_liabilities, claims)
    assert ncav == current_assets - total_liabilities - claims
    assert ncav <= net_current_asset_value(current_assets, total_liabilities)
