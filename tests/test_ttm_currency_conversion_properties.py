"""
Property-Based Tests for TTM Currency Conversion

Tests that currency conversion is correctly applied to all monetary values
in TTM calculations.

Feature: ttm-graham-calculations
Property 12: Currency Conversion Application
Validates: Requirements 5.1, 5.2, 5.3
"""

import pytest
from hypothesis import given, strategies as st, settings
from core.ttm_calculator import TTMCalculator


# Strategy for generating valid quarterly data
@st.composite
def quarterly_data_strategy(draw, num_periods=4):
    """Generate quarterly data with monetary values."""
    balance_sheet = {}
    income_statement = {}
    
    # Generate periods (most recent first)
    base_year = 2024
    for i in range(num_periods):
        quarter = num_periods - i
        month = quarter * 3
        if month > 12:
            month = month - 12
            year = base_year + 1
        else:
            year = base_year
        
        date = f"{year}-{month:02d}-30"
        
        # Generate balance sheet data
        balance_sheet[date] = {
            'total_equity': draw(st.floats(min_value=1000.0, max_value=1000000.0)),
            'intangible_assets': draw(st.floats(min_value=0.0, max_value=100000.0)),
            'goodwill': draw(st.floats(min_value=0.0, max_value=100000.0)),
            'current_assets': draw(st.floats(min_value=1000.0, max_value=500000.0)),
            'total_liabilities': draw(st.floats(min_value=1000.0, max_value=500000.0)),
            'shares_outstanding': draw(st.floats(min_value=1000.0, max_value=10000000.0))
        }
        
        # Generate income statement data
        income_statement[date] = {
            'revenue': draw(st.floats(min_value=1000.0, max_value=1000000.0)),
            'net_income': draw(st.floats(min_value=100.0, max_value=100000.0))
        }
    
    return {
        'balance_sheet': balance_sheet,
        'income_statement': income_statement
    }


@given(
    quarterly_data=quarterly_data_strategy(),
    price=st.floats(min_value=1.0, max_value=1000.0),
    fx_rate=st.floats(min_value=0.5, max_value=2.0)
)
@settings(max_examples=100)
def test_property_currency_conversion_applied_to_all_monetary_values(quarterly_data, price, fx_rate):
    """
    **Feature: ttm-graham-calculations, Property 12: Currency Conversion Application**
    **Validates: Requirements 5.1, 5.2, 5.3**
    
    Property: When currency conversion is applied, all monetary values in TTM data
    should be multiplied by the FX rate.
    
    For any quarterly data in currency A and FX rate R to convert to currency B:
    - All revenue values should be multiplied by R
    - All net income values should be multiplied by R
    - All equity values should be multiplied by R
    - All asset values should be multiplied by R
    - All liability values should be multiplied by R
    - A warning should be added indicating the conversion
    """
    # Store original values for comparison
    original_data = {
        'balance_sheet': {},
        'income_statement': {}
    }
    
    for date, data in quarterly_data['balance_sheet'].items():
        original_data['balance_sheet'][date] = data.copy()
    
    for date, data in quarterly_data['income_statement'].items():
        original_data['income_statement'][date] = data.copy()
    
    # Create calculator with currency conversion
    calculator = TTMCalculator(
        quarterly_data=quarterly_data,
        price=price,
        currency='USD',
        original_currency='GBP',
        fx_rate=fx_rate
    )
    
    # Verify conversion warning was added
    conversion_warnings = [w for w in calculator.warnings if 'Currency Conversion' in w]
    assert len(conversion_warnings) > 0, "Currency conversion warning should be added"
    assert 'GBP → USD' in conversion_warnings[0], "Warning should specify currencies"
    assert f'{fx_rate:.4f}' in conversion_warnings[0], "Warning should include FX rate"
    
    # Verify all monetary values were converted
    # Check income statement
    for date, original in original_data['income_statement'].items():
        converted = quarterly_data['income_statement'][date]
        
        # Revenue should be multiplied by FX rate
        expected_revenue = original['revenue'] * fx_rate
        assert abs(converted['revenue'] - expected_revenue) < 0.01, \
            f"Revenue should be multiplied by FX rate: {converted['revenue']} vs {expected_revenue}"
        
        # Net income should be multiplied by FX rate
        expected_net_income = original['net_income'] * fx_rate
        assert abs(converted['net_income'] - expected_net_income) < 0.01, \
            f"Net income should be multiplied by FX rate: {converted['net_income']} vs {expected_net_income}"
    
    # Check balance sheet
    for date, original in original_data['balance_sheet'].items():
        converted = quarterly_data['balance_sheet'][date]
        
        # Total equity should be multiplied by FX rate
        expected_equity = original['total_equity'] * fx_rate
        assert abs(converted['total_equity'] - expected_equity) < 0.01, \
            f"Total equity should be multiplied by FX rate: {converted['total_equity']} vs {expected_equity}"
        
        # Intangible assets should be multiplied by FX rate
        expected_intangibles = original['intangible_assets'] * fx_rate
        assert abs(converted['intangible_assets'] - expected_intangibles) < 0.01, \
            "Intangible assets should be multiplied by FX rate"
        
        # Goodwill should be multiplied by FX rate
        expected_goodwill = original['goodwill'] * fx_rate
        assert abs(converted['goodwill'] - expected_goodwill) < 0.01, \
            "Goodwill should be multiplied by FX rate"
        
        # Current assets should be multiplied by FX rate
        expected_current_assets = original['current_assets'] * fx_rate
        assert abs(converted['current_assets'] - expected_current_assets) < 0.01, \
            "Current assets should be multiplied by FX rate"
        
        # Total liabilities should be multiplied by FX rate
        expected_liabilities = original['total_liabilities'] * fx_rate
        assert abs(converted['total_liabilities'] - expected_liabilities) < 0.01, \
            "Total liabilities should be multiplied by FX rate"
        
        # Shares outstanding should NOT be converted (it's a count, not monetary)
        assert converted['shares_outstanding'] == original['shares_outstanding'], \
            "Shares outstanding should not be converted (it's a count, not monetary)"


