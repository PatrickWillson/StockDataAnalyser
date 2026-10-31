"""
Graham's seven defensive-investor criteria (GRAHAM_METHODOLOGY §4; adequate size ignored by D7).

Moved verbatim from GrahamCalculator (M4.4); the Graham alignment of each criterion is F20.
"""

from config.graham_constants import GRAHAM_MULTIPLIER
from config.investor_thresholds import DEFENSIVE
from core.formulas import tangible_equity
from core.financial_data_processor import FinancialDataProcessor
from core.investor_tests.criteria import current_ratio_test, earnings_stability, latest_financial_year


def debt_to_net_current_assets(history: dict, years: list) -> str:
    """
    Criterion 4.2 (industrials): long-term debt "should not exceed the net current assets (or
    working capital)" — LTD ≤ current assets − current liabilities.
    """
    if not years:
        return 'FAIL'
    latest_year = latest_financial_year(history, years)
    if not latest_year:
        return 'FAIL'
    long_term_debt = history[latest_year].get('long_term_debt', 0.0)
    current_assets = history[latest_year].get('current_assets', 0.0)
    current_liabilities = history[latest_year].get('current_liabilities', 0.0)
    net_current_assets = current_assets - current_liabilities
    return 'PASS' if long_term_debt <= net_current_assets else 'FAIL'


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
    """
    Criterion 4.6: "current price should not be more than 15 times average earnings of the past
    three years" — price / mean EPS of the three latest reported years ≤ max_pe. Fewer than three
    reported years, or a non-positive average: the criterion is not met.
    """
    if not years or price == 0:
        return 'FAIL'
    eps_data = FinancialDataProcessor.extract_3year_eps_data(history)
    if not eps_data['valid']:
        return 'FAIL'
    average_eps = sum(eps_data['eps_values']) / len(eps_data['eps_values'])
    if average_eps <= 0:
        return 'FAIL'
    return 'PASS' if price / average_eps <= max_pe else 'FAIL'


def pe_pb_multiples(history: dict, years: list, price: float) -> dict:
    """
    The two multiples of criterion 4.7: P/E on the three-year average EPS (the 4.6 multiplier) and
    P/B on the latest tangible book value per share (GRAHAM_METHODOLOGY §3.5). Unrounded; None
    when not computable (fewer than three reported years, non-positive average EPS or tangible book).
    """
    pe, pb = None, None
    if price > 0:
        eps_data = FinancialDataProcessor.extract_3year_eps_data(history)
        if eps_data['valid']:
            average_eps = sum(eps_data['eps_values']) / len(eps_data['eps_values'])
            if average_eps > 0:
                pe = price / average_eps
        latest_year = latest_financial_year(history, years)
        if latest_year:
            row = history[latest_year]
            shares = row.get('shares_outstanding', 0.0)
            book = tangible_equity(row.get('total_equity', 0.0), row.get('intangible_assets', 0.0),
                                   row.get('goodwill', 0.0))
            if shares > 0 and book > 0:
                pb = price / (book / shares)
    return {'pe': pe, 'pb': pb, 'product': pe * pb if pe is not None and pb is not None else None}


def pb_ratio(history: dict, years: list, price: float, max_pb: float = 1.5) -> str:
    """
    Criterion 4.7: "current price should not be more than 1½ times the book value last reported",
    or, since "a multiplier of earnings below 15 could justify a correspondingly higher multiplier
    of assets", the product of the P/E (three-year average) and P/B not above 22.5. Book value is
    tangible book value per share (§3.5).
    """
    if not years or price == 0:
        return 'FAIL'
    multiples = pe_pb_multiples(history, years, price)
    if multiples['pb'] is None:
        return 'FAIL'
    if multiples['pb'] <= max_pb:
        return 'PASS'
    product = multiples['product']
    return 'PASS' if product is not None and product <= GRAHAM_MULTIPLIER else 'FAIL'


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
