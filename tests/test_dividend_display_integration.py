"""
Integration test for dividend display in dossier generation.

This test verifies that the complete flow from data parsing to dossier
generation correctly displays dividend information with appropriate labels
and warnings.
"""

import pytest
import json
from unittest.mock import Mock, patch
from clients.eodhd_client import EODHDClient
from output.dossier_generator import DossierGenerator
from core.graham_math import GrahamCalculator


class TestDividendDisplayIntegration:
    """Integration tests for dividend display in dossier."""
    
    def test_dividend_display_with_cash_flow_data(self):
        """
        Test that when dividend comes from cash flow, the dossier shows
        "Paid (Cash Flow)" label without warning.
        """
        # Create mock data with cash flow dividend
        mock_data = {
            'General': {
                'Code': 'TEST',
                'Exchange': 'US',
                'CurrencyCode': 'USD',
                'Name': 'Test Company',
                'Sector': 'Technology',
                'Industry': 'Software',
                'FullTimeEmployees': 100,
                'Officers': {'0': {'Name': 'Test CEO', 'Title': 'CEO'}}
            },
            'Financials': {
                'Balance_Sheet': {
                    'currency_symbol': 'USD',
                    'yearly': {
                        '2024-12-31': {
                            'totalStockholderEquity': 500000,
                            'intangibleAssets': 0,
                            'goodwill': 0,
                            'totalCurrentAssets': 300000,
                            'totalCurrentLiabilities': 100000,
                            'totalLiab': 200000,
                            'longTermDebt': 50000
                        }
                    }
                },
                'Income_Statement': {
                    'yearly': {
                        '2024-12-31': {
                            'totalRevenue': 1000000,
                            'netIncome': 100000,
                            'eps': 10.0
                        }
                    }
                },
                'Cash_Flow': {
                    'currency_symbol': 'USD',
                    'yearly': {
                        '2024-12-31': {
                            'dividendsPaid': -50000  # Negative because it's cash outflow
                        }
                    }
                }
            },
            'Highlights': {
                'SharePrice': 100.0,
                'PERatio': 10.0,
                'BookValue': 50.0,
                'ReturnOnEquityTTM': 0.20,
                'ReturnOnAssetsTTM': 0.15,
                'ProfitMargin': 0.10
            },
            'SplitsDividends': {
                'ForwardAnnualDividendRate': 5.0
            },
            'SharesStats': {
                'SharesOutstanding': 10000,
                'PercentInsiders': 10.0,
                'PercentInstitutions': 50.0
            },
            'Technicals': {
                'Beta': 1.0,
                '52WeekHigh': 110.0,
                '52WeekLow': 90.0
            },
            'Valuation': {
                'PriceBookMRQ': 2.0,
                'EnterpriseValue': 1000000
            },
            'outstandingShares': {
                'annual': {
                    '0': {'date': '2024', 'shares': 10000}
                }
            }
        }
        
        # Create client and fetch data
        with patch('clients.eodhd_client.EODHDClient._make_eodhd_request', return_value=mock_data):
            client = EODHDClient('test_key', debug=False)
            financial_data = client.fetch_all_data('TEST.US')
        
        # Generate metrics
        calculator = GrahamCalculator(financial_data)
        metrics = calculator.compute_all()
        
        # Generate dossier
        dossier = DossierGenerator('TEST.US', financial_data, metrics, []).generate()
        
        # Verify dividend display
        assert 'Paid (Cash Flow)' in dossier
        # Should NOT have warning since using cash flow
        assert '⚠️ 2024 dividend uses forward declared rate' not in dossier
    
    def test_dividend_display_with_forward_rate_only(self):
        """
        Test that when dividend comes from forward rate only, the dossier shows
        "Forward Annual Dividend" label with warning.
        
        Note: To trigger "Forward Annual Dividend" display, we need NO complete years
        with financial data. If there's a complete year, the forward rate gets assigned
        to that year and shows as "Trailing Dividend" instead.
        """
        # Create mock data with NO financial history, only forward rate
        mock_data = {
            'General': {
                'Code': 'TEST',
                'Exchange': 'US',
                'CurrencyCode': 'USD',
                'Name': 'Test Company',
                'Sector': 'Technology',
                'Industry': 'Software',
                'FullTimeEmployees': 100,
                'Officers': {'0': {'Name': 'Test CEO', 'Title': 'CEO'}}
            },
            'Financials': {
                'Balance_Sheet': {
                    'currency_symbol': 'USD',
                    'yearly': {}  # Empty - no historical data
                },
                'Income_Statement': {
                    'yearly': {}  # Empty - no historical data
                },
                'Cash_Flow': {
                    'currency_symbol': 'USD',
                    'yearly': {}  # Empty - no historical data
                }
            },
            'Highlights': {
                'SharePrice': 100.0,
                'PERatio': 10.0,
                'BookValue': 50.0,
                'ReturnOnEquityTTM': 0.20,
                'ReturnOnAssetsTTM': 0.15,
                'ProfitMargin': 0.10
            },
            'SplitsDividends': {
                'ForwardAnnualDividendRate': 5.0
            },
            'SharesStats': {
                'SharesOutstanding': 10000,
                'PercentInsiders': 10.0,
                'PercentInstitutions': 50.0
            },
            'Technicals': {
                'Beta': 1.0,
                '52WeekHigh': 110.0,
                '52WeekLow': 90.0
            },
            'Valuation': {
                'PriceBookMRQ': 2.0,
                'EnterpriseValue': 1000000
            },
            'outstandingShares': {
                'annual': {}
            }
        }
        
        # Create client and fetch data
        with patch('clients.eodhd_client.EODHDClient._make_eodhd_request', return_value=mock_data):
            client = EODHDClient('test_key', debug=False)
            financial_data = client.fetch_all_data('TEST.US')
        
        # Generate metrics
        calculator = GrahamCalculator(financial_data)
        metrics = calculator.compute_all()
        
        # Generate dossier
        dossier = DossierGenerator('TEST.US', financial_data, metrics, []).generate()
        
        # Verify dividend display (updated to match current implementation)
        assert 'Forward Annual Dividend' in dossier
        # Should have warning since using forward rate
        assert '⚠️ No historical dividend data available - using forward declared rate' in dossier
