"""
Pins down every place where output depends on the current date.

Uses time-machine (see requirements-dev.txt) to fix "now". Each test proves that
behaviour follows the pinned date, so snapshot tests can rely on
@pytest.mark.time_machine(..., tick=False) for reproducible dossiers.

Times are timezone-aware UTC at noon so local timezone offsets cannot move the date.
"""

from datetime import datetime, timezone

import pytest

from clients.eodhd_client import EODHDClient
from core.financial_data_processor import FinancialDataProcessor
from core.ttm_calculator import TTMCalculator
from output.dossier_generator import DossierGenerator

PINNED = datetime(2026, 1, 31, 12, 0, tzinfo=timezone.utc)


@pytest.mark.time_machine(PINNED, tick=False)
def test_dossier_header_date():
    financial_data = {'currency': 'USD', 'original_stock_currency': 'USD', 'history': {},
                      'warnings': [], 'price': 10.0}
    header = DossierGenerator('TEST.US', financial_data, {}, [])._generate_header()
    assert '# DATE: 2026-01-31' in header


@pytest.mark.time_machine(PINNED, tick=False)
def test_api_staleness_warning():
    client = EODHDClient('test_key', fx_client=object())
    data = {'General': {'UpdatedAt': '2026-01-01'}}

    warnings = client._cross_validate_metrics(data, 0.0, 0.0, 0.0, 0.0, 0.0)

    assert any('API data is 30 days old' in w for w in warnings)


@pytest.mark.time_machine(PINNED, tick=False)
def test_ttm_dividend_window():
    processor = FinancialDataProcessor(currency_converter=object())
    dividends = [
        {'paymentDate': '2026-01-15', 'value': 0.25, 'currency': 'USD'},   # inside 365 days
        {'paymentDate': '2025-02-15', 'value': 0.25, 'currency': 'USD'},   # inside
        {'paymentDate': '2025-01-15', 'value': 0.25, 'currency': 'USD'},   # outside (cutoff 2025-01-31)
    ]

    total, payments, _ = processor.calculate_ttm_dividend(dividends)

    assert total == 0.5
    assert [p['date'] for p in payments] == ['2026-01-15', '2025-02-15']


def test_data_staleness_default_date(time_machine):
    history = {'2024-12-31': {'revenue': 1.0}}

    time_machine.move_to(PINNED, tick=False)  # 13 months after the report
    assert FinancialDataProcessor.check_data_staleness(history) is not None

    time_machine.move_to(datetime(2025, 3, 1, 12, 0, tzinfo=timezone.utc), tick=False)
    assert FinancialDataProcessor.check_data_staleness(history) is None


def test_ttm_future_date_limit(time_machine):
    calculator = TTMCalculator({'balance_sheet': {}, 'income_statement': {}}, 10.0, 'USD')

    time_machine.move_to(PINNED, tick=False)
    assert calculator._validate_date_ranges(['2027-06-30']) is True   # limit is 2027-12-31

    time_machine.move_to(datetime(2025, 1, 31, 12, 0, tzinfo=timezone.utc), tick=False)
    assert calculator._validate_date_ranges(['2027-06-30']) is False  # limit is 2026-12-31
