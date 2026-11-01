"""
Characterisation tests for GrahamCalculator's individual investor tests and verdict,
which previously had no direct tests.

These pin CURRENT behaviour, including known defects (marked "Known defect"), so the
refactor cannot change them silently. When a rule is deliberately aligned with Graham,
update the marked assertion in the same commit.
"""

import pytest
from hypothesis import given, settings, strategies as st

from config.investor_thresholds import DEFENSIVE, ENTERPRISING
from core.graham_math import GrahamCalculator
from core.investor_tests import criteria, defensive, enterprising
from core.verdict import determine_verdict


def _year(**fields):
    """A complete financial year; override fields as needed."""
    base = {
        "revenue": 1000.0, "net_income": 100.0, "eps": 2.0, "dividend": 0.5,
        "total_equity": 500.0, "intangible_assets": 0.0, "goodwill": 0.0,
        "shares_outstanding": 50.0, "current_assets": 400.0, "current_liabilities": 100.0,
        "total_liabilities": 300.0, "long_term_debt": 100.0,
    }
    base.update(fields)
    return base


DIVIDEND_ONLY_YEAR = {"revenue": 0.0, "net_income": 0.0, "eps": 0.0, "dividend": 0.6,
                      "total_equity": 0.0, "current_assets": 0.0, "current_liabilities": 0.0,
                      "long_term_debt": 0.0, "shares_outstanding": 50.0}


def _calc(history, price=20.0):
    return GrahamCalculator({"history": history, "price": price, "sector": "Industrials"})


def _years(history):
    return sorted(history, reverse=True)


# The criterion functions in core.investor_tests, by their former GrahamCalculator method names
CRITERIA = {
    "_test_current_ratio": criteria.current_ratio_test,
    "_test_debt_to_assets": defensive.debt_to_net_current_assets,
    "_test_dividend_record": defensive.dividend_record,
    "_test_earnings_growth": defensive.earnings_growth,
    "_test_pe_ratio": defensive.pe_ratio,
    "_test_pb_ratio": defensive.pb_ratio,
    "_test_enterprising_debt": enterprising.debt_to_net_current_assets,
    "_test_current_dividend": enterprising.current_dividend,
    "_test_enterprising_price": enterprising.price_test,
}
PRICED_TESTS = {"_test_pe_ratio", "_test_pb_ratio", "_test_enterprising_price"}


def _run(method, history, *args, price=20.0, **kwargs):
    """Call an investor criterion the way run_investor_tests does."""
    if method in PRICED_TESTS:
        args = (price, *args)
    if method == "_test_enterprising_price":
        args = (*args, _calc(history, price).compute_tbvps(round_result=False))
    return CRITERIA[method](history, _years(history), *args, **kwargs)


ratios = st.floats(min_value=0.01, max_value=10.0, allow_nan=False, allow_infinity=False)


class TestCurrentRatio:
    @settings(max_examples=200)
    @given(ratio=ratios)
    def test_passes_when_ratio_at_or_above_minimum(self, ratio):
        history = {"2023-12-31": _year(current_assets=ratio * 100.0, current_liabilities=100.0)}
        expected = "PASS" if (ratio * 100.0) / 100.0 >= DEFENSIVE.MIN_CURRENT_RATIO else "FAIL"
        assert _run("_test_current_ratio", history, min_ratio=DEFENSIVE.MIN_CURRENT_RATIO) == expected

    def test_exact_minimum_passes(self):
        history = {"2023-12-31": _year(current_assets=200.0, current_liabilities=100.0)}
        assert _run("_test_current_ratio", history, min_ratio=2.0) == "PASS"

    def test_uses_latest_year_with_assets_or_equity(self):
        history = {"2024-12-31": DIVIDEND_ONLY_YEAR,
                   "2023-12-31": _year(current_assets=300.0, current_liabilities=100.0)}
        assert _run("_test_current_ratio", history, min_ratio=2.0) == "PASS"

    def test_zero_current_liabilities_fails(self):
        assert _run("_test_current_ratio", {"2023-12-31": _year(current_liabilities=0.0)}) == "FAIL"

    def test_no_years_or_no_financial_year_fails(self):
        assert _run("_test_current_ratio", {}) == "FAIL"
        assert _run("_test_current_ratio", {"2024-12-31": DIVIDEND_ONLY_YEAR}) == "FAIL"


