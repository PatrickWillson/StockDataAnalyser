"""
Property-Based Tests for FXClient Historical Rate Functionality

Tests the historical FX rate fetching and matching using Hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from clients.fx_client import FXClient


# Property 1: Historical FX Rate Date Matching
# Validates: Requirements 1.2
@given(
    fiscal_year_ends=st.lists(
        st.dates(min_value=date(2010, 1, 1), max_value=date(2024, 12, 31)),
        min_size=1,
        max_size=10,
        unique=True
    )
)
@settings(max_examples=100)
def test_matched_rates_within_7_day_window(fiscal_year_ends):
    """
    **Feature: historical-fx-rates, Property 1: Historical FX Rate Date Matching**
    
    Property: For any fiscal year end, if a rate is matched, it must be from
    the same date or within 7 days prior.
    
    This ensures that the match_fiscal_year_end_rates() method correctly
    searches backwards up to 7 days to find the nearest available rate.
    """
    client = FXClient()
    
    # Convert dates to strings
    fiscal_ends_str = [d.strftime('%Y-%m-%d') for d in fiscal_year_ends]
    
    # Create rate data with some dates having rates
    rate_data = {}
    for fiscal_end in fiscal_year_ends:
        # Add rates for some dates within the 7-day window
        for days_back in range(0, 8):
            check_date = fiscal_end - timedelta(days=days_back)
            # Randomly add rates (50% chance)
            if hash(check_date) % 2 == 0:
                rate_data[check_date.strftime('%Y-%m-%d')] = 1.0 + (hash(check_date) % 100) / 100.0
    
    # Match rates to fiscal year ends
    result = client.match_fiscal_year_end_rates(rate_data, fiscal_ends_str)
    
    # Verify property: If a rate is matched, it must be from within 7 days prior
    for fiscal_end_str, matched_rate in result.items():
        if matched_rate is not None:
            # Find the date that provided this rate
            fiscal_date = date.fromisoformat(fiscal_end_str)
            
            # Check that the rate came from within 7 days prior (or exact match)
            found_within_window = False
            for days_back in range(0, 8):
                check_date = (fiscal_date - timedelta(days=days_back)).strftime('%Y-%m-%d')
                if check_date in rate_data and abs(rate_data[check_date] - matched_rate) < 0.0001:
                    found_within_window = True
                    break
            
            assert found_within_window, f"Matched rate {matched_rate} for {fiscal_end_str} not from within 7-day window"


# Property 4: Historical Rate Caching
# Validates: Requirements 2.5, 6.2
@given(
    from_currency=st.sampled_from(['GBP', 'EUR', 'JPY', 'CAD']),
    to_currency=st.sampled_from(['USD', 'EUR', 'GBP']),
    start_date=st.dates(min_value=date(2020, 1, 1), max_value=date(2022, 12, 31)),
    end_date=st.dates(min_value=date(2023, 1, 1), max_value=date(2024, 12, 31))
)
@settings(max_examples=50, deadline=None)  # Disable deadline for API calls
def test_historical_rate_caching(from_currency, to_currency, start_date, end_date):
    """
    **Feature: historical-fx-rates, Property 4: Historical Rate Caching**
    
    Property: For any currency pair and date range, fetching historical FX rates
    multiple times within the same session should result in only one API call,
    with subsequent calls returning cached data.
    
    This ensures efficient API usage and faster subsequent analyses.
    """
    # Skip if same currency (no API call needed)
    if from_currency == to_currency:
        return
    
    # Ensure start_date < end_date
    if start_date >= end_date:
        start_date, end_date = end_date, start_date
    
    client = FXClient(debug=True)
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    with patch('yfinance.Ticker') as mock_ticker_class:
        # Create mock historical data
        mock_ticker = MagicMock()
        
        # Create a mock DataFrame with historical rates
        dates = pd.date_range(start=start_str, end=end_str, freq='D')
        mock_hist = pd.DataFrame({
            'Close': [1.2 + (i % 10) / 100.0 for i in range(len(dates))]
        }, index=dates)
        
        mock_ticker.history.return_value = mock_hist
        mock_ticker_class.return_value = mock_ticker
        
        # First call should hit the API
        result1 = client.fetch_historical_rates(from_currency, to_currency, start_str, end_str)
        assert result1 is not None
        assert len(result1) > 0
        assert mock_ticker.history.call_count == 1
        
        # Second call should use cache (no additional API call)
        result2 = client.fetch_historical_rates(from_currency, to_currency, start_str, end_str)
        assert result2 is not None
        assert len(result2) > 0
        assert mock_ticker.history.call_count == 1  # Still 1, not 2
        
        # Results should be identical
        assert result1 == result2


# Property 5: Fiscal Year End Matching
# Validates: Requirements 2.4, 5.1
@given(
    fiscal_year_end=st.dates(min_value=date(2020, 1, 1), max_value=date(2024, 12, 31)),
    days_offset=st.integers(min_value=0, max_value=7)
)
@settings(max_examples=100)
def test_fiscal_year_end_matching_searches_backwards(fiscal_year_end, days_offset):
    """
    **Feature: historical-fx-rates, Property 5: Fiscal Year End Matching**
    
    Property: For any fiscal year end date that falls on a weekend or holiday,
    the matched FX rate should be from the most recent trading day within 7 days
    prior, not from a future date.
    
    This ensures we use the last available rate before the fiscal year end,
    which is the correct approach for historical valuations.
    """
    client = FXClient()
    
    fiscal_end_str = fiscal_year_end.strftime('%Y-%m-%d')
    
    # Create rate data with a rate available at days_offset days before fiscal year end
    rate_date = fiscal_year_end - timedelta(days=days_offset)
    rate_date_str = rate_date.strftime('%Y-%m-%d')
    
    rate_data = {
        rate_date_str: 1.25
    }
    
    # Match rate to fiscal year end
    result = client.match_fiscal_year_end_rates(rate_data, [fiscal_end_str])
    
    # If days_offset <= 7, should find the rate
    if days_offset <= 7:
        assert result[fiscal_end_str] == 1.25, f"Should find rate {days_offset} days back"
    
    # Verify that we never match a future date
    # Add a rate 1 day in the future
    future_date = fiscal_year_end + timedelta(days=1)
    future_date_str = future_date.strftime('%Y-%m-%d')
    rate_data[future_date_str] = 1.50
    
    # Re-match
    result = client.match_fiscal_year_end_rates(rate_data, [fiscal_end_str])
    
    # Should still use the past rate (1.25), not the future rate (1.50)
    if days_offset <= 7:
        assert result[fiscal_end_str] == 1.25, "Should not use future rate"


# Additional test: Exact match takes precedence
@given(
    fiscal_year_end=st.dates(min_value=date(2020, 1, 1), max_value=date(2024, 12, 31))
)
@settings(max_examples=50)
def test_exact_match_takes_precedence(fiscal_year_end):
    """
    Property: When an exact match exists for a fiscal year end date,
    it should be used instead of searching backwards.
    """
    client = FXClient()
    
    fiscal_end_str = fiscal_year_end.strftime('%Y-%m-%d')
    
    # Create rate data with exact match and a different rate 1 day prior
    rate_data = {
        fiscal_end_str: 1.30,  # Exact match
        (fiscal_year_end - timedelta(days=1)).strftime('%Y-%m-%d'): 1.25  # 1 day prior
    }
    
    result = client.match_fiscal_year_end_rates(rate_data, [fiscal_end_str])
    
    # Should use exact match (1.30), not the prior date (1.25)
    assert result[fiscal_end_str] == 1.30, "Exact match should take precedence"


# Test: Returns None when no rate within 7-day window
@given(
    fiscal_year_end=st.dates(min_value=date(2020, 1, 15), max_value=date(2024, 12, 15))
)
@settings(max_examples=50)
def test_returns_none_when_no_rate_within_window(fiscal_year_end):
    """
    Property: When no rate is available within the 7-day window,
    the method should return None for that fiscal year end.
    """
    client = FXClient()
    
    fiscal_end_str = fiscal_year_end.strftime('%Y-%m-%d')
    
    # Create rate data with rates only 8+ days before fiscal year end
    rate_data = {
        (fiscal_year_end - timedelta(days=8)).strftime('%Y-%m-%d'): 1.25,
        (fiscal_year_end - timedelta(days=10)).strftime('%Y-%m-%d'): 1.20
    }
    
    result = client.match_fiscal_year_end_rates(rate_data, [fiscal_end_str])
    
    # Should return None (no rate within 7-day window)
    assert result[fiscal_end_str] is None, "Should return None when no rate within 7 days"


# Test: GBX normalization in historical rates
def test_gbx_normalization_in_historical_rates():
    """
    Test that GBX is normalized to GBP when fetching historical rates.
    """
    client = FXClient()
    
    with patch('yfinance.Ticker') as mock_ticker_class:
        mock_ticker = MagicMock()
        
        # Create mock historical data
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        mock_hist = pd.DataFrame({
            'Close': [1.25 + (i % 10) / 100.0 for i in range(len(dates))]
        }, index=dates)
        
        mock_ticker.history.return_value = mock_hist
        mock_ticker_class.return_value = mock_ticker
        
        # Request GBX to USD historical rates (should normalize to GBP/USD)
        result = client.fetch_historical_rates('GBX', 'USD', '2023-01-01', '2023-12-31')
        
        # Verify yfinance.Ticker was called with GBP, not GBX
        mock_ticker_class.assert_called_once_with('GBPUSD=X')
        assert result is not None
        assert len(result) > 0


# Test: Same currency returns empty dict
def test_same_currency_returns_empty_dict():
    """
    Test that fetching historical rates for same currency returns empty dict.
    """
    client = FXClient()
    
    result = client.fetch_historical_rates('USD', 'USD', '2023-01-01', '2023-12-31')
    
    # Should return empty dict (no conversion needed)
    assert result == {}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
