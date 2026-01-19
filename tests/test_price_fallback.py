"""
Unit tests for price fallback logic in FinancialDataProcessor.

Tests the priority order: EODHD → Alpha Vantage → 0.0
"""

import pytest
from core.financial_data_processor import FinancialDataProcessor


class MockAlphaVantageClient:
    """Mock Alpha Vantage client for testing."""
    
    def __init__(self, price_to_return=None):
        self.price_to_return = price_to_return
        self.get_price_called = False
        self.ticker_received = None
    
    def get_price(self, ticker):
        """Mock get_price method."""
        self.get_price_called = True
        self.ticker_received = ticker
        return self.price_to_return


def test_eodhd_price_from_highlights():
    """Test EODHD price extraction from Highlights.SharePrice."""
    data = {
        'Highlights': {
            'SharePrice': 150.50
        }
    }
    
    warnings = []
    price, source = FinancialDataProcessor.get_current_price(data, warnings=warnings)
    
    assert price == 150.50
    assert source == 'EODHD'
    assert len(warnings) == 0


def test_eodhd_price_from_general_share_price():
    """Test EODHD price extraction from General.SharePrice."""
    data = {
        'Highlights': {},
        'General': {
            'SharePrice': 200.75
        }
    }
    
    warnings = []
    price, source = FinancialDataProcessor.get_current_price(data, warnings=warnings)
    
    assert price == 200.75
    assert source == 'EODHD'
    assert len(warnings) == 0


def test_eodhd_price_from_general_last_price():
    """Test EODHD price extraction from General.LastPrice."""
    data = {
        'Highlights': {},
        'General': {
            'LastPrice': 99.99
        }
    }
    
    warnings = []
    price, source = FinancialDataProcessor.get_current_price(data, warnings=warnings)
    
    assert price == 99.99
    assert source == 'EODHD'
    assert len(warnings) == 0


def test_alphavantage_fallback_when_eodhd_missing():
    """Test Alpha Vantage fallback when EODHD price is missing."""
    data = {
        'Highlights': {},
        'General': {}
    }
    
    av_client = MockAlphaVantageClient(price_to_return=175.25)
    warnings = []
    
    price, source = FinancialDataProcessor.get_current_price(
        data, 
        av_client=av_client, 
        ticker="AAPL.US",
        warnings=warnings
    )
    
    assert price == 175.25
    assert source == 'Alpha Vantage'
    assert av_client.get_price_called
    assert av_client.ticker_received == "AAPL.US"
    assert len(warnings) == 1
    assert "Price from Alpha Vantage (EODHD price unavailable)" in warnings[0]


def test_warning_message_when_using_alphavantage():
    """Test that warning message is added when using Alpha Vantage price."""
    data = {
        'Highlights': {},
        'General': {}
    }
    
    av_client = MockAlphaVantageClient(price_to_return=50.00)
    warnings = []
    
    price, source = FinancialDataProcessor.get_current_price(
        data,
        av_client=av_client,
        ticker="YU.LSE",
        warnings=warnings
    )
    
    assert source == 'Alpha Vantage'
    assert len(warnings) == 1
    assert "Price from Alpha Vantage (EODHD price unavailable)" in warnings[0]


def test_returns_zero_when_both_sources_fail():
    """Test returns 0.0 when both EODHD and Alpha Vantage fail."""
    data = {
        'Highlights': {},
        'General': {}
    }
    
    av_client = MockAlphaVantageClient(price_to_return=None)
    warnings = []
    
    price, source = FinancialDataProcessor.get_current_price(
        data,
        av_client=av_client,
        ticker="INVALID.XX",
        warnings=warnings
    )
    
    assert price == 0.0
    assert source == 'Missing'
    assert av_client.get_price_called
    assert len(warnings) == 0  # No warning when both fail


def test_returns_zero_when_no_av_client_and_eodhd_missing():
    """Test returns 0.0 when EODHD missing and no AV client provided."""
    data = {
        'Highlights': {},
        'General': {}
    }
    
    warnings = []
    price, source = FinancialDataProcessor.get_current_price(data, warnings=warnings)
    
    assert price == 0.0
    assert source == 'Missing'
    assert len(warnings) == 0


def test_eodhd_takes_priority_over_alphavantage():
    """Test that EODHD price is used even when AV client is available."""
    data = {
        'Highlights': {
            'SharePrice': 100.00
        }
    }
    
    av_client = MockAlphaVantageClient(price_to_return=200.00)
    warnings = []
    
    price, source = FinancialDataProcessor.get_current_price(
        data,
        av_client=av_client,
        ticker="TEST.US",
        warnings=warnings
    )
    
    assert price == 100.00
    assert source == 'EODHD'
    assert not av_client.get_price_called  # Should not call AV
    assert len(warnings) == 0


def test_sanitizes_na_values():
    """Test that 'NA' strings are sanitized to 0.0."""
    data = {
        'Highlights': {
            'SharePrice': 'NA'
        }
    }
    
    warnings = []
    price, source = FinancialDataProcessor.get_current_price(data, warnings=warnings)
    
    assert price == 0.0
    assert source == 'Missing'


def test_alphavantage_lse_price_conversion():
    """
    Test that Alpha Vantage prices for LSE stocks are used as-is.
    
    Alpha Vantage returns LSE prices in GBX (pence), same as EODHD.
    No conversion is needed.
    
    Requirements: 1.1, 1.2 (Price fallback)
    """
    # Arrange: Mock LSE data with no EODHD price
    data = {
        'General': {
            'Exchange': 'LSE',
            'CurrencyCode': 'GBX'
        },
        'Highlights': {}  # No SharePrice
    }
    
    # Mock Alpha Vantage client returning price in GBX
    av_client = MockAlphaVantageClient(price_to_return=1650.0)  # 1650.0 GBX from Alpha Vantage
    
    # Act
    warnings = []
    price, source = FinancialDataProcessor.get_current_price(
        data,
        av_client=av_client,
        ticker='YU.LSE',
        warnings=warnings
    )
    
    # Assert: Price should be used as-is (no conversion)
    assert price == 1650.0, f"Expected 1650.0 GBX (no conversion), got {price}"
    assert source == 'Alpha Vantage'
    assert any('Alpha Vantage' in w for w in warnings), "Should have Alpha Vantage warning"


def test_alphavantage_non_lse_price_no_conversion():
    """
    Test that Alpha Vantage prices for non-LSE stocks are used as-is.
    
    Alpha Vantage returns prices in the same currency as the exchange.
    No conversion is needed for any exchange.
    
    Requirements: 1.1, 1.2 (Price fallback)
    """
    # Arrange: Mock US data with no EODHD price
    data = {
        'General': {
            'Exchange': 'US',
            'CurrencyCode': 'USD'
        },
        'Highlights': {}  # No SharePrice
    }
    
    # Mock Alpha Vantage client
    av_client = MockAlphaVantageClient(price_to_return=150.50)  # USD price
    
    # Act
    warnings = []
    price, source = FinancialDataProcessor.get_current_price(
        data,
        av_client=av_client,
        ticker='AAPL.US',
        warnings=warnings
    )
    
    # Assert: Price should be used as-is (no conversion)
    assert price == 150.50, f"Expected 150.50 USD (no conversion), got {price}"
    assert source == 'Alpha Vantage'
    assert any('Alpha Vantage' in w for w in warnings), "Should have Alpha Vantage warning"
