"""
Unit tests for Enterprising Investor functionality.
"""

from core.graham_math import GrahamCalculator


def test_enterprising_investor_tests_structure():
    """Test that enterprising investor tests return correct structure."""
    financial_data = {
        'ticker': 'TEST.US',
        'price': 50.0,
        'currency': 'USD',
        'history': {
            '2023': {
                'net_income': 100000.0,
                'current_assets': 2000000.0,
                'current_liabilities': 1000000.0,
                'total_liabilities': 1200000.0,
                'long_term_debt': 200000.0,
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'shares_outstanding': 1000000.0,
                'eps': 5.0,
                'dividend': 1.0
            },
            '2022': {'net_income': 90000.0, 'eps': 4.5, 'dividend': 1.0},
            '2021': {'net_income': 80000.0, 'eps': 4.0, 'dividend': 1.0},
            '2020': {'net_income': 70000.0, 'eps': 3.5, 'dividend': 1.0},
            '2019': {'net_income': 60000.0, 'eps': 3.0, 'dividend': 1.0}
        }
    }
    
    calculator = GrahamCalculator(financial_data)
    results = calculator.run_investor_tests("enterprising")
    
    # Verify structure
    assert 'earnings_stability' in results
    assert 'current_ratio' in results
    assert 'debt_to_assets' in results
    assert 'dividend_record' in results
    assert 'earnings_growth' in results
    assert 'price_test' in results
    
    # Verify earnings growth is not required
    assert results['earnings_growth'] == 'N/A - Not Required'


def test_enterprising_current_ratio():
    """Test that enterprising current ratio threshold is 1.5."""
    financial_data = {
        'ticker': 'TEST.US',
        'price': 50.0,
        'currency': 'USD',
        'history': {
            '2023': {
                'current_assets': 1600000.0,  # Ratio = 1.6 (passes enterprising, fails defensive)
                'current_liabilities': 1000000.0,
                'net_income': 100000.0,
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'shares_outstanding': 1000000.0,
                'eps': 5.0,
                'dividend': 1.0,
                'long_term_debt': 100000.0,
                'total_liabilities': 1100000.0
            }
        }
    }
    
    calculator = GrahamCalculator(financial_data)
    
    # Enterprising should pass with ratio 1.6
    ent_results = calculator.run_investor_tests("enterprising")
    assert ent_results['current_ratio'] == 'PASS'
    
    # Defensive should fail with ratio 1.6 (needs 2.0)
    def_results = calculator.run_investor_tests("defensive")
    assert def_results['current_ratio'] == 'FAIL'


def test_enterprising_earnings_stability():
    """Test that enterprising requires 5 years of positive earnings."""
    financial_data = {
        'ticker': 'TEST.US',
        'price': 50.0,
        'currency': 'USD',
        'history': {
            '2023': {'net_income': 100000.0, 'eps': 5.0, 'dividend': 1.0, 'current_assets': 2000000.0, 'current_liabilities': 1000000.0, 'total_equity': 1000000.0, 'intangible_assets': 0.0, 'goodwill': 0.0, 'shares_outstanding': 1000000.0, 'long_term_debt': 100000.0, 'total_liabilities': 1100000.0},
            '2022': {'net_income': 90000.0, 'eps': 4.5, 'dividend': 1.0},
            '2021': {'net_income': 80000.0, 'eps': 4.0, 'dividend': 1.0},
            '2020': {'net_income': 70000.0, 'eps': 3.5, 'dividend': 1.0},
            '2019': {'net_income': 60000.0, 'eps': 3.0, 'dividend': 1.0},
            '2018': {'net_income': -10000.0, 'eps': -0.5, 'dividend': 1.0},  # Negative year
            '2017': {'net_income': 40000.0, 'eps': 2.0, 'dividend': 1.0}
        }
    }
    
    calculator = GrahamCalculator(financial_data)
    
    # Enterprising should pass (5 consecutive positive years)
    ent_results = calculator.run_investor_tests("enterprising")
    assert ent_results['earnings_stability'] == 'PASS'
    
    # Defensive should fail (only 6 of last 10 years positive, needs 8)
    def_results = calculator.run_investor_tests("defensive")
    assert def_results['earnings_stability'] == 'FAIL'


def test_compute_all_includes_both_test_suites():
    """Test that compute_all returns both defensive and enterprising tests."""
    financial_data = {
        'ticker': 'TEST.US',
        'price': 50.0,
        'currency': 'USD',
        'history': {
            '2023': {
                'net_income': 100000.0,
                'current_assets': 2000000.0,
                'current_liabilities': 1000000.0,
                'total_liabilities': 1200000.0,
                'long_term_debt': 200000.0,
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'shares_outstanding': 1000000.0,
                'eps': 5.0,
                'dividend': 1.0
            }
        }
    }
    
    calculator = GrahamCalculator(financial_data)
    results = calculator.compute_all()
    
    # Verify both test suites are present
    assert 'defensive_tests' in results
    assert 'enterprising_tests' in results
    
    # Verify they have different structures
    assert 'pe_ratio' in results['defensive_tests']
    assert 'pb_ratio' in results['defensive_tests']
    assert 'price_test' in results['enterprising_tests']


def test_enterprising_buy_verdict():
    """Test that verdict is 'ENTERPRISING BUY' when defensive fails but enterprising passes."""
    financial_data = {
        'ticker': 'TEST.US',
        'price': 8.0,  # Low P/E for enterprising
        'currency': 'USD',
        'history': {
            '2023': {
                'net_income': 100000.0,
                'current_assets': 1600000.0,  # Ratio 1.6 - passes enterprising, fails defensive
                'current_liabilities': 1000000.0,
                'total_liabilities': 1100000.0,
                'long_term_debt': 100000.0,
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'shares_outstanding': 1000000.0,
                'eps': 1.0,  # P/E = 8 (passes enterprising)
                'dividend': 1.0
            },
            '2022': {'net_income': 90000.0, 'eps': 0.9, 'dividend': 1.0},
            '2021': {'net_income': 80000.0, 'eps': 0.8, 'dividend': 1.0},
            '2020': {'net_income': 70000.0, 'eps': 0.7, 'dividend': 1.0},
            '2019': {'net_income': 60000.0, 'eps': 0.6, 'dividend': 1.0}
        }
    }
    
    calculator = GrahamCalculator(financial_data)
    results = calculator.compute_all()
    
    # Should get ENTERPRISING BUY verdict
    assert results['verdict'] == 'ENTERPRISING BUY'


if __name__ == '__main__':
    test_enterprising_investor_tests_structure()
    test_enterprising_current_ratio()
    test_enterprising_earnings_stability()
    test_compute_all_includes_both_test_suites()
    test_enterprising_buy_verdict()
    print("All enterprising investor tests passed!")
