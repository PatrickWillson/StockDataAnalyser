"""
F10: Highlights.BookValue is converted to the financials currency whether or not a dividend is
reported, and the BVPS cross-check compares both figures in that currency.
"""

from unittest.mock import Mock

from core.currency_converter import CurrencyConverter
from core.financial_data_assembler import FinancialDataAssembler
from core.financial_data_processor import FinancialDataProcessor
from clients.eodhd_mapper import to_fundamentals
from core.price_quote import PriceQuote
from tests.fixtures import EODHDFixtures
from tests.snapshot_scenarios import set_currencies

EUR_USD = 1.10


def _assemble(dividend_share, book_value):
    raw = set_currencies(EODHDFixtures.get_aapl_fundamentals(), "XETRA", "EUR", "USD")
    raw["Highlights"]["DividendShare"] = dividend_share
    raw["Highlights"]["BookValue"] = book_value
    fx = Mock()
    fx.get_rate.return_value = EUR_USD
    fx.fetch_historical_rates.return_value = None
    converter = CurrencyConverter(fx_client=fx)
    assembler = FinancialDataAssembler(FinancialDataProcessor(currency_converter=converter), converter, fx)
    return assembler.assemble(to_fundamentals(raw, None, "AAPL.XETRA"), "AAPL.XETRA", quote=PriceQuote(170.0, "EUR"))


def test_book_value_converted_without_a_dividend():
    fd = _assemble(dividend_share=0, book_value=4.0)
    assert fd['book_value_per_share'] == 4.0 * EUR_USD


def test_book_value_converted_with_a_dividend():
    fd = _assemble(dividend_share=0.9, book_value=4.0)
    assert fd['book_value_per_share'] == 4.0 * EUR_USD


def test_bvps_cross_check_is_in_the_financials_currency():
    fd = _assemble(dividend_share=0, book_value=10.0)  # far from equity / shares (~4) -> warning
    bv_warnings = [w for w in fd['warnings'] if 'Book Value Discrepancy' in w]
    assert len(bv_warnings) == 1
    assert f"API shows {10.0 * EUR_USD:.2f} USD" in bv_warnings[0]
    assert "subtracts intangibles" not in bv_warnings[0]
