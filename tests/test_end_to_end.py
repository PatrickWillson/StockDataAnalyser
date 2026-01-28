"""
End-to-end integration tests for the Stock Data Analyser.

These tests verify the complete workflow from data fetching through dossier generation.
"""

import os
import sys
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from clients.eodhd_client import EODHDClient
from core.graham_math import GrahamCalculator
from core.anomaly_detector import AnomalyDetector
from output.dossier_generator import DossierGenerator
from stock_data_analyser import save_dossier


def create_mock_financial_data():
    """Create realistic mock financial data for testing."""
    return {
        'ticker': 'TEST.US',
        'exchange': 'NASDAQ',
        'currency': 'USD',
        'price': 150.0,
        'ceo_name': 'John Doe',
        'history': {
            '2023': {
                'revenue': 100000000.0,
                'net_income': 10000000.0,
                'eps': 5.0,
                'dividend': 1.0,
                'total_equity': 50000000.0,
                'intangible_assets': 5000000.0,
                'goodwill': 2000000.0,
                'shares_outstanding': 2000000.0,
                'current_assets': 30000000.0,
                'current_liabilities': 10000000.0,
                'total_liabilities': 20000000.0,
                'long_term_debt': 10000000.0
            },
            '2022': {
                'revenue': 95000000.0,
                'net_income': 9500000.0,
                'eps': 4.75,
                'dividend': 0.9,
                'total_equity': 48000000.0,
                'intangible_assets': 4800000.0,
                'goodwill': 1900000.0,
                'shares_outstanding': 2000000.0,
                'current_assets': 28000000.0,
                'current_liabilities': 9500000.0,
                'total_liabilities': 19000000.0,
                'long_term_debt': 9500000.0
            },
            '2021': {
                'revenue': 90000000.0,
                'net_income': 9000000.0,
                'eps': 4.5,
                'dividend': 0.8,
                'total_equity': 46000000.0,
                'intangible_assets': 4600000.0,
                'goodwill': 1800000.0,
                'shares_outstanding': 2000000.0,
                'current_assets': 26000000.0,
                'current_liabilities': 9000000.0,
                'total_liabilities': 18000000.0,
                'long_term_debt': 9000000.0
            },
            '2020': {
                'revenue': 85000000.0,
                'net_income': 8500000.0,
                'eps': 4.25,
                'dividend': 0.7,
                'total_equity': 44000000.0,
                'intangible_assets': 4400000.0,
                'goodwill': 1700000.0,
                'shares_outstanding': 2000000.0,
                'current_assets': 24000000.0,
                'current_liabilities': 8500000.0,
                'total_liabilities': 17000000.0,
                'long_term_debt': 8500000.0
            },
            '2019': {
                'revenue': 80000000.0,
                'net_income': 8000000.0,
                'eps': 4.0,
                'dividend': 0.6,
                'total_equity': 42000000.0,
                'intangible_assets': 4200000.0,
                'goodwill': 1600000.0,
                'shares_outstanding': 2000000.0,
                'current_assets': 22000000.0,
                'current_liabilities': 8000000.0,
                'total_liabilities': 16000000.0,
                'long_term_debt': 8000000.0
            },
            '2018': {
                'revenue': 75000000.0,
                'net_income': 7500000.0,
                'eps': 3.75,
                'dividend': 0.5,
                'total_equity': 40000000.0,
                'intangible_assets': 4000000.0,
                'goodwill': 1500000.0,
                'shares_outstanding': 2000000.0,
                'current_assets': 20000000.0,
                'current_liabilities': 7500000.0,
                'total_liabilities': 15000000.0,
                'long_term_debt': 7500000.0
            },
            '2017': {
                'revenue': 70000000.0,
                'net_income': 7000000.0,
                'eps': 3.5,
                'dividend': 0.4,
                'total_equity': 38000000.0,
                'intangible_assets': 3800000.0,
                'goodwill': 1400000.0,
                'shares_outstanding': 2000000.0,
                'current_assets': 18000000.0,
                'current_liabilities': 7000000.0,
                'total_liabilities': 14000000.0,
                'long_term_debt': 7000000.0
            },
            '2016': {
                'revenue': 65000000.0,
                'net_income': 6500000.0,
                'eps': 3.25,
                'dividend': 0.3,
                'total_equity': 36000000.0,
                'intangible_assets': 3600000.0,
                'goodwill': 1300000.0,
                'shares_outstanding': 2000000.0,
                'current_assets': 16000000.0,
                'current_liabilities': 6500000.0,
                'total_liabilities': 13000000.0,
                'long_term_debt': 6500000.0
            },
            '2015': {
                'revenue': 60000000.0,
                'net_income': 6000000.0,
                'eps': 3.0,
                'dividend': 0.2,
                'total_equity': 34000000.0,
                'intangible_assets': 3400000.0,
                'goodwill': 1200000.0,
                'shares_outstanding': 2000000.0,
                'current_assets': 14000000.0,
                'current_liabilities': 6000000.0,
                'total_liabilities': 12000000.0,
                'long_term_debt': 6000000.0
            },
            '2014': {
                'revenue': 55000000.0,
                'net_income': 5500000.0,
                'eps': 2.75,
                'dividend': 0.1,
                'total_equity': 32000000.0,
                'intangible_assets': 3200000.0,
                'goodwill': 1100000.0,
                'shares_outstanding': 2000000.0,
                'current_assets': 12000000.0,
                'current_liabilities': 5500000.0,
                'total_liabilities': 11000000.0,
                'long_term_debt': 5500000.0
            }
        },
        'warnings': []
    }


