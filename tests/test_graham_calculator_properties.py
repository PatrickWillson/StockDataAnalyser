"""
Property-based tests for GrahamCalculator using Hypothesis.

These tests verify universal properties that should hold across all valid inputs.
Each test runs 100+ iterations with randomly generated data.
"""

from hypothesis import given, strategies as st, settings
import math
from core.graham_math import GrahamCalculator


# Feature: stock-data-analyser, Property 4: TBVPS calculation correctness
# Validates: Requirements 4.2
@settings(max_examples=100)
@given(
    equity=st.floats(min_value=1.0, max_value=1e12, allow_nan=False, allow_infinity=False),
    intangibles=st.floats(min_value=0.0, max_value=1e11, allow_nan=False, allow_infinity=False),
    goodwill=st.floats(min_value=0.0, max_value=1e11, allow_nan=False, allow_infinity=False),
    shares=st.floats(min_value=1.0, max_value=1e10, allow_nan=False, allow_infinity=False)
)
def test_tbvps_calculation_correctness(equity, intangibles, goodwill, shares):
    """
    Property: For any valid financial data, TBVPS should equal 
    (Total Equity - Intangible Assets - Goodwill) / Shares Outstanding.
    
    This test verifies the TBVPS formula is correctly implemented.
    """
    # Arrange: Create financial data with random values
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
        'currency': 'USD',
        'history': {
            '2023': {
                'total_equity': equity,
                'intangible_assets': intangibles,
                'goodwill': goodwill,
                'shares_outstanding': shares,
                'eps': 5.0,
                'revenue': 1000000.0,
                'net_income': 100000.0
            }
        }
    }
    
    # Act: Calculate TBVPS
    calculator = GrahamCalculator(financial_data)
    result = calculator.compute_tbvps()
    
    # Assert: Verify formula correctness
    expected_tbvps = (equity - intangibles - goodwill) / shares
    
    # Handle negative TBVPS case
    if expected_tbvps < 0:
        assert result == "N/A", f"Expected 'N/A' for negative TBVPS, got {result}"
    else:
        assert isinstance(result, float), f"Expected float, got {type(result)}"
        assert abs(result - round(expected_tbvps, 2)) < 0.01, \
            f"TBVPS mismatch: expected {round(expected_tbvps, 2)}, got {result}"


# Feature: stock-data-analyser, Property 5: Graham Number formula correctness
# Validates: Requirements 4.3
@settings(max_examples=100)
@given(
    eps=st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False),
    tbvps=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_graham_number_formula_correctness(eps, tbvps):
    """
    Property: For any valid positive EPS and TBVPS, Graham Number should equal 
    sqrt(22.5 × EPS × TBVPS).
    
    This test verifies the Graham Number formula is correctly implemented.
    """
    # Arrange: Create financial data with positive EPS and valid equity
    # We need to reverse-engineer equity from TBVPS
    shares = 1000000.0  # Fixed shares for simplicity
    total_equity = tbvps * shares
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
        'currency': 'USD',
        'history': {
            '2023': {
                'total_equity': total_equity,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'shares_outstanding': shares,
                'eps': eps,
                'revenue': 1000000.0,
                'net_income': 100000.0
            }
        }
    }
    
    # Act: Calculate Graham Number
    calculator = GrahamCalculator(financial_data)
    result = calculator.compute_graham_number()
    
    # Assert: Verify formula correctness
    # The implementation rounds to 2 decimals, so we compare the unrounded expected
    # value to the result, allowing for rounding tolerance
    expected_graham = math.sqrt(22.5 * eps * tbvps)
    
    assert isinstance(result, float), f"Expected float, got {type(result)}"
    # Result is rounded to 2 decimals, so tolerance should account for rounding
    assert abs(result - expected_graham) < 0.01, \
        f"Graham Number mismatch: expected ~{round(expected_graham, 2)}, got {result}"


# Feature: stock-data-analyser, Property 13: Net-Net Value calculation correctness
# Validates: Requirements 13.1
@settings(max_examples=100)
@given(
    current_assets=st.floats(min_value=1.0, max_value=1e12, allow_nan=False, allow_infinity=False),
    total_liabilities=st.floats(min_value=0.0, max_value=1e12, allow_nan=False, allow_infinity=False),
    shares=st.floats(min_value=1.0, max_value=1e10, allow_nan=False, allow_infinity=False)
)
def test_net_net_value_calculation_correctness(current_assets, total_liabilities, shares):
    """
    Property: For any valid balance sheet data, Net-Net Value should equal 
    (Current Assets - Total Liabilities) / Shares Outstanding.
    
    This test verifies the Net-Net Value formula is correctly implemented.
    """
    # Arrange: Create financial data with random balance sheet values
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
        'currency': 'USD',
        'history': {
            '2023': {
                'current_assets': current_assets,
                'total_liabilities': total_liabilities,
                'shares_outstanding': shares,
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'eps': 5.0
            }
        }
    }
    
    # Act: Calculate Net-Net Value
    calculator = GrahamCalculator(financial_data)
    result = calculator.compute_net_net()
    
    # Assert: Verify formula correctness
    expected_net_net = (current_assets - total_liabilities) / shares
    
    assert isinstance(result, float), f"Expected float, got {type(result)}"
    assert abs(result - expected_net_net) < 0.01, \
        f"Net-Net Value mismatch: expected ~{round(expected_net_net, 2)}, got {result}"


