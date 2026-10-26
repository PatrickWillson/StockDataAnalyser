"""
Property-based tests for TTM Graham formula calculations.

Tests Properties 6-10 from the design document:
- Property 6: TTM TBVPS Formula Correctness
- Property 7: TTM Graham Number Formula Correctness
- Property 8: TTM Net-Net Formula Correctness
- Property 9: TTM Margin of Safety Formula Correctness
- Property 10: TTM P/E and P/B Formula Correctness
"""

import math
from hypothesis import given, strategies as st
from core.ttm_calculator import TTMCalculator


# Strategy for generating valid financial values (positive floats)
positive_floats = st.floats(min_value=0.01, max_value=1e12, allow_nan=False, allow_infinity=False)
small_positive_floats = st.floats(min_value=0.01, max_value=1e6, allow_nan=False, allow_infinity=False)


@given(
    total_equity=positive_floats,
    intangible_assets=st.floats(min_value=0.0, max_value=1e12, allow_nan=False, allow_infinity=False),
    goodwill=st.floats(min_value=0.0, max_value=1e12, allow_nan=False, allow_infinity=False),
    shares_outstanding=positive_floats
)
def test_property_6_ttm_tbvps_formula_correctness(total_equity, intangible_assets, goodwill, shares_outstanding):
    """
    Feature: ttm-graham-calculations, Property 6: TTM TBVPS Formula Correctness
    
    For any TTM metrics with positive equity and shares outstanding,
    TTM TBVPS should equal (Total Equity - Intangible Assets - Goodwill) / Shares Outstanding,
    rounded to 2 decimals.
    
    Validates: Requirements 4.1
    """
    # Ensure intangibles don't exceed equity (to avoid negative TBVPS in this test)
    # Also ensure there's a meaningful gap to avoid rounding to zero
    if intangible_assets + goodwill >= total_equity * 0.95:
        intangible_assets = total_equity * 0.3
        goodwill = total_equity * 0.2
    
    # Create TTM metrics
    ttm_metrics = {
        'total_equity': total_equity,
        'intangible_assets': intangible_assets,
        'goodwill': goodwill,
        'shares_outstanding': shares_outstanding
    }
    
    # Create calculator
    calculator = TTMCalculator({}, 100.0, 'USD')
    
    # Calculate TBVPS
    result = calculator.compute_ttm_tbvps(ttm_metrics)
    
    # Should not be N/A for valid inputs
    assert result != "N/A", "TBVPS should not be N/A for valid positive inputs"
    
    # Calculate expected value
    tangible_book_value = total_equity - intangible_assets - goodwill
    expected_tbvps = round(tangible_book_value / shares_outstanding, 2)
    
    # Verify formula correctness
    assert result == expected_tbvps, f"TBVPS {result} != expected {expected_tbvps}"


@given(
    ttm_eps=positive_floats,
    total_equity=positive_floats,
    intangible_assets=st.floats(min_value=0.0, max_value=1e12, allow_nan=False, allow_infinity=False),
    goodwill=st.floats(min_value=0.0, max_value=1e12, allow_nan=False, allow_infinity=False),
    shares_outstanding=positive_floats
)
def test_property_7_ttm_graham_number_formula_correctness(ttm_eps, total_equity, intangible_assets, goodwill, shares_outstanding):
    """
    Feature: ttm-graham-calculations, Property 7: TTM Graham Number Formula Correctness
    
    For any TTM metrics with positive EPS and positive TBVPS,
    TTM Graham Number should equal sqrt(22.5 × TTM_EPS × TTM_TBVPS),
    rounded to 2 decimals.
    
    Validates: Requirements 4.2
    """
    # Ensure intangibles don't exceed equity (to avoid negative TBVPS)
    # Also ensure there's a meaningful gap to avoid rounding to zero
    if intangible_assets + goodwill >= total_equity * 0.95:
        intangible_assets = total_equity * 0.3
        goodwill = total_equity * 0.2
    
    # Create TTM metrics
    ttm_metrics = {
        'ttm_eps': ttm_eps,
        'total_equity': total_equity,
        'intangible_assets': intangible_assets,
        'goodwill': goodwill,
        'shares_outstanding': shares_outstanding
    }
    
    # Create calculator
    calculator = TTMCalculator({}, 100.0, 'USD')
    
    # Calculate Graham Number
    result = calculator.compute_ttm_graham_number(ttm_metrics)
    
    # Should not be N/A for valid inputs
    assert result != "N/A", "Graham Number should not be N/A for valid positive inputs"
    
    # Calculate expected value
    # Note: The implementation rounds TBVPS first, then uses the rounded value
    tangible_book_value = total_equity - intangible_assets - goodwill
    tbvps = round(tangible_book_value / shares_outstanding, 2)
    expected_graham = round(math.sqrt(22.5 * ttm_eps * tbvps), 2)
    
    # Verify formula correctness
    assert result == expected_graham, f"Graham Number {result} != expected {expected_graham}"


