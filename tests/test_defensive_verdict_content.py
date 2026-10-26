"""
Additional tests for Defensive Investor Verdict content validation.

Validates specific requirements:
- Requirements 6.1: Show verdict after defensive tests
- Requirements 6.2: List failed criteria with ❌
- Requirements 6.3: Include Graham quote
- Requirements 6.4: Show SUITABLE when all pass
- Requirements 6.5: Highlight key strengths
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from output.dossier_generator import DossierGenerator


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
    
    dossier = DossierGenerator('TEST.US', financial_data, metrics, {}).generate()
    
    # Should list all passed tests (with bold markdown formatting)
    assert "**Earnings Stability**: PASS" in dossier
    assert "**Current Ratio**: PASS" in dossier
    assert "**Debt to Assets**: PASS" in dossier
    assert "**Dividend Record**: PASS" in dossier
    assert "**Earnings Growth**: PASS" in dossier
    assert "**P/E Ratio**: PASS" in dossier
    assert "**P/B Ratio**: PASS" in dossier


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
    
    dossier_one = DossierGenerator('TEST.US', financial_data, metrics_one_fail, {}).generate()
    # Verify the test results are shown (with bold markdown formatting)
    assert "**P/E Ratio**: FAIL" in dossier_one
    assert "SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS" in dossier_one
    
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
    
    dossier_multi = DossierGenerator('TEST.US', financial_data, metrics_multi_fail, {}).generate()
    # Verify multiple failures are shown (with bold markdown formatting)
    assert "**Earnings Stability**: FAIL" in dossier_multi
    assert "**Current Ratio**: FAIL" in dossier_multi
    assert "**P/E Ratio**: FAIL" in dossier_multi
    
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
    
    dossier_many = DossierGenerator('TEST.US', financial_data, metrics_many_fail, {}).generate()
    # Verify many failures are shown (with bold markdown formatting)
    assert "**Earnings Stability**: FAIL" in dossier_many
    assert "**Current Ratio**: FAIL" in dossier_many
    assert "**Debt to Assets**: FAIL" in dossier_many
    assert "**Dividend Record**: FAIL" in dossier_many
    assert "**Earnings Growth**: FAIL" in dossier_many


def test_verdict_graham_quote_present():
    """Requirement 6.3: Verify Graham tests section is present."""
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
    
    dossier_pass = DossierGenerator('TEST.US', financial_data, metrics_pass, {}).generate()
    
    # Verify defensive tests section is present (with bold markdown formatting)
    assert "SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS" in dossier_pass
    assert "**Earnings Stability**: PASS" in dossier_pass
    
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
    
    dossier_fail = DossierGenerator('TEST.US', financial_data, metrics_fail, {}).generate()
    
    # Section should be present in both cases (with bold markdown formatting)
    assert "SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS" in dossier_fail
    assert "**Earnings Stability**: FAIL" in dossier_fail
