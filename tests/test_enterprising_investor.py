"""
Test for Enterprising Investor Assessment section in dossier.

Requirements 7.1-7.7: Verify that the Enterprising Investor Assessment section
is generated with proper evaluation of recent profitability, balance sheet strength,
ROE/ROA trends, valuation, and appropriate verdict.
"""

import os
import sys
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.graham_math import GrahamCalculator
from core.anomaly_detector import AnomalyDetector
from stock_data_analyser import generate_dossier_content


def create_strong_company_data():
    """Create mock data for a company with strong current fundamentals."""
    return {
        'ticker': 'STRONG.US',
        'exchange': 'NASDAQ',
        'currency': 'USD',
        'price': 50.0,
        'ceo_name': 'Jane Smith',
        'sector': 'Technology',
        'industry': 'Software',
        'employees': 1000,
        'roe': 0.20,  # 20% ROE
        'roa': 0.12,  # 12% ROA
        'pe_ratio': 12.0,
        'price_to_book': 1.1,
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
                'current_assets': 40000000.0,
                'current_liabilities': 20000000.0,
                'total_liabilities': 25000000.0,
                'long_term_debt': 5000000.0,
                'total_assets': 75000000.0,
                'cash': 30000000.0
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
                'current_assets': 38000000.0,
                'current_liabilities': 19000000.0,
                'total_liabilities': 24000000.0,
                'long_term_debt': 5000000.0,
                'total_assets': 72000000.0,
                'cash': 28000000.0
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
                'current_assets': 36000000.0,
                'current_liabilities': 18000000.0,
                'total_liabilities': 23000000.0,
                'long_term_debt': 5000000.0,
                'total_assets': 69000000.0,
                'cash': 26000000.0
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
                'current_assets': 34000000.0,
                'current_liabilities': 17000000.0,
                'total_liabilities': 22000000.0,
                'long_term_debt': 5000000.0,
                'total_assets': 66000000.0,
                'cash': 24000000.0
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
                'current_assets': 32000000.0,
                'current_liabilities': 16000000.0,
                'total_liabilities': 21000000.0,
                'long_term_debt': 5000000.0,
                'total_assets': 63000000.0,
                'cash': 22000000.0
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
                'current_assets': 30000000.0,
                'current_liabilities': 15000000.0,
                'total_liabilities': 20000000.0,
                'long_term_debt': 5000000.0,
                'total_assets': 60000000.0,
                'cash': 20000000.0
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
                'current_assets': 28000000.0,
                'current_liabilities': 14000000.0,
                'total_liabilities': 19000000.0,
                'long_term_debt': 5000000.0,
                'total_assets': 57000000.0,
                'cash': 18000000.0
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
                'current_assets': 26000000.0,
                'current_liabilities': 13000000.0,
                'total_liabilities': 18000000.0,
                'long_term_debt': 5000000.0,
                'total_assets': 54000000.0,
                'cash': 16000000.0
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
                'current_assets': 24000000.0,
                'current_liabilities': 12000000.0,
                'total_liabilities': 17000000.0,
                'long_term_debt': 5000000.0,
                'total_assets': 51000000.0,
                'cash': 14000000.0
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
                'current_assets': 22000000.0,
                'current_liabilities': 11000000.0,
                'total_liabilities': 16000000.0,
                'long_term_debt': 5000000.0,
                'total_assets': 48000000.0,
                'cash': 12000000.0
            }
        },
        'warnings': []
    }


def create_weak_company_data():
    """Create mock data for a company with weak fundamentals."""
    return {
        'ticker': 'WEAK.US',
        'exchange': 'NASDAQ',
        'currency': 'USD',
        'price': 50.0,
        'ceo_name': 'Bob Jones',
        'sector': 'Retail',
        'industry': 'Department Stores',
        'employees': 500,
        'roe': 0.05,  # 5% ROE
        'roa': 0.02,  # 2% ROA
        'pe_ratio': 20.0,
        'price_to_book': 2.0,
        'history': {
            '2023': {
                'revenue': 100000000.0,
                'net_income': -5000000.0,  # Loss
                'eps': -2.5,
                'dividend': 0.0,
                'total_equity': 50000000.0,
                'intangible_assets': 5000000.0,
                'goodwill': 2000000.0,
                'shares_outstanding': 2000000.0,
                'current_assets': 20000000.0,
                'current_liabilities': 18000000.0,
                'total_liabilities': 45000000.0,
                'long_term_debt': 27000000.0,
                'total_assets': 95000000.0,
                'cash': 5000000.0
            },
            '2022': {
                'revenue': 95000000.0,
                'net_income': 2000000.0,
                'eps': 1.0,
                'dividend': 0.0,
                'total_equity': 48000000.0,
                'intangible_assets': 4800000.0,
                'goodwill': 1900000.0,
                'shares_outstanding': 2000000.0,
                'current_assets': 19000000.0,
                'current_liabilities': 17000000.0,
                'total_liabilities': 44000000.0,
                'long_term_debt': 27000000.0,
                'total_assets': 92000000.0,
                'cash': 4500000.0
            },
            '2021': {
                'revenue': 90000000.0,
                'net_income': -3000000.0,  # Loss
                'eps': -1.5,
                'dividend': 0.0,
                'total_equity': 46000000.0,
                'intangible_assets': 4600000.0,
                'goodwill': 1800000.0,
                'shares_outstanding': 2000000.0,
                'current_assets': 18000000.0,
                'current_liabilities': 16000000.0,
                'total_liabilities': 43000000.0,
                'long_term_debt': 27000000.0,
                'total_assets': 89000000.0,
                'cash': 4000000.0
            }
        },
        'warnings': []
    }


