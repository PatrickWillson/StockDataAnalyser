"""
Tests for Defensive Investor Verdict section in dossier.

Requirements 6.1-6.5:
- Show "SUITABLE" or "NOT SUITABLE" based on test results
- List failed criteria with ❌ indicators
- Include Graham quote about defensive investing
- Provide clear recommendation
"""

import pytest
import sys
import os

# Add parent directory to path to import stock_data_analyser
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stock_data_analyser import generate_dossier_content


def test_defensive_verdict_suitable():
    """Test verdict when all defensive tests pass."""
    # Mock data with all tests passing
    financial_data = {
        'ticker': 'TEST.US',
        'price': 50.0,
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'ceo_name': 'Test CEO',
        'sector': 'Technology',
        'industry': 'Software',
        'employees': 1000,
        'history': {
            '2024-12-31': {
                'revenue': 1000000,
                'net_income': 100000,
                'eps': 5.0,
                'dividend': 1.0,
                'total_equity': 500000,
                'shares_outstanding': 10000
            }
        }
    }
    
    metrics = {
        'verdict': 'STRONG BUY',
        'graham_number': 100.0,
        'epv': 1000000,
        'epv_details': {
            'epv': 1000000,
            'epv_per_share': 100.0,
            'normalized_earnings': 100000,
            'years_used': 10,
            'cost_of_capital': 0.10
        },
        'net_net_value': 50.0,
        'margin_of_safety': 50.0,
        'defensive_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_assets': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'PASS',
            'pe_ratio': 'PASS',
            'pb_ratio': 'PASS'
        },
        'enterprising_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_assets': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'N/A - Not Required',
            'price_test': 'PASS'
        },
        'warnings': []
    }
    
    anomalies = []
    
    dossier = generate_dossier_content('TEST.US', financial_data, metrics, anomalies)
    
    # Verify verdict section exists
    assert "## GRAHAM DEFENSIVE INVESTOR VERDICT" in dossier
    assert "VERDICT: SUITABLE FOR DEFENSIVE INVESTORS" in dossier
    
    # Verify Graham quote is present (Requirement 6.3)
    assert "Graham's Guidance" in dossier
    assert "defensive investor should confine himself" in dossier
    
    # Verify recommendation is present (Requirement 6.5)
    assert "Recommendation" in dossier
    assert "stability, financial strength" in dossier
    
    # Verify checkmarks for passed tests
    assert "✓" in dossier


def test_defensive_verdict_not_suitable():
    """Test verdict when defensive tests fail."""
    financial_data = {
        'ticker': 'TEST.US',
        'price': 50.0,
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'ceo_name': 'Test CEO',
        'sector': 'Technology',
        'industry': 'Software',
        'employees': 1000,
        'history': {
            '2024-12-31': {
                'revenue': 1000000,
                'net_income': 100000,
                'eps': 5.0,
                'dividend': 1.0,
                'total_equity': 500000,
                'shares_outstanding': 10000
            }
        }
    }
    
    metrics = {
        'verdict': 'OVERVALUED',
        'graham_number': 100.0,
        'epv': 1000000,
        'epv_details': {
            'epv': 1000000,
            'epv_per_share': 100.0,
            'normalized_earnings': 100000,
            'years_used': 10,
            'cost_of_capital': 0.10
        },
        'net_net_value': 50.0,
        'margin_of_safety': -20.0,
        'defensive_tests': {
            'earnings_stability': 'FAIL',
            'current_ratio': 'FAIL',
            'debt_to_assets': 'PASS',
            'dividend_record': 'FAIL',
            'earnings_growth': 'FAIL',
            'pe_ratio': 'PASS',
            'pb_ratio': 'FAIL'
        },
        'enterprising_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_assets': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'N/A - Not Required',
            'price_test': 'PASS'
        },
        'warnings': []
    }
    
    anomalies = []
    
    dossier = generate_dossier_content('TEST.US', financial_data, metrics, anomalies)
    
    # Verify verdict section exists (Requirement 6.1)
    assert "## GRAHAM DEFENSIVE INVESTOR VERDICT" in dossier
    assert "VERDICT: NOT SUITABLE FOR DEFENSIVE INVESTORS" in dossier
    
    # Verify failed criteria are listed with ❌ (Requirement 6.2)
    assert "Failed Criteria:" in dossier
    assert "❌" in dossier
    assert "❌ Earnings Stability: FAIL" in dossier
    assert "❌ Current Ratio: FAIL" in dossier
    assert "❌ Dividend Record: FAIL" in dossier
    
    # Verify Graham quote is present (Requirement 6.3)
    assert "Graham's Guidance" in dossier
    assert "defensive investor should confine himself" in dossier
    
    # Verify recommendation is present (Requirement 6.2)
    assert "Recommendation" in dossier
    assert "avoid this stock" in dossier or "unsuitable" in dossier.lower()