@given(
    current_assets=positive_floats,
    total_liabilities=st.floats(min_value=0.0, max_value=1e12, allow_nan=False, allow_infinity=False),
    shares_outstanding=positive_floats
)
def test_property_8_ttm_net_net_formula_correctness(current_assets, total_liabilities, shares_outstanding):
    """
    Feature: ttm-graham-calculations, Property 8: TTM Net-Net Formula Correctness
    
    For any TTM metrics with valid current assets, total liabilities, and shares outstanding,
    TTM Net-Net should equal (Current Assets - Total Liabilities) / Shares Outstanding,
    rounded to 2 decimals.
    
    Validates: Requirements 4.3
    """
    # Create TTM metrics
    ttm_metrics = {
        'current_assets': current_assets,
        'total_liabilities': total_liabilities,
        'shares_outstanding': shares_outstanding
    }
    
    # Create calculator
    calculator = TTMCalculator({}, 100.0, 'USD')
    
    # Calculate Net-Net
    result = calculator.compute_ttm_net_net(ttm_metrics)
    
    # Should not be N/A for valid inputs
    assert result != "N/A", "Net-Net should not be N/A for valid inputs"
    
    # Calculate expected value
    expected_net_net = round((current_assets - total_liabilities) / shares_outstanding, 2)
    
    # Verify formula correctness
    assert result == expected_net_net, f"Net-Net {result} != expected {expected_net_net}"


@given(
    graham_number=positive_floats,
    price=positive_floats
)
def test_property_9_ttm_margin_of_safety_formula_correctness(graham_number, price):
    """
    Feature: ttm-graham-calculations, Property 9: TTM Margin of Safety Formula Correctness
    
    For any TTM Graham Number and price,
    TTM Margin of Safety should equal ((TTM_Graham_Number - Price) / TTM_Graham_Number) × 100,
    rounded to 1 decimal.
    
    Validates: Requirements 4.4
    """
    # Create calculator
    calculator = TTMCalculator({}, price, 'USD')
    
    # Calculate Margin of Safety
    result = calculator.compute_ttm_margin_of_safety(graham_number)
    
    # Should not be N/A for valid inputs
    assert result != "N/A", "Margin of Safety should not be N/A for valid inputs"
    
    # Calculate expected value
    expected_mos = round(((graham_number - price) / graham_number) * 100, 1)
    
    # Verify formula correctness
    assert result == expected_mos, f"Margin of Safety {result} != expected {expected_mos}"


@given(
    price=positive_floats,
    ttm_eps=positive_floats,
    total_equity=positive_floats,
    shares_outstanding=positive_floats
)
def test_property_10_ttm_pe_pb_formula_correctness(price, ttm_eps, total_equity, shares_outstanding):
    """
    Feature: ttm-graham-calculations, Property 10: TTM P/E and P/B Formula Correctness
    
    For any price, TTM EPS, and TTM book value per share,
    TTM P/E should equal Price / TTM_EPS and
    TTM P/B should equal Price / TTM_Book_Value_Per_Share,
    both rounded to 2 decimals.
    
    Validates: Requirements 4.5, 4.6
    """
    # Create TTM metrics
    ttm_metrics = {
        'ttm_eps': ttm_eps,
        'total_equity': total_equity,
        'shares_outstanding': shares_outstanding
    }
    
    # Create calculator
    calculator = TTMCalculator({}, price, 'USD')
    
    # Calculate P/E and P/B ratios
    result = calculator.compute_ttm_pe_pb_ratios(ttm_metrics)
    
    # Should not be N/A for valid inputs
    assert result['ttm_pe_ratio'] != "N/A", "P/E ratio should not be N/A for valid inputs"
    assert result['ttm_pb_ratio'] != "N/A", "P/B ratio should not be N/A for valid inputs"
    
    # Calculate expected values
    expected_pe = round(price / ttm_eps, 2)
    book_value_per_share = total_equity / shares_outstanding
    expected_pb = round(price / book_value_per_share, 2)
    
    # Verify formula correctness
    assert result['ttm_pe_ratio'] == expected_pe, f"P/E ratio {result['ttm_pe_ratio']} != expected {expected_pe}"
    assert result['ttm_pb_ratio'] == expected_pb, f"P/B ratio {result['ttm_pb_ratio']} != expected {expected_pb}"


