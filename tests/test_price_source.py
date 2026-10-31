"""
Current price source: yfinance only (F21, GRAHAM_METHODOLOGY §8.1).

EODHD price fields and MarketCapitalization / SharesOutstanding are never used: no yfinance
price means no dossier (PriceUnavailableError).
"""

from unittest.mock import Mock, patch

import pytest
from hypothesis import given, strategies as st

from clients.eodhd_client import EODHDClient
from core.errors import PriceUnavailableError
from core.financial_data_processor import FinancialDataProcessor

# Every EODHD location the old fallback chain read a price from
EODHD_PRICES = {
    'Highlights': {'MarketCapitalization': 1_000_000_000, 'SharePrice': 100.0},
    'SharesStats': {'SharesOutstanding': 10_000_000},
    'General': {'SharePrice': 100.0, 'LastPrice': 100.0},
}


class MockYFinanceClient:
    def __init__(self, price_to_return=None):
        self.price_to_return = price_to_return
        self.ticker_received = None

    def get_price(self, ticker):
        self.ticker_received = ticker
        return self.price_to_return


def _fetch(ticker, payload, yf_client):
    client = EODHDClient("test_key", fx_client=Mock())
    with patch.object(client, "_make_eodhd_request", return_value=payload), \
         patch.object(client, "_fetch_dividend_history", return_value=None):
        return client.fetch_all_data(ticker, yf_client=yf_client)


@given(yf_price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False))
def test_positive_yfinance_price_is_used(yf_price):
    warnings = []
    assert FinancialDataProcessor.get_current_price(yf_price, warnings) == (yf_price, 'yfinance')
    assert warnings == ["Price Source: yfinance (primary source)"]


@pytest.mark.parametrize("invalid", [None, 0, 0.0, -1, -100.5])
def test_invalid_yfinance_price_is_missing(invalid):
    warnings = []
    assert FinancialDataProcessor.get_current_price(invalid, warnings) == (0.0, 'Missing')
    assert warnings == []


@given(
    ticker=st.text(min_size=3, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    yf_price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False),
)
def test_ticker_passed_to_yfinance_client_and_its_price_used(ticker, yf_price):
    """The I/O shell passes the ticker unchanged to yfinance; EODHD prices are ignored."""
    ticker = ticker + ".US"
    yf_client = MockYFinanceClient(price_to_return=yf_price)
    result = _fetch(ticker, dict(EODHD_PRICES), yf_client)
    assert yf_client.ticker_received == ticker
    assert result['price'] == yf_price
    assert result['price_source'] == 'yfinance'


@pytest.mark.parametrize("yf_client", [None, MockYFinanceClient(price_to_return=None)])
def test_no_yfinance_price_means_no_dossier_even_with_eodhd_prices(yf_client):
    with pytest.raises(PriceUnavailableError, match="unavailable from yfinance"):
        _fetch("AAPL.US", dict(EODHD_PRICES), yf_client)
