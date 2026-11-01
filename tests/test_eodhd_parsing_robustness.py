"""
EODHD payload edge cases: nulls and junk degrade gracefully, and LSE dividend records follow
CODEBASE_GUIDE §11 E1 (amounts in pounds) on every dividend path.
"""

import pytest

from core.currency_converter import CurrencyConverter
from core.financial_data_assembler import FinancialDataAssembler
from core.financial_data_processor import FinancialDataProcessor
from clients.eodhd_mapper import dividend_payments, to_fundamentals


class _NoRates:
    def get_rate(self, from_currency, to_currency):
        return None


def _processor():
    return FinancialDataProcessor(currency_converter=CurrencyConverter(fx_client=_NoRates()))


def test_lse_dividend_records_labelled_gbx_are_pounds_in_the_history_too():
    data = {'General': {'Exchange': 'LSE', 'CurrencyCode': 'GBX'}}
    records = [{'date': '2023-06-01', 'value': 0.25, 'currency': 'GBX'}]
    history, _, is_amounts, currency, _ = _processor().parse_dividend_history(to_fundamentals(data, records))
    assert is_amounts and history == {'2023': 0.25}
    assert currency == 'GBP'


def test_dividend_record_with_null_currency_falls_back_to_the_trading_currency():
    data = {'General': {'Exchange': 'US', 'CurrencyCode': 'USD'}}
    records = [{'date': '2023-06-01', 'value': 0.25, 'currency': None}]
    *_, currency, _ = _processor().parse_dividend_history(to_fundamentals(data, records))
    assert currency == 'USD'
    _, payments, ttm_currency = _processor().calculate_ttm_dividend(dividend_payments(records, 'USD', 'US'), reference_date='2023-12-31')
    assert ttm_currency == 'USD' and payments[0]['currency'] == 'USD'


def test_null_financials_still_reads_the_dividends_array():
    data = {'General': {'CurrencyCode': 'USD'}, 'Financials': None,
            'SplitsDividends': {'Dividends': [{'Date': '2022-03-01', 'Value': 0.5}]}}
    history, _, is_amounts, _, sources = _processor().parse_dividend_history(to_fundamentals(data))
    assert is_amounts and history == {'2022': 0.5} and sources == {'2022': 'dividends_array'}


def test_cross_validation_ignores_junk_api_values():
    processor = _processor()
    assembler = FinancialDataAssembler(processor, processor.currency_converter, _NoRates())
    data = {'Highlights': {'PERatio': 'NA', 'BookValue': 'NA', 'ReturnOnEquityTTM': 'NA',
                           'ReturnOnAssetsTTM': None, 'ProfitMargin': 'junk'},
            'SharesStats': {'SharesOutstanding': 'NA'}, 'General': None}
    assert assembler._cross_validate_metrics(to_fundamentals(data), 12.0, 5.0, 0.1, 0.05, 0.2) == []


def test_52_53_week_years_get_no_phantom_dividend_rows():
    """Apple's fiscal years end 2025-09-27, 2024-09-28, 2023-09-30: each year's dividend joins its own row."""
    balance = {'2025-09-27': {'total_equity': 70.0}, '2024-09-28': {'total_equity': 57.0},
               '2023-09-30': {'total_equity': 62.0}}
    income = {end: {'revenue': 100.0, 'net_income': 10.0, 'eps': 1.0} for end in balance}
    dividends = {'2025': 1.0, '2024': 0.98, '2023': 0.94, '1995': 0.12}
    history = FinancialDataProcessor.merge_financial_data(balance, income, dividends, 15.0)
    assert sorted(history) == ['1995-09-27', '2023-09-30', '2024-09-28', '2025-09-27']
    assert history['2024-09-28']['dividend'] == 0.98


@pytest.mark.parametrize("end, label", [("2023-01-01", "2022"), ("2023-01-07", "2022"), ("2023-01-08", "2023"),
                                        ("2023-12-31", "2023"), ("2026-01-31", "2026"), ("2025-06-30", "2025"),
                                        ("2023", "2023"), ("junk", "junk")])
def test_fiscal_year_of_a_period_end(end, label):
    from core.history import fiscal_year
    assert fiscal_year(end) == label


def test_years_ending_in_early_january_belong_to_the_previous_year():
    """Johnson & Johnson: FY2022 ended 2023-01-01, FY2023 ended 2023-12-31 -> two years, not two '2023's."""
    from core.investor_tests.defensive import dividend_record
    balance = {'2023-12-31': {'total_equity': 70.0}, '2023-01-01': {'total_equity': 60.0},
               '2022-01-02': {'total_equity': 55.0}}
    income = {end: {'revenue': 100.0, 'net_income': 10.0, 'eps': 1.0} for end in balance}
    dividends = {'2023': 4.76, '2022': 4.45, '2021': 4.19}
    history = FinancialDataProcessor.merge_financial_data(balance, income, dividends, 2.6e9)
    assert sorted(history) == ['2022-01-02', '2023-01-01', '2023-12-31']
    assert history['2023-01-01']['dividend'] == 4.45          # FY2022 gets 2022's dividends
    assert history['2023-12-31']['dividend'] == 4.76
    assert history['2022-01-02']['dividend'] == 4.19
    years = sorted(history, reverse=True)
    assert dividend_record(history, years, 3) == 'FAIL'       # 3 years cannot show a 20-year record
