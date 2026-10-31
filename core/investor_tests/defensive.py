"""
Graham's seven defensive-investor criteria (GRAHAM_METHODOLOGY §4; adequate size ignored by D7).

Moved verbatim from GrahamCalculator (M4.4); the Graham alignment of each criterion is F20.
"""

from config.investor_thresholds import DEFENSIVE
from core.investor_tests.criteria import current_ratio_test, earnings_stability, latest_financial_year


def debt_to_net_current_assets(history: dict, years: list) -> str:
    """Long-term debt below net current assets (current assets − current liabilities)."""
    if not years:
        return 'FAIL'
    latest_year = latest_financial_year(history, years)
    if not latest_year:
        return 'FAIL'
    long_term_debt = history[latest_year].get('long_term_debt', 0.0)
    current_assets = history[latest_year].get('current_assets', 0.0)
    current_liabilities = history[latest_year].get('current_liabilities', 0.0)
    net_current_assets = current_assets - current_liabilities
    return 'PASS' if long_term_debt < net_current_assets else 'FAIL'


def dividend_record(history: dict, years: list, num_years: int) -> str:
    """Dividend paid in every one of the latest min(num_years, 20) years."""
    years_to_check = min(num_years, DEFENSIVE.MIN_DIVIDEND_YEARS)
    for year in years[:years_to_check]:
        if history[year].get('dividend', 0.0) <= 0:
            return 'FAIL'
    return 'PASS'


def earnings_growth(history: dict, years: list, num_years: int) -> str:
    """Latest net income at least MIN_EARNINGS_GROWTH × that of the 10th financial year back."""
    if num_years < DEFENSIVE.EARNINGS_GROWTH_YEARS:
        return 'N/A (Too Young)'
    latest_year = latest_financial_year(history, years)
    if not latest_year:
        return 'FAIL'
    # The 10th financial year before the latest (dividend-only years skipped)
    financial_years = [y for y in years if latest_financial_year(history, [y])]
    if len(financial_years) < DEFENSIVE.EARNINGS_GROWTH_YEARS:
        return 'N/A (Too Young)'
    oldest_year = financial_years[DEFENSIVE.EARNINGS_GROWTH_YEARS - 1]
    old_earnings = history[oldest_year].get('net_income', 0.0)
    recent_earnings = history[latest_year].get('net_income', 0.0)
    if old_earnings <= 0:
        return 'FAIL'
    return 'PASS' if recent_earnings / old_earnings >= DEFENSIVE.MIN_EARNINGS_GROWTH else 'FAIL'


def pe_ratio(history: dict, years: list, price: float, max_pe: float = 15) -> str:
    """Price / latest EPS below max_pe."""
    if not years or price == 0:
        return 'FAIL'
    latest_year = latest_financial_year(history, years)
    if not latest_year:
        return 'FAIL'
    eps = history[latest_year].get('eps', 0.0)
    if eps <= 0:
        return 'FAIL'
    return 'PASS' if price / eps < max_pe else 'FAIL'


def pb_ratio(history: dict, years: list, price: float, max_pb: float = 1.5) -> str:
    """Price / latest (total-equity) book value per share below max_pb."""
    if not years or price == 0:
        return 'FAIL'
    latest_year = latest_financial_year(history, years)
    if not latest_year:
        return 'FAIL'
    total_equity = history[latest_year].get('total_equity', 0.0)
    shares_outstanding = history[latest_year].get('shares_outstanding', 0.0)
    if shares_outstanding == 0 or total_equity <= 0:
        return 'FAIL'
    book_value_per_share = total_equity / shares_outstanding
    return 'PASS' if price / book_value_per_share < max_pb else 'FAIL'


def run_defensive_tests(history: dict, years: list, num_years: int, price: float) -> dict:
    """All defensive criteria for a history with at least one year (years newest first)."""
    return {
        'earnings_stability': earnings_stability(history, years, min_years=DEFENSIVE.MIN_EARNINGS_YEARS,
                                                 period=DEFENSIVE.EARNINGS_STABILITY_YEARS),
        'current_ratio': current_ratio_test(history, years, min_ratio=DEFENSIVE.MIN_CURRENT_RATIO),
        'debt_to_assets': debt_to_net_current_assets(history, years),
        'dividend_record': dividend_record(history, years, num_years),
        'earnings_growth': earnings_growth(history, years, num_years),
        'pe_ratio': pe_ratio(history, years, price, max_pe=DEFENSIVE.MAX_PE_RATIO),
        'pb_ratio': pb_ratio(history, years, price, max_pb=DEFENSIVE.MAX_PB_RATIO),
    }


EMPTY_RESULTS = {
    'earnings_stability': 'FAIL',
    'current_ratio': 'FAIL',
    'debt_to_assets': 'FAIL',
    'dividend_record': 'FAIL',
    'earnings_growth': 'FAIL',
    'pe_ratio': 'FAIL',
    'pb_ratio': 'FAIL',
}