def test_defensive_verdict_with_na_tests():
    """Test verdict when some tests are N/A (young company)."""
    financial_data = {
        'ticker': 'TEST.US',
        'price': 50.0,
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'ceo_name': 'Test CEO',
        'sector': 'Technology',
        'industry': 'Software',
        'employees': 1000,
        'history': {
            '2024-12-31': {
                'revenue': 1000000,
                'net_income': 100000,
                'eps': 5.0,
                'dividend': 1.0,
                'total_equity': 500000,
                'shares_outstanding': 10000
            }
        }
    }
    
    metrics = {
        'verdict': 'UNDERVALUED',
        'graham_number': 100.0,
        'epv': 1000000,
        'epv_details': {
            'epv': 1000000,
            'epv_per_share': 100.0,
            'normalized_earnings': 100000,
            'years_used': 10,
            'cost_of_capital': 0.10
        },
        'net_net_value': 50.0,
        'margin_of_safety': 10.0,
        'defensive_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_assets': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'N/A (Too Young)',  # Young company
            'pe_ratio': 'PASS',
            'pb_ratio': 'PASS'
        },
        'enterprising_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_assets': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'N/A - Not Required',
            'price_test': 'PASS'
        },
        'warnings': []
    }
    
    anomalies = []
    
    dossier = generate_dossier_content('TEST.US', financial_data, metrics, anomalies)
    
    # N/A tests should not count as failures
    assert "VERDICT: SUITABLE FOR DEFENSIVE INVESTORS" in dossier
    
    # Should not list N/A as a failed criterion
    assert "❌ Earnings Growth: N/A" not in dossier


def test_defensive_verdict_section_placement():
    """Test that verdict section appears after defensive tests."""
    financial_data = {
        'ticker': 'TEST.US',
        'price': 50.0,
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'ceo_name': 'Test CEO',
        'sector': 'Technology',
        'industry': 'Software',
        'employees': 1000,
        'history': {
            '2024-12-31': {
                'revenue': 1000000,
                'net_income': 100000,
                'eps': 5.0,
                'dividend': 1.0,
                'total_equity': 500000,
                'shares_outstanding': 10000
            }
        }
    }
    
    metrics = {
        'verdict': 'STRONG BUY',
        'graham_number': 100.0,
        'epv': 1000000,
        'epv_details': {
            'epv': 1000000,
            'epv_per_share': 100.0,
            'normalized_earnings': 100000,
            'years_used': 10,
            'cost_of_capital': 0.10
        },
        'net_net_value': 50.0,
        'margin_of_safety': 50.0,
        'defensive_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_assets': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'PASS',
            'pe_ratio': 'PASS',
            'pb_ratio': 'PASS'
        },
        'enterprising_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_assets': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'N/A - Not Required',
            'price_test': 'PASS'
        },
        'warnings': []
    }
    
    anomalies = []
    
    dossier = generate_dossier_content('TEST.US', financial_data, metrics, anomalies)
    
    # Find positions of sections
    defensive_tests_pos = dossier.find("## SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS")
    verdict_pos = dossier.find("## GRAHAM DEFENSIVE INVESTOR VERDICT")
    enterprising_tests_pos = dossier.find("## SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS")
    
    # Verify order: Defensive Tests -> Verdict -> Enterprising Tests
    assert defensive_tests_pos < verdict_pos < enterprising_tests_pos
