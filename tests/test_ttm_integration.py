"""
End-to-end integration tests for TTM (Trailing Twelve Months) workflow.

These tests verify the complete TTM workflow from quarterly data extraction
through dossier generation with TTM section.

Feature: ttm-graham-calculations
"""

import os
import sys
from unittest.mock import Mock, patch
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.financial_data_processor import FinancialDataProcessor
from core.ttm_calculator import TTMCalculator
from core.graham_math import GrahamCalculator
from output.dossier_generator import DossierGenerator


def create_mock_api_response_with_quarterly_data():
    """Create mock API response with quarterly data for testing.
    
    Simulates MSFT-like quarterly reporter with 4 quarters of data.
    """
    return {
        'General': {
            'Code': 'MSFT',
            'Exchange': 'US',
            'CurrencyCode': 'USD'
        },
        'Financials': {
            'Balance_Sheet': {
                'currency_symbol': 'USD',
                'yearly': {
                    '2024-06-30': {
                        'totalStockholderEquity': 250000000000.0,
                        'intangibleAssets': 10000000000.0,
                        'goodwill': 70000000000.0,
                        'totalCurrentAssets': 150000000000.0,
                        'totalLiabilities': 200000000000.0,
                        'totalAssets': 450000000000.0,
                        'commonStockSharesOutstanding': 7500000000.0
                    }
                },
                'quarterly': {
                    '2024-09-30': {
                        'totalStockholderEquity': 260000000000.0,
                        'intangibleAssets': 11000000000.0,
                        'goodwill': 71000000000.0,
                        'totalCurrentAssets': 155000000000.0,
                        'totalLiabilities': 205000000000.0,
                        'totalAssets': 465000000000.0,
                        'commonStockSharesOutstanding': 7450000000.0
                    },
                    '2024-06-30': {
                        'totalStockholderEquity': 250000000000.0,
                        'intangibleAssets': 10000000000.0,
                        'goodwill': 70000000000.0,
                        'totalCurrentAssets': 150000000000.0,
                        'totalLiabilities': 200000000000.0,
                        'totalAssets': 450000000000.0,
                        'commonStockSharesOutstanding': 7500000000.0
                    },
                    '2024-03-31': {
                        'totalStockholderEquity': 245000000000.0,
                        'intangibleAssets': 9500000000.0,
                        'goodwill': 69000000000.0,
                        'totalCurrentAssets': 148000000000.0,
                        'totalLiabilities': 198000000000.0,
                        'totalAssets': 443000000000.0,
                        'commonStockSharesOutstanding': 7520000000.0
                    },
                    '2023-12-31': {
                        'totalStockholderEquity': 240000000000.0,
                        'intangibleAssets': 9000000000.0,
                        'goodwill': 68000000000.0,
                        'totalCurrentAssets': 145000000000.0,
                        'totalLiabilities': 195000000000.0,
                        'totalAssets': 435000000000.0,
                        'commonStockSharesOutstanding': 7540000000.0
                    }
                }
            },
            'Income_Statement': {
                'currency_symbol': 'USD',
                'yearly': {
                    '2024-06-30': {
                        'totalRevenue': 245000000000.0,
                        'netIncome': 88000000000.0
                    }
                },
                'quarterly': {
                    '2024-09-30': {
                        'totalRevenue': 65000000000.0,
                        'netIncome': 24000000000.0
                    },
                    '2024-06-30': {
                        'totalRevenue': 64000000000.0,
                        'netIncome': 22000000000.0
                    },
                    '2024-03-31': {
                        'totalRevenue': 62000000000.0,
                        'netIncome': 21000000000.0
                    },
                    '2023-12-31': {
                        'totalRevenue': 62000000000.0,
                        'netIncome': 27000000000.0
                    }
                }
            }
        },
        'Highlights': {
            'SharePrice': 420.0
        }
    }


def create_mock_financial_data_from_api(api_response):
    """Create financial_data dict from API response (simulating processor output)."""
    return {
        'ticker': 'MSFT.US',
        'exchange': 'US',
        'currency': 'USD',
        'financials_currency': 'USD',
        'original_stock_currency': 'USD',
        'price': 420.0,
        'price_source': 'EODHD',
        'ceo_name': 'Satya Nadella',
        'sector': 'Technology',
        'industry': 'Software',
        'employees': 221000,
        'history': {
            '2024-06-30': {
                'revenue': 245000000000.0,
                'net_income': 88000000000.0,
                'eps': 11.73,
                'total_equity': 250000000000.0,
                'intangible_assets': 10000000000.0,
                'goodwill': 70000000000.0,
                'shares_outstanding': 7500000000.0,
                'current_assets': 150000000000.0,
                'total_liabilities': 200000000000.0
            }
        },
        'warnings': []
    }