# Edge case tests for "N/A" returns

def test_tbvps_returns_na_for_zero_shares():
    """Test that TBVPS returns N/A when shares outstanding is zero."""
    ttm_metrics = {
        'total_equity': 1000000.0,
        'intangible_assets': 100000.0,
        'goodwill': 50000.0,
        'shares_outstanding': 0.0
    }
    
    calculator = TTMCalculator({}, 100.0, 'USD')
    result = calculator.compute_ttm_tbvps(ttm_metrics)
    
    assert result == "N/A"
    assert any("Shares outstanding is zero or negative" in w for w in calculator.warnings)


def test_tbvps_returns_na_for_negative_tangible_book_value():
    """Test that TBVPS returns N/A when tangible book value is negative."""
    ttm_metrics = {
        'total_equity': 100000.0,
        'intangible_assets': 80000.0,
        'goodwill': 50000.0,  # Total intangibles > equity
        'shares_outstanding': 1000.0
    }
    
    calculator = TTMCalculator({}, 100.0, 'USD')
    result = calculator.compute_ttm_tbvps(ttm_metrics)
    
    assert result == "N/A"
    assert any("Negative tangible book value" in w for w in calculator.warnings)


def test_graham_number_returns_na_for_zero_eps():
    """Test that Graham Number returns N/A when EPS is zero."""
    ttm_metrics = {
        'ttm_eps': 0.0,
        'total_equity': 1000000.0,
        'intangible_assets': 100000.0,
        'goodwill': 50000.0,
        'shares_outstanding': 1000.0
    }
    
    calculator = TTMCalculator({}, 100.0, 'USD')
    result = calculator.compute_ttm_graham_number(ttm_metrics)
    
    assert result == "N/A"
    assert any("EPS is zero or negative" in w for w in calculator.warnings)


def test_graham_number_returns_na_for_negative_eps():
    """Test that Graham Number returns N/A when EPS is negative."""
    ttm_metrics = {
        'ttm_eps': -5.0,
        'total_equity': 1000000.0,
        'intangible_assets': 100000.0,
        'goodwill': 50000.0,
        'shares_outstanding': 1000.0
    }
    
    calculator = TTMCalculator({}, 100.0, 'USD')
    result = calculator.compute_ttm_graham_number(ttm_metrics)
    
    assert result == "N/A"
    assert any("EPS is zero or negative" in w for w in calculator.warnings)


def test_net_net_returns_na_for_zero_shares():
    """Test that Net-Net returns N/A when shares outstanding is zero."""
    ttm_metrics = {
        'current_assets': 500000.0,
        'total_liabilities': 300000.0,
        'shares_outstanding': 0.0
    }
    
    calculator = TTMCalculator({}, 100.0, 'USD')
    result = calculator.compute_ttm_net_net(ttm_metrics)
    
    assert result == "N/A"
    assert any("Shares outstanding is zero or negative" in w for w in calculator.warnings)


def test_margin_of_safety_returns_na_for_na_graham_number():
    """Test that Margin of Safety returns N/A when Graham Number is N/A."""
    calculator = TTMCalculator({}, 100.0, 'USD')
    result = calculator.compute_ttm_margin_of_safety("N/A")
    
    assert result == "N/A"
    assert any("Cannot calculate - Graham Number is N/A" in w for w in calculator.warnings)


def test_pe_ratio_returns_na_for_zero_eps():
    """Test that P/E ratio returns N/A when EPS is zero."""
    ttm_metrics = {
        'ttm_eps': 0.0,
        'total_equity': 1000000.0,
        'shares_outstanding': 1000.0
    }
    
    calculator = TTMCalculator({}, 100.0, 'USD')
    result = calculator.compute_ttm_pe_pb_ratios(ttm_metrics)
    
    assert result['ttm_pe_ratio'] == "N/A"
    assert any("P/E: EPS is zero or negative" in w for w in calculator.warnings)


def test_pb_ratio_returns_na_for_zero_book_value():
    """Test that P/B ratio returns N/A when book value per share is zero."""
    ttm_metrics = {
        'ttm_eps': 5.0,
        'total_equity': 0.0,
        'shares_outstanding': 1000.0
    }
    
    calculator = TTMCalculator({}, 100.0, 'USD')
    result = calculator.compute_ttm_pe_pb_ratios(ttm_metrics)
    
    assert result['ttm_pb_ratio'] == "N/A"
    assert any("P/B: Book value per share is zero or negative" in w for w in calculator.warnings)
