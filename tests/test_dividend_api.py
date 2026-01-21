"""
Tests for EODHD Dividend API integration.

Tests the priority-based dividend data sourcing:
1. EODHD Dividend API (primary)
2. Cash Flow dividendsPaid (fallback)
3. ForwardAnnualDividendRate (last resort)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from core.financial_data_processor import FinancialDataProcessor


class TestDividendAPIIntegration:
    """Test Dividend API integration and fallback behavior."""
    
    def test_dividend_api_data_takes_priority_over_cash_flow(self):
        """Test that Dividend API data is used when available, even if Cash Flow data exists."""
        processor = FinancialDataProcessor(debug=False)
        
        # Mock fundamentals data with Cash Flow dividends
        fundamentals_data = {
            'General': {'CurrencyCode': 'USD'},
            'SplitsDividends': {'ForwardAnnualDividendRate': 2.50},
            'Financials': {
                'Cash_Flow': {
                    'currency_symbol': 'USD',
                    'yearly': {
                        '2024-12-31': {'dividendsPaid': '1000000.00'},
                        '2023-12-31': {'dividendsPaid': '900000.00'}
                    }
                }
            },
            'outstandingShares': {
                'annual': {
                    '0': {'date': '2024', 'shares': 1000000},
                    '1': {'date': '2023', 'shares': 1000000}
                }
            }
        }
        
        # Mock Dividend API data (declared dividends)
        dividend_api_data = [
            {'date': '2024-06-15', 'value': 1.25, 'paymentDate': '2024-07-01', 'currency': 'USD'},
            {'date': '2024-12-15', 'value': 1.10, 'paymentDate': '2024-12-31', 'currency': 'USD'},  # Paid in 2024
            {'date': '2023-06-15', 'value': 1.10, 'paymentDate': '2023-07-01', 'currency': 'USD'},
            {'date': '2023-12-15', 'value': 1.10, 'paymentDate': '2023-12-31', 'currency': 'USD'}  # Paid in 2023
        ]
        
        result, forward_rate, is_amount, currency, sources = processor.parse_dividend_history(
            fundamentals_data, 
            dividend_api_data=dividend_api_data
        )
        
        # Should use Dividend API data (2.35 for 2024, 2.20 for 2023) not Cash Flow (1.00 per year)
        assert result['2024'] == 2.35  # 1.25 + 1.10
        assert result['2023'] == 2.20  # 1.10 + 1.10
        assert sources['2024'] == 'dividend_api'
        assert sources['2023'] == 'dividend_api'
        assert is_amount is True
        assert currency == 'USD'
    
    def test_falls_back_to_cash_flow_when_dividend_api_unavailable(self):
        """Test that system falls back to Cash Flow when Dividend API returns None."""
        processor = FinancialDataProcessor(debug=False)
        
        fundamentals_data = {
            'General': {'CurrencyCode': 'USD'},
            'SplitsDividends': {'ForwardAnnualDividendRate': 2.50},
            'Financials': {
                'Cash_Flow': {
                    'currency_symbol': 'USD',
                    'yearly': {
                        '2024-12-31': {'dividendsPaid': '1000000.00'},
                        '2023-12-31': {'dividendsPaid': '900000.00'}
                    }
                }
            },
            'outstandingShares': {
                'annual': {
                    '0': {'date': '2024', 'shares': 1000000},
                    '1': {'date': '2023', 'shares': 1000000}
                }
            }
        }
        
        # Dividend API unavailable (None)
        result, forward_rate, is_amount, currency, sources = processor.parse_dividend_history(
            fundamentals_data, 
            dividend_api_data=None
        )
        
        # Should use Cash Flow data
        assert result['2024'] == 1.00  # 1000000 / 1000000
        assert result['2023'] == 0.90  # 900000 / 1000000
        assert sources['2024'] == 'cash_flow'
        assert sources['2023'] == 'cash_flow'
    
    def test_dividend_api_aggregates_multiple_payments_per_year(self):
        """Test that Dividend API correctly aggregates multiple dividend payments in same year."""
        processor = FinancialDataProcessor(debug=False)
        
        fundamentals_data = {
            'General': {'CurrencyCode': 'GBP'},
            'SplitsDividends': {}
        }
        
        # Multiple payments in 2024 (quarterly dividends)
        dividend_api_data = [
            {'date': '2024-03-15', 'value': 0.15, 'currency': 'GBP'},
            {'date': '2024-06-15', 'value': 0.15, 'currency': 'GBP'},
            {'date': '2024-09-15', 'value': 0.15, 'currency': 'GBP'},
            {'date': '2024-12-15', 'value': 0.15, 'currency': 'GBP'}
        ]
        
        result, _, _, currency, sources = processor.parse_dividend_history(
            fundamentals_data, 
            dividend_api_data=dividend_api_data
        )
        
        # Should aggregate all 4 payments
        assert result['2024'] == 0.60  # 0.15 * 4
        assert sources['2024'] == 'dividend_api'
        assert currency == 'GBP'
    
    def test_dividend_api_uses_payment_date_over_ex_date(self):
        """Test that Dividend API prefers paymentDate over ex-dividend date for year assignment."""
        processor = FinancialDataProcessor(debug=False)
        
        fundamentals_data = {
            'General': {'CurrencyCode': 'USD'},
            'SplitsDividends': {}
        }
        
        # Dividend declared in Dec 2023, paid in Jan 2024
        dividend_api_data = [
            {
                'date': '2023-12-15',  # Ex-dividend date
                'paymentDate': '2024-01-15',  # Payment date
                'value': 1.00,
                'currency': 'USD'
            }
        ]
        
        result, _, _, _, sources = processor.parse_dividend_history(
            fundamentals_data, 
            dividend_api_data=dividend_api_data
        )
        
        # Should use payment date (2024) not ex-date (2023)
        assert '2024' in result
        assert result['2024'] == 1.00
        assert sources['2024'] == 'dividend_api'
    
    def test_dividend_api_handles_empty_list(self):
        """Test that empty Dividend API list falls back to Cash Flow."""
        processor = FinancialDataProcessor(debug=False)
        
        fundamentals_data = {
            'General': {'CurrencyCode': 'USD'},
            'SplitsDividends': {'ForwardAnnualDividendRate': 2.50},
            'Financials': {
                'Cash_Flow': {
                    'currency_symbol': 'USD',
                    'yearly': {
                        '2024-12-31': {'dividendsPaid': '1000000.00'}
                    }
                }
            },
            'outstandingShares': {
                'annual': {
                    '0': {'date': '2024', 'shares': 1000000}
                }
            }
        }
        
        # Empty Dividend API list
        result, _, _, _, sources = processor.parse_dividend_history(
            fundamentals_data, 
            dividend_api_data=[]
        )
        
        # Should fall back to Cash Flow
        assert result['2024'] == 1.00
        assert sources['2024'] == 'cash_flow'
    
    def test_dividend_api_skips_zero_value_dividends(self):
        """Test that Dividend API skips dividends with zero or negative values."""
        processor = FinancialDataProcessor(debug=False)
        
        fundamentals_data = {
            'General': {'CurrencyCode': 'USD'},
            'SplitsDividends': {}
        }
        
        dividend_api_data = [
            {'date': '2024-06-15', 'value': 1.25, 'currency': 'USD'},
            {'date': '2024-09-15', 'value': 0.0, 'currency': 'USD'},  # Zero - should skip
            {'date': '2024-12-15', 'value': 1.25, 'currency': 'USD'}
        ]
        
        result, _, _, _, _ = processor.parse_dividend_history(
            fundamentals_data, 
            dividend_api_data=dividend_api_data
        )
        
        # Should only include non-zero dividends
        assert result['2024'] == 2.50  # 1.25 + 1.25 (skipped 0.0)
    
    def test_dividend_api_extracts_currency_from_first_record(self):
        """Test that Dividend API uses currency from first dividend record."""
        processor = FinancialDataProcessor(debug=False)
        
        fundamentals_data = {
            'General': {'CurrencyCode': 'USD'},  # Stock currency
            'SplitsDividends': {}
        }
        
        dividend_api_data = [
            {'date': '2024-06-15', 'value': 0.50, 'currency': 'GBP'},  # Dividend currency
            {'date': '2024-12-15', 'value': 0.50, 'currency': 'GBP'}
        ]
        
        _, _, _, currency, _ = processor.parse_dividend_history(
            fundamentals_data, 
            dividend_api_data=dividend_api_data
        )
        
        # Should use dividend currency (GBP) not stock currency (USD)
        assert currency == 'GBP'


class TestDividendAPIClientMethod:
    """Test the EODHD client's _fetch_dividend_history method."""
    
    @patch('clients.eodhd_client.BaseAPIClient._make_request')
    def test_fetch_dividend_history_success(self, mock_request):
        """Test successful Dividend API fetch."""
        from clients.eodhd_client import EODHDClient
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'date': '2024-06-15', 'value': 1.25, 'currency': 'USD'},
            {'date': '2024-12-15', 'value': 1.25, 'currency': 'USD'}
        ]
        mock_request.return_value = mock_response
        
        client = EODHDClient(api_key='test_key', debug=False)
        result = client._fetch_dividend_history('AAPL.US')
        
        assert result is not None
        assert len(result) == 2
        assert result[0]['value'] == 1.25
    
    @patch('clients.eodhd_client.BaseAPIClient._make_request')
    def test_fetch_dividend_history_403_returns_none(self, mock_request):
        """Test that 403 (subscription tier) returns None gracefully."""
        from clients.eodhd_client import EODHDClient
        
        # Mock 403 response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_request.return_value = mock_response
        
        client = EODHDClient(api_key='test_key', debug=False)
        result = client._fetch_dividend_history('AAPL.US')
        
        assert result is None
    
    @patch('clients.eodhd_client.BaseAPIClient._make_request')
    def test_fetch_dividend_history_404_returns_none(self, mock_request):
        """Test that 404 (no data) returns None gracefully."""
        from clients.eodhd_client import EODHDClient
        
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response
        
        client = EODHDClient(api_key='test_key', debug=False)
        result = client._fetch_dividend_history('AAPL.US')
        
        assert result is None
    
    @patch('clients.eodhd_client.BaseAPIClient._make_request')
    def test_fetch_dividend_history_exception_returns_none(self, mock_request):
        """Test that exceptions are caught and return None."""
        from clients.eodhd_client import EODHDClient
        
        # Mock exception
        mock_request.side_effect = Exception("Network error")
        
        client = EODHDClient(api_key='test_key', debug=False)
        result = client._fetch_dividend_history('AAPL.US')
        
        assert result is None
    
    @patch('clients.eodhd_client.BaseAPIClient._make_request')
    def test_fetch_dividend_history_uses_correct_endpoint(self, mock_request):
        """Test that correct API endpoint and parameters are used."""
        from clients.eodhd_client import EODHDClient
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_request.return_value = mock_response
        
        client = EODHDClient(api_key='test_key', debug=False)
        client._fetch_dividend_history('VOD.LSE')
        
        # Verify correct URL and params
        call_args = mock_request.call_args
        assert 'https://eodhd.com/api/div/VOD.LSE' in str(call_args)
        assert call_args[1]['params']['api_token'] == 'test_key'
        assert call_args[1]['params']['fmt'] == 'json'


