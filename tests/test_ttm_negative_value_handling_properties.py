"""
Property-based tests for TTM negative value handling.

Tests Property 11 from the design document:
- Property 11: Negative Value Handling

For any TTM calculation where EPS ≤ 0 or TBVPS < 0, the system should return "N/A"
for TTM Graham Number and add a warning explaining why.

Validates: Requirements 4.7, 4.8
"""

from hypothesis import given, strategies as st
from core.ttm_calculator import TTMCalculator


# Strategy for generating negative and zero values
negative_floats = st.floats(min_value=-1e12, max_value=-0.01, allow_nan=False, allow_infinity=False)
zero_or_negative_floats = st.floats(min_value=-1e12, max_value=0.0, allow_nan=False, allow_infinity=False)
positive_floats = st.floats(min_value=0.01, max_value=1e12, allow_nan=False, allow_infinity=False)


@given(
    ttm_eps=zero_or_negative_floats,
    total_equity=positive_floats,
    intangible_assets=st.floats(min_value=0.0, max_value=1e12, allow_nan=False, allow_infinity=False),
    goodwill=st.floats(min_value=0.0, max_value=1e12, allow_nan=False, allow_infinity=False),
    shares_outstanding=positive_floats
)
def test_property_11_negative_eps_returns_na(ttm_eps, total_equity, intangible_assets, goodwill, shares_outstanding):
    """
    Feature: ttm-graham-calculations, Property 11: Negative Value Handling (EPS)
    
    For any TTM data with EPS ≤ 0, the system should return "N/A" for TTM Graham Number
    and add a warning explaining why.
    
    Validates: Requirements 4.7
    """
    # Ensure intangibles don't exceed equity (to avoid negative TBVPS interfering with test)
    if intangible_assets + goodwill >= total_equity * 0.95:
        intangible_assets = total_equity * 0.3
        goodwill = total_equity * 0.2
    
    # Create TTM metrics with non-positive EPS
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
    
    # Should return N/A for non-positive EPS
    assert result == "N/A", f"Graham Number should be N/A for EPS={ttm_eps}, got {result}"
    
    # Should have warning about EPS
    assert any("EPS is zero or negative" in w for w in calculator.warnings), \
        f"Expected warning about EPS, got warnings: {calculator.warnings}"


@given(
    ttm_eps=positive_floats,
    total_equity=positive_floats,
    intangible_assets=st.floats(min_value=0.0, max_value=1e12, allow_nan=False, allow_infinity=False),
    goodwill=st.floats(min_value=0.0, max_value=1e12, allow_nan=False, allow_infinity=False),
    shares_outstanding=positive_floats
)
def test_property_11_negative_tbvps_returns_na(ttm_eps, total_equity, intangible_assets, goodwill, shares_outstanding):
    """
    Feature: ttm-graham-calculations, Property 11: Negative Value Handling (TBVPS)
    
    For any TTM data with TBVPS < 0, the system should return "N/A" for TTM Graham Number
    and add a warning explaining why.
    
    Validates: Requirements 4.8
    """
    # Force intangibles to exceed equity (to create negative TBVPS)
    intangible_assets = total_equity * 0.6
    goodwill = total_equity * 0.5
    
    # Create TTM metrics with negative TBVPS
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
    
    # Should return N/A for negative TBVPS
    assert result == "N/A", f"Graham Number should be N/A for negative TBVPS, got {result}"
    
    # Should have warning about negative tangible book value
    assert any("Negative tangible book value" in w for w in calculator.warnings), \
        f"Expected warning about negative TBVPS, got warnings: {calculator.warnings}"


