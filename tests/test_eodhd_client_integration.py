"""
Integration tests for EODHD Client

These tests verify the client works correctly with mocked API responses.
"""

import pytest
from unittest.mock import Mock, patch
from clients.eodhd_client import EODHDClient


def test_fetch_all_data_basic():
    """Test basic fetch_all_data functionality with a complete mock response."""
    client = EODHDClient("test_api_key")
    
    mock_response_data = {
        'General': {
            'Code': 'AAPL',
            'Exchange': 'NASDAQ',
            'CurrencyCode': 'USD',
            'IsDelisted': False,
            'Officers': [{'Name': 'Tim Cook'}]
        },
        'SharesStats': {
            'SharesOutstanding': 16000000000
        },
        'Financials': {
            'Balance_Sheet': {
                'yearly': {
                    '2023-09-30': {
                        'totalStockholderEquity': 62146000000,
                        'intangibleAssets': 0,
                        'goodwill': 0,
                        'totalCurrentAssets': 143566000000,
                        'totalCurrentLiabilities': 145308000000,
                        'totalLiab': 290437000000,
                        'longTermDebt': 106000000000
                    },
                    '2022-09-30': {
                        'totalStockholderEquity': 50672000000,
                        'intangibleAssets': 0,
                        'goodwill': 0,
                        'totalCurrentAssets': 135405000000,
                        'totalCurrentLiabilities': 153982000000,
                        'totalLiab': 302083000000,
                        'longTermDebt': 120069000000
                    }
                }
            },
            'Income_Statement': {
                'yearly': {
                    '2023-09-30': {
                        'totalRevenue': 383285000000,
                        'netIncome': 96995000000,
                        'eps': 6.16
                    },
                    '2022-09-30': {
                        'totalRevenue': 394328000000,
                        'netIncome': 99803000000,
                        'eps': 6.15
                    }
                }
            }
        },
        'SplitsDividends': {
            'NumberDividendsByYear': {
                '2023': 4,
                '2022': 4
            }
        },
        'Highlights': {
            'SharePrice': 150.0
        }
    }
    
    with patch.object(client.session, 'get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_get.return_value = mock_response
        
        result = client.fetch_all_data('AAPL.US')
        
        # Verify basic structure
        assert result['ticker'] == 'AAPL'
        assert result['exchange'] == 'NASDAQ'
        assert result['currency'] == 'USD'
        assert result['price'] == 150.0
        assert result['ceo_name'] == 'Tim Cook'
        
        # Verify history data
        assert '2023-09-30' in result['history']
        assert '2022-09-30' in result['history']
        
        # Verify 2023 data
        data_2023 = result['history']['2023-09-30']
        assert data_2023['revenue'] == 383285000000
        assert data_2023['net_income'] == 96995000000
        assert data_2023['eps'] == 6.16
        assert data_2023['dividend'] == 4
        assert data_2023['total_equity'] == 62146000000
        assert data_2023['shares_outstanding'] == 16000000000


def test_london_fix_integration():
    """Test London Fix is applied correctly in full fetch_all_data flow."""
    client = EODHDClient("test_api_key")
    
    mock_response_data = {
        'General': {
            'Code': 'VOD',
            'Exchange': 'LSE',
            'CurrencyCode': 'GBP',
            'IsDelisted': False,
            'Officers': [{'Name': 'John Doe'}]
        },
        'SharesStats': {
            'SharesOutstanding': 26000000000
        },
        'Financials': {
            'Balance_Sheet': {'yearly': {}},
            'Income_Statement': {
                'yearly': {
                    '2023-03-31': {
                        'totalRevenue': 45000000000,
                        'netIncome': 2000000000,
                        'eps': 0.08  # Low EPS to trigger London Fix
                    }
                }
            }
        },
        'SplitsDividends': {'NumberDividendsByYear': {}},
        'Highlights': {
            'SharePrice': 80.0  # Price in GBp, P/E = 1000 > 500
        }
    }
    
    with patch.object(client.session, 'get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_get.return_value = mock_response
        
        result = client.fetch_all_data('VOD.L')
        
        # Price should be divided by 100
        assert result['price'] == 0.8
        
        # Warning should be present
        assert any('London Fix' in w for w in result['warnings'])


def test_data_sanitization():
    """Test that NA values and nulls are properly sanitized to 0.0."""
    client = EODHDClient("test_api_key")
    
    mock_response_data = {
        'General': {
            'Code': 'TEST',
            'Exchange': 'NASDAQ',
            'CurrencyCode': 'USD',
            'Officers': []
        },
        'SharesStats': {
            'SharesOutstanding': 1000000
        },
        'Financials': {
            'Balance_Sheet': {
                'yearly': {
                    '2023-12-31': {
                        'totalStockholderEquity': 'NA',
                        'intangibleAssets': None,
                        'goodwill': '',
                        'totalCurrentAssets': 1000000,
                        'totalCurrentLiabilities': 500000,
                        'totalLiab': 600000,
                        'longTermDebt': 'N/A'
                    }
                }
            },
            'Income_Statement': {
                'yearly': {
                    '2023-12-31': {
                        'totalRevenue': 5000000,
                        'netIncome': None,
                        'eps': 'NA'
                    }
                }
            }
        },
        'SplitsDividends': {'NumberDividendsByYear': {}},
        'Highlights': {'SharePrice': 10.0}
    }
    
    with patch.object(client.session, 'get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_get.return_value = mock_response
        
        result = client.fetch_all_data('TEST.US')
        
        # Verify NA values are converted to 0.0
        data = result['history']['2023-12-31']
        assert data['total_equity'] == 0.0
        assert data['intangible_assets'] == 0.0
        assert data['goodwill'] == 0.0
        assert data['net_income'] == 0.0
        assert data['eps'] == 0.0
        assert data['long_term_debt'] == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