class TestDebtToAssets:
    """Defensive: long-term debt < net current assets (current assets - current liabilities)."""

    def test_debt_below_net_current_assets_passes(self):
        assert _run("_test_debt_to_assets", {"2023-12-31": _year(long_term_debt=299.0)}) == "PASS"

    def test_debt_equal_to_net_current_assets_passes(self):
        # "should not exceed": equality passes (F20)
        assert _run("_test_debt_to_assets", {"2023-12-31": _year(long_term_debt=300.0)}) == "PASS"
        assert _run("_test_debt_to_assets", {"2023-12-31": _year(long_term_debt=300.01)}) == "FAIL"

    def test_known_defect_missing_debt_passes(self):
        # Known defect: missing long-term debt is 0.0, which passes silently
        history = {"2023-12-31": {k: v for k, v in _year().items() if k != "long_term_debt"}}
        assert _run("_test_debt_to_assets", history) == "PASS"

    def test_skips_dividend_only_year(self):
        history = {"2024-12-31": DIVIDEND_ONLY_YEAR, "2023-12-31": _year(long_term_debt=50.0)}
        assert _run("_test_debt_to_assets", history) == "PASS"

    def test_no_years_or_no_financial_year_fails(self):
        assert _run("_test_debt_to_assets", {}) == "FAIL"
        assert _run("_test_debt_to_assets", {"2024-12-31": {"dividend": 1.0}}) == "FAIL"


class TestDividendRecord:
    def test_dividend_every_year_passes(self):
        history = {f"{2023 - i}-12-31": _year() for i in range(20)}
        assert _run("_test_dividend_record", history, len(history)) == "PASS"

    def test_any_missed_dividend_fails(self):
        history = {f"{2023 - i}-12-31": _year() for i in range(20)}
        history["2010-12-31"] = _year(dividend=0.0)
        assert _run("_test_dividend_record", history, len(history)) == "FAIL"

    def test_only_most_recent_20_years_checked(self):
        history = {f"{2023 - i}-12-31": _year() for i in range(25)}
        history["2000-12-31"] = _year(dividend=0.0)  # 24th year back
        assert _run("_test_dividend_record", history, len(history)) == "PASS"

    def test_fewer_than_twenty_years_fails(self):
        # Graham requires 20 years (F20): a 19-year record paying every year cannot confirm it
        history = {f"{2023 - i}-12-31": _year() for i in range(19)}
        assert _run("_test_dividend_record", history, len(history)) == "FAIL"

    def test_missing_year_is_an_interruption(self):
        history = {f"{2023 - i}-12-31": _year() for i in range(21)}
        del history["2012-12-31"]  # no row at all for 2012
        assert _run("_test_dividend_record", history, len(history)) == "FAIL"

    def test_payment_counts_show_payments(self):
        history = {f"{2023 - i}-12-31": _year(dividend=4.0) for i in range(20)}  # 4 payments a year
        assert _run("_test_dividend_record", history, len(history)) == "PASS"


