"""
Graham's enterprising-investor criteria (GRAHAM_METHODOLOGY §5).

Moved verbatim from GrahamCalculator (M4.4); the Graham alignment of each criterion is F20.
"""

from typing import Optional

from config.investor_thresholds import ENTERPRISING
from core.investor_tests.criteria import current_ratio_test, earnings_stability, latest_financial_year


def debt_to_net_current_assets(history: dict, years: list) -> str:
    """Criterion 5.2: debt "not more than 110% of net current assets" — LTD ≤ 1.10 × (CA − CL)."""
    if not years:
        return 'FAIL'
    latest_year = latest_financial_year(history, years)
    if not latest_year:
        return 'FAIL'
    long_term_debt = history[latest_year].get('long_term_debt', 0.0)
    current_assets = history[latest_year].get('current_assets', 0.0)
    current_liabilities = history[latest_year].get('current_liabilities', 0.0)
    max_allowed_debt = (current_assets - current_liabilities) * ENTERPRISING.MAX_DEBT_ASSETS
    return 'PASS' if long_term_debt <= max_allowed_debt else 'FAIL'


def current_dividend(history: dict, years: list) -> str:
    """A dividend in the latest financial year."""
    if not years:
        return 'FAIL'
    latest_year = latest_financial_year(history, years)
    if not latest_year:
        return 'FAIL'
    return 'PASS' if history[latest_year].get('dividend', 0.0) > 0 else 'FAIL'


def price_test(history: dict, years: list, price: float, tbvps: Optional[object]) -> str:
    """P/E below MAX_PE_RATIO or price below MAX_PB_RATIO × TBVPS (tbvps: unrounded float or "N/A")."""
    if not years or price == 0:
        return 'FAIL'
    latest_year = latest_financial_year(history, years)
    if not latest_year:
        return 'FAIL'
    eps = history[latest_year].get('eps', 0.0)
    if eps > 0 and price / eps < ENTERPRISING.MAX_PE_RATIO:
        return 'PASS'
    if isinstance(tbvps, float) and tbvps > 0 and price < tbvps * ENTERPRISING.MAX_PB_RATIO:
        return 'PASS'
    return 'FAIL'


def run_enterprising_tests(history: dict, years: list, num_years: int, price: float, tbvps) -> dict:
    """All enterprising criteria for a history with at least one year (years newest first)."""
    return {
        'earnings_stability': earnings_stability(history, years, min_years=ENTERPRISING.MIN_EARNINGS_YEARS,
                                                 period=ENTERPRISING.EARNINGS_STABILITY_YEARS),
        'current_ratio': current_ratio_test(history, years, min_ratio=ENTERPRISING.MIN_CURRENT_RATIO),
        'debt_to_assets': debt_to_net_current_assets(history, years),
        'dividend_record': current_dividend(history, years),
        'earnings_growth': 'N/A - Not Required',
        'price_test': price_test(history, years, price, tbvps),
    }


EMPTY_RESULTS = {
    'earnings_stability': 'FAIL',
    'current_ratio': 'FAIL',
    'debt_to_assets': 'FAIL',
    'dividend_record': 'FAIL',
    'earnings_growth': 'N/A - Not Required',
    'price_test': 'FAIL',
}
