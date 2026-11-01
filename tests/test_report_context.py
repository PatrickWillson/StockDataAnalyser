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
    assert context.latest_row['eps'] == 1.0


def test_no_reported_year():
    context = build_report_context(_fd({}))
    assert context.latest_year is None and context.latest_year_label is None and context.latest_row == {}


def test_generator_shares_one_context_with_every_section():
    history = {'2023-12-31': {'revenue': 100.0, 'net_income': 10.0, 'total_equity': 50.0, 'eps': 1.0}}
    generator = DossierGenerator('T.US', _fd(history), {}, [])
    contexts = {id(section.context) for section in generator.sections() if hasattr(section, 'context')}
    assert contexts == {id(generator.context)}