def test_enterprising_assessment_section_exists():
    """
    Test that the Enterprising Investor Assessment section is generated.
    
    Requirement 7.1: System SHALL include an "Enterprising Investor Assessment" section
    """
    # Arrange
    financial_data = create_strong_company_data()
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    # Act
    dossier_content = generate_dossier_content('STRONG.US', financial_data, metrics, anomalies)
    
    # Assert
    assert 'GRAHAM ENTERPRISING INVESTOR ASSESSMENT' in dossier_content


def test_enterprising_assessment_evaluates_profitability():
    """
    Test that the assessment evaluates recent 3-5 year profitability trends.
    
    Requirement 7.2: System SHALL evaluate recent 3-5 year profitability trends
    """
    # Arrange
    financial_data = create_strong_company_data()
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    # Act
    dossier_content = generate_dossier_content('STRONG.US', financial_data, metrics, anomalies)
    
    # Assert
    assert 'Recent Profitability Trends' in dossier_content
    assert 'consecutive profitable years' in dossier_content or 'years profitable' in dossier_content


def test_enterprising_assessment_evaluates_balance_sheet():
    """
    Test that the assessment evaluates current balance sheet strength.
    
    Requirement 7.3: System SHALL evaluate current balance sheet strength (cash, debt, current ratio)
    """
    # Arrange
    financial_data = create_strong_company_data()
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    # Act
    dossier_content = generate_dossier_content('STRONG.US', financial_data, metrics, anomalies)
    
    # Assert
    assert 'Current Balance Sheet Strength' in dossier_content
    assert 'Cash Position' in dossier_content
    assert 'Debt' in dossier_content
    assert 'Current Ratio' in dossier_content


def test_enterprising_assessment_evaluates_roe_roa():
    """
    Test that the assessment evaluates recent ROE and ROA trends.
    
    Requirement 7.4: System SHALL evaluate recent ROE and ROA trends
    """
    # Arrange
    financial_data = create_strong_company_data()
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    # Act
    dossier_content = generate_dossier_content('STRONG.US', financial_data, metrics, anomalies)
    
    # Assert
    assert 'Recent Return Metrics' in dossier_content
    assert 'ROE' in dossier_content
    assert 'ROA' in dossier_content


def test_enterprising_assessment_evaluates_valuation():
    """
    Test that the assessment evaluates current valuation (P/E, P/B).
    
    Requirement 7.5: System SHALL evaluate current valuation (P/E, P/B)
    """
    # Arrange
    financial_data = create_strong_company_data()
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    # Act
    dossier_content = generate_dossier_content('STRONG.US', financial_data, metrics, anomalies)
    
    # Assert
    assert 'Current Valuation' in dossier_content
    assert 'P/E Ratio' in dossier_content
    assert 'P/B Ratio' in dossier_content


def test_enterprising_assessment_potential_opportunity_verdict():
    """
    Test that strong companies are labeled as "POTENTIAL OPPORTUNITY".
    
    Requirement 7.6: System SHALL label as "POTENTIAL OPPORTUNITY" or "NOT SUITABLE"
    """
    # Arrange
    financial_data = create_strong_company_data()
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    # Act
    dossier_content = generate_dossier_content('STRONG.US', financial_data, metrics, anomalies)
    
    # Assert
    assert 'POTENTIAL OPPORTUNITY' in dossier_content


def test_enterprising_assessment_not_suitable_verdict():
    """
    Test that weak companies are labeled as "NOT SUITABLE".
    
    Requirement 7.6: System SHALL label as "POTENTIAL OPPORTUNITY" or "NOT SUITABLE"
    """
    # Arrange
    financial_data = create_weak_company_data()
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    # Act
    dossier_content = generate_dossier_content('WEAK.US', financial_data, metrics, anomalies)
    
    # Assert
    assert 'NOT SUITABLE' in dossier_content


def test_enterprising_assessment_includes_graham_quote():
    """
    Test that the assessment includes Graham quote about enterprising investors.
    
    Requirement 7.7: System SHALL include Graham's quote about enterprising investors
    """
    # Arrange
    financial_data = create_strong_company_data()
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    # Act
    dossier_content = generate_dossier_content('STRONG.US', financial_data, metrics, anomalies)
    
    # Assert
    assert "Graham's Guidance" in dossier_content
    assert 'enterprising investor' in dossier_content.lower()


def test_enterprising_assessment_risk_warning_short_track_record():
    """
    Test that risk warning is added for companies with short track records.
    
    Requirement 7.7: System SHALL add risk warning for companies with short track records
    """
    # Arrange - Create company with only 5 years of history
    financial_data = create_strong_company_data()
    # Keep only 5 years
    years_to_keep = ['2023', '2022', '2021', '2020', '2019']
    financial_data['history'] = {
        year: financial_data['history'][year] 
        for year in years_to_keep
    }
    
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    detector = AnomalyDetector(financial_data)
    anomalies = detector.scan()
    
    # Act
    dossier_content = generate_dossier_content('STRONG.US', financial_data, metrics, anomalies)
    
    # Assert
    assert 'RISK WARNING' in dossier_content or 'risk warning' in dossier_content.lower()
    assert 'track record' in dossier_content.lower() or 'history' in dossier_content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