# Feature: stock-data-analyser, Property 6: Margin of Safety formula correctness
# Validates: Requirements 5.1
@settings(max_examples=100)
@given(
    graham_number=st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    price=st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
def test_margin_of_safety_formula_correctness(graham_number, price):
    """
    Property: For any valid Graham Number and price, Margin of Safety should equal 
    ((Graham Number - Price) / Graham Number) × 100.
    
    This test verifies the Margin of Safety formula is correctly implemented.
    """
    # Arrange: Create calculator with dummy data
    financial_data = {
        'ticker': 'TEST.US',
        'price': price,
        'currency': 'USD',
        'history': {}
    }
    
    calculator = GrahamCalculator(financial_data)
    
    # Act: Calculate Margin of Safety
    result = calculator.compute_margin_of_safety(graham_number, price)
    
    # Assert: Verify formula correctness
    expected_mos = ((graham_number - price) / graham_number) * 100
    
    assert isinstance(result, float), f"Expected float, got {type(result)}"
    assert abs(result - expected_mos) < 0.1, \
        f"Margin of Safety mismatch: expected ~{round(expected_mos, 1)}, got {result}"


# Feature: stock-data-analyser, Property 10: EPV normalization correctness
# Validates: Requirements 8.1
@settings(max_examples=100)
@given(
    earnings_list=st.lists(
        st.floats(min_value=-1e9, max_value=1e9, allow_nan=False, allow_infinity=False),
        min_size=5,
        max_size=10
    )
)
def test_epv_normalization_correctness(earnings_list):
    """
    Property: For any earnings history, normalized earnings should equal 
    the average of the most recent 5-10 years of earnings.
    
    This test verifies the EPV normalization is correctly implemented.
    """
    # Arrange: Create financial data with random earnings history
    history = {}
    for i, earnings in enumerate(earnings_list):
        year = str(2023 - i)
        history[year] = {
            'net_income': earnings,
            'total_equity': 1000000.0,
            'intangible_assets': 0.0,
            'goodwill': 0.0,
            'shares_outstanding': 1000000.0,
            'eps': 5.0
        }
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
        'currency': 'USD',
        'history': history
    }
    
    # Act: Calculate EPV
    calculator = GrahamCalculator(financial_data)
    result = calculator.compute_epv()
    
    # Assert: Verify normalization correctness
    normalized_earnings = sum(earnings_list) / len(earnings_list)
    expected_epv = normalized_earnings / 0.10  # Cost of capital = 10%
    
    # EPV now returns a dict with detailed breakdown
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert 'epv' in result, "Result should contain 'epv' key"
    assert abs(result['epv'] - expected_epv) < 0.01, \
        f"EPV mismatch: expected ~{round(expected_epv, 2)}, got {result['epv']}"


# Feature: stock-data-analyser, Property 7: Earnings stability test correctness
# Validates: Requirements 6.1
@settings(max_examples=100)
@given(
    earnings_list=st.lists(
        st.floats(min_value=-1e9, max_value=1e9, allow_nan=False, allow_infinity=False),
        min_size=10,
        max_size=10
    )
)
def test_earnings_stability_test_correctness(earnings_list):
    """
    Property: For any earnings history, the earnings stability test should pass 
    if and only if at least 8 of the last 10 years have positive earnings.
    
    This test verifies the earnings stability test logic is correctly implemented.
    """
    # Arrange: Create financial data with 10 years of earnings
    history = {}
    for i, earnings in enumerate(earnings_list):
        year = str(2023 - i)
        history[year] = {
            'net_income': earnings,
            'total_equity': 1000000.0,
            'intangible_assets': 0.0,
            'goodwill': 0.0,
            'shares_outstanding': 1000000.0,
            'eps': 5.0,
            'current_assets': 1000000.0,
            'current_liabilities': 400000.0,
            'long_term_debt': 100000.0,
            'dividend': 1.0
        }
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
        'currency': 'USD',
        'history': history
    }
    
    # Act: Run defensive tests
    calculator = GrahamCalculator(financial_data)
    results = calculator.run_defensive_tests()
    
    # Assert: Verify earnings stability test correctness
    positive_years = sum(1 for e in earnings_list if e > 0)
    expected_result = 'PASS' if positive_years >= 8 else 'FAIL'
    
    assert results['earnings_stability'] == expected_result, \
        f"Earnings stability test mismatch: expected {expected_result}, got {results['earnings_stability']} (positive years: {positive_years})"