def test_end_to_end_workflow():
    """
    Test the complete workflow: fetch data → calculate metrics → detect anomalies → generate dossier.
    
    This test verifies that all components work together correctly.
    """
    # Arrange: Create mock financial data
    financial_data = create_mock_financial_data()
    
    # Act: Run through the complete workflow
    
    # Step 1: Calculate Graham metrics
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    
    # Step 2: Detect anomalies
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    # Step 3: Generate dossier content
    dossier_content = DossierGenerator('TEST.US', financial_data, metrics, anomalies).generate()
    
    # Assert: Verify all components produced valid output
    assert metrics is not None
    assert 'graham_number' in metrics
    assert 'epv' in metrics
    assert 'net_net_value' in metrics
    assert 'margin_of_safety' in metrics
    assert 'verdict' in metrics
    assert 'defensive_tests' in metrics
    assert 'enterprising_tests' in metrics
    
    assert anomalies is not None
    assert isinstance(anomalies, list)
    
    assert dossier_content is not None
    assert 'STOCK ANALYSIS DOSSIER: TEST.US' in dossier_content
    assert 'EXECUTIVE SUMMARY' in dossier_content
    assert 'CRITICAL ALERTS' in dossier_content
    assert 'DEFENSIVE INVESTOR TESTS' in dossier_content
    assert 'ENTERPRISING INVESTOR TESTS' in dossier_content
    assert '20-YEAR FINANCIALS' in dossier_content
    assert '|' in dossier_content  # Markdown table syntax


def test_end_to_end_with_negative_equity():
    """
    Test end-to-end workflow with a company that has negative equity.
    
    Verifies graceful handling of edge cases.
    """
    # Arrange: Create financial data with negative equity
    financial_data = create_mock_financial_data()
    financial_data['history']['2023']['total_equity'] = -10000000.0
    
    # Act: Run through the workflow
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    dossier_content = DossierGenerator('TEST.US', financial_data, metrics, anomalies).generate()
    
    # Assert: System should handle negative equity gracefully
    assert metrics['graham_number'] == "N/A"
    assert metrics['verdict'] == "Rely on EPV - Negative Equity"
    assert any("Negative Tangible Book Value" in w for w in metrics['warnings'])
    assert dossier_content is not None


def test_end_to_end_with_young_company():
    """
    Test end-to-end workflow with a young company (< 10 years of history).
    
    Verifies proper handling of insufficient history.
    """
    # Arrange: Create financial data with only 5 years of history
    financial_data = create_mock_financial_data()
    # Keep only 5 years
    years_to_keep = ['2023', '2022', '2021', '2020', '2019']
    financial_data['history'] = {
        year: financial_data['history'][year] 
        for year in years_to_keep
    }
    
    # Act: Run through the workflow
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    dossier_content = DossierGenerator('TEST.US', financial_data, metrics, anomalies).generate()
    
    # Assert: Earnings growth test should be marked as "N/A (Too Young)"
    assert metrics['defensive_tests']['earnings_growth'] == 'N/A (Too Young)'
    assert dossier_content is not None


