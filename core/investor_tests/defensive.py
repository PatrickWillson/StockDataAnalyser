"""
Graham's seven defensive-investor criteria (GRAHAM_METHODOLOGY §4; adequate size ignored by D7).

Moved verbatim from GrahamCalculator (M4.4); the Graham alignment of each criterion is F20.
"""

from config.graham_constants import GRAHAM_MULTIPLIER
from config.investor_thresholds import DEFENSIVE, REGULATED_UTILITY_INDUSTRIES
from core.formulas import tangible_equity
from core.financial_data_processor import FinancialDataProcessor
from core.history import has_statement_data
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
    """
    Criterion 4.4: "uninterrupted payments for at least the past 20 years". Every one of the 20
    calendar years ending with the newest year must have a row with a dividend (a payment count
    above 0 also shows a payment). Fewer years of data, or a missing year, cannot confirm an
    uninterrupted record, so the criterion is not met.
    """
    if not years:
        return 'FAIL'
    paid_years = {year[:4] for year in years if history[year].get('dividend', 0.0) > 0}
    newest = int(max(year[:4] for year in years))
    required = [str(newest - offset) for offset in range(DEFENSIVE.MIN_DIVIDEND_YEARS)]
    return 'PASS' if all(year in paid_years for year in required) else 'FAIL'


def earnings_growth(history: dict, years: list, num_years: int) -> str:
    """
    Criterion 4.5: "a minimum increase of at least one-third in per-share earnings in the past ten
    years using three-year averages at the beginning and end" — mean EPS of the latest three
    reported years ≥ 4/3 × mean EPS of the reported years 9-11 back (window: user decision
    2026-11-01, GRAHAM_METHODOLOGY §4.5). Fewer than 12 reported years: "N/A (Too Young)", which
    the verdict does not count as a pass. A non-positive base average fails.
    """
    reported = [year for year in years if has_statement_data(history[year])]
    span = DEFENSIVE.EARNINGS_GROWTH_AVERAGE_YEARS
    base_start = DEFENSIVE.EARNINGS_GROWTH_BASE_OFFSET
    if len(reported) < base_start + span:
        return 'N/A (Too Young)'

    def average_eps(selected):
        return sum(history[year].get('eps', 0.0) for year in selected) / len(selected)

    recent = average_eps(reported[:span])
    base = average_eps(reported[base_start:base_start + span])
    if base <= 0:
        return 'FAIL'
    return 'PASS' if recent >= DEFENSIVE.MIN_EARNINGS_GROWTH * base else 'FAIL'


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


NOT_APPLICABLE_UTILITY = 'NOT APPLICABLE (public utility)'


def is_public_utility(industry) -> bool:
    """Graham's public utilities: EODHD's regulated-utility industries only (GRAHAM_METHODOLOGY §4.2)."""
    return industry in REGULATED_UTILITY_INDUSTRIES


def utility_debt_to_equity(history: dict, years: list) -> str:
    """
    Criterion 4.2 for public utilities: debt not more than twice the stock equity at book value.
    Total debt (short- and long-term incl. leases) is used for Graham's unqualified "debt" — the
    conservative reading (§8.4); equity is total stockholders' equity (user decision 2026-11-01).
    """
    if not years:
        return 'FAIL'
    latest_year = latest_financial_year(history, years)
    if not latest_year:
        return 'FAIL'
    equity = history[latest_year].get('total_equity', 0.0)
    if equity <= 0:
        return 'FAIL'
    total_debt = history[latest_year].get('total_debt', 0.0)
    return 'PASS' if total_debt <= DEFENSIVE.UTILITY_MAX_DEBT_TO_EQUITY * equity else 'FAIL'


def run_defensive_tests(history: dict, years: list, num_years: int, price: float, industry=None) -> dict:
    """All defensive criteria for a history with at least one year (years newest first)."""
    utility = is_public_utility(industry)
    return {
        'earnings_stability': earnings_stability(history, years, min_years=DEFENSIVE.MIN_EARNINGS_YEARS,
                                                 period=DEFENSIVE.EARNINGS_STABILITY_YEARS),
        # Graham drops the current-ratio test for public utilities
        'current_ratio': NOT_APPLICABLE_UTILITY if utility else
                         current_ratio_test(history, years, min_ratio=DEFENSIVE.MIN_CURRENT_RATIO),
        'debt_to_assets': utility_debt_to_equity(history, years) if utility else
                          debt_to_net_current_assets(history, years),
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