@given(
    ttm_eps=zero_or_negative_floats,
    total_equity=positive_floats,
    shares_outstanding=positive_floats
)
def test_property_11_negative_eps_affects_pe_ratio(ttm_eps, total_equity, shares_outstanding):
    """
    Feature: ttm-graham-calculations, Property 11: Negative Value Handling (P/E)
    
    For any TTM data with EPS ≤ 0, the P/E ratio should return "N/A"
    and add a warning.
    
    Validates: Requirements 4.7
    """
    # Create TTM metrics with non-positive EPS
    ttm_metrics = {
        'ttm_eps': ttm_eps,
        'total_equity': total_equity,
        'shares_outstanding': shares_outstanding
    }
    
    # Create calculator
    calculator = TTMCalculator({}, 100.0, 'USD')
    
    # Calculate P/E and P/B ratios
    result = calculator.compute_ttm_pe_pb_ratios(ttm_metrics)
    
    # P/E should return N/A for non-positive EPS
    assert result['ttm_pe_ratio'] == "N/A", \
        f"P/E ratio should be N/A for EPS={ttm_eps}, got {result['ttm_pe_ratio']}"
    
    # Should have warning about EPS
    assert any("P/E: EPS is zero or negative" in w for w in calculator.warnings), \
        f"Expected warning about P/E EPS, got warnings: {calculator.warnings}"


@given(
    ttm_eps=positive_floats,
    total_equity=zero_or_negative_floats,
    shares_outstanding=positive_floats
)
def test_property_11_negative_book_value_affects_pb_ratio(ttm_eps, total_equity, shares_outstanding):
    """
    Feature: ttm-graham-calculations, Property 11: Negative Value Handling (P/B)
    
    For any TTM data with book value per share ≤ 0, the P/B ratio should return "N/A"
    and add a warning.
    
    Validates: Requirements 4.8
    """
    # Create TTM metrics with non-positive book value
    ttm_metrics = {
        'ttm_eps': ttm_eps,
        'total_equity': total_equity,
        'shares_outstanding': shares_outstanding
    }
    
    # Create calculator
    calculator = TTMCalculator({}, 100.0, 'USD')
    
    # Calculate P/E and P/B ratios
    result = calculator.compute_ttm_pe_pb_ratios(ttm_metrics)
    
    # P/B should return N/A for non-positive book value
    assert result['ttm_pb_ratio'] == "N/A", \
        f"P/B ratio should be N/A for book value={total_equity/shares_outstanding}, got {result['ttm_pb_ratio']}"
    
    # Should have warning about book value
    assert any("P/B: Book value per share is zero or negative" in w for w in calculator.warnings), \
        f"Expected warning about P/B book value, got warnings: {calculator.warnings}"


@given(
    total_equity=positive_floats,
    intangible_assets=st.floats(min_value=0.0, max_value=1e12, allow_nan=False, allow_infinity=False),
    goodwill=st.floats(min_value=0.0, max_value=1e12, allow_nan=False, allow_infinity=False),
    shares_outstanding=positive_floats
)
def test_property_11_negative_tbvps_standalone(total_equity, intangible_assets, goodwill, shares_outstanding):
    """
    Feature: ttm-graham-calculations, Property 11: Negative Value Handling (TBVPS standalone)
    
    For any TTM data where intangibles exceed equity, TBVPS should return "N/A"
    and add a warning.
    
    Validates: Requirements 4.8
    """
    # Force intangibles to exceed equity
    intangible_assets = total_equity * 0.6
    goodwill = total_equity * 0.5
    
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
    
    # Should return N/A for negative tangible book value
    assert result == "N/A", f"TBVPS should be N/A for negative tangible book value, got {result}"
    
    # Should have warning
    assert any("Negative tangible book value" in w for w in calculator.warnings), \
        f"Expected warning about negative tangible book value, got warnings: {calculator.warnings}"


# Additional edge case tests

def test_zero_eps_returns_na_for_graham_number():
    """Test that exactly zero EPS returns N/A for Graham Number."""
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


def test_exactly_zero_tangible_book_value_returns_zero():
    """Test that exactly zero tangible book value returns 0.0 (not N/A)."""
    ttm_metrics = {
        'total_equity': 150000.0,
        'intangible_assets': 100000.0,
        'goodwill': 50000.0,  # Exactly equals equity
        'shares_outstanding': 1000.0
    }
    
    calculator = TTMCalculator({}, 100.0, 'USD')
    result = calculator.compute_ttm_tbvps(ttm_metrics)
    
    # Zero tangible book value is valid (0.0), not N/A
    # Only negative values return N/A
    assert result == 0.0, f"Expected 0.0 for zero tangible book value, got {result}"