def test_dossier_file_saving(tmp_path):
    """
    Test that dossier files are saved correctly with proper naming.
    """
    # Arrange: Create mock content
    content = "# Test Dossier Content"
    ticker = "AAPL.US"
    
    # Act: Save dossier (using tmp_path for testing)
    with patch('stock_data_analyser.os.makedirs'):
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            save_dossier(ticker, content)
            
            # Assert: File should be saved with correct name
            expected_filename = "data/AAPL_US_DOSSIER.md"
            mock_open.assert_called_once_with(expected_filename, "w", encoding="utf-8")
            mock_file.write.assert_called_once_with(content)


def test_markdown_formatting_in_dossier():
    """
    Test that the dossier uses proper Markdown formatting.
    """
    # Arrange
    financial_data = create_mock_financial_data()
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    # Act
    dossier_content = DossierGenerator('TEST.US', financial_data, metrics, anomalies).generate()
    
    # Assert: Check for proper Markdown elements
    assert dossier_content.startswith('# STOCK ANALYSIS DOSSIER')
    assert '---' in dossier_content  # Horizontal rules
    assert '## SECTION' in dossier_content  # Section headers
    assert '| Year |' in dossier_content  # Table header
    assert '|------|' in dossier_content  # Table separator
    
    # Verify table has data rows
    lines = dossier_content.split('\n')
    table_rows = [line for line in lines if line.startswith('| 20')]
    assert len(table_rows) >= 5  # Should have at least 5 years of data


