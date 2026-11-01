"""
Current price source: the yfinance quote only (F21), accepted only when its currency matches
EODHD's trading currency (F7). GRAHAM_METHODOLOGY §8.1.

EODHD price fields and MarketCapitalization / SharesOutstanding are never used: no usable
yfinance price means no dossier (PriceUnavailableError).
"""

from unittest.mock import Mock, patch

import pytest
from hypothesis import given, strategies as st

from clients.eodhd_client import EODHDClient
from core.errors import PriceUnavailableError
from core.financial_data_processor import FinancialDataProcessor
from core.price_quote import PriceQuote, major_currency, same_currency
from core.financial_data_assembler import load_financial_data

# Every EODHD location the old fallback chain read a price from
EODHD_PRICES = {
    'General': {'CurrencyCode': 'USD', 'SharePrice': 100.0, 'LastPrice': 100.0},
    'Highlights': {'MarketCapitalization': 1_000_000_000, 'SharePrice': 100.0},
    'SharesStats': {'SharesOutstanding': 10_000_000},
}

prices = st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)


class MockYFinanceClient:
    def __init__(self, quote=None):
        self.quote = quote
        self.ticker_received = None

    def get_quote(self, ticker):
        self.ticker_received = ticker
        return self.quote


def _fetch(ticker, payload, yf_client):
    client = EODHDClient("test_key")
    with patch.object(client, "_make_eodhd_request", return_value=payload), \
         patch.object(client, "_fetch_dividend_history", return_value=None):
        return load_financial_data(ticker, client, yf_client, Mock())


@given(price=prices)
def test_matching_quote_is_used(price):
    warnings = []
    assert FinancialDataProcessor.get_current_price(PriceQuote(price, "USD"), "USD", warnings) == (price, None)
    assert warnings == ["Price Source: yfinance (primary source)"]


@pytest.mark.parametrize("quote_ccy, trading_ccy", [
    ("GBp", "GBX"), ("GBp", "GBP"), ("GBP", "GBX"), ("ZAc", "ZAR"), ("ILA", "ILS"), ("usd", "USD"),
])
def test_minor_units_match_their_currency(quote_ccy, trading_ccy):
    price, problem = FinancialDataProcessor.get_current_price(PriceQuote(10.0, quote_ccy), trading_ccy)
    assert (price, problem) == (10.0, None)


def test_minor_unit_case_is_significant():
    """yfinance writes pence as 'GBp' and pounds as 'GBP'; both are GBP, the unit differs."""
    assert major_currency("GBp") == major_currency("GBP") == "GBP"
    assert not same_currency(None, "GBP")
    assert not same_currency("EUR", "USD")


@pytest.mark.parametrize("quote", [None, PriceQuote(0.0, "USD"), PriceQuote(-1.0, "USD")])
def test_no_positive_price_is_missing(quote):
    warnings = []
    price, problem = FinancialDataProcessor.get_current_price(quote, "USD", warnings)
    assert price == 0.0 and problem == "no price from yfinance"
    assert warnings == []


def test_quote_currency_mismatch_is_rejected():
    """A bare-symbol lookup that found another listing (e.g. a US ADR for a Paris stock)."""
    price, problem = FinancialDataProcessor.get_current_price(PriceQuote(50.0, "USD"), "EUR", source="EODHD")
    assert price == 0.0
    assert "yfinance quotes USD but EODHD trades this ticker in EUR" in problem


def test_unreported_quote_currency_is_rejected():
    price, problem = FinancialDataProcessor.get_current_price(PriceQuote(50.0, None), "EUR")
    assert price == 0.0
    assert "did not report the quote currency" in problem


@given(
    ticker=st.text(min_size=3, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    price=prices,
)
def test_ticker_passed_to_yfinance_client_and_its_price_used(ticker, price):
    """The I/O shell passes the ticker unchanged to yfinance; EODHD prices are ignored."""
    ticker = ticker + ".US"
    yf_client = MockYFinanceClient(PriceQuote(price, "USD"))
    result = _fetch(ticker, dict(EODHD_PRICES), yf_client)
    assert yf_client.ticker_received == ticker
    assert result['price'] == price
    assert result['price_source'] == 'yfinance'


@pytest.mark.parametrize("yf_client, reason", [
    (MockYFinanceClient(None), "no price from yfinance"),
    (MockYFinanceClient(PriceQuote(100.0, "EUR")), "probably a different listing"),
])
def test_no_usable_quote_means_no_dossier_even_with_eodhd_prices(yf_client, reason):
    with pytest.raises(PriceUnavailableError, match=reason):
        _fetch("AAPL.US", dict(EODHD_PRICES), yf_client)
