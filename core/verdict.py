"""
Investment verdict from the computed metrics and investor tests.

Moved verbatim from GrahamCalculator._determine_verdict (M4.4). It does not yet follow Graham:
the redesign (quality AND margin of safety, N/A never a pass) is D8 / F20, GRAHAM_METHODOLOGY §7, §9.
"""

from typing import Union

from config.valuation_config import STRONG_BUY_MIN_MOS_PCT


def determine_verdict(graham_number: Union[float, str],
                      margin_of_safety: Union[float, str],
                      epv: float,
                      defensive_tests: dict = None,
                      enterprising_tests: dict = None) -> str:
    """
    Args:
        graham_number: Graham Number or "N/A"
        margin_of_safety: Margin of Safety or "N/A"
        epv: Earnings Power Value (unused)
        defensive_tests: Results from defensive investor tests
        enterprising_tests: Results from enterprising investor tests

    Returns:
        Verdict string
    """
    # Handle negative equity case
    if graham_number == "N/A":
        return "Rely on EPV - Negative Equity"

    # Check if passes enterprising tests (if defensive fails)
    if defensive_tests and enterprising_tests:
        defensive_pass = all(v == 'PASS' or 'N/A' in str(v) for v in defensive_tests.values())
        enterprising_pass = all(v == 'PASS' or 'N/A' in str(v) for v in enterprising_tests.values())

        if not defensive_pass and enterprising_pass:
            return "ENTERPRISING BUY"

    # Handle positive margin of safety with tiers
    if isinstance(margin_of_safety, float):
        if margin_of_safety >= STRONG_BUY_MIN_MOS_PCT:
            return "STRONG BUY (Undervalued)"
        elif margin_of_safety > 0:
            return "UNDERVALUED"
        else:
            return "OVERVALUED"

    return "PENDING"