# Feature: stock-data-analyser, Property 8: Current ratio test correctness
# Validates: Requirements 6.2
@settings(max_examples=100)
@given(
    current_assets=st.floats(min_value=1.0, max_value=1e12, allow_nan=False, allow_infinity=False),
    current_liabilities=st.floats(min_value=1.0, max_value=1e12, allow_nan=False, allow_infinity=False)
)
def test_current_ratio_test_correctness(current_assets, current_liabilities):
    """
    Property: For any balance sheet data, the current ratio test should pass 
    if and only if (Current Assets / Current Liabilities) >= 2.0.
    
    This test verifies the current ratio test logic is correctly implemented.
    """
    # Arrange: Create financial data with specific current assets and liabilities
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
        'currency': 'USD',
        'history': {
            '2023': {
                'current_assets': current_assets,
                'current_liabilities': current_liabilities,
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'shares_outstanding': 1000000.0,
                'eps': 5.0,
                'net_income': 100000.0,
                'long_term_debt': 100000.0,
                'dividend': 1.0
            }
        }
    }
    
    # Act: Run defensive tests
    calculator = GrahamCalculator(financial_data)
    results = calculator.run_defensive_tests()
    
    # Assert: Verify current ratio test correctness
    current_ratio = current_assets / current_liabilities
    expected_result = 'PASS' if current_ratio >= 2.0 else 'FAIL'
    
    assert results['current_ratio'] == expected_result, \
        f"Current ratio test mismatch: expected {expected_result}, got {results['current_ratio']} (ratio: {current_ratio:.2f})"


# Feature: stock-data-analyser, Property 12: No crashes on negative equity
# Validates: Requirements 10.5
@settings(max_examples=100)
@given(
    negative_equity=st.floats(min_value=-1e12, max_value=-1.0, allow_nan=False, allow_infinity=False)
)
def test_no_crashes_on_negative_equity(negative_equity):
    """
    Property: For any financial data with negative TBVPS, the system should complete 
    execution without crashing and set Graham Number to "N/A".
    
    This test verifies the system handles negative equity gracefully.
    """
    # Arrange: Create financial data with negative equity
    financial_data = {
        'ticker': 'TEST.US',
        'price': 100.0,
        'currency': 'USD',
        'history': {
            '2023': {
                'total_equity': negative_equity,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'shares_outstanding': 1000000.0,
                'eps': 5.0,
                'net_income': 100000.0,
                'current_assets': 1000000.0,
                'current_liabilities': 400000.0,
                'total_liabilities': 500000.0,
                'long_term_debt': 100000.0,
                'dividend': 1.0
            }
        }
    }
    
    # Act: Compute all metrics (should not crash)
    calculator = GrahamCalculator(financial_data)
    
    try:
        result = calculator.compute_all()
        
        # Assert: Verify Graham Number is "N/A" and system didn't crash
        assert result['graham_number'] == "N/A", \
            f"Expected Graham Number to be 'N/A' for negative equity, got {result['graham_number']}"
        
        assert result['verdict'] == "Rely on EPV - Negative Equity", \
            f"Expected verdict 'Rely on EPV - Negative Equity', got {result['verdict']}"
        
        # Verify warning was added
        assert any("Negative Tangible Book Value" in w for w in result['warnings']), \
            "Expected warning about negative equity"
        
    except Exception as e:
        raise AssertionError(f"System crashed on negative equity: {e}")


# Feature: stock-data-analyser, Property 14: Deep value opportunity flagging
# Validates: Requirements 13.3
@settings(max_examples=100)
@given(
    net_net_value=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    price_multiplier=st.floats(min_value=0.1, max_value=2.0, allow_nan=False, allow_infinity=False)
)
def test_deep_value_opportunity_flagging(net_net_value, price_multiplier):
    """
    Property: For any ticker where current price is less than Net-Net Value, 
    the system should flag "DEEP VALUE OPPORTUNITY" in the warnings.
    
    This test verifies the deep value detection logic is correctly implemented.
    """
    # Arrange: Create financial data with specific Net-Net Value
    # Calculate current assets and liabilities to produce the desired Net-Net Value
    shares = 1000000.0
    current_assets = (net_net_value * shares) + 500000.0
    total_liabilities = 500000.0
    price = net_net_value * price_multiplier
    
    financial_data = {
        'ticker': 'TEST.US',
        'price': price,
        'currency': 'USD',
        'history': {
            '2023': {
                'current_assets': current_assets,
                'total_liabilities': total_liabilities,
                'shares_outstanding': shares,
                'total_equity': 1000000.0,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'eps': 5.0,
                'net_income': 100000.0,
                'current_liabilities': 400000.0,
                'long_term_debt': 100000.0,
                'dividend': 1.0
            }
        }
    }
    
    # Act: Compute all metrics
    calculator = GrahamCalculator(financial_data)
    result = calculator.compute_all()
    
    # Assert: Verify deep value flagging correctness
    has_deep_value_warning = any("DEEP VALUE OPPORTUNITY" in w for w in result['warnings'])
    
    if price < net_net_value:
        assert has_deep_value_warning, \
            f"Expected DEEP VALUE OPPORTUNITY warning when price ({price:.2f}) < Net-Net ({net_net_value:.2f})"
    else:
        assert not has_deep_value_warning, \
            f"Did not expect DEEP VALUE OPPORTUNITY warning when price ({price:.2f}) >= Net-Net ({net_net_value:.2f})"
