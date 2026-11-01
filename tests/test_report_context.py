"""M5: core.report_context — the dossier's view model, derived once and shared by every section."""

from core.report_context import build_report_context
from output.dossier_generator import DossierGenerator


def _fd(history):
    return {'history': history, 'currency': 'USD', 'price': 10.0, 'warnings': []}


def test_latest_year_skips_dividend_only_rows():
    history = {
        '2024-12-31': {'revenue': 0.0, 'net_income': 0.0, 'total_equity': 0.0, 'eps': 0.0, 'dividend': 0.5},
        '2023-12-31': {'revenue': 100.0, 'net_income': 10.0, 'total_equity': 50.0, 'eps': 1.0},
    }
    context = build_report_context(_fd(history))
    assert context.latest_year == '2023-12-31'
    assert context.latest_year_label == '2023'
    assert context.latest_row.eps == 1.0


def test_no_reported_year():
    context = build_report_context(_fd({}))
    assert context.latest_year is None and context.latest_year_label is None and context.latest_row.to_dict() == {}


def test_generator_shares_one_context_with_every_section():
    history = {'2023-12-31': {'revenue': 100.0, 'net_income': 10.0, 'total_equity': 50.0, 'eps': 1.0}}
    generator = DossierGenerator('T.US', _fd(history), {}, [])
    contexts = {id(section.context) for section in generator.sections() if hasattr(section, 'context')}
    assert contexts == {id(generator.context)}


def test_earnings_window_counts_reported_years_only():
    """Dividend-only placeholder rows are not years of results (loss years, margins)."""
    history = {f"{2023 - i}-12-31": {'revenue': 100.0, 'net_income': 10.0 if i else -5.0, 'total_equity': 50.0,
                                     'eps': 1.0, 'dividend': 0.5} for i in range(3)}
    for year in ('2024-12-31', '2025-12-31'):
        history[year] = {'revenue': 0.0, 'net_income': 0.0, 'total_equity': 0.0, 'eps': 0.0, 'dividend': 0.5}
    risk = build_report_context(_fd(history)).risk
    assert risk.window_years == 3
    assert risk.loss_years == 1
    assert len(risk.profit_margins) == 3
    assert risk.dividend_window_years == 5 and risk.dividend_years == 5  # payment years count every row


def test_book_values_and_yields():
    history = {'2023-12-31': {'revenue': 100.0, 'net_income': 10.0, 'total_equity': 500.0, 'eps': 1.0,
                              'intangible_assets': 50.0, 'goodwill': 50.0, 'shares_outstanding': 100.0,
                              'dividend': 0.4}}
    fd = {**_fd(history), 'is_dividend_amounts': True, 'forward_dividend_rate': 0.5}
    context = build_report_context(fd)
    assert (context.latest_bvps, context.latest_tangible_equity, context.latest_tbvps) == (5.0, 400.0, 4.0)
    assert context.trailing_yield_pct == 4.0 and context.forward_yield_pct == 5.0


def test_payment_counts_have_no_yield():
    history = {'2023-12-31': {'revenue': 100.0, 'net_income': 10.0, 'total_equity': 500.0, 'eps': 1.0,
                              'shares_outstanding': 100.0, 'dividend': 4.0}}
    context = build_report_context({**_fd(history), 'is_dividend_amounts': False})
    assert context.trailing_dividend == 0.0 and context.trailing_yield_pct is None