class TestEarningsGrowth:
    """Defensive 4.5 (F20): mean EPS of reported years 0-2 >= 4/3 x mean EPS of years 9-11."""

    @staticmethod
    def _history(recent_eps, base_eps, years=12):
        history = {}
        for i in range(years):
            eps = recent_eps if i < 3 else base_eps if 9 <= i <= 11 else 2.0
            history[f"{2023 - i}-12-31"] = _year(eps=eps)
        return history

    @settings(max_examples=200)
    @given(growth=st.floats(min_value=0.5, max_value=3.0, allow_nan=False))
    def test_passes_at_or_above_one_third(self, growth):
        history = self._history(recent_eps=1.5 * growth, base_eps=1.5)
        expected = "PASS" if 1.5 * growth >= (4 / 3) * 1.5 else "FAIL"
        assert _run("_test_earnings_growth", history, len(history)) == expected

    def test_exactly_one_third_passes_and_33_percent_does_not(self):
        assert _run("_test_earnings_growth", self._history(4.0, 3.0), 12) == "PASS"   # +33.3...%
        assert _run("_test_earnings_growth", self._history(3.99, 3.0), 12) == "FAIL"  # +33.0%

    def test_uses_three_year_averages_not_single_years(self):
        history = self._history(recent_eps=3.0, base_eps=2.0)
        history["2023-12-31"] = _year(eps=1.0)  # one weak latest year: average (1+3+3)/3 = 2.33 < 2.67
        assert _run("_test_earnings_growth", history, len(history)) == "FAIL"

    def test_fewer_than_twelve_reported_years_is_too_young(self):
        history = self._history(4.0, 2.0, years=11)
        assert _run("_test_earnings_growth", history, len(history)) == "N/A (Too Young)"

    def test_dividend_only_years_do_not_count(self):
        history = self._history(4.0, 2.0, years=11)
        history["2024-12-31"] = DIVIDEND_ONLY_YEAR
        assert _run("_test_earnings_growth", history, len(history)) == "N/A (Too Young)"

    def test_non_positive_base_fails(self):
        assert _run("_test_earnings_growth", self._history(4.0, 0.0), 12) == "FAIL"
        assert _run("_test_earnings_growth", self._history(4.0, -1.0), 12) == "FAIL"


def _three_years(eps_newest_first):
    return {f"{2023 - i}-12-31": _year(eps=eps) for i, eps in enumerate(eps_newest_first)}


class TestPeRatio:
    """Defensive 4.6 (F20): price ≤ 15 × the average EPS of the three latest reported years."""

    @settings(max_examples=200)
    @given(pe=st.floats(min_value=1.0, max_value=40.0, allow_nan=False))
    def test_uses_three_year_average_inclusive(self, pe):
        history = _three_years([3.0, 2.0, 1.0])  # average 2.0
        price = 2.0 * pe
        expected = "PASS" if price / 2.0 <= DEFENSIVE.MAX_PE_RATIO else "FAIL"
        assert _run("_test_pe_ratio", history, price=price, max_pe=DEFENSIVE.MAX_PE_RATIO) == expected

    def test_exact_maximum_passes(self):
        assert _run("_test_pe_ratio", _three_years([2.0, 2.0, 2.0]), price=30.0, max_pe=15) == "PASS"

    def test_one_good_year_does_not_pass(self):
        """Latest EPS alone gives P/E 10; the three-year average (2.0) gives 30."""
        assert _run("_test_pe_ratio", _three_years([4.5, 1.0, 0.5]), price=45.0, max_pe=15) == "FAIL"

    def test_fewer_than_three_reported_years_fails(self):
        assert _run("_test_pe_ratio", _three_years([2.0, 2.0]), price=10.0) == "FAIL"

    def test_non_positive_average_fails(self):
        assert _run("_test_pe_ratio", _three_years([1.0, -2.0, -1.0]), price=10.0) == "FAIL"

    def test_zero_price_or_no_financial_year_fails(self):
        assert _run("_test_pe_ratio", _three_years([2.0, 2.0, 2.0]), price=0.0) == "FAIL"
        assert _run("_test_pe_ratio", {"2024-12-31": {"dividend": 1.0}}, price=10.0) == "FAIL"


