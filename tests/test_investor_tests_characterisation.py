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


PRICED_TESTS = {"_test_pe_ratio", "_test_pb_ratio", "_test_enterprising_price"}


def _run(method, history, *args, price=20.0, **kwargs):
    """Call a GrahamCalculator investor test the way run_investor_tests does."""
    calc = _calc(history, price)
    if method in PRICED_TESTS:
        args = (price, *args)
    return getattr(calc, method)(history, _years(history), *args, **kwargs)


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

    def test_debt_equal_to_net_current_assets_fails(self):
        assert _run("_test_debt_to_assets", {"2023-12-31": _year(long_term_debt=300.0)}) == "FAIL"

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

    def test_known_defect_young_company_can_pass(self):
        # Known defect: Graham requires 20 years; a 3-year record paying every year passes
        history = {f"{2023 - i}-12-31": _year() for i in range(3)}
        assert _run("_test_dividend_record", history, len(history)) == "PASS"


class TestEarningsGrowth:
    """Defensive: latest net income / net income of the 10th financial year >= 1.33."""

    @staticmethod
    def _history(latest_ni, oldest_ni):
        history = {f"{2023 - i}-12-31": _year() for i in range(10)}
        history["2023-12-31"] = _year(net_income=latest_ni)
        history["2014-12-31"] = _year(net_income=oldest_ni)
        return history

    @settings(max_examples=200)
    @given(growth=st.floats(min_value=0.5, max_value=3.0, allow_nan=False))
    def test_passes_at_or_above_minimum_growth(self, growth):
        history = self._history(latest_ni=100.0 * growth, oldest_ni=100.0)
        expected = "PASS" if (100.0 * growth) / 100.0 >= DEFENSIVE.MIN_EARNINGS_GROWTH else "FAIL"
        assert _run("_test_earnings_growth", history, len(history)) == expected

    def test_fewer_than_ten_years_is_too_young(self):
        history = {f"{2023 - i}-12-31": _year() for i in range(9)}
        assert _run("_test_earnings_growth", history, len(history)) == "N/A (Too Young)"

    def test_dividend_only_years_do_not_count_towards_ten(self):
        history = {f"{2023 - i}-12-31": _year() for i in range(9)}
        history["2024-12-31"] = DIVIDEND_ONLY_YEAR
        assert _run("_test_earnings_growth", history, len(history)) == "N/A (Too Young)"

    def test_non_positive_old_earnings_fails(self):
        assert _run("_test_earnings_growth", self._history(200.0, 0.0), 10) == "FAIL"
        assert _run("_test_earnings_growth", self._history(200.0, -5.0), 10) == "FAIL"

    def test_no_financial_year_fails(self):
        history = {f"{2023 - i}-12-31": {"dividend": 1.0} for i in range(10)}
        assert _run("_test_earnings_growth", history, len(history)) == "FAIL"

    def test_known_defect_uses_single_year_total_net_income(self):
        # Known defect: Graham uses per-share 3-year averages; this compares single-year totals,
        # so a share-count change does not affect the result
        history = self._history(latest_ni=140.0, oldest_ni=100.0)
        history["2014-12-31"]["shares_outstanding"] = 10.0
        assert _run("_test_earnings_growth", history, len(history)) == "PASS"


class TestPeRatio:
    @settings(max_examples=200)
    @given(pe=st.floats(min_value=1.0, max_value=40.0, allow_nan=False))
    def test_passes_strictly_below_maximum(self, pe):
        price = 2.0 * pe
        expected = "PASS" if price / 2.0 < DEFENSIVE.MAX_PE_RATIO else "FAIL"
        assert _run("_test_pe_ratio", {"2023-12-31": _year(eps=2.0)}, price=price,
                    max_pe=DEFENSIVE.MAX_PE_RATIO) == expected

    def test_exact_maximum_fails(self):
        assert _run("_test_pe_ratio", {"2023-12-31": _year(eps=2.0)}, price=30.0, max_pe=15) == "FAIL"

    @pytest.mark.parametrize("eps", [0.0, -1.0])
    def test_non_positive_eps_fails(self, eps):
        assert _run("_test_pe_ratio", {"2023-12-31": _year(eps=eps)}, price=10.0) == "FAIL"

    def test_zero_price_or_no_financial_year_fails(self):
        assert _run("_test_pe_ratio", {"2023-12-31": _year()}, price=0.0) == "FAIL"
        assert _run("_test_pe_ratio", {"2024-12-31": {"dividend": 1.0}}, price=10.0) == "FAIL"


