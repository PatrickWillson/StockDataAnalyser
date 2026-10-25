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
    import logging
    
    with patch('sys.argv', ['stock_data_analyser.py', 'AAPL.US']):
        with patch.object(stock_data_analyser, 'API_KEY', None):
            # Capture logging output
            with patch('logging.Logger.error') as mock_log_error:
                # Act & Assert: Run main and expect SystemExit
                with pytest.raises(SystemExit) as exc_info:
                    stock_data_analyser.main()
                
                # Verify exit code is 1
                assert exc_info.value.code == 1, f"Expected exit code 1, got {exc_info.value.code}"
                
                # Check that error message was logged
                log_calls = [str(call) for call in mock_log_error.call_args_list]
                error_logged = any('EODHD_API_KEY' in str(call) for call in log_calls)
                assert error_logged, "Expected error message about missing API key"


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
            with patch('stock_data_analyser.ClientFactory.create_eodhd_client') as mock_create_eodhd:
                with patch('stock_data_analyser.ClientFactory.create_yfinance_client') as mock_create_yf:
                    with patch('stock_data_analyser.GrahamCalculator') as MockCalculator:
                        with patch('stock_data_analyser.AnomalyDetector') as MockDetector:
                            with patch('stock_data_analyser.save_dossier') as mock_save:
                                # Setup mocks
                                mock_client_instance = Mock()
                                mock_client_instance.fetch_all_data.return_value = mock_financial_data
                                mock_create_eodhd.return_value = mock_client_instance
                                
                                mock_yf_instance = Mock()
                                mock_yf_instance.fetch_historical_prices.return_value = None  # No historical prices
                                mock_create_yf.return_value = mock_yf_instance
                                
                                mock_calculator_instance = Mock()
                                mock_calculator_instance.compute_all.return_value = mock_metrics
                                MockCalculator.return_value = mock_calculator_instance
                                
                                mock_detector_instance = Mock()
                                mock_detector_instance.scan.return_value = mock_anomalies
                                MockDetector.return_value = mock_detector_instance
                                
                                # Act: Run main
                                stock_data_analyser.main()
                                
                                # Assert: Verify US market data was fetched with yf_client
                                assert mock_client_instance.fetch_all_data.called
                                call_args = mock_client_instance.fetch_all_data.call_args
                                assert call_args[0][0] == 'AAPL.US'
                                assert 'yf_client' in call_args[1]
                                
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
            with patch('stock_data_analyser.ClientFactory.create_eodhd_client') as mock_create_eodhd:
                mock_client_instance = Mock()
                mock_client_instance.fetch_all_data.return_value = mock_financial_data_9_years
                mock_create_eodhd.return_value = mock_client_instance
                
                # Act
                import stock_data_analyser
                from clients.factory import ClientFactory
                client = ClientFactory.create_eodhd_client('test_key')
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
            with patch('stock_data_analyser.ClientFactory.create_eodhd_client') as mock_create_eodhd:
                mock_client_instance = Mock()
                mock_client_instance.fetch_all_data.return_value = mock_financial_data_10_years
                mock_create_eodhd.return_value = mock_client_instance
                
                # Act
                import stock_data_analyser
                from clients.factory import ClientFactory
                client = ClientFactory.create_eodhd_client('test_key')
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
            with patch('stock_data_analyser.ClientFactory.create_eodhd_client') as mock_create_eodhd:
                with patch('stock_data_analyser.GrahamCalculator') as MockCalculator:
                    # Setup mocks
                    mock_client_instance = Mock()
                    mock_client_instance.fetch_all_data.return_value = mock_financial_data
                    mock_create_eodhd.return_value = mock_client_instance
                    
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


def test_fatal_error_when_both_sources_fail():
    """
    Test system exits with code 1 when both yfinance and EODHD fail to provide price.
    Validates: Requirements 1.5
    """
    # Arrange: Mock financial data with price = 0.0 (both sources failed)
    mock_financial_data = {
        'ticker': 'NOPRICE',
        'exchange': 'NASDAQ',
        'currency': 'USD',
        'price': 0.0,  # Both sources failed
        'ceo_name': 'Test CEO',
        'history': {},
        'warnings': []
    }
    
    with patch.dict(os.environ, {'EODHD_API_KEY': 'test_key'}):
        import importlib
        import stock_data_analyser
        importlib.reload(stock_data_analyser)
        
        with patch('sys.argv', ['stock_data_analyser.py', 'NOPRICE.US']):
            with patch('stock_data_analyser.ClientFactory.create_eodhd_client') as mock_create_eodhd:
                with patch('stock_data_analyser.ClientFactory.create_yfinance_client') as mock_create_yf:
                    # Capture logging output
                    with patch('logging.Logger.error') as mock_log_error:
                        # Setup mocks
                        mock_client_instance = Mock()
                        mock_client_instance.fetch_all_data.return_value = mock_financial_data
                        mock_create_eodhd.return_value = mock_client_instance
                        
                        mock_yf_instance = Mock()
                        mock_yf_instance.fetch_historical_prices.return_value = None  # No historical prices
                        mock_create_yf.return_value = mock_yf_instance
                        
                        # Act & Assert: Run main and expect SystemExit
                        with pytest.raises(SystemExit) as exc_info:
                            stock_data_analyser.main()
                        
                        # Verify exit code is 1
                        assert exc_info.value.code == 1, f"Expected exit code 1, got {exc_info.value.code}"
                        
                        # Check that fatal error message was logged
                        # Get all logged text
                        all_logged_text = ' '.join([str(call[0][0]) if call[0] else '' 
                                                     for call in mock_log_error.call_args_list])
                        
                        assert 'FATAL ERROR' in all_logged_text, "Expected 'FATAL ERROR' in output"
                        assert 'Current price unavailable' in all_logged_text, "Expected 'Current price unavailable' in output"
                        assert "No data is better than wrong data" in all_logged_text, "Expected Graham quote in output"
                        assert 'EODHD' in all_logged_text, "Expected 'EODHD' in output"
                        assert 'yfinance' in all_logged_text, "Expected 'yfinance' in output"