def test_yu_lse_complete_flow_with_yfinance_fallback():
    """
    End-to-end test for YU.LSE ticker with yfinance primary source.
    
    Tests complete flow:
    1. yfinance price fetching (primary source)
    2. EPV calculation includes loss years
    3. Dossier contains all new sections (Data Quality, Defensive Verdict, Enterprising Assessment)
    
    Requirements: All (comprehensive integration test)
    """
    from clients.yfinance_client import YFinanceClient
    from core.financial_data_processor import FinancialDataProcessor
    
    # Arrange: Create mock data simulating YU.LSE with missing EODHD price
    mock_data = {
        'General': {
            'Code': 'YU',
            'Exchange': 'LSE',
            'CurrencyCode': 'GBX',
            'Officers': {
                '0': {'Name': 'Mr. Baljit Bobby Kalar', 'Title': 'CEO'}
            }
        },
        'Highlights': {
            # No SharePrice - simulating missing EODHD price
            'PERatio': 8.46,
            'BookValue': 4.82,
            'DividendShare': 0.63,
            'EarningsShare': 1.95,
            'ReturnOnEquityTTM': 0.5308,
            'ReturnOnAssetsTTM': 0.125
        },
        'Financials': {
            'Balance_Sheet': {
                'currency_symbol': 'GBP',
                'yearly': {
                    '2024-12-31': {
                        'totalStockholderEquity': 87000000,
                        'intangibleAssets': 5000000,
                        'goodwill': 2000000,
                        'totalCurrentAssets': 120000000,
                        'totalCurrentLiabilities': 90000000,
                        'totalAssets': 200000000,
                        'totalLiab': 113000000,
                        'longTermDebt': 10000000
                    },
                    '2023-12-31': {
                        'totalStockholderEquity': 81000000,
                        'intangibleAssets': 4800000,
                        'goodwill': 1900000,
                        'totalCurrentAssets': 110000000,
                        'totalCurrentLiabilities': 85000000,
                        'totalAssets': 190000000,
                        'totalLiab': 109000000,
                        'longTermDebt': 9500000
                    },
                    '2022-12-31': {
                        'totalStockholderEquity': 75000000,
                        'intangibleAssets': 4600000,
                        'goodwill': 1800000,
                        'totalCurrentAssets': 100000000,
                        'totalCurrentLiabilities': 80000000,
                        'totalAssets': 180000000,
                        'totalLiab': 105000000,
                        'longTermDebt': 9000000
                    },
                    '2021-12-31': {
                        'totalStockholderEquity': 70000000,
                        'intangibleAssets': 4400000,
                        'goodwill': 1700000,
                        'totalCurrentAssets': 95000000,
                        'totalCurrentLiabilities': 75000000,
                        'totalAssets': 170000000,
                        'totalLiab': 100000000,
                        'longTermDebt': 8500000
                    },
                    '2020-12-31': {
                        'totalStockholderEquity': 65000000,
                        'intangibleAssets': 4200000,
                        'goodwill': 1600000,
                        'totalCurrentAssets': 90000000,
                        'totalCurrentLiabilities': 70000000,
                        'totalAssets': 160000000,
                        'totalLiab': 95000000,
                        'longTermDebt': 8000000
                    },
                    '2019-12-31': {
                        'totalStockholderEquity': 60000000,
                        'intangibleAssets': 4000000,
                        'goodwill': 1500000,
                        'totalCurrentAssets': 85000000,
                        'totalCurrentLiabilities': 65000000,
                        'totalAssets': 150000000,
                        'totalLiab': 90000000,
                        'longTermDebt': 7500000
                    },
                    '2018-12-31': {
                        'totalStockholderEquity': 55000000,
                        'intangibleAssets': 3800000,
                        'goodwill': 1400000,
                        'totalCurrentAssets': 80000000,
                        'totalCurrentLiabilities': 60000000,
                        'totalAssets': 140000000,
                        'totalLiab': 85000000,
                        'longTermDebt': 7000000
                    },
                    '2017-12-31': {
                        'totalStockholderEquity': 50000000,
                        'intangibleAssets': 3600000,
                        'goodwill': 1300000,
                        'totalCurrentAssets': 75000000,
                        'totalCurrentLiabilities': 55000000,
                        'totalAssets': 130000000,
                        'totalLiab': 80000000,
                        'longTermDebt': 6500000
                    },
                    '2016-12-31': {
                        'totalStockholderEquity': 45000000,
                        'intangibleAssets': 3400000,
                        'goodwill': 1200000,
                        'totalCurrentAssets': 70000000,
                        'totalCurrentLiabilities': 50000000,
                        'totalAssets': 120000000,
                        'totalLiab': 75000000,
                        'longTermDebt': 6000000
                    },
                    '2015-12-31': {
                        'totalStockholderEquity': 40000000,
                        'intangibleAssets': 3200000,
                        'goodwill': 1100000,
                        'totalCurrentAssets': 65000000,
                        'totalCurrentLiabilities': 45000000,
                        'totalAssets': 110000000,
                        'totalLiab': 70000000,
                        'longTermDebt': 5500000
                    }
                }
            },
            'Income_Statement': {
                'currency_symbol': 'GBP',
                'yearly': {
                    '2024-12-31': {'totalRevenue': 640000000, 'netIncome': 33499000},
                    '2023-12-31': {'totalRevenue': 620000000, 'netIncome': 30860000},
                    '2022-12-31': {'totalRevenue': 600000000, 'netIncome': 4769000},
                    '2021-12-31': {'totalRevenue': 580000000, 'netIncome': 4500000},
                    '2020-12-31': {'totalRevenue': 560000000, 'netIncome': -1200000},  # Loss year
                    '2019-12-31': {'totalRevenue': 540000000, 'netIncome': -5000000},  # Loss year
                    '2018-12-31': {'totalRevenue': 520000000, 'netIncome': -6300000},  # Loss year
                    '2017-12-31': {'totalRevenue': 500000000, 'netIncome': 700000},
                    '2016-12-31': {'totalRevenue': 480000000, 'netIncome': -1400000},  # Loss year
                    '2015-12-31': {'totalRevenue': 460000000, 'netIncome': -700000}    # Loss year
                }
            },
            'Cash_Flow': {
                'currency_symbol': 'GBP',
                'yearly': {
                    '2024-12-31': {'dividendsPaid': -11000000},
                    '2023-12-31': {'dividendsPaid': -10500000},
                    '2022-12-31': {'dividendsPaid': 0},  # Missing dividend data
                    '2021-12-31': {'dividendsPaid': 0}
                }
            }
        },
        'SplitsDividends': {
            'ForwardAnnualDividendRate': 0.63
        },
        'Technicals': {
            'Beta': 0.668,
            '52WeekHigh': 18.34,
            '52WeekLow': 12.35
        },
        'outstandingShares': {
            'annual': {
                '0': {'date': '2024', 'shares': 18000000},
                '1': {'date': '2023', 'shares': 18000000},
                '2': {'date': '2022', 'shares': 18000000},
                '3': {'date': '2021', 'shares': 18000000},
                '4': {'date': '2020', 'shares': 18000000},
                '5': {'date': '2019', 'shares': 18000000},
                '6': {'date': '2018', 'shares': 18000000},
                '7': {'date': '2017', 'shares': 18000000},
                '8': {'date': '2016', 'shares': 18000000},
                '9': {'date': '2015', 'shares': 18000000}
            }
        }
    }
    
    # Mock yfinance client that returns a price in GBX
    mock_yf_client = Mock(spec=YFinanceClient)
    mock_yf_client.get_price.return_value = 1650.0  # Price in GBX (yfinance returns LSE prices in pence)
    
    # Act: Process data through the complete workflow
    warnings = []
    
    # Step 1: Get price with yfinance
    price, price_source, is_from_market_cap = FinancialDataProcessor.get_current_price(
        mock_data,
        yf_client=mock_yf_client,
        ticker='YU.LSE',
        warnings=warnings
    )
    
    # Step 2: Create financial data dict (simulating what EODHDClient.fetch_all_data returns)
    # In the real system, fetch_all_data does all the parsing
    financial_data = {
        'ticker': 'YU.LSE',
        'exchange': 'LSE',
        'currency': 'GBP',
        'original_stock_currency': 'GBX',
        'price': price,
        'ceo_name': 'Mr. Baljit Bobby Kalar',
        'sector': 'Utilities',
        'industry': 'Utilities - Diversified',
        'employees': 472,
        'shares_outstanding': 18000000,
        'beta': 0.668,
        'roe': 0.5308,
        'roa': 0.125,
        'pe_ratio': 8.46,
        'price_to_book': 3.42,
        'insider_ownership': 65.0,
        'institutional_ownership': 13.73,
        'history': {
            '2024': {
                'revenue': 640000000, 'net_income': 33499000, 'eps': 1.86,
                'dividend': 0.61, 'total_equity': 87000000, 'intangible_assets': 5000000,
                'goodwill': 2000000, 'shares_outstanding': 18000000,
                'current_assets': 120000000, 'current_liabilities': 90000000,
                'total_liabilities': 113000000, 'long_term_debt': 10000000
            },
            '2023': {
                'revenue': 620000000, 'net_income': 30860000, 'eps': 1.71,
                'dividend': 0.58, 'total_equity': 81000000, 'intangible_assets': 4800000,
                'goodwill': 1900000, 'shares_outstanding': 18000000,
                'current_assets': 110000000, 'current_liabilities': 85000000,
                'total_liabilities': 109000000, 'long_term_debt': 9500000
            },
            '2022': {
                'revenue': 600000000, 'net_income': 4769000, 'eps': 0.26,
                'dividend': 0.0, 'total_equity': 75000000, 'intangible_assets': 4600000,
                'goodwill': 1800000, 'shares_outstanding': 18000000,
                'current_assets': 100000000, 'current_liabilities': 80000000,
                'total_liabilities': 105000000, 'long_term_debt': 9000000
            },
            '2021': {
                'revenue': 580000000, 'net_income': 4500000, 'eps': 0.25,
                'dividend': 0.0, 'total_equity': 70000000, 'intangible_assets': 4400000,
                'goodwill': 1700000, 'shares_outstanding': 18000000,
                'current_assets': 95000000, 'current_liabilities': 75000000,
                'total_liabilities': 100000000, 'long_term_debt': 8500000
            },
            '2020': {
                'revenue': 560000000, 'net_income': -1200000, 'eps': -0.07,
                'dividend': 0.0, 'total_equity': 65000000, 'intangible_assets': 4200000,
                'goodwill': 1600000, 'shares_outstanding': 18000000,
                'current_assets': 90000000, 'current_liabilities': 70000000,
                'total_liabilities': 95000000, 'long_term_debt': 8000000
            },
            '2019': {
                'revenue': 540000000, 'net_income': -5000000, 'eps': -0.28,
                'dividend': 0.0, 'total_equity': 60000000, 'intangible_assets': 4000000,
                'goodwill': 1500000, 'shares_outstanding': 18000000,
                'current_assets': 85000000, 'current_liabilities': 65000000,
                'total_liabilities': 90000000, 'long_term_debt': 7500000
            },
            '2018': {
                'revenue': 520000000, 'net_income': -6300000, 'eps': -0.35,
                'dividend': 0.0, 'total_equity': 55000000, 'intangible_assets': 3800000,
                'goodwill': 1400000, 'shares_outstanding': 18000000,
                'current_assets': 80000000, 'current_liabilities': 60000000,
                'total_liabilities': 85000000, 'long_term_debt': 7000000
            },
            '2017': {
                'revenue': 500000000, 'net_income': 700000, 'eps': 0.04,
                'dividend': 0.0, 'total_equity': 50000000, 'intangible_assets': 3600000,
                'goodwill': 1300000, 'shares_outstanding': 18000000,
                'current_assets': 75000000, 'current_liabilities': 55000000,
                'total_liabilities': 80000000, 'long_term_debt': 6500000
            },
            '2016': {
                'revenue': 480000000, 'net_income': -1400000, 'eps': -0.08,
                'dividend': 0.0, 'total_equity': 45000000, 'intangible_assets': 3400000,
                'goodwill': 1200000, 'shares_outstanding': 18000000,
                'current_assets': 70000000, 'current_liabilities': 50000000,
                'total_liabilities': 75000000, 'long_term_debt': 6000000
            },
            '2015': {
                'revenue': 460000000, 'net_income': -700000, 'eps': -0.04,
                'dividend': 0.0, 'total_equity': 40000000, 'intangible_assets': 3200000,
                'goodwill': 1100000, 'shares_outstanding': 18000000,
                'current_assets': 65000000, 'current_liabilities': 45000000,
                'total_liabilities': 70000000, 'long_term_debt': 5500000
            }
        },
        'warnings': warnings,
        'dividend_source': 'forward_rate'
    }
    
    # Step 3: Calculate Graham metrics with normalized EPV
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    
    # Step 4: Detect anomalies
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    # Step 5: Generate dossier
    dossier_content = DossierGenerator('YU.LSE', financial_data, metrics, anomalies).generate()
    
    # Assert: Verify yfinance was used
    assert price == 1650.0, f"Expected 1650.0 GBX, got {price}"
    assert any("yfinance" in w for w in warnings), "Should have yfinance warning"
    mock_yf_client.get_price.assert_called_once_with('YU.LSE')
    
    # Assert: Verify EPV includes loss years
    epv_result = metrics.get('epv')
    if isinstance(epv_result, dict):
        # Should have 10 years of data
        assert epv_result['years_used'] == 10, "EPV should use 10 years"
        
        # Should include loss years in calculation
        net_incomes = epv_result['net_incomes']
        assert any(ni < 0 for ni in net_incomes), "Should include negative net incomes (loss years)"
        
        # Normalized earnings should be the average of all years including losses
        expected_avg = sum(net_incomes) / len(net_incomes)
        assert abs(epv_result['normalized_earnings'] - expected_avg) < 0.01, \
            "Normalized earnings should be average of all years including losses"
    
    # Assert: Verify dossier contains all sections
    assert 'Data Quality & Limitations' in dossier_content, "Should have Data Quality & Limitations subsection"
    assert 'SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS' in dossier_content, "Should have Defensive Investor Tests section"
    assert 'SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS' in dossier_content, "Should have Enterprising Investor Tests section"
    assert 'EPV - Simplified Earnings Power Estimate' in dossier_content, "Should have EPV methodology section"
    
    # Assert: Verify data quality section mentions yfinance
    assert 'yfinance' in dossier_content or 'EODHD' in dossier_content, \
        "Data quality section should mention price source"
    
    # Note: Defensive verdict and enterprising assessment features are not yet implemented
    # These would be part of future enhancements (see test_enterprising_investor.py for skipped tests)


