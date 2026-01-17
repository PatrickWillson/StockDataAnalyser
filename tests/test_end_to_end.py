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

from core.eodhd_client import EODHDClient
from core.graham_math import GrahamCalculator
from core.anomaly_detector import AnomalyDetector
from stock_data_analyser import generate_dossier_content, save_dossier


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
    dossier_content = generate_dossier_content('TEST.US', financial_data, metrics, anomalies)
    
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
    assert '10-YEAR FINANCIALS' in dossier_content
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
    
    dossier_content = generate_dossier_content('TEST.US', financial_data, metrics, anomalies)
    
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
    
    dossier_content = generate_dossier_content('TEST.US', financial_data, metrics, anomalies)
    
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
    dossier_content = generate_dossier_content('TEST.US', financial_data, metrics, anomalies)
    
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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