class TestPbRatio:
    """Defensive: price / (total equity / shares) < 1.5."""

    @settings(max_examples=200)
    @given(pb=st.floats(min_value=0.1, max_value=5.0, allow_nan=False))
    def test_passes_strictly_below_maximum(self, pb):
        price = 10.0 * pb  # BVPS = 500 / 50 = 10
        expected = "PASS" if price / 10.0 < DEFENSIVE.MAX_PB_RATIO else "FAIL"
        assert _run("_test_pb_ratio", {"2023-12-31": _year()}, price=price,
                    max_pb=DEFENSIVE.MAX_PB_RATIO) == expected

    def test_known_defect_uses_book_value_not_tangible_book_value(self):
        # Known defect: goodwill is ignored here (BVPS), unlike the Graham Number (TBVPS)
        history = {"2023-12-31": _year(goodwill=450.0)}
        assert _run("_test_pb_ratio", history, price=14.0, max_pb=1.5) == "PASS"

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

    def test_debt_at_limit_fails(self):
        limit = 300.0 * ENTERPRISING.MAX_DEBT_ASSETS
        assert _run("_test_enterprising_debt", {"2023-12-31": _year(long_term_debt=limit)}) == "FAIL"

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
    """Currently: P/E < 10 OR price < 1.2 x TBVPS (TBVPS = 500 / 50 = 10 in _year())."""

    def test_low_pe_alone_passes(self):
        assert _run("_test_enterprising_price", {"2023-12-31": _year(eps=2.0)}, price=19.0) == "PASS"

    def test_price_below_120_percent_of_tbvps_alone_passes(self):
        assert _run("_test_enterprising_price", {"2023-12-31": _year(eps=0.5)}, price=11.9) == "PASS"

    def test_non_positive_eps_falls_back_to_tbvps_rule(self):
        assert _run("_test_enterprising_price", {"2023-12-31": _year(eps=0.0, net_income=-5.0)},
                    price=11.0) == "PASS"

    def test_neither_condition_fails(self):
        assert _run("_test_enterprising_price", {"2023-12-31": _year(eps=1.0)}, price=12.0) == "FAIL"

    def test_known_defect_either_condition_is_enough(self):
        # Known defect: rules are OR'd, so a stock far above tangible book still passes on P/E alone
        assert _run("_test_enterprising_price", {"2023-12-31": _year(eps=10.0)}, price=99.0) == "PASS"

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
    def _verdict(self, graham_number=25.0, mos=10.0, defensive=None, enterprising=None):
        return _calc({})._determine_verdict(graham_number, mos, 0.0, defensive, enterprising)

    def test_graham_number_na_short_circuits(self):
        assert self._verdict(graham_number="N/A", mos=50.0) == "Rely on EPV - Negative Equity"

    @pytest.mark.parametrize("mos,expected", [
        (20.0, "STRONG BUY (Undervalued)"), (50.0, "STRONG BUY (Undervalued)"),
        (19.9, "UNDERVALUED"), (0.1, "UNDERVALUED"),
        (0.0, "OVERVALUED"), (-30.0, "OVERVALUED"),
    ])
    def test_margin_of_safety_tiers(self, mos, expected):
        assert self._verdict(mos=mos) == expected

    def test_non_numeric_margin_of_safety_is_pending(self):
        assert self._verdict(mos="N/A") == "PENDING"

    def test_known_defect_integer_margin_of_safety_is_pending(self):
        # Known defect: only float is accepted, so an int MoS falls through to PENDING
        assert self._verdict(mos=25) == "PENDING"

    def test_defensive_failure_with_enterprising_pass_is_enterprising_buy(self):
        defensive = {**ALL_PASS_DEFENSIVE, "pb_ratio": "FAIL"}
        assert self._verdict(mos=10.0, defensive=defensive, enterprising=ALL_PASS_ENTERPRISING) == "ENTERPRISING BUY"

    def test_known_defect_enterprising_buy_overrides_negative_margin_of_safety(self):
        defensive = {**ALL_PASS_DEFENSIVE, "pb_ratio": "FAIL"}
        assert self._verdict(mos=-80.0, defensive=defensive, enterprising=ALL_PASS_ENTERPRISING) == "ENTERPRISING BUY"

    def test_known_defect_na_results_count_as_passes(self):
        defensive = {**ALL_PASS_DEFENSIVE, "pb_ratio": "FAIL"}
        enterprising = {**ALL_PASS_ENTERPRISING, "earnings_growth": "N/A - Not Required",
                        "current_ratio": "N/A (Too Young)"}
        assert self._verdict(mos=-5.0, defensive=defensive, enterprising=enterprising) == "ENTERPRISING BUY"

    def test_all_defensive_pass_falls_through_to_margin_of_safety(self):
        assert self._verdict(mos=-5.0, defensive=ALL_PASS_DEFENSIVE,
                             enterprising=ALL_PASS_ENTERPRISING) == "OVERVALUED"

    def test_both_failing_falls_through_to_margin_of_safety(self):
        defensive = {**ALL_PASS_DEFENSIVE, "pb_ratio": "FAIL"}
        enterprising = {**ALL_PASS_ENTERPRISING, "price_test": "FAIL"}
        assert self._verdict(mos=25.0, defensive=defensive, enterprising=enterprising) == "STRONG BUY (Undervalued)"