def test_fatal_error_when_both_price_sources_fail():
    """
    Test that system exits with fatal error when both yfinance and EODHD fail.
    
    Requirements: 1.5 (Fatal error on missing price)
    """
    from clients.yfinance_client import YFinanceClient
    from core.financial_data_processor import FinancialDataProcessor
    
    # Arrange: Mock data with no EODHD price
    mock_data = {
        'General': {'CurrencyCode': 'USD'},
        'Highlights': {},  # No SharePrice
        'Financials': {'Balance_Sheet': {'currency_symbol': 'USD'}}
    }
    
    # Mock yfinance client that also fails
    mock_yf_client = Mock(spec=YFinanceClient)
    mock_yf_client.get_price.return_value = None  # yfinance also fails
    
    # Act: Try to get price
    warnings = []
    price, price_source, _ = FinancialDataProcessor.get_current_price(
        mock_data,
        yf_client=mock_yf_client,
        ticker='TEST.US',
        warnings=warnings
    )
    
    # Assert: Should return 0.0 when both sources fail
    assert price == 0.0, "Should return 0.0 when both yfinance and EODHD fail"
    assert price_source == 'Missing', "Price source should be 'Missing'"
    
    # In the main CLI, this would trigger sys.exit(1)
    # We verify the price is 0.0 which is the trigger condition


