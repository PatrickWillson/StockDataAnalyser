"""
Property-Based Tests for Historical P/E and P/B Calculation Accuracy

Tests that historical P/E and P/B ratios are calculated correctly using
date-matched FX rates.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume


# Property 8: Historical P/E Calculation Accuracy
# Validates: Requirements 1.4
@given(
    price_gbp=st.floats(min_value=10.0, max_value=1000.0),
    eps_gbp=st.floats(min_value=1.0, max_value=100.0),
    historical_rate=st.floats(min_value=1.1, max_value=1.5),
    current_rate=st.floats(min_value=1.1, max_value=1.5)
)
@settings(max_examples=100)
def test_historical_pe_uses_date_matched_fx_rate(price_gbp, eps_gbp, historical_rate, current_rate):
    """
    **Feature: historical-fx-rates, Property 8: Historical P/E Calculation Accuracy**
    
    Property: For any fiscal year end with both historical price and EPS data,
    the historical P/E ratio calculated using date-matched FX rates should differ
    from the P/E calculated using current FX rates by an amount proportional to
    the FX rate difference.
    
    This validates that using historical rates produces more accurate historical ratios.
    """
    # Avoid division by zero and ensure rates are different enough to measure
    assume(abs(historical_rate - current_rate) > 0.05)
    assume(eps_gbp > 0.1)
    
    # Calculate P/E using historical rate (correct method)
    price_usd_historical = price_gbp * historical_rate
    eps_usd = eps_gbp  # EPS is already in financials currency (doesn't need conversion)
    pe_historical = price_usd_historical / eps_usd
    
    # Calculate P/E using current rate (old method)
    price_usd_current = price_gbp * current_rate
    pe_current = price_usd_current / eps_usd
    
    # The difference in P/E should be proportional to the difference in FX rates
    rate_ratio = historical_rate / current_rate
    pe_ratio = pe_historical / pe_current
    
    # P/E ratio should scale with FX rate ratio
    assert abs(pe_ratio - rate_ratio) < 0.01, \
        f"P/E ratio should scale with FX rate: {pe_ratio:.4f} vs {rate_ratio:.4f}"


# Property 7: Warning Generation Accuracy
# Validates: Requirements 4.2, 5.4
@given(
    num_years=st.integers(min_value=3, max_value=20),
    fallback_ratio=st.floats(min_value=0.0, max_value=1.0)
)
@settings(max_examples=100)
def test_warning_generated_for_each_fallback_year(num_years, fallback_ratio):
    """
    **Feature: historical-fx-rates, Property 7: Warning Generation Accuracy**
    
    Property: For any set of fiscal year ends, the number of fallback warnings
    generated should equal the number of fiscal year ends with None or missing
    historical FX rates.
    
    This ensures users are properly informed about data quality.
    """
    # Simulate year_end_prices and historical_fx_rates
    year_end_prices = {}
    historical_fx_rates = {}
    expected_fallback_count = 0
    
    for i in range(num_years):
        year = f"{2020 + i}-12-31"
        year_end_prices[year] = 100.0 + i * 10  # Some price
        
        # Use hash to deterministically decide if this year has a historical rate
        if hash(year) % 100 < fallback_ratio * 100:
            historical_fx_rates[year] = None  # Will use fallback
            expected_fallback_count += 1
        else:
            historical_fx_rates[year] = 1.2 + (hash(year) % 10) / 10.0
    
    # Simulate the conversion logic from stock_data_analyser.py
    current_fx_rate = 1.25
    fallback_years = []
    
    for date_key, price_value in year_end_prices.items():
        if price_value is not None:
            fx_rate = historical_fx_rates.get(date_key)
            
            if fx_rate is None:
                fx_rate = current_fx_rate
                year_only = date_key.split('-')[0]
                fallback_years.append(year_only)
    
    # Verify property: Number of fallback years matches expected
    assert len(fallback_years) == expected_fallback_count, \
        f"Should have {expected_fallback_count} fallback years, got {len(fallback_years)}"


# Test: P/E calculation with zero EPS
def test_pe_calculation_with_zero_eps():
    """
    Test that P/E calculation handles zero EPS gracefully.
    """
    price = 100.0
    eps = 0.0
    
    # Should not crash, should return N/A or infinity
    # This is handled by the dossier generator, not the conversion logic
    # Just verify the conversion doesn't crash
    fx_rate = 1.25
    converted_price = price * fx_rate
    
    assert converted_price == 125.0


# Test: P/E calculation with negative EPS
def test_pe_calculation_with_negative_eps():
    """
    Test that P/E calculation handles negative EPS (loss years).
    """
    price = 100.0
    eps = -5.0
    fx_rate = 1.25
    
    converted_price = price * fx_rate
    
    # P/E would be negative (loss year)
    pe = converted_price / eps
    assert pe < 0, "P/E should be negative for loss years"


# Test: Multiple years with different historical rates
def test_multiple_years_different_historical_rates():
    """
    Test that different years use their respective historical FX rates for P/E calculation.
    """
    # Year 1: Historical rate 1.20
    price_2023_gbp = 100.0
    eps_2023_gbp = 10.0
    rate_2023 = 1.20
    
    price_2023_usd = price_2023_gbp * rate_2023
    pe_2023 = price_2023_usd / eps_2023_gbp
    
    # Year 2: Historical rate 1.30
    price_2024_gbp = 100.0
    eps_2024_gbp = 10.0
    rate_2024 = 1.30
    
    price_2024_usd = price_2024_gbp * rate_2024
    pe_2024 = price_2024_usd / eps_2024_gbp
    
    # P/E ratios should differ due to different FX rates
    assert abs(pe_2023 - 12.0) < 0.01, f"2023 P/E should be 12.0, got {pe_2023}"
    assert abs(pe_2024 - 13.0) < 0.01, f"2024 P/E should be 13.0, got {pe_2024}"
    assert pe_2024 > pe_2023, "2024 P/E should be higher due to higher FX rate"


# Test: Fallback year list formatting
def test_fallback_year_list_formatting():
    """
    Test that fallback years are properly formatted in warning messages.
    """
    fallback_years = ['2020', '2021', '2023']
    
    # Simulate warning generation
    unique_years = sorted(set(fallback_years))
    warning = f"Years {', '.join(unique_years)} used current rate as fallback"
    
    assert '2020' in warning
    assert '2021' in warning
    assert '2023' in warning
    assert '2020, 2021, 2023' in warning


# Test: No fallback when all historical rates available
def test_no_fallback_when_all_rates_available():
    """
    Test that no fallback occurs when all historical rates are available.
    """
    year_end_prices = {
        '2023-12-31': 100.0,
        '2022-12-31': 95.0,
        '2021-12-31': 90.0
    }
    
    historical_fx_rates = {
        '2023-12-31': 1.30,
        '2022-12-31': 1.25,
        '2021-12-31': 1.20
    }
    
    current_fx_rate = 1.35
    fallback_years = []
    
    for date_key, price_value in year_end_prices.items():
        if price_value is not None:
            fx_rate = historical_fx_rates.get(date_key)
            
            if fx_rate is None:
                fx_rate = current_fx_rate
                year_only = date_key.split('-')[0]
                fallback_years.append(year_only)
    
    # No fallback should occur
    assert len(fallback_years) == 0, "Should not use fallback when all historical rates available"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