class TestPbRatio:
    """Defensive 4.7 (F20): price ≤ 1.5 × tangible BVPS, or P/E (3-year average) × P/B ≤ 22.5."""

    @settings(max_examples=200)
    @given(pb=st.floats(min_value=0.1, max_value=5.0, allow_nan=False))
    def test_single_year_passes_at_or_below_maximum(self, pb):
        price = 10.0 * pb  # TBVPS = 500 / 50 = 10; one year, so no three-year P/E for the product rule
        expected = "PASS" if price / 10.0 <= DEFENSIVE.MAX_PB_RATIO else "FAIL"
        assert _run("_test_pb_ratio", {"2023-12-31": _year()}, price=price,
                    max_pb=DEFENSIVE.MAX_PB_RATIO) == expected

    def test_uses_tangible_book_value(self):
        # TBVPS = (500 - 450) / 50 = 1, so P/B = 14 (it was 1.4 on total equity, a pass)
        history = {"2023-12-31": _year(goodwill=450.0)}
        assert _run("_test_pb_ratio", history, price=14.0, max_pb=1.5) == "FAIL"

    def test_product_rule_admits_higher_pb_with_lower_pe(self):
        # Average EPS 2.0 -> P/E 9; TBVPS 10 -> P/B 1.8 > 1.5; product 16.2 <= 22.5
        history = _three_years([2.0, 2.0, 2.0])
        assert _run("_test_pb_ratio", history, price=18.0, max_pb=1.5) == "PASS"
        # P/E 13 x P/B 2.6 = 33.8 > 22.5
        assert _run("_test_pb_ratio", history, price=26.0, max_pb=1.5) == "FAIL"

    @pytest.mark.parametrize("fields", [{"shares_outstanding": 0.0}, {"total_equity": -1.0}])
    def test_zero_shares_or_non_positive_equity_fails(self, fields):
        # total_equity -1 with revenue keeps the year "financial"
        assert _run("_test_pb_ratio", {"2023-12-31": _year(**fields)}, price=5.0) == "FAIL"

    def test_zero_price_or_no_financial_year_fails(self):
        assert _run("_test_pb_ratio", {"2023-12-31": _year()}, price=0.0) == "FAIL"
        assert _run("_test_pb_ratio", {"2024-12-31": {"dividend": 1.0}}, price=5.0) == "FAIL"


class TestEnterprisingDebt:
    """Enterprising: long-term debt < 110% of (current assets - current liabilities)."""

    def test_debt_below_limit_passes(self):
        assert _run("_test_enterprising_debt", {"2023-12-31": _year(long_term_debt=329.0)}) == "PASS"

    def test_debt_at_limit_passes(self):
        # "not more than 110%": equality passes (F20)
        limit = 300.0 * ENTERPRISING.MAX_DEBT_ASSETS
        assert _run("_test_enterprising_debt", {"2023-12-31": _year(long_term_debt=limit)}) == "PASS"
        assert _run("_test_enterprising_debt", {"2023-12-31": _year(long_term_debt=limit + 0.01)}) == "FAIL"

    def test_no_years_or_no_financial_year_fails(self):
        assert _run("_test_enterprising_debt", {}) == "FAIL"
        assert _run("_test_enterprising_debt", {"2024-12-31": {"dividend": 1.0}}) == "FAIL"


class TestCurrentDividend:
    def test_dividend_in_latest_financial_year_passes(self):
        assert _run("_test_current_dividend", {"2023-12-31": _year(dividend=0.1)}) == "PASS"

    def test_no_dividend_fails(self):
        assert _run("_test_current_dividend", {"2023-12-31": _year(dividend=0.0)}) == "FAIL"

    def test_dividend_only_year_is_skipped(self):
        # The latest *financial* year is used, so a declared dividend in a dividend-only year is ignored
        history = {"2024-12-31": DIVIDEND_ONLY_YEAR, "2023-12-31": _year(dividend=0.0)}
        assert _run("_test_current_dividend", history) == "FAIL"

    def test_no_years_or_no_financial_year_fails(self):
        assert _run("_test_current_dividend", {}) == "FAIL"
        assert _run("_test_current_dividend", {"2024-12-31": {"dividend": 1.0}}) == "FAIL"