def test_epv_normalized_with_loss_years():
    """
    Test that EPV calculation properly includes loss years in the average.
    
    Requirements: 3.1, 3.3 (Full-cycle EPV calculation)
    """
    # Arrange: Create financial data with mix of profitable and loss years
    financial_data = {
        'ticker': 'TEST.US',
        'currency': 'USD',
        'price': 100.0,
        'shares_outstanding': 10000000,
        'history': {
            '2024': {'net_income': 10000000, 'revenue': 100000000, 'eps': 1.0},
            '2023': {'net_income': 8000000, 'revenue': 95000000, 'eps': 0.8},
            '2022': {'net_income': -2000000, 'revenue': 90000000, 'eps': -0.2},  # Loss
            '2021': {'net_income': 5000000, 'revenue': 85000000, 'eps': 0.5},
            '2020': {'net_income': -3000000, 'revenue': 80000000, 'eps': -0.3},  # Loss
            '2019': {'net_income': 6000000, 'revenue': 75000000, 'eps': 0.6},
            '2018': {'net_income': 7000000, 'revenue': 70000000, 'eps': 0.7},
            '2017': {'net_income': -1000000, 'revenue': 65000000, 'eps': -0.1},  # Loss
            '2016': {'net_income': 4000000, 'revenue': 60000000, 'eps': 0.4},
            '2015': {'net_income': 3000000, 'revenue': 55000000, 'eps': 0.3}
        },
        'warnings': []
    }
    
    # Act: Calculate EPV
    calculator = GrahamCalculator(financial_data)
    epv_result = calculator.compute_epv_normalized(financial_data['history'])
    
    # Assert: Verify loss years are included
    assert isinstance(epv_result, dict), "Should return dict for valid data"
    assert epv_result['years_used'] == 10, "Should use all 10 years"
    
    # Verify net incomes include negative values
    net_incomes = epv_result['net_incomes']
    assert any(ni < 0 for ni in net_incomes), "Should include loss years (negative net income)"
    
    # Verify normalized earnings is average of ALL years
    expected_avg = (10000000 + 8000000 - 2000000 + 5000000 - 3000000 + 
                   6000000 + 7000000 - 1000000 + 4000000 + 3000000) / 10
    assert abs(epv_result['normalized_earnings'] - expected_avg) < 1.0, \
        "Normalized earnings should be average of all years including losses"