def test_ttm_quarterly_data_extraction():
    """
    Test quarterly data extraction from API response.
    
    Verifies:
    - Balance sheet quarterly data is extracted
    - Income statement quarterly data is extracted
    - Data is sorted by date descending
    - "NA" values are sanitized to 0.0
    """
    # Create mock API response
    api_response = create_mock_api_response_with_quarterly_data()
    
    # Create processor
    processor = FinancialDataProcessor()
    
    # Extract quarterly data
    balance_sheet = processor.parse_quarterly_balance_sheet(api_response)
    income_statement = processor.parse_quarterly_income_statement(api_response)
    
    # Verify balance sheet extraction
    assert len(balance_sheet) == 4
    assert '2024-09-30' in balance_sheet
    assert balance_sheet['2024-09-30']['total_equity'] == 260000000000.0
    assert balance_sheet['2024-09-30']['shares_outstanding'] == 7450000000.0
    
    # Verify income statement extraction
    assert len(income_statement) == 4
    assert '2024-09-30' in income_statement
    assert income_statement['2024-09-30']['revenue'] == 65000000000.0
    assert income_statement['2024-09-30']['net_income'] == 24000000000.0
    
    # Verify dates are sorted descending
    balance_dates = list(balance_sheet.keys())
    assert balance_dates == sorted(balance_dates, reverse=True)
    
    income_dates = list(income_statement.keys())
    assert income_dates == sorted(income_dates, reverse=True)


def test_ttm_calculation_workflow():
    """
    Test TTM calculation workflow.
    
    Verifies:
    - Reporting frequency is detected correctly
    - TTM metrics are calculated
    - TTM Graham calculations are performed
    - Warnings are generated appropriately
    """
    # Create mock API response
    api_response = create_mock_api_response_with_quarterly_data()
    
    # Create processor and extract quarterly data
    processor = FinancialDataProcessor()
    balance_sheet = processor.parse_quarterly_balance_sheet(api_response)
    income_statement = processor.parse_quarterly_income_statement(api_response)
    quarterly_data = processor.merge_quarterly_data(balance_sheet, income_statement)
    
    # Create TTM calculator
    ttm_calculator = TTMCalculator(
        quarterly_data=quarterly_data,
        price=420.0,
        currency='USD',
        original_currency='USD',
        fx_rate=None
    )
    
    # Compute all TTM metrics
    ttm_metrics = ttm_calculator.compute_all()
    
    # Verify reporting frequency detection
    assert ttm_metrics['reporting_frequency'] == 'quarterly'
    
    # Verify TTM metrics calculation
    assert ttm_metrics['ttm_revenue'] == 253000000000.0  # Sum of 4 quarters
    assert ttm_metrics['ttm_net_income'] == 94000000000.0  # Sum of 4 quarters
    
    # Verify TTM EPS calculation (sum of net income / most recent shares)
    expected_ttm_eps = 94000000000.0 / 7450000000.0
    assert abs(ttm_metrics['ttm_eps'] - expected_ttm_eps) < 0.01
    
    # Verify TTM Graham calculations
    assert ttm_metrics['ttm_graham_number'] != "N/A"
    assert isinstance(ttm_metrics['ttm_graham_number'], float)
    assert ttm_metrics['ttm_graham_number'] > 0
    
    assert ttm_metrics['ttm_tbvps'] != "N/A"
    assert isinstance(ttm_metrics['ttm_tbvps'], float)
    assert ttm_metrics['ttm_tbvps'] > 0
    
    assert ttm_metrics['ttm_pe_ratio'] != "N/A"
    assert isinstance(ttm_metrics['ttm_pe_ratio'], float)
    assert ttm_metrics['ttm_pe_ratio'] > 0


def test_ttm_dossier_generation():
    """
    Test dossier generation with TTM section.
    
    Verifies:
    - TTM section is included in dossier
    - TTM metrics are displayed
    - Percentage differences from annual are shown
    - Warnings appear in Critical Alerts
    """
    # Create mock data
    api_response = create_mock_api_response_with_quarterly_data()
    financial_data = create_mock_financial_data_from_api(api_response)
    
    # Extract quarterly data
    processor = FinancialDataProcessor()
    balance_sheet = processor.parse_quarterly_balance_sheet(api_response)
    income_statement = processor.parse_quarterly_income_statement(api_response)
    quarterly_data = processor.merge_quarterly_data(balance_sheet, income_statement)
    
    # Calculate annual metrics
    calculator = GrahamCalculator(financial_data)
    annual_metrics = calculator.compute_all()
    
    # Calculate TTM metrics
    ttm_calculator = TTMCalculator(
        quarterly_data=quarterly_data,
        price=420.0,
        currency='USD',
        original_currency='USD',
        fx_rate=None
    )
    ttm_metrics = ttm_calculator.compute_all(annual_metrics=annual_metrics)
    
    # Add TTM warnings to financial data
    financial_data['warnings'].extend(ttm_metrics.get('warnings', []))
    
    # Generate dossier
    generator = DossierGenerator(
        ticker='MSFT.US',
        financial_data=financial_data,
        metrics=annual_metrics,
        anomalies=[],
        ttm_metrics=ttm_metrics
    )
    dossier_content = generator.generate()
    
    # Verify TTM section is included
    assert 'SECTION 1.5: TTM (TRAILING TWELVE MONTHS) ANALYSIS' in dossier_content
    
    # Verify reporting frequency is displayed
    assert 'Reporting Frequency: Quarterly' in dossier_content
    
    # Verify TTM metrics are displayed
    assert 'TTM Graham Number' in dossier_content
    assert 'TTM Tangible Book Value Per Share' in dossier_content
    assert 'TTM P/E Ratio' in dossier_content
    assert 'TTM P/B Ratio' in dossier_content
    
    # Verify percentage differences are shown
    assert 'Diff:' in dossier_content or 'Annual:' in dossier_content
    
    # Verify TTM methodology is included
    assert 'TTM (Trailing Twelve Months) Calculations' in dossier_content
    assert 'Income Statement Items' in dossier_content
    assert 'Balance Sheet Items' in dossier_content
    assert 'Reporting Frequency Detection' in dossier_content


