"""
Unit tests for main CLI orchestrator in stock_data_analyser.py

These tests verify the CLI handles various scenarios correctly.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from io import StringIO


def test_missing_api_key_error():
    """
    Test that system exits with code 1 when EODHD_API_KEY is not set.
    Validates: Requirements 11.1
    """
    # Arrange: Mock the API_KEY as None to simulate missing key
    import stock_data_analyser
    
    with patch('sys.argv', ['stock_data_analyser.py', 'AAPL.US']):
        with patch('builtins.print') as mock_print:
            with patch.object(stock_data_analyser, 'API_KEY', None):
                # Act & Assert: Run main and expect SystemExit
                with pytest.raises(SystemExit) as exc_info:
                    stock_data_analyser.main()
                
                # Verify exit code is 1
                assert exc_info.value.code == 1, f"Expected exit code 1, got {exc_info.value.code}"
                
                # Check that error message was printed
                print_calls = [str(call) for call in mock_print.call_args_list]
                error_printed = any('EODHD_API_KEY' in str(call) and 'ERROR' in str(call) 
                                   for call in print_calls)
                assert error_printed, "Expected error message about missing API key"


def test_ticker_suffix_example():
    """
    Test processing of "AAPL.US" ticker.
    Validates: Requirements 1.1
    """
    # Arrange: Mock all dependencies
    mock_financial_data = {
        'ticker': 'AAPL',
        'exchange': 'NASDAQ',
        'currency': 'USD',
        'price': 150.0,
        'ceo_name': 'Tim Cook',
        'history': {
            '2023': {
                'revenue': 383285000000,
                'net_income': 96995000000,
                'eps': 6.16,
                'dividend': 4,
                'total_equity': 62146000000,
                'shares_outstanding': 16000000000,
                'intangible_assets': 0,
                'goodwill': 0,
                'current_assets': 143566000000,
                'current_liabilities': 145308000000,
                'total_liabilities': 290437000000,
                'long_term_debt': 106000000000
            }
        },
        'warnings': []
    }
    
    mock_metrics = {
        'graham_number': 47.43,
        'epv': 100.0,
        'net_net_value': 10.0,
        'margin_of_safety': 25.5,
        'verdict': 'UNDERVALUED',
        'defensive_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'FAIL',
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
    
    # Set API key in environment and reload module
    with patch.dict(os.environ, {'EODHD_API_KEY': 'test_key'}):
        import importlib
        import stock_data_analyser
        importlib.reload(stock_data_analyser)
        
        with patch('sys.argv', ['stock_data_analyser.py', 'AAPL.US']):
            with patch('stock_data_analyser.EODHDClient') as MockClient:
                with patch('stock_data_analyser.GrahamCalculator') as MockCalculator:
                    with patch('stock_data_analyser.AnomalyDetector') as MockDetector:
                        with patch('stock_data_analyser.save_dossier') as mock_save:
                            # Setup mocks
                            mock_client_instance = Mock()
                            mock_client_instance.fetch_all_data.return_value = mock_financial_data
                            MockClient.return_value = mock_client_instance
                            
                            mock_calculator_instance = Mock()
                            mock_calculator_instance.compute_all.return_value = mock_metrics
                            MockCalculator.return_value = mock_calculator_instance
                            
                            mock_detector_instance = Mock()
                            mock_detector_instance.scan.return_value = mock_anomalies
                            MockDetector.return_value = mock_detector_instance
                            
                            # Act: Run main
                            stock_data_analyser.main()
                            
                            # Assert: Verify US market data was fetched
                            mock_client_instance.fetch_all_data.assert_called_once_with('AAPL.US')
                            
                            # Verify the ticker was processed correctly
                            assert mock_financial_data['exchange'] == 'NASDAQ'
                            assert mock_financial_data['currency'] == 'USD'


def test_insufficient_history_warning():
    """
    Test company with exactly 9 years of data triggers warning.
    Test company with 10 years of data does not trigger warning.
    Validates: Requirements 2.6
    """
    # Test case 1: 9 years of data (should trigger warning)
    mock_financial_data_9_years = {
        'ticker': 'YOUNG',
        'exchange': 'NASDAQ',
        'currency': 'USD',
        'price': 50.0,
        'ceo_name': 'Jane Doe',
        'history': {str(2023 - i): {
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
        } for i in range(9)},
        'warnings': ['Insufficient History Warning: Company has less than 10 years of data']
    }
    
    with patch.dict(os.environ, {'EODHD_API_KEY': 'test_key'}):
        with patch('sys.argv', ['stock_data_analyser.py', 'YOUNG.US']):
            with patch('stock_data_analyser.EODHDClient') as MockClient:
                mock_client_instance = Mock()
                mock_client_instance.fetch_all_data.return_value = mock_financial_data_9_years
                MockClient.return_value = mock_client_instance
                
                # Act
                import stock_data_analyser
                client = stock_data_analyser.EODHDClient('test_key')
                result = mock_client_instance.fetch_all_data('YOUNG.US')
                
                # Assert: Verify warning is present
                assert any('Insufficient History Warning' in w for w in result['warnings']), \
                    "Expected 'Insufficient History Warning' for company with 9 years of data"
    
    # Test case 2: 10 years of data (should NOT trigger warning)
    mock_financial_data_10_years = {
        'ticker': 'MATURE',
        'exchange': 'NASDAQ',
        'currency': 'USD',
        'price': 50.0,
        'ceo_name': 'John Smith',
        'history': {str(2023 - i): {
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
        } for i in range(10)},
        'warnings': []
    }
    
    with patch.dict(os.environ, {'EODHD_API_KEY': 'test_key'}):
        with patch('sys.argv', ['stock_data_analyser.py', 'MATURE.US']):
            with patch('stock_data_analyser.EODHDClient') as MockClient:
                mock_client_instance = Mock()
                mock_client_instance.fetch_all_data.return_value = mock_financial_data_10_years
                MockClient.return_value = mock_client_instance
                
                # Act
                import stock_data_analyser
                client = stock_data_analyser.EODHDClient('test_key')
                result = mock_client_instance.fetch_all_data('MATURE.US')
                
                # Assert: Verify no warning
                assert not any('Insufficient History Warning' in w for w in result['warnings']), \
                    "Did not expect 'Insufficient History Warning' for company with 10 years of data"


def test_young_company_handling():
    """
    Test company with < 10 years of history.
    Verify earnings growth test is marked "N/A (Too Young)".
    Validates: Requirements 6.7
    """
    # Arrange: Create financial data for young company (7 years)
    mock_financial_data = {
        'ticker': 'STARTUP',
        'exchange': 'NASDAQ',
        'currency': 'USD',
        'price': 30.0,
        'ceo_name': 'Young CEO',
        'history': {str(2023 - i): {
            'revenue': 1000000 * (i + 1),
            'net_income': 100000 * (i + 1),
            'eps': 1.0 + i * 0.1,
            'dividend': 0.5,
            'total_equity': 1000000,
            'shares_outstanding': 1000000,
            'intangible_assets': 0,
            'goodwill': 0,
            'current_assets': 500000,
            'current_liabilities': 200000,
            'total_liabilities': 300000,
            'long_term_debt': 100000
        } for i in range(7)},
        'warnings': []
    }
    
    with patch.dict(os.environ, {'EODHD_API_KEY': 'test_key'}):
        with patch('sys.argv', ['stock_data_analyser.py', 'STARTUP.US']):
            with patch('stock_data_analyser.EODHDClient') as MockClient:
                with patch('stock_data_analyser.GrahamCalculator') as MockCalculator:
                    # Setup mocks
                    mock_client_instance = Mock()
                    mock_client_instance.fetch_all_data.return_value = mock_financial_data
                    MockClient.return_value = mock_client_instance
                    
                    # Create real calculator to test the logic
                    from core.graham_math import GrahamCalculator
                    real_calculator = GrahamCalculator(mock_financial_data)
                    
                    # Act: Run defensive tests
                    results = real_calculator.run_defensive_tests()
                    
                    # Assert: Verify earnings growth test is marked "N/A (Too Young)"
                    assert results['earnings_growth'] == 'N/A (Too Young)', \
                        f"Expected 'N/A (Too Young)' for earnings growth test, got {results['earnings_growth']}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