class TestEnterprisingPrice:
    """F20: P/E < 10 AND price < 1.2 x TBVPS (TBVPS = 500 / 50 = 10 in _year())."""

    def test_both_conditions_pass(self):
        assert _run("_test_enterprising_price", {"2023-12-31": _year(eps=2.0)}, price=11.9) == "PASS"

    def test_low_pe_alone_fails(self):
        # P/E 9.5 but price 19 is 190% of tangible book
        assert _run("_test_enterprising_price", {"2023-12-31": _year(eps=2.0)}, price=19.0) == "FAIL"

    def test_price_below_120_percent_of_tbvps_alone_fails(self):
        # Price 11.9 < 12 but P/E 23.8
        assert _run("_test_enterprising_price", {"2023-12-31": _year(eps=0.5)}, price=11.9) == "FAIL"

    def test_non_positive_eps_fails(self):
        assert _run("_test_enterprising_price", {"2023-12-31": _year(eps=0.0, net_income=-5.0)},
                    price=11.0) == "FAIL"

    def test_neither_condition_fails(self):
        assert _run("_test_enterprising_price", {"2023-12-31": _year(eps=1.0)}, price=12.0) == "FAIL"

    def test_negative_tbvps_and_high_pe_fails(self):
        history = {"2023-12-31": _year(eps=1.0, goodwill=1000.0)}
        assert _run("_test_enterprising_price", history, price=50.0) == "FAIL"

    def test_zero_price_or_no_financial_year_fails(self):
        assert _run("_test_enterprising_price", {"2023-12-31": _year()}, price=0.0) == "FAIL"
        assert _run("_test_enterprising_price", {"2024-12-31": {"dividend": 1.0}}, price=5.0) == "FAIL"


ALL_PASS_DEFENSIVE = {k: "PASS" for k in ("earnings_stability", "current_ratio", "debt_to_assets",
                                          "dividend_record", "earnings_growth", "pe_ratio", "pb_ratio")}
ALL_PASS_ENTERPRISING = {k: "PASS" for k in ("earnings_stability", "current_ratio", "debt_to_assets",
                                             "dividend_record", "price_test")}


class TestDetermineVerdict:
    """Design D8 (GRAHAM_METHODOLOGY §7): first matching rule wins."""

    @staticmethod
    def _verdict(mos=10.0, intrinsic=25.0, net_net="N/A", price=20.0, defensive=None, enterprising=None,
                 note=None):
        details = {'mos_percentage': mos, 'intrinsic_value_used': intrinsic, 'note': note}
        return determine_verdict(details, net_net, price, defensive, enterprising)['verdict']

    def test_no_intrinsic_value_is_insufficient_data(self):
        assert self._verdict(mos="N/A", intrinsic="N/A") == "INSUFFICIENT DATA"

    def test_net_net_bargain_at_two_thirds_of_ncav(self):
        assert self._verdict(net_net=30.0, price=20.0, mos=-50.0) == "NET-NET BARGAIN"
        assert self._verdict(net_net=29.9, price=20.0, mos=-50.0) == "OVERVALUED"

    @pytest.mark.parametrize("mos", [0.0, -30.0, "N/A"])
    def test_no_margin_of_safety_is_overvalued_even_if_criteria_pass(self, mos):
        assert self._verdict(mos=mos, defensive=ALL_PASS_DEFENSIVE,
                             enterprising=ALL_PASS_ENTERPRISING) == "OVERVALUED"

    def test_defensive_buy_needs_all_defensive_criteria(self):
        assert self._verdict(mos=0.1, defensive=ALL_PASS_DEFENSIVE) == "DEFENSIVE BUY"

    def test_enterprising_buy_when_defensive_fails(self):
        defensive = {**ALL_PASS_DEFENSIVE, "pb_ratio": "FAIL"}
        assert self._verdict(defensive=defensive, enterprising=ALL_PASS_ENTERPRISING) == "ENTERPRISING BUY"

    def test_na_is_never_a_pass(self):
        defensive = {**ALL_PASS_DEFENSIVE, "earnings_growth": "N/A (Too Young)"}
        enterprising = {**ALL_PASS_ENTERPRISING, "current_ratio": "N/A"}
        assert self._verdict(defensive=defensive, enterprising=enterprising) == "UNDERVALUED – FAILS GRAHAM CRITERIA"

    def test_cheap_but_failing_both_lists_the_failures(self):
        defensive = {**ALL_PASS_DEFENSIVE, "pb_ratio": "FAIL"}
        enterprising = {**ALL_PASS_ENTERPRISING, "price_test": "FAIL"}
        result = determine_verdict({'mos_percentage': 25.0, 'intrinsic_value_used': 25.0}, "N/A", 20.0,
                                   defensive, enterprising)
        assert result['verdict'] == "UNDERVALUED – FAILS GRAHAM CRITERIA"
        assert "defensive: P/B; enterprising: price" in result['reason']

    def test_no_strong_buy_tier(self):
        assert self._verdict(mos=90.0, defensive=ALL_PASS_DEFENSIVE) == "DEFENSIVE BUY"


