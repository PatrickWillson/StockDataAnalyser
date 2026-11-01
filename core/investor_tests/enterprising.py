"""
Graham's enterprising-investor criteria (GRAHAM_METHODOLOGY §5).

Moved verbatim from GrahamCalculator (M4.4); the Graham alignment of each criterion is F20.
"""

from typing import Optional

from config.investor_thresholds import ENTERPRISING
from core.history import has_statement_data
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
    """
    Criteria 5.1 and 5.6 together (GRAHAM_METHODOLOGY §5: all criteria apply together): a low
    multiplier, P/E on the latest EPS below MAX_PE_RATIO, AND price below MAX_PB_RATIO (120%) of
    net tangible assets per share (tbvps: unrounded float or "N/A").
    """
    if not years or price == 0:
        return 'FAIL'
    latest_year = latest_financial_year(history, years)
    if not latest_year:
        return 'FAIL'
    eps = history[latest_year].get('eps', 0.0)
    low_multiple = eps > 0 and price / eps < ENTERPRISING.MAX_PE_RATIO
    below_assets = isinstance(tbvps, float) and tbvps > 0 and price < tbvps * ENTERPRISING.MAX_PB_RATIO
    return 'PASS' if low_multiple and below_assets else 'FAIL'


def earnings_growth(history: dict, years: list) -> str:
    """
    Criterion 5.5: "last year's earnings more than those of 1966" (five years earlier in Graham's
    1971 data) — the latest reported EPS above the EPS of the reported year EARNINGS_GROWTH_YEARS
    earlier. Fewer reported years: the criterion is not met.
    """
    reported = [year for year in years if has_statement_data(history[year])]
    if len(reported) <= ENTERPRISING.EARNINGS_GROWTH_YEARS:
        return 'FAIL'
    latest_eps = history[reported[0]].get('eps', 0.0)
    earlier_eps = history[reported[ENTERPRISING.EARNINGS_GROWTH_YEARS]].get('eps', 0.0)
    return 'PASS' if latest_eps > earlier_eps else 'FAIL'


def run_enterprising_tests(history: dict, years: list, num_years: int, price: float, tbvps) -> dict:
    """All enterprising criteria for a history with at least one year (years newest first)."""
    return {
        'earnings_stability': earnings_stability(history, years, min_years=ENTERPRISING.MIN_EARNINGS_YEARS,
                                                 period=ENTERPRISING.EARNINGS_STABILITY_YEARS),
        'current_ratio': current_ratio_test(history, years, min_ratio=ENTERPRISING.MIN_CURRENT_RATIO),
        'debt_to_assets': debt_to_net_current_assets(history, years),
        'dividend_record': current_dividend(history, years),
        'earnings_growth': earnings_growth(history, years),
        'price_test': price_test(history, years, price, tbvps),
    }


EMPTY_RESULTS = {
    'earnings_stability': 'FAIL',
    'current_ratio': 'FAIL',
    'debt_to_assets': 'FAIL',
    'dividend_record': 'FAIL',
    'earnings_growth': 'FAIL',
    'price_test': 'FAIL',
}