@given(
    quarterly_data=quarterly_data_strategy(),
    price=st.floats(min_value=1.0, max_value=1000.0)
)
@settings(max_examples=100)
def test_property_same_currency_no_conversion(quarterly_data, price):
    """
    **Feature: ttm-graham-calculations, Property 12: Currency Conversion Application**
    **Validates: Requirements 5.1, 5.2**
    
    Property: When original currency equals unified currency, no conversion should occur.
    
    For any quarterly data where original_currency == currency:
    - No monetary values should be modified
    - No currency conversion warning should be added
    """
    # Store original values
    original_revenue = list(quarterly_data['income_statement'].values())[0]['revenue']
    original_equity = list(quarterly_data['balance_sheet'].values())[0]['total_equity']
    
    # Create calculator with same currency
    calculator = TTMCalculator(
        quarterly_data=quarterly_data,
        price=price,
        currency='USD',
        original_currency='USD',
        fx_rate=1.0
    )
    
    # Verify no conversion warning
    conversion_warnings = [w for w in calculator.warnings if 'Currency Conversion' in w]
    assert len(conversion_warnings) == 0, "No currency conversion warning should be added for same currency"
    
    # Verify values unchanged
    current_revenue = list(quarterly_data['income_statement'].values())[0]['revenue']
    current_equity = list(quarterly_data['balance_sheet'].values())[0]['total_equity']
    
    assert current_revenue == original_revenue, "Revenue should not change when currencies are the same"
    assert current_equity == original_equity, "Equity should not change when currencies are the same"


@given(
    quarterly_data=quarterly_data_strategy(),
    price=st.floats(min_value=1.0, max_value=1000.0)
)
@settings(max_examples=100)
def test_property_missing_fx_rate_warning(quarterly_data, price):
    """
    **Feature: ttm-graham-calculations, Property 12: Currency Conversion Application**
    **Validates: Requirements 5.3**
    
    Property: When FX rate is unavailable, a warning should be added.
    
    For any quarterly data where original_currency != currency but fx_rate is None:
    - A warning should be added indicating conversion failure
    - Values should remain unchanged
    """
    # Store original values
    original_revenue = list(quarterly_data['income_statement'].values())[0]['revenue']
    
    # Create calculator with missing FX rate
    calculator = TTMCalculator(
        quarterly_data=quarterly_data,
        price=price,
        currency='USD',
        original_currency='GBP',
        fx_rate=None
    )
    
    # Verify warning was added
    conversion_warnings = [w for w in calculator.warnings if 'Currency Conversion' in w]
    assert len(conversion_warnings) > 0, "Warning should be added when FX rate unavailable"
    assert 'Unable to convert' in conversion_warnings[0], "Warning should indicate conversion failure"
    
    # Verify values unchanged
    current_revenue = list(quarterly_data['income_statement'].values())[0]['revenue']
    assert current_revenue == original_revenue, "Revenue should not change when FX rate unavailable"


@given(
    quarterly_data=quarterly_data_strategy(),
    price=st.floats(min_value=1.0, max_value=1000.0),
    fx_rate=st.floats(min_value=0.5, max_value=2.0)
)
@settings(max_examples=100)
def test_property_currency_metadata_stored(quarterly_data, price, fx_rate):
    """
    **Feature: ttm-graham-calculations, Property 12: Currency Conversion Application**
    **Validates: Requirements 5.5**
    
    Property: Currency conversion metadata should be stored in results.
    
    For any TTM calculation with currency conversion:
    - Result should include 'currency' field
    - Result should include 'original_currency' field
    - Result should include 'fx_rate_used' field
    """
    # Create calculator with currency conversion
    calculator = TTMCalculator(
        quarterly_data=quarterly_data,
        price=price,
        currency='USD',
        original_currency='GBP',
        fx_rate=fx_rate
    )
    
    # Compute all metrics
    result = calculator.compute_all()
    
    # Verify metadata is present
    assert 'currency' in result, "Result should include currency field"
    assert result['currency'] == 'USD', "Currency should match unified currency"
    
    assert 'original_currency' in result, "Result should include original_currency field"
    assert result['original_currency'] == 'GBP', "Original currency should be stored"
    
    assert 'fx_rate_used' in result, "Result should include fx_rate_used field"
    assert result['fx_rate_used'] == fx_rate, "FX rate should be stored"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
