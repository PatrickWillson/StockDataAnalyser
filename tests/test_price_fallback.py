"""
Unit tests for price fallback logic in FinancialDataProcessor.

Tests the priority order: yfinance → EODHD → 0.0
"""

from core.financial_data_processor import FinancialDataProcessor


class MockYFinanceClient:
    """Mock yfinance client for testing."""
    
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
    price, source, _ = FinancialDataProcessor.get_current_price(data, warnings=warnings)
    
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
    price, source, _ = FinancialDataProcessor.get_current_price(data, warnings=warnings)
    
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
    price, source, _ = FinancialDataProcessor.get_current_price(data, warnings=warnings)
    
    assert price == 99.99
    assert source == 'EODHD'
    assert len(warnings) == 0


def test_yfinance_primary_when_available():
    """Test yfinance is used as primary source when available."""
    data = {
        'Highlights': {
            'SharePrice': 100.00  # EODHD has a price
        }
    }
    
    yf_client = MockYFinanceClient(price_to_return=175.25)
    warnings = []
    
    price, source, _ = FinancialDataProcessor.get_current_price(
        data, 
        yf_client=yf_client, 
        ticker="AAPL.US",
        warnings=warnings
    )
    
    # yfinance should be used as primary source
    assert price == 175.25
    assert source == 'yfinance'
    assert yf_client.get_price_called
    assert yf_client.ticker_received == "AAPL.US"
    assert len(warnings) == 1
    assert "Price Source: yfinance" in warnings[0]


def test_yfinance_fallback_to_eodhd():
    """Test fallback to EODHD when yfinance fails."""
    data = {
        'Highlights': {
            'SharePrice': 100.00
        }
    }
    
    yf_client = MockYFinanceClient(price_to_return=None)  # yfinance fails
    warnings = []
    
    price, source, _ = FinancialDataProcessor.get_current_price(
        data,
        yf_client=yf_client,
        ticker="AAPL.US",
        warnings=warnings
    )
    
    # Should fall back to EODHD
    assert price == 100.00
    assert source == 'EODHD'
    assert yf_client.get_price_called
    # Should have a warning about falling back to EODHD
    assert len(warnings) == 1
    assert "EODHD" in warnings[0]


def test_warning_message_when_using_yfinance():
    """Test that warning message is added when using yfinance price."""
    data = {
        'Highlights': {},
        'General': {}
    }
    
    yf_client = MockYFinanceClient(price_to_return=50.00)
    warnings = []
    
    price, source, _ = FinancialDataProcessor.get_current_price(
        data,
        yf_client=yf_client,
        ticker="YU.LSE",
        warnings=warnings
    )
    
    assert source == 'yfinance'
    assert len(warnings) == 1
    assert "Price Source: yfinance" in warnings[0]


def test_returns_zero_when_both_sources_fail():
    """Test returns 0.0 when both yfinance and EODHD fail."""
    data = {
        'Highlights': {},
        'General': {}
    }
    
    yf_client = MockYFinanceClient(price_to_return=None)
    warnings = []
    
    price, source, _ = FinancialDataProcessor.get_current_price(
        data,
        yf_client=yf_client,
        ticker="INVALID.XX",
        warnings=warnings
    )
    
    assert price == 0.0
    assert source == 'Missing'
    assert yf_client.get_price_called
    assert len(warnings) == 0  # No warning when both fail


def test_returns_zero_when_no_yf_client_and_eodhd_missing():
    """Test returns 0.0 when EODHD missing and no yfinance client provided."""
    data = {
        'Highlights': {},
        'General': {}
    }
    
    warnings = []
    price, source, _ = FinancialDataProcessor.get_current_price(data, warnings=warnings)
    
    assert price == 0.0
    assert source == 'Missing'
    assert len(warnings) == 0


def test_yfinance_takes_priority_over_eodhd():
    """Test that yfinance price is used even when EODHD has a price."""
    data = {
        'Highlights': {
            'SharePrice': 100.00
        }
    }
    
    yf_client = MockYFinanceClient(price_to_return=200.00)
    warnings = []
    
    price, source, _ = FinancialDataProcessor.get_current_price(
        data,
        yf_client=yf_client,
        ticker="TEST.US",
        warnings=warnings
    )
    
    # yfinance should take priority
    assert price == 200.00
    assert source == 'yfinance'
    assert yf_client.get_price_called
    assert len(warnings) == 1
    assert "Price Source: yfinance" in warnings[0]


def test_sanitizes_na_values():
    """Test that 'NA' strings are sanitized to 0.0."""
    data = {
        'Highlights': {
            'SharePrice': 'NA'
        }
    }
    
    warnings = []
    price, source, _ = FinancialDataProcessor.get_current_price(data, warnings=warnings)
    
    assert price == 0.0
    assert source == 'Missing'


def test_yfinance_lse_price_used_as_is():
    """
    Test that yfinance prices for LSE stocks are used as-is.
    
    yfinance returns LSE prices in GBX (pence), same as EODHD.
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
    
    # Mock yfinance client returning price in GBX
    yf_client = MockYFinanceClient(price_to_return=1650.0)  # 1650.0 GBX from yfinance
    
    # Act
    warnings = []
    price, source, _ = FinancialDataProcessor.get_current_price(
        data,
        yf_client=yf_client,
        ticker='YU.LSE',
        warnings=warnings
    )
    
    # Assert: Price should be used as-is (no conversion)
    assert price == 1650.0, f"Expected 1650.0 GBX (no conversion), got {price}"
    assert source == 'yfinance'
    assert any('yfinance' in w for w in warnings), "Should have yfinance warning"


def test_yfinance_non_lse_price_no_conversion():
    """
    Test that yfinance prices for non-LSE stocks are used as-is.
    
    yfinance returns prices in the same currency as the exchange.
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
    
    # Mock yfinance client
    yf_client = MockYFinanceClient(price_to_return=150.50)  # USD price
    
    # Act
    warnings = []
    price, source, _ = FinancialDataProcessor.get_current_price(
        data,
        yf_client=yf_client,
        ticker='AAPL.US',
        warnings=warnings
    )
    
    # Assert: Price should be used as-is (no conversion)
    assert price == 150.50, f"Expected 150.50 USD (no conversion), got {price}"
    assert source == 'yfinance'
    assert any('yfinance' in w for w in warnings), "Should have yfinance warning"
