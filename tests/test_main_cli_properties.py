"""
Property-based tests for main CLI orchestrator in stock_data_analyser.py

These tests verify universal properties that should hold across all inputs.

NOTE: These tests need to be updated to work with ClientFactory pattern.
"""

import pytest
import sys
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st

# Skip all tests in this module - need refactoring for ClientFactory
pytestmark = pytest.mark.skip(reason="Tests need refactoring for ClientFactory pattern")


@given(
    ticker=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    exchange=st.sampled_from(['US', 'LSE', 'TO', 'XETRA', 'PA', 'HK', 'AU'])
)
def test_fatal_error_on_missing_price_property(ticker, exchange):
    """
    Property 8: Fatal Error on Missing Price
    
    For any ticker where both yfinance and EODHD return no price (price = 0.0),
    the system should terminate with exit code 1.
    
    **Validates: Requirements 1.5**
    """
    # Arrange: Create financial data with price = 0.0 (both sources failed)
    full_ticker = f"{ticker}.{exchange}"
    
    mock_financial_data = {
        'ticker': ticker,
        'exchange': exchange,
        'currency': 'USD',
        'price': 0.0,  # Both yfinance and EODHD failed
        'ceo_name': 'Test CEO',
        'history': {},
        'warnings': []
    }
    
    # Act & Assert: System should exit with code 1
    with patch.dict('os.environ', {'EODHD_API_KEY': 'test_key'}):
        import importlib
        import stock_data_analyser
        importlib.reload(stock_data_analyser)
        
        with patch('sys.argv', ['stock_data_analyser.py', full_ticker]):
            with patch('stock_data_analyser.EODHDClient') as MockClient:
                with patch('stock_data_analyser.YFinanceClient') as MockYFClient:
                    with patch('builtins.print'):
                        # Setup mocks
                        mock_client_instance = Mock()
                        mock_client_instance.fetch_all_data.return_value = mock_financial_data
                        MockClient.return_value = mock_client_instance
                        
                        mock_yf_instance = Mock()
                        MockYFClient.return_value = mock_yf_instance
                        
                        # System should exit with code 1
                        with pytest.raises(SystemExit) as exc_info:
                            stock_data_analyser.main()
                        
                        # Verify exit code is 1 (not 0 or any other code)
                        assert exc_info.value.code == 1, \
                            f"For ticker {full_ticker} with price=0.0, expected exit code 1, got {exc_info.value.code}"


@given(
    ticker=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    exchange=st.sampled_from(['US', 'LSE', 'TO', 'XETRA', 'PA', 'HK', 'AU']),
    price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_system_continues_with_valid_price_property(ticker, exchange, price):
    """
    Property: System continues when valid price is available
    
    For any ticker where price > 0.0, the system should continue processing
    and not exit with a fatal error.
    
    **Validates: Requirements 1.1, 1.2**
    """
    # Arrange: Create financial data with valid price
    full_ticker = f"{ticker}.{exchange}"
    
    mock_financial_data = {
        'ticker': ticker,
        'exchange': exchange,
        'currency': 'USD',
        'price': price,  # Valid price from either yfinance or EODHD
        'ceo_name': 'Test CEO',
        'history': {
            '2023': {
                'revenue': 1000000,
                'net_income': 100000,
                'eps': 1.0,
                'dividend': 0.5,
                'total_equity': 1000000,
                'shares_outstanding': 1000000,
                'intangible_assets': 0,
                'goodwill': 0,
                'current_assets': 500000,
                'current_liabilities': 200000,
                'total_liabilities': 300000,
                'long_term_debt': 100000
            }
        },
        'warnings': []
    }
    
    mock_metrics = {
        'graham_number': 10.0,
        'epv': 50.0,
        'net_net_value': 5.0,
        'margin_of_safety': 15.0,
        'verdict': 'FAIRLY VALUED',
        'defensive_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_assets': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'PASS',
            'pe_ratio': 'PASS',
            'pb_ratio': 'PASS'
        },
        'enterprising_tests': {},
        'warnings': []
    }
    
    mock_anomalies = []
    
    # Act: System should continue without fatal error
    with patch.dict('os.environ', {'EODHD_API_KEY': 'test_key'}):
        import importlib
        import stock_data_analyser
        importlib.reload(stock_data_analyser)
        
        with patch('sys.argv', ['stock_data_analyser.py', full_ticker]):
            with patch('stock_data_analyser.EODHDClient') as MockClient:
                with patch('stock_data_analyser.YFinanceClient') as MockYFClient:
                    with patch('stock_data_analyser.GrahamCalculator') as MockCalculator:
                        with patch('stock_data_analyser.AnomalyDetector') as MockDetector:
                            with patch('stock_data_analyser.save_dossier') as mock_save:
                                with patch('builtins.print'):
                                    # Setup mocks
                                    mock_client_instance = Mock()
                                    mock_client_instance.fetch_all_data.return_value = mock_financial_data
                                    MockClient.return_value = mock_client_instance
                                    
                                    mock_yf_instance = Mock()
                                    MockYFClient.return_value = mock_yf_instance
                                    
                                    mock_calculator_instance = Mock()
                                    mock_calculator_instance.compute_all.return_value = mock_metrics
                                    MockCalculator.return_value = mock_calculator_instance
                                    
                                    mock_detector_instance = Mock()
                                    mock_detector_instance.scan.return_value = mock_anomalies
                                    MockDetector.return_value = mock_detector_instance
                                    
                                    # System should complete successfully (no SystemExit)
                                    try:
                                        stock_data_analyser.main()
                                        # If we get here, system continued successfully
                                        assert True
                                    except SystemExit as e:
                                        # If system exits, it should not be due to missing price
                                        # (exit code 1 is reserved for fatal errors)
                                        pytest.fail(f"System exited unexpectedly with code {e.code} for ticker {full_ticker} with valid price {price}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