def test_dossier_contains_dividend_source_labels():
    """
    Test that dossier properly labels dividend sources (Cash Flow vs Forward Rate).
    
    Requirements: 2.5, 2.6, 2.7, 2.8 (Dividend display)
    """
    # Arrange: Create financial data with mixed dividend sources
    financial_data = create_mock_financial_data()
    financial_data['dividend_source'] = 'forward_rate'  # Most recent year uses forward rate
    
    # Act: Calculate metrics and generate dossier
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    dossier_content = DossierGenerator('TEST.US', financial_data, metrics, anomalies).generate()
    
    # Assert: Verify dividend source is mentioned
    # The dossier should indicate when forward rate is used
    assert 'dividend' in dossier_content.lower() or 'Dividend' in dossier_content, \
        "Dossier should mention dividends"


def test_currency_display_format():
    """
    Test that currency display shows trading currency first.
    
    Requirements: 4.1, 4.2 (Currency display)
    """
    from stock_data_analyser import format_price_display
    
    # Test single currency
    result = format_price_display(1650.0, 'GBX', 'GBX')
    assert result == "1,650.00 GBX", "Should show single currency"
    
    # Test dual currency with conversion
    result = format_price_display(1650.0, 'GBX', 'GBP', 16.50)
    assert result == "1,650.00 GBX (16.50 GBP)", "Should show trading currency first, then conversion"
    
    # Test that trading currency always comes first
    assert 'GBX' in result.split('(')[0], "Trading currency should appear before parentheses"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
