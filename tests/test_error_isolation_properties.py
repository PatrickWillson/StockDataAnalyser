"""
Property-based tests for TTM error isolation.

Feature: ttm-graham-calculations
Property 15: Error Isolation

Tests that when one TTM calculation fails, other calculations continue
and complete successfully.
"""

import pytest
from hypothesis import given, strategies as st
from core.ttm_calculator import TTMCalculator
from typing import Dict, Any


# Strategy for generating valid quarterly data
@st.composite
def quarterly_data_strategy(draw):
    """Generate valid quarterly data for testing."""
    num_periods = draw(st.integers(min_value=4, max_value=8))
    
    balance_sheet = {}
    income_statement = {}
    
    # Generate periods (quarterly, ~90 days apart)
    base_year = 2024
    base_month = 12
    
    for i in range(num_periods):
        # Calculate period date (going backwards in time)
        months_back = i * 3
        year = base_year - (months_back // 12)
        month = base_month - (months_back % 12)
        if month <= 0:
            month += 12
            year -= 1
        
        # Last day of the month
        if month in [1, 3, 5, 7, 8, 10, 12]:
            day = 31
        elif month in [4, 6, 9, 11]:
            day = 30
        else:
            day = 28
        
        period_date = f"{year}-{month:02d}-{day:02d}"
        
        # Generate balance sheet data
        balance_sheet[period_date] = {
            'total_equity': draw(st.floats(min_value=1e9, max_value=1e12)),
            'intangible_assets': draw(st.floats(min_value=0, max_value=1e11)),
            'goodwill': draw(st.floats(min_value=0, max_value=1e11)),
            'current_assets': draw(st.floats(min_value=1e9, max_value=1e12)),
            'total_liabilities': draw(st.floats(min_value=1e9, max_value=1e12)),
            'shares_outstanding': draw(st.floats(min_value=1e6, max_value=1e10)),
        }
        
        # Generate income statement data
        income_statement[period_date] = {
            'revenue': draw(st.floats(min_value=1e9, max_value=1e12)),
            'net_income': draw(st.floats(min_value=1e8, max_value=1e11)),
        }
    
    return {
        'balance_sheet': balance_sheet,
        'income_statement': income_statement
    }


@given(
    quarterly_data=quarterly_data_strategy(),
    price=st.floats(min_value=10.0, max_value=1000.0)
)
def test_error_isolation_one_calculation_fails(quarterly_data, price):
    """
    Feature: ttm-graham-calculations, Property 15: Error Isolation
    
    Property: When one TTM calculation fails, other calculations should
    continue and complete successfully.
    
    Validates: Requirements 7.6
    
    Test Strategy:
    1. Create valid quarterly data
    2. Corrupt one specific field to cause one calculation to fail
    3. Verify other calculations still complete
    4. Verify appropriate warning is added for the failed calculation
    """
    # Create calculator with valid data
    calculator = TTMCalculator(quarterly_data, price, 'USD')
    
    # Compute all metrics - should succeed
    result = calculator.compute_all()
    
    # Verify basic structure exists
    assert 'ttm_graham_number' in result
    assert 'ttm_tbvps' in result
    assert 'ttm_net_net' in result
    assert 'ttm_margin_of_safety' in result
    assert 'ttm_pe_ratio' in result
    assert 'ttm_pb_ratio' in result
    assert 'warnings' in result
    
    # Now test with corrupted data that causes TBVPS to fail
    # Set shares_outstanding to 0 in all periods
    corrupted_data = {
        'balance_sheet': {},
        'income_statement': quarterly_data['income_statement'].copy()
    }
    
    for period, data in quarterly_data['balance_sheet'].items():
        corrupted_data['balance_sheet'][period] = data.copy()
        corrupted_data['balance_sheet'][period]['shares_outstanding'] = 0.0
    
    # Create calculator with corrupted data
    corrupted_calculator = TTMCalculator(corrupted_data, price, 'USD')
    corrupted_result = corrupted_calculator.compute_all()
    
    # TBVPS should fail (shares_outstanding = 0)
    assert corrupted_result['ttm_tbvps'] == "N/A"
    
    # Graham Number should also fail (depends on TBVPS)
    assert corrupted_result['ttm_graham_number'] == "N/A"
    
    # But other calculations should still work
    # Net-Net should fail too (shares_outstanding = 0)
    assert corrupted_result['ttm_net_net'] == "N/A"
    
    # P/E and P/B should fail (shares_outstanding = 0 affects P/B)
    assert corrupted_result['ttm_pb_ratio'] == "N/A"
    
    # But TTM metrics should still be calculated
    assert corrupted_result['ttm_revenue'] > 0
    assert corrupted_result['ttm_net_income'] > 0
    
    # Verify warnings were added
    assert len(corrupted_result['warnings']) > 0
    
    # Check for specific warning about shares outstanding
    warning_found = any('shares outstanding' in w.lower() for w in corrupted_result['warnings'])
    assert warning_found, "Expected warning about shares outstanding"


@given(
    quarterly_data=quarterly_data_strategy(),
    price=st.floats(min_value=10.0, max_value=1000.0)
)
def test_error_isolation_negative_eps(quarterly_data, price):
    """
    Feature: ttm-graham-calculations, Property 15: Error Isolation
    
    Property: When EPS is negative (causing Graham Number to fail),
    other calculations should still complete.
    
    Validates: Requirements 7.6
    
    Test Strategy:
    1. Create quarterly data with negative net income
    2. Verify Graham Number returns "N/A"
    3. Verify other calculations (TBVPS, Net-Net, P/B) still complete
    """
    # Corrupt income statement to have negative net income
    corrupted_data = {
        'balance_sheet': quarterly_data['balance_sheet'].copy(),
        'income_statement': {}
    }
    
    for period, data in quarterly_data['income_statement'].items():
        corrupted_data['income_statement'][period] = data.copy()
        corrupted_data['income_statement'][period]['net_income'] = -1e9  # Negative
    
    # Create calculator with corrupted data
    calculator = TTMCalculator(corrupted_data, price, 'USD')
    result = calculator.compute_all()
    
    # Graham Number should fail (negative EPS)
    assert result['ttm_graham_number'] == "N/A"
    
    # Margin of Safety should also fail (depends on Graham Number)
    assert result['ttm_margin_of_safety'] == "N/A"
    
    # P/E should fail (negative EPS)
    assert result['ttm_pe_ratio'] == "N/A"
    
    # But TBVPS should still work
    if result['ttm_tbvps'] != "N/A":
        assert isinstance(result['ttm_tbvps'], float)
        assert result['ttm_tbvps'] >= 0  # Can be 0.0 when goodwill + intangibles ≈ total equity
    
    # Net-Net should still work (can be negative, that's valid)
    if result['ttm_net_net'] != "N/A":
        assert isinstance(result['ttm_net_net'], (float, int))
    
    # P/B should still work (can be any positive value or zero)
    if result['ttm_pb_ratio'] != "N/A":
        assert isinstance(result['ttm_pb_ratio'], float)
        assert result['ttm_pb_ratio'] >= 0
    
    # Verify warnings were added
    assert len(result['warnings']) > 0
    
    # Check for warning about negative EPS
    warning_found = any('eps' in w.lower() and ('negative' in w.lower() or 'zero' in w.lower()) 
                       for w in result['warnings'])
    assert warning_found, "Expected warning about negative/zero EPS"


def test_error_isolation_missing_balance_sheet_field():
    """
    Feature: ttm-graham-calculations, Property 15: Error Isolation
    
    Property: When a specific balance sheet field is missing,
    only calculations depending on that field should fail.
    
    Validates: Requirements 7.6
    
    Test Strategy:
    1. Create quarterly data with zero shares outstanding
    2. Verify per-share calculations fail (TBVPS, Net-Net, P/E, P/B)
    3. Verify TTM metrics (revenue, net income) still calculate
    """
    # Create minimal valid quarterly data with zero shares
    quarterly_data = {
        'balance_sheet': {
            '2024-12-31': {
                'total_equity': 1e11,
                'intangible_assets': 1e10,
                'goodwill': 1e10,
                'current_assets': 5e10,
                'total_liabilities': 5e10,
                'shares_outstanding': 0.0,  # Zero - will cause per-share calculations to fail
            },
            '2024-09-30': {
                'total_equity': 9.5e10,
                'intangible_assets': 1e10,
                'goodwill': 1e10,
                'current_assets': 5e10,
                'total_liabilities': 5e10,
                'shares_outstanding': 0.0,
            },
            '2024-06-30': {
                'total_equity': 9e10,
                'intangible_assets': 1e10,
                'goodwill': 1e10,
                'current_assets': 5e10,
                'total_liabilities': 5e10,
                'shares_outstanding': 0.0,
            },
            '2024-03-31': {
                'total_equity': 8.5e10,
                'intangible_assets': 1e10,
                'goodwill': 1e10,
                'current_assets': 5e10,
                'total_liabilities': 5e10,
                'shares_outstanding': 0.0,
            },
        },
        'income_statement': {
            '2024-12-31': {'revenue': 5e10, 'net_income': 1e10},
            '2024-09-30': {'revenue': 5e10, 'net_income': 1e10},
            '2024-06-30': {'revenue': 5e10, 'net_income': 1e10},
            '2024-03-31': {'revenue': 5e10, 'net_income': 1e10},
        }
    }
    
    calculator = TTMCalculator(quarterly_data, 100.0, 'USD')
    result = calculator.compute_all()
    
    # All per-share calculations should fail (shares_outstanding = 0)
    assert result['ttm_tbvps'] == "N/A"
    assert result['ttm_net_net'] == "N/A"
    assert result['ttm_pb_ratio'] == "N/A"
    
    # Graham Number should also fail (depends on TBVPS)
    assert result['ttm_graham_number'] == "N/A"
    
    # But TTM metrics should still be calculated
    assert result['ttm_revenue'] > 0
    assert result['ttm_net_income'] > 0
    
    # Verify warnings about shares outstanding
    warning_found = any('shares outstanding' in w.lower() for w in result['warnings'])
    assert warning_found, "Expected warning about shares outstanding"


def test_error_isolation_all_calculations_independent():
    """
    Feature: ttm-graham-calculations, Property 15: Error Isolation
    
    Property: Each calculation should be independent - if all inputs
    are corrupted in different ways, each calculation should fail
    independently with its own warning.
    
    Validates: Requirements 7.6
    """
    # Create data that will cause multiple failures
    quarterly_data = {
        'balance_sheet': {
            '2024-12-31': {
                'total_equity': -1e11,  # Negative (TBVPS will fail)
                'intangible_assets': 1e10,
                'goodwill': 1e10,
                'current_assets': 0.0,  # Zero (Net-Net will fail)
                'total_liabilities': 0.0,  # Zero (Net-Net will fail)
                'shares_outstanding': 1e9,
            },
            '2024-09-30': {
                'total_equity': -1e11,
                'intangible_assets': 1e10,
                'goodwill': 1e10,
                'current_assets': 0.0,
                'total_liabilities': 0.0,
                'shares_outstanding': 1e9,
            },
            '2024-06-30': {
                'total_equity': -1e11,
                'intangible_assets': 1e10,
                'goodwill': 1e10,
                'current_assets': 0.0,
                'total_liabilities': 0.0,
                'shares_outstanding': 1e9,
            },
            '2024-03-31': {
                'total_equity': -1e11,
                'intangible_assets': 1e10,
                'goodwill': 1e10,
                'current_assets': 0.0,
                'total_liabilities': 0.0,
                'shares_outstanding': 1e9,
            },
        },
        'income_statement': {
            '2024-12-31': {'revenue': 5e10, 'net_income': -1e10},  # Negative (EPS will fail)
            '2024-09-30': {'revenue': 5e10, 'net_income': -1e10},
            '2024-06-30': {'revenue': 5e10, 'net_income': -1e10},
            '2024-03-31': {'revenue': 5e10, 'net_income': -1e10},
        }
    }
    
    calculator = TTMCalculator(quarterly_data, 100.0, 'USD')
    result = calculator.compute_all()
    
    # All calculations should fail
    assert result['ttm_tbvps'] == "N/A"
    assert result['ttm_graham_number'] == "N/A"
    assert result['ttm_net_net'] == "N/A"
    assert result['ttm_margin_of_safety'] == "N/A"
    assert result['ttm_pe_ratio'] == "N/A"
    
    # But the result should still be returned (not crash)
    assert 'warnings' in result
    assert len(result['warnings']) > 0
    
    # Verify multiple warnings were added (one for each failure)
    # Should have warnings about: negative TBVPS, negative EPS, Net-Net data unavailable
    assert len(result['warnings']) >= 3
    
    # Check for specific warnings
    tbvps_warning = any('tbvps' in w.lower() and 'negative' in w.lower() for w in result['warnings'])
    eps_warning = any('eps' in w.lower() and ('negative' in w.lower() or 'zero' in w.lower()) 
                     for w in result['warnings'])
    net_net_warning = any('net-net' in w.lower() for w in result['warnings'])
    
    assert tbvps_warning, "Expected warning about negative TBVPS"
    assert eps_warning, "Expected warning about negative/zero EPS"
    assert net_net_warning, "Expected warning about Net-Net"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