def test_system_continues_when_eodhd_has_price():
    """
    Test system continues normally when EODHD provides price (no fallback needed).
    Validates: Requirements 1.5
    """
    # Arrange: Mock financial data with valid price from EODHD
    mock_financial_data = {
        'ticker': 'AAPL',
        'exchange': 'NASDAQ',
        'currency': 'USD',
        'price': 150.0,  # EODHD has price
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
    
    with patch.dict(os.environ, {'EODHD_API_KEY': 'test_key'}):
        import importlib
        import stock_data_analyser
        importlib.reload(stock_data_analyser)
        
        with patch('sys.argv', ['stock_data_analyser.py', 'AAPL.US']):
            with patch('stock_data_analyser.ClientFactory.create_eodhd_client') as mock_create_eodhd:
                with patch('stock_data_analyser.ClientFactory.create_yfinance_client') as mock_create_yf:
                    with patch('stock_data_analyser.GrahamCalculator') as MockCalculator:
                        with patch('stock_data_analyser.AnomalyDetector') as MockDetector:
                            with patch('stock_data_analyser.save_dossier') as mock_save:
                                # Setup mocks
                                mock_client_instance = Mock()
                                mock_client_instance.fetch_all_data.return_value = mock_financial_data
                                mock_create_eodhd.return_value = mock_client_instance
                                
                                mock_yf_instance = Mock()
                                mock_yf_instance.fetch_historical_prices.return_value = None  # No historical prices
                                mock_create_yf.return_value = mock_yf_instance
                                
                                mock_calculator_instance = Mock()
                                mock_calculator_instance.compute_all.return_value = mock_metrics
                                MockCalculator.return_value = mock_calculator_instance
                                
                                mock_detector_instance = Mock()
                                mock_detector_instance.scan.return_value = mock_anomalies
                                MockDetector.return_value = mock_detector_instance
                                
                                # Act: Run main (should not raise SystemExit)
                                stock_data_analyser.main()
                                
                                # Assert: Verify dossier was saved (system continued)
                                mock_save.assert_called_once()


def test_system_continues_when_yfinance_fallback_succeeds():
    """
    Test system continues when yfinance provides price.
    Validates: Requirements 1.5
    """
    # Arrange: Mock financial data with price from yfinance
    mock_financial_data = {
        'ticker': 'YU',
        'exchange': 'LSE',
        'currency': 'GBP',
        'price': 16.50,  # From yfinance
        'ceo_name': 'Test CEO',
        'history': {
            '2023': {
                'revenue': 100000000,
                'net_income': 10000000,
                'eps': 0.50,
                'dividend': 0.10,
                'total_equity': 50000000,
                'shares_outstanding': 20000000,
                'intangible_assets': 0,
                'goodwill': 0,
                'current_assets': 30000000,
                'current_liabilities': 20000000,
                'total_liabilities': 25000000,
                'long_term_debt': 5000000
            }
        },
        'warnings': ['Price Source: yfinance (primary source)']
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
    
    with patch.dict(os.environ, {'EODHD_API_KEY': 'test_key'}):
        import importlib
        import stock_data_analyser
        importlib.reload(stock_data_analyser)
        
        with patch('sys.argv', ['stock_data_analyser.py', 'YU.LSE']):
            with patch('stock_data_analyser.ClientFactory.create_eodhd_client') as mock_create_eodhd:
                with patch('stock_data_analyser.ClientFactory.create_yfinance_client') as mock_create_yf:
                    with patch('stock_data_analyser.GrahamCalculator') as MockCalculator:
                        with patch('stock_data_analyser.AnomalyDetector') as MockDetector:
                            with patch('stock_data_analyser.save_dossier') as mock_save:
                                # Setup mocks
                                mock_client_instance = Mock()
                                mock_client_instance.fetch_all_data.return_value = mock_financial_data
                                mock_create_eodhd.return_value = mock_client_instance
                                
                                mock_yf_instance = Mock()
                                mock_yf_instance.fetch_historical_prices.return_value = None  # No historical prices
                                mock_create_yf.return_value = mock_yf_instance
                                
                                mock_calculator_instance = Mock()
                                mock_calculator_instance.compute_all.return_value = mock_metrics
                                MockCalculator.return_value = mock_calculator_instance
                                
                                mock_detector_instance = Mock()
                                mock_detector_instance.scan.return_value = mock_anomalies
                                MockDetector.return_value = mock_detector_instance
                                
                                # Act: Run main (should not raise SystemExit)
                                stock_data_analyser.main()
                                
                                # Assert: Verify dossier was saved (system continued)
                                mock_save.assert_called_once()
                                
                                # Verify warning about yfinance is present
                                assert any('yfinance' in w for w in mock_financial_data['warnings']), \
                                    "Expected warning about yfinance"