class TestDividendSourceLabels:
    """Test that dividend source labels are displayed correctly."""
    
    def test_dividend_api_source_label(self):
        """Test that 'dividend_api' source shows correct label."""
        from output.dossier_generator import DossierGenerator
        
        financial_data = {
            'ticker': 'TEST.US',
            'exchange': 'US',
            'currency': 'USD',
            'original_stock_currency': 'USD',
            'price': 100.0,
            'ceo_name': 'Test CEO',
            'sector': 'Technology',
            'industry': 'Software',
            'employees': 100,
            'forward_dividend_rate': 2.50,
            'dividend_source': 'Dividend API',
            'dividend_sources': {'2024': 'dividend_api'},
            'history': {
                '2024-12-31': {
                    'revenue': 1000000,
                    'net_income': 100000,
                    'eps': 10.0,
                    'dividend': 2.50,
                    'total_equity': 500000,
                    'shares_outstanding': 10000
                }
            },
            'pe_ratio': 10.0,
            'price_to_book': 2.0,
            'is_dividend_amounts': True
        }
        
        metrics = {
            'verdict': 'UNDERVALUED',
            'graham_number': 150.0,
            'epv': 200.0,
            'net_net_value': 'N/A',
            'margin_of_safety': 33.3,
            'defensive_tests': {},
            'enterprising_tests': {},
            'warnings': [],
            'epv_details': {}
        }
        
        dossier = DossierGenerator('TEST.US', financial_data, metrics, []).generate()
        
        # Should show "Declared (Dividend API)" label
        assert 'Declared (Dividend API)' in dossier
        assert '2.50 USD' in dossier
    
    @pytest.mark.skip(reason="Dividend API status display not implemented in dossier")
    def test_data_quality_shows_dividend_api_status(self):
        """Test that DATA QUALITY ASSESSMENT shows Dividend API status."""
        from output.dossier_generator import DossierGenerator
        
        financial_data = {
            'ticker': 'TEST.US',
            'exchange': 'US',
            'currency': 'USD',
            'original_stock_currency': 'USD',
            'price': 100.0,
            'ceo_name': 'Test CEO',
            'sector': 'Technology',
            'industry': 'Software',
            'employees': 100,
            'dividend_source': 'Dividend API',
            'price_source': 'EODHD',
            'history': {
                '2024-12-31': {
                    'revenue': 1000000,
                    'net_income': 100000,
                    'eps': 10.0,
                    'dividend': 2.50,
                    'total_equity': 500000,
                    'shares_outstanding': 10000
                }
            },
            'pe_ratio': 10.0,
            'is_dividend_amounts': True
        }
        
        metrics = {
            'verdict': 'UNDERVALUED',
            'graham_number': 150.0,
            'epv': 200.0,
            'net_net_value': 'N/A',
            'margin_of_safety': 33.3,
            'defensive_tests': {},
            'enterprising_tests': {},
            'warnings': [],
            'epv_details': {}
        }
        
        dossier = DossierGenerator('TEST.US', financial_data, metrics, []).generate()
        
        # Should show Dividend API in data quality assessment
        assert 'From Dividend API (declared dividends with exact dates)' in dossier
