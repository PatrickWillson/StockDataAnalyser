"""
Property-based tests for TTM data quality validation.

Feature: ttm-graham-calculations
Properties tested:
- Property 16: Data Quality Validation (Requirements 10.1, 10.2, 10.3)
- Property 17: Variance Validation (Requirements 10.4, 10.5)
- Property 18: Irregular Pattern Detection (Requirements 2.4, 10.7)
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime, timedelta, date
from core.ttm_calculator import TTMCalculator


# Feature: ttm-graham-calculations, Property 16: Data Quality Validation
# Validates: Requirements 10.1, 10.2, 10.3

# Note: Properties 16a and 16b are difficult to test with property-based testing
# because Python's dict structure automatically handles these cases:
# - Dict keys are automatically deduplicated
# - We sort the keys before validation
# These validations are defensive programming for edge cases.

@given(st.random_module())
def test_property_16c_date_range_validation(random_module):
    """
    Property 16c: Date Range Validation
    
    For any periodic data with dates outside expected ranges
    (future dates or dates before 1950), the system should add a warning.
    """
    # Create dates with invalid ranges
    base_date = datetime(2024, 12, 31)
    dates = [
        '2050-12-31',  # Future date
        base_date.strftime('%Y-%m-%d'),
        (base_date - timedelta(days=90)).strftime('%Y-%m-%d'),
        '1940-01-01',  # Too old
    ]
    
    quarterly_data = {
        'balance_sheet': {},
        'income_statement': {}
    }
    
    for date_str in dates:
        quarterly_data['income_statement'][date_str] = {
            'revenue': 10000000.0,
            'net_income': 1000000.0,
        }
        quarterly_data['balance_sheet'][date_str] = {
            'total_equity': 5000000.0,
            'intangible_assets': 0.0,
            'goodwill': 0.0,
            'current_assets': 2500000.0,
            'total_liabilities': 1500000.0,
            'shares_outstanding': 1000000.0,
        }
    
    calculator = TTMCalculator(
        quarterly_data=quarterly_data,
        price=100.0,
        currency='USD'
    )
    
    # Calculate TTM metrics (which calls validation)
    result = calculator.compute_all()
    
    # Should have warning about invalid dates
    warnings = result.get('warnings', [])
    date_warnings = [w for w in warnings if 'Invalid period dates' in w or 'Data Quality' in w]
    
    assert len(date_warnings) > 0, f"Should warn about invalid period dates. Warnings: {warnings}"


# Feature: ttm-graham-calculations, Property 17: Variance Validation
# Validates: Requirements 10.4, 10.5
@given(
    ttm_eps=st.floats(min_value=1.0, max_value=10.0),
    variance_pct=st.floats(min_value=21.0, max_value=100.0)  # Changed from 25.0 to 21.0
)
@settings(max_examples=50)
def test_property_17a_eps_variance_warning(ttm_eps, variance_pct):
    """
    Property 17a: EPS Variance Warning
    
    For any TTM EPS that differs from annual EPS by more than 20%,
    the system should add a specific warning explaining the difference.
    
    Note: The variance calculation is: abs(ttm - annual) / annual * 100
    So if annual = ttm * (1 + variance_pct/100), then:
    diff% = abs(ttm - ttm*(1+variance_pct/100)) / (ttm*(1+variance_pct/100)) * 100
          = abs(-ttm*variance_pct/100) / (ttm*(1+variance_pct/100)) * 100
          = (ttm*variance_pct/100) / (ttm*(1+variance_pct/100)) * 100
          = variance_pct / (1+variance_pct/100)
    
    For variance_pct=25: diff% = 25/(1+0.25) = 25/1.25 = 20% (NOT > 20!)
    For variance_pct=21: diff% = 21/(1+0.21) = 21/1.21 = 17.4% (NOT > 20!)
    
    We need to solve: variance_pct / (1+variance_pct/100) > 20
    variance_pct > 20 * (1+variance_pct/100)
    variance_pct > 20 + 20*variance_pct/100
    variance_pct > 20 + 0.2*variance_pct
    0.8*variance_pct > 20
    variance_pct > 25
    
    So we need variance_pct > 25 to get diff% > 20%
    """
    # Skip if variance is exactly 25 (edge case)
    assume(variance_pct > 25.0)
    
    # Calculate annual EPS that differs by variance_pct
    annual_eps = ttm_eps * (1 + variance_pct / 100)
    
    # Create quarterly data
    base_date = datetime(2024, 12, 31)
    dates = [
        base_date.strftime('%Y-%m-%d'),
        (base_date - timedelta(days=90)).strftime('%Y-%m-%d'),
        (base_date - timedelta(days=180)).strftime('%Y-%m-%d'),
        (base_date - timedelta(days=270)).strftime('%Y-%m-%d'),
    ]
    
    shares = 1000000.0
    net_income_per_quarter = (ttm_eps * shares) / 4
    
    quarterly_data = {
        'balance_sheet': {},
        'income_statement': {}
    }
    
    for date_str in dates:
        quarterly_data['income_statement'][date_str] = {
            'revenue': 10000000.0,
            'net_income': net_income_per_quarter,
        }
        quarterly_data['balance_sheet'][date_str] = {
            'total_equity': 5000000.0,
            'intangible_assets': 0.0,
            'goodwill': 0.0,
            'current_assets': 2500000.0,
            'total_liabilities': 1500000.0,
            'shares_outstanding': shares,
        }
    
    calculator = TTMCalculator(
        quarterly_data=quarterly_data,
        price=100.0,
        currency='USD'
    )
    
    # Provide annual metrics for comparison
    annual_metrics = {
        'eps': annual_eps,
        'revenue': 40000000.0,
        'net_income': annual_eps * shares
    }
    
    result = calculator.compute_all(annual_metrics=annual_metrics)
    
    # Should have warning about EPS difference
    warnings = result.get('warnings', [])
    eps_warnings = [w for w in warnings if 'TTM EPS differs from annual EPS' in w or 'TTM Validation' in w]
    
    assert len(eps_warnings) > 0, f"Should warn about significant EPS difference. TTM EPS: {ttm_eps}, Annual EPS: {annual_eps}, Warnings: {warnings}"


@given(
    ttm_revenue=st.floats(min_value=1000000, max_value=100000000),
    variance_pct=st.floats(min_value=101.0, max_value=200.0)  # Changed from 55.0 to 101.0
)
@settings(max_examples=50)
def test_property_17b_revenue_variance_warning(ttm_revenue, variance_pct):
    """
    Property 17b: Revenue Variance Warning
    
    For any TTM revenue that differs from annual revenue by more than 50%,
    the system should add a warning.
    
    Note: Same calculation as EPS test.
    For variance_pct=100: diff% = 100/(1+1.00) = 100/2 = 50% (NOT > 50!)
    We need variance_pct > 100 to get diff% > 50%
    """
    # Skip if variance is exactly 100 (edge case)
    assume(variance_pct > 100.0)
    
    # Calculate annual revenue that differs by variance_pct
    annual_revenue = ttm_revenue * (1 + variance_pct / 100)
    
    # Create quarterly data
    base_date = datetime(2024, 12, 31)
    dates = [
        base_date.strftime('%Y-%m-%d'),
        (base_date - timedelta(days=90)).strftime('%Y-%m-%d'),
        (base_date - timedelta(days=180)).strftime('%Y-%m-%d'),
        (base_date - timedelta(days=270)).strftime('%Y-%m-%d'),
    ]
    
    revenue_per_quarter = ttm_revenue / 4
    shares = 1000000.0
    
    quarterly_data = {
        'balance_sheet': {},
        'income_statement': {}
    }
    
    for date_str in dates:
        quarterly_data['income_statement'][date_str] = {
            'revenue': revenue_per_quarter,
            'net_income': revenue_per_quarter * 0.1,
        }
        quarterly_data['balance_sheet'][date_str] = {
            'total_equity': 5000000.0,
            'intangible_assets': 0.0,
            'goodwill': 0.0,
            'current_assets': 2500000.0,
            'total_liabilities': 1500000.0,
            'shares_outstanding': shares,
        }
    
    calculator = TTMCalculator(
        quarterly_data=quarterly_data,
        price=100.0,
        currency='USD'
    )
    
    # Provide annual metrics for comparison
    annual_metrics = {
        'eps': 1.0,
        'revenue': annual_revenue,
        'net_income': annual_revenue * 0.1
    }
    
    result = calculator.compute_all(annual_metrics=annual_metrics)
    
    # Should have warning about revenue difference
    warnings = result.get('warnings', [])
    revenue_warnings = [w for w in warnings if 'TTM revenue differs from annual revenue' in w or 'TTM Validation' in w]
    
    assert len(revenue_warnings) > 0, f"Should warn about significant revenue difference. TTM revenue: {ttm_revenue}, Annual revenue: {annual_revenue}, Warnings: {warnings}"


# Feature: ttm-graham-calculations, Property 18: Irregular Pattern Detection
# Validates: Requirements 2.4, 10.7
@given(st.random_module())
def test_property_18_irregular_pattern_detection(random_module):
    """
    Property 18: Irregular Pattern Detection
    
    For any periodic data where intervals between periods vary significantly
    (not matching quarterly or semi-annual patterns), the system should
    add a warning about inconsistent reporting patterns.
    """
    # Create dates with irregular intervals (not quarterly or semi-annual)
    base_date = datetime(2024, 12, 31)
    dates = [
        base_date.strftime('%Y-%m-%d'),
        (base_date - timedelta(days=60)).strftime('%Y-%m-%d'),  # 60 days
        (base_date - timedelta(days=150)).strftime('%Y-%m-%d'),  # 90 days gap
        (base_date - timedelta(days=220)).strftime('%Y-%m-%d'),  # 70 days gap
    ]
    
    quarterly_data = {
        'balance_sheet': {},
        'income_statement': {}
    }
    
    for date_str in dates:
        quarterly_data['income_statement'][date_str] = {
            'revenue': 10000000.0,
            'net_income': 1000000.0,
        }
        quarterly_data['balance_sheet'][date_str] = {
            'total_equity': 5000000.0,
            'intangible_assets': 0.0,
            'goodwill': 0.0,
            'current_assets': 2500000.0,
            'total_liabilities': 1500000.0,
            'shares_outstanding': 1000000.0,
        }
    
    calculator = TTMCalculator(
        quarterly_data=quarterly_data,
        price=100.0,
        currency='USD'
    )
    
    result = calculator.compute_all()
    
    # Should have warning about irregular pattern
    warnings = result.get('warnings', [])
    irregular_warnings = [w for w in warnings if 'Irregular reporting pattern' in w or 'irregular reporting' in w or 'Cannot calculate metrics with irregular reporting' in w]
    
    assert len(irregular_warnings) > 0, f"Should warn about irregular reporting pattern. Warnings: {warnings}"


# Additional test: Valid data should not generate quality warnings
@given(st.random_module())
def test_valid_data_no_quality_warnings(random_module):
    """
    Test that valid data does not generate data quality warnings.
    
    For any periodic data that is properly ordered, has no duplicates,
    and has valid dates, the system should not add data quality warnings.
    """
    # Create valid quarterly data
    base_date = datetime(2024, 12, 31)
    dates = [
        base_date.strftime('%Y-%m-%d'),
        (base_date - timedelta(days=90)).strftime('%Y-%m-%d'),
        (base_date - timedelta(days=180)).strftime('%Y-%m-%d'),
        (base_date - timedelta(days=270)).strftime('%Y-%m-%d'),
    ]
    
    quarterly_data = {
        'balance_sheet': {},
        'income_statement': {}
    }
    
    for date_str in dates:
        quarterly_data['income_statement'][date_str] = {
            'revenue': 10000000.0,
            'net_income': 1000000.0,
        }
        quarterly_data['balance_sheet'][date_str] = {
            'total_equity': 5000000.0,
            'intangible_assets': 0.0,
            'goodwill': 0.0,
            'current_assets': 2500000.0,
            'total_liabilities': 1500000.0,
            'shares_outstanding': 1000000.0,
        }
    
    calculator = TTMCalculator(
        quarterly_data=quarterly_data,
        price=100.0,
        currency='USD'
    )
    
    result = calculator.compute_all()
    
    # Should not have data quality warnings
    warnings = result.get('warnings', [])
    quality_warnings = [w for w in warnings if 'Data Quality' in w]
    
    assert len(quality_warnings) == 0, f"Valid data should not generate data quality warnings. Warnings: {warnings}"