class TestComputeCurrentRatio:
    """The displayed current ratio and the current-ratio tests use the same year and value."""

    def test_ratio_and_fiscal_year_from_latest_balance_sheet(self):
        history = {"2024-12-31": DIVIDEND_ONLY_YEAR,
                   "2023-12-31": _year(current_assets=300.0, current_liabilities=120.0)}
        assert _calc(history).compute_current_ratio() == {"ratio": 2.5, "fiscal_year_end": "2023-12-31"}

    def test_zero_current_liabilities_is_na(self):
        history = {"2023-12-31": _year(current_liabilities=0.0)}
        assert _calc(history).compute_current_ratio() == {"ratio": "N/A", "fiscal_year_end": "2023-12-31"}

    def test_no_balance_sheet_year_is_na(self):
        assert _calc({"2024-12-31": {"dividend": 1.0}}).compute_current_ratio() == {
            "ratio": "N/A", "fiscal_year_end": None}

    @settings(max_examples=200)
    @given(ratio=ratios)
    def test_display_value_agrees_with_test_verdict(self, ratio):
        history = {"2023-12-31": _year(current_assets=ratio * 100.0, current_liabilities=100.0)}
        calc = _calc(history)
        unrounded = (ratio * 100.0) / 100.0
        assert calc.compute_current_ratio()["ratio"] == round(unrounded, 2)
        assert _run("_test_current_ratio", history, min_ratio=2.0) == ("PASS" if unrounded >= 2.0 else "FAIL")


class TestPublicUtility:
    """Defensive 4.2 for public utilities (F20): debt ≤ 2 × book equity; no current-ratio test."""

    @staticmethod
    def _tests(industry, **fields):
        history = {f"{2023 - i}-12-31": _year(**fields) for i in range(3)}
        return defensive.run_defensive_tests(history, _years(history), len(history), 20.0, industry)

    def test_regulated_utility_uses_debt_to_equity_and_drops_current_ratio(self):
        # current ratio 0.5 and total debt 900 > NCA, but 900 <= 2 x 500 equity
        tests = self._tests("Utilities - Regulated Electric", current_assets=50.0, current_liabilities=100.0,
                            total_debt=900.0)
        assert tests['current_ratio'] == defensive.NOT_APPLICABLE_UTILITY
        assert tests['debt_to_assets'] == "PASS"

    def test_utility_debt_above_twice_equity_fails(self):
        tests = self._tests("Utilities - Regulated Water", total_debt=1000.01)
        assert tests['debt_to_assets'] == "FAIL"

    def test_unregulated_utility_sector_keeps_industrial_tests(self):
        tests = self._tests("Utilities - Diversified", current_assets=50.0, current_liabilities=100.0)
        assert tests['current_ratio'] == "FAIL"

    def test_not_applicable_does_not_block_the_verdict(self):
        tests = {**ALL_PASS_DEFENSIVE, 'current_ratio': defensive.NOT_APPLICABLE_UTILITY}
        result = determine_verdict({'mos_percentage': 10.0, 'intrinsic_value_used': 25.0}, "N/A", 20.0, tests, None)
        assert result['verdict'] == "DEFENSIVE BUY"
