"""
Tests for Historical FX Rate Error Handling and Graceful Degradation

Tests that the system continues processing when historical rates are unavailable.
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch, MagicMock
from clients.fx_client import FXClient
from core.financial_data_processor import FinancialDataProcessor


# Property Test: Graceful Degradation
# Validates: Requirements 5.5, 6.5
@given(
    num_years=st.integers(min_value=1, max_value=20),
    current_rate=st.floats(min_value=0.5, max_value=2.0)
)
@settings(max_examples=100)
def test_system_continues_when_historical_rates_missing(num_years, current_rate):
    """
    **Feature: historical-fx-rates, Property: Graceful Degradation**
    **Validates: Requirements 5.5, 6.5**
    
    Property: For any financial history, the system should continue processing
    even when all historical FX rates are missing, falling back to current rate.
    
    This ensures the system never crashes due to missing historical data.
    """
    # Create history with random years
    history = {}
    for i in range(num_years):
        year = f"{2020 + i}-12-31"
        history[year] = {
            'revenue': 1000.0 + i * 100,
            'net_income': 100.0 + i * 10,
            'eps': 1.0 + i * 0.1
        }
    
    # All historical rates are None (unavailable)
    historical_fx_rates = {year: None for year in history.keys()}
    
    # Apply historical FX rates (should not crash)
    try:
        converted_history, warnings = FinancialDataProcessor.apply_historical_fx_rates(
            history,
            historical_fx_rates,
            'GBP',
            'USD',
            current_rate
        )
        
        # Verify processing completed
        assert converted_history is not None, "Should return converted history"
        assert len(converted_history) == num_years, "Should process all years"
        assert len(warnings) > 0, "Should generate warnings for fallback"
        
        # Verify all values were converted using current rate
        for year, data in converted_history.items():
            if 'revenue' in history[year] and history[year]['revenue'] != 0:
                expected = history[year]['revenue'] * current_rate
                assert abs(converted_history[year]['revenue'] - expected) < 0.01
        
    except Exception as e:
        pytest.fail(f"System should not crash when historical rates missing: {e}")


# Integration Test: Error Handling
# Validates: Requirements 6.5
def test_fx_client_handles_api_failure_gracefully():
    """
    **Feature: historical-fx-rates, Integration Test**
    **Validates: Requirements 6.5**
    
    Test that FXClient handles yfinance API failures gracefully.
    """
    client = FXClient(debug=True)
    
    with patch('yfinance.Ticker') as mock_ticker_class:
        # Simulate API failure
        mock_ticker_class.side_effect = Exception("Network error")
        
        # Should not crash, should return None
        result = client.fetch_historical_rates('GBP', 'USD', '2023-01-01', '2023-12-31')
        
        assert result is None, "Should return None on API failure"


def test_fx_client_handles_empty_data_gracefully():
    """
    Test that FXClient handles empty historical data gracefully.
    """
    client = FXClient(debug=True)
    
    with patch('yfinance.Ticker') as mock_ticker_class:
        # Simulate empty DataFrame
        mock_ticker = MagicMock()
        import pandas as pd
        mock_ticker.history.return_value = pd.DataFrame()  # Empty DataFrame
        mock_ticker_class.return_value = mock_ticker
        
        # Should not crash, should return None
        result = client.fetch_historical_rates('GBP', 'USD', '2023-01-01', '2023-12-31')
        
        assert result is None, "Should return None when no data available"


def test_match_fiscal_year_end_handles_invalid_dates():
    """
    Test that match_fiscal_year_end_rates handles invalid date formats gracefully.
    """
    client = FXClient(debug=True)
    
    rate_data = {
        '2023-12-31': 1.25,
        '2023-12-30': 1.24
    }
    
    # Include invalid date format
    fiscal_year_ends = [
        '2023-12-31',  # Valid
        'invalid-date',  # Invalid
        '2023-13-45'  # Invalid (month 13, day 45)
    ]
    
    # Should not crash
    try:
        result = client.match_fiscal_year_end_rates(rate_data, fiscal_year_ends)
        
        # Valid date should have rate
        assert result['2023-12-31'] == 1.25
        
        # Invalid dates should have None
        assert result['invalid-date'] is None
        assert result['2023-13-45'] is None
        
    except Exception as e:
        pytest.fail(f"Should handle invalid dates gracefully: {e}")


def test_apply_historical_fx_rates_handles_missing_fields():
    """
    Test that apply_historical_fx_rates handles missing monetary fields gracefully.
    """
    # History with some missing fields
    history = {
        '2023-12-31': {
            'revenue': 1000.0,
            # 'net_income' is missing
            'eps': 1.0
            # 'dividend' is missing
        }
    }
    
    historical_fx_rates = {'2023-12-31': 1.25}
    
    # Should not crash
    try:
        converted_history, warnings = FinancialDataProcessor.apply_historical_fx_rates(
            history,
            historical_fx_rates,
            'GBP',
            'USD',
            1.30
        )
        
        # Should process available fields
        assert converted_history['2023-12-31']['revenue'] == 1250.0
        assert converted_history['2023-12-31']['eps'] == 1.25
        
    except Exception as e:
        pytest.fail(f"Should handle missing fields gracefully: {e}")


def test_system_continues_with_partial_historical_rates():
    """
    Test that system continues processing when some (but not all) historical rates are available.
    """
    history = {
        '2023-12-31': {'revenue': 1000.0, 'eps': 1.0},
        '2022-12-31': {'revenue': 950.0, 'eps': 0.95},
        '2021-12-31': {'revenue': 900.0, 'eps': 0.90}
    }
    
    # Only 2023 and 2021 have rates, 2022 is missing
    historical_fx_rates = {
        '2023-12-31': 1.30,
        '2022-12-31': None,  # Missing
        '2021-12-31': 1.20
    }
    
    current_rate = 1.25
    
    # Should not crash
    try:
        converted_history, warnings = FinancialDataProcessor.apply_historical_fx_rates(
            history,
            historical_fx_rates,
            'GBP',
            'USD',
            current_rate
        )
        
        # All years should be processed
        assert len(converted_history) == 3
        
        # 2023 uses historical rate
        assert abs(converted_history['2023-12-31']['revenue'] - 1300.0) < 0.01
        
        # 2022 uses current rate (fallback)
        assert abs(converted_history['2022-12-31']['revenue'] - 1187.5) < 0.01
        
        # 2021 uses historical rate
        assert abs(converted_history['2021-12-31']['revenue'] - 1080.0) < 0.01
        
        # Should have warning about 2022
        assert len(warnings) > 0
        assert '2022' in warnings[0]
        
    except Exception as e:
        pytest.fail(f"Should handle partial historical rates gracefully: {e}")


def test_empty_historical_fx_rates_dict():
    """
    Test that empty historical_fx_rates dict is handled gracefully.
    """
    history = {
        '2023-12-31': {'revenue': 1000.0}
    }
    
    # Empty dict (no historical rates)
    historical_fx_rates = {}
    current_rate = 1.25
    
    # Should not crash, should use current rate for all
    try:
        converted_history, warnings = FinancialDataProcessor.apply_historical_fx_rates(
            history,
            historical_fx_rates,
            'GBP',
            'USD',
            current_rate
        )
        
        # Should use current rate
        assert abs(converted_history['2023-12-31']['revenue'] - 1250.0) < 0.01
        
        # Should have warning
        assert len(warnings) > 0
        
    except Exception as e:
        pytest.fail(f"Should handle empty historical_fx_rates dict gracefully: {e}")


def test_zero_current_rate_handled():
    """
    Test that zero or invalid current rate is handled.
    """
    history = {
        '2023-12-31': {'revenue': 1000.0}
    }
    
    historical_fx_rates = {'2023-12-31': None}
    current_rate = 0.0  # Invalid
    
    # Should not crash (though results may be zero)
    try:
        converted_history, warnings = FinancialDataProcessor.apply_historical_fx_rates(
            history,
            historical_fx_rates,
            'GBP',
            'USD',
            current_rate
        )
        
        # Should complete without crashing
        assert converted_history is not None
        
    except Exception as e:
        pytest.fail(f"Should handle zero current rate gracefully: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
