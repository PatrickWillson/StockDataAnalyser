"""
Investment verdict (design D8, GRAHAM_METHODOLOGY §7).

Graham's principles: a purchase needs both a qualifying company (the investor's criteria) and a
margin of safety; "N/A" is never evidence of quality; net-current-asset bargains are their own
category; a price above conservative value is never a buy. Rules are evaluated in order and the
first match wins; the reason says which rule fired and, where relevant, which criteria failed.
"""

from typing import Dict, Optional, Union

# Graham: buy at no more than two-thirds of net current asset value (GRAHAM_METHODOLOGY §3.3)
NET_NET_MAX_PRICE_FRACTION = 2 / 3

INSUFFICIENT_DATA = "INSUFFICIENT DATA"
NET_NET_BARGAIN = "NET-NET BARGAIN"
OVERVALUED = "OVERVALUED"
DEFENSIVE_BUY = "DEFENSIVE BUY"
ENTERPRISING_BUY = "ENTERPRISING BUY"
FAILS_CRITERIA = "UNDERVALUED – FAILS GRAHAM CRITERIA"

TEST_NAMES = {
    'earnings_stability': "earnings stability", 'current_ratio': "current ratio",
    'debt_to_assets': "debt", 'dividend_record': "dividend record", 'earnings_growth': "earnings growth",
    'pe_ratio': "P/E", 'pb_ratio': "P/B", 'price_test': "price",
}


def _not_passed(tests: Optional[dict]) -> list:
    """Criteria that did not PASS ("N/A" never counts as a pass)."""
    return [TEST_NAMES.get(name, name) for name, result in (tests or {}).items() if result != 'PASS']


def determine_verdict(margin_of_safety_details: dict, net_net_value: Union[float, str, None], price: float,
                      defensive_tests: Optional[dict], enterprising_tests: Optional[dict]) -> Dict[str, str]:
    """
    Args:
        margin_of_safety_details: GrahamCalculator.compute_margin_of_safety result
        net_net_value: Unrounded NCAV per share, or "N/A"
        price: Current price (unified currency)
        defensive_tests, enterprising_tests: criterion name -> 'PASS' / 'FAIL' / 'N/A ...'

    Returns:
        {'verdict': one of the constants above, 'reason': explanation for the dossier}
    """
    intrinsic_value = margin_of_safety_details.get('intrinsic_value_used', "N/A")
    mos = margin_of_safety_details.get('mos_percentage', "N/A")
    note = margin_of_safety_details.get('note')

    # 1. No conservative value to compare the price with
    if not isinstance(intrinsic_value, (int, float)):
        return {'verdict': INSUFFICIENT_DATA,
                'reason': f"No usable intrinsic value ({note or 'normalized Graham Number and EPV unavailable'})"}

    # 2. Graham's net-current-asset bargain
    if isinstance(net_net_value, (int, float)) and net_net_value > 0 and price <= NET_NET_MAX_PRICE_FRACTION * net_net_value:
        return {'verdict': NET_NET_BARGAIN,
                'reason': (f"Price {price:.2f} is at most two-thirds of net current asset value per share "
                           f"({net_net_value:.2f}); Graham bought such issues as a diversified group")}

    # 3. A price at or above conservative value is never a buy
    if not isinstance(mos, (int, float)) or mos <= 0:
        detail = f"margin of safety {mos:.1f}%" if isinstance(mos, (int, float)) else (note or "no margin of safety")
        return {'verdict': OVERVALUED, 'reason': f"Price is not below conservative intrinsic value ({detail})"}

    # 4-5. Margin of safety AND a qualifying company
    defensive_failed = _not_passed(defensive_tests)
    enterprising_failed = _not_passed(enterprising_tests)
    if defensive_tests and not defensive_failed:
        return {'verdict': DEFENSIVE_BUY,
                'reason': f"Margin of safety {mos:.1f}% and all defensive criteria passed"}
    if enterprising_tests and not enterprising_failed:
        return {'verdict': ENTERPRISING_BUY,
                'reason': (f"Margin of safety {mos:.1f}% and all enterprising criteria passed "
                           f"(defensive not passed: {', '.join(defensive_failed) or 'none run'})")}

    # 6. Cheap, but not a company Graham's criteria qualify
    return {'verdict': FAILS_CRITERIA,
            'reason': (f"Margin of safety {mos:.1f}%, but criteria not passed — defensive: "
                       f"{', '.join(defensive_failed) or 'none run'}; enterprising: "
                       f"{', '.join(enterprising_failed) or 'none run'}")}
