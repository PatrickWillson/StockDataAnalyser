"""
TTMCalculator must use the price it is given: price normalisation (London Fix, GBX -> GBP,
FX) happens once, upstream in the client. A second "London Fix" in TTM used to divide an
already-converted LSE price by 100 whenever a single quarter's EPS gave P/E > 500.
"""

from core.ttm_calculator import TTMCalculator


def _quarterly(net_income_latest):
    dates = ["2023-12-31", "2023-09-30", "2023-06-30", "2023-03-31"]
    income = {d: {"revenue": 10_000_000.0, "net_income": 2_000_000.0, "eps": 0.11} for d in dates}
    income[dates[0]]["net_income"] = net_income_latest
    balance = {d: {"total_equity": 50_000_000.0, "intangible_assets": 0.0, "goodwill": 0.0,
                   "current_assets": 30_000_000.0, "total_liabilities": 20_000_000.0,
                   "shares_outstanding": 18_000_000.0} for d in dates}
    return {"income_statement": income, "balance_sheet": balance}


def test_price_is_used_as_given_even_when_one_quarter_is_weak():
    # Latest quarter EPS = 500k / 18m = 0.028 -> P/E on that quarter alone = 594
    calc = TTMCalculator(_quarterly(500_000.0), price=16.50, currency="GBP", original_currency="GBP")

    assert calc.price == 16.50
    assert not any("London Fix" in w for w in calc.warnings)


def test_ttm_pe_uses_unadjusted_price():
    calc = TTMCalculator(_quarterly(500_000.0), price=16.50, currency="GBP", original_currency="GBP")

    metrics = calc.compute_all()

    ttm_eps = metrics["ttm_eps"]
    assert ttm_eps > 0
    assert metrics["ttm_pe_ratio"] == round(16.50 / ttm_eps, 2)