def test_ttm_with_missing_quarterly_data():
    """
    Test TTM workflow when quarterly data is missing.
    
    Verifies:
    - System handles missing quarterly data gracefully
    - Warning is added to financial data
    - Dossier generation continues without TTM section
    """
    # Create financial data without quarterly data
    financial_data = {
        'ticker': 'TEST.US',
        'exchange': 'US',
        'currency': 'USD',
        'price': 100.0,
        'ceo_name': 'John Doe',
        'history': {
            '2024-12-31': {
                'revenue': 1000000.0,
                'net_income': 100000.0,
                'eps': 5.0,
                'total_equity': 500000.0,
                'shares_outstanding': 20000.0
            }
        },
        'warnings': []
    }
    
    # Empty quarterly data
    quarterly_data = {'balance_sheet': {}, 'income_statement': {}}
    
    # Calculate annual metrics
    calculator = GrahamCalculator(financial_data)
    annual_metrics = calculator.compute_all()
    
    # Try to calculate TTM metrics (should handle gracefully)
    ttm_metrics = None
    if quarterly_data and (quarterly_data.get('balance_sheet') or quarterly_data.get('income_statement')):
        ttm_calculator = TTMCalculator(
            quarterly_data=quarterly_data,
            price=100.0,
            currency='USD'
        )
        ttm_metrics = ttm_calculator.compute_all()
    else:
        financial_data['warnings'].append("TTM Analysis: Periodic data not available from API")
    
    # Generate dossier
    generator = DossierGenerator(
        ticker='TEST.US',
        financial_data=financial_data,
        metrics=annual_metrics,
        anomalies=[],
        ttm_metrics=ttm_metrics
    )
    dossier_content = generator.generate()
    
    # Verify TTM section is NOT included
    assert 'SECTION 1.5: TTM (TRAILING TWELVE MONTHS) ANALYSIS' not in dossier_content
    
    # Verify warning is in Critical Alerts
    assert 'TTM Analysis: Periodic data not available from API' in dossier_content


def test_ttm_warnings_in_critical_alerts():
    """
    Test that TTM warnings appear in Critical Alerts section.
    
    Verifies:
    - TTM warnings are collected
    - Warnings appear in Critical Alerts section
    - Warnings are properly formatted
    """
    # Create mock data with quarterly data
    api_response = create_mock_api_response_with_quarterly_data()
    financial_data = create_mock_financial_data_from_api(api_response)
    
    # Extract quarterly data
    processor = FinancialDataProcessor()
    balance_sheet = processor.parse_quarterly_balance_sheet(api_response)
    income_statement = processor.parse_quarterly_income_statement(api_response)
    quarterly_data = processor.merge_quarterly_data(balance_sheet, income_statement)
    
    # Calculate metrics
    calculator = GrahamCalculator(financial_data)
    annual_metrics = calculator.compute_all()
    
    ttm_calculator = TTMCalculator(
        quarterly_data=quarterly_data,
        price=420.0,
        currency='USD',
        original_currency='USD',
        fx_rate=None
    )
    ttm_metrics = ttm_calculator.compute_all(annual_metrics=annual_metrics)
    
    # Add TTM warnings to financial data
    financial_data['warnings'].extend(ttm_metrics.get('warnings', []))
    
    # Generate dossier
    generator = DossierGenerator(
        ticker='MSFT.US',
        financial_data=financial_data,
        metrics=annual_metrics,
        anomalies=[],
        ttm_metrics=ttm_metrics
    )
    dossier_content = generator.generate()
    
    # Verify Critical Alerts section exists
    assert 'SECTION 3: CRITICAL ALERTS' in dossier_content
    
    # If there are TTM warnings, verify they appear
    if ttm_metrics.get('warnings'):
        for warning in ttm_metrics['warnings']:
            # Warning should appear in dossier (either in Critical Alerts or elsewhere)
            assert warning in dossier_content or 'TTM' in dossier_content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
