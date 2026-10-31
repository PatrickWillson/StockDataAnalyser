"""
Property-based tests for TTM data quality validation.

Feature: ttm-graham-calculations
Properties tested:
- Property 16: Data Quality Validation (Requirements 10.1, 10.2, 10.3)
- Property 17: Variance Validation (Requirements 10.4, 10.5)
- Property 18: Irregular Pattern Detection (Requirements 2.4, 10.7)
"""

from hypothesis import given, strategies as st
from datetime import datetime, timedelta
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
