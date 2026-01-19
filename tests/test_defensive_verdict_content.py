"""
Additional tests for Defensive Investor Verdict content validation.

Validates specific requirements:
- Requirements 6.1: Show verdict after defensive tests
- Requirements 6.2: List failed criteria with ❌
- Requirements 6.3: Include Graham quote
- Requirements 6.4: Show SUITABLE when all pass
- Requirements 6.5: Highlight key strengths
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stock_data_analyser import generate_dossier_content


def test_verdict_shows_all_passed_tests():
    """Requirement 6.5: Highlight key strengths when suitable."""
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
    
    dossier = generate_dossier_content('TEST.US', financial_data, metrics, {})
    
    # Should list all passed tests with checkmarks
    assert "✓ Earnings Stability" in dossier
    assert "✓ Current Ratio" in dossier
    assert "✓ Debt To Assets" in dossier
    assert "✓ Dividend Record" in dossier
    assert "✓ Earnings Growth" in dossier
    assert "✓ Pe Ratio" in dossier
    assert "✓ Pb Ratio" in dossier


def test_verdict_recommendation_varies_by_failure_count():
    """Test that recommendation text varies based on number of failures."""
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
    
    # Test with 1 failure
    metrics_one_fail = {
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
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_assets': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'PASS',
            'pe_ratio': 'FAIL',  # Only 1 failure
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
    
    dossier_one = generate_dossier_content('TEST.US', financial_data, metrics_one_fail, {})
    assert "fails one of Graham's defensive investor criteria" in dossier_one
    
    # Test with multiple failures (2-3)
    metrics_multi_fail = {
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
            'dividend_record': 'PASS',
            'earnings_growth': 'PASS',
            'pe_ratio': 'FAIL',  # 3 failures
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
    
    dossier_multi = generate_dossier_content('TEST.US', financial_data, metrics_multi_fail, {})
    assert "fails multiple Graham defensive investor criteria" in dossier_multi
    
    # Test with many failures (>3)
    metrics_many_fail = {
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
            'debt_to_assets': 'FAIL',
            'dividend_record': 'FAIL',
            'earnings_growth': 'FAIL',  # 5 failures
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
    
    dossier_many = generate_dossier_content('TEST.US', financial_data, metrics_many_fail, {})
    assert "fails most of Graham's defensive investor tests" in dossier_many
    assert "clearly unsuitable" in dossier_many


def test_verdict_graham_quote_present():
    """Requirement 6.3: Verify Graham quote is always present."""
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
    
    # Test with passing
    metrics_pass = {
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
    
    dossier_pass = generate_dossier_content('TEST.US', financial_data, metrics_pass, {})
    
    # Verify quote is present
    assert "Graham's Guidance" in dossier_pass
    assert "defensive investor should confine himself to the shares of important companies" in dossier_pass
    
    # Test with failing
    metrics_fail = metrics_pass.copy()
    metrics_fail['defensive_tests'] = {
        'earnings_stability': 'FAIL',
        'current_ratio': 'FAIL',
        'debt_to_assets': 'FAIL',
        'dividend_record': 'FAIL',
        'earnings_growth': 'FAIL',
        'pe_ratio': 'FAIL',
        'pb_ratio': 'FAIL'
    }
    
    dossier_fail = generate_dossier_content('TEST.US', financial_data, metrics_fail, {})
    
    # Quote should be present in both cases
    assert "Graham's Guidance" in dossier_fail
    assert "defensive investor should confine himself to the shares of important companies" in dossier_fail
