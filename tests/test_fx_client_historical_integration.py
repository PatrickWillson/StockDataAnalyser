"""
Integration Tests for FXClient Historical Rate Functionality

Tests the historical FX rate fetching with live yfinance data.
These tests require network access and are marked with @pytest.mark.live.
"""

import pytest
from datetime import date
from clients.fx_client import FXClient


@pytest.mark.live
def test_fetch_historical_fx_rates_gbp_usd():
    """
    **Feature: historical-fx-rates, Integration Test**
    **Validates: Requirements 2.2, 2.3**
    
    Test fetching real historical FX rates from yfinance for GBP/USD.
    
    This integration test verifies that:
    1. Historical FX data can be fetched from yfinance
    2. The data structure is correct (dict mapping dates to rates)
    3. The rates are reasonable (GBP/USD typically 1.1 - 1.5)
    4. Multiple years of data are returned
    """
    client = FXClient(debug=True)
    
    # Fetch 5 years of GBP/USD rates
    rate_data = client.fetch_historical_rates(
        'GBP',
        'USD',
        '2019-01-01',
        '2024-12-31'
    )
    
    # Verify data was fetched
    assert rate_data is not None, "Should fetch historical FX data"
    assert len(rate_data) > 1000, f"Should have ~1250 trading days, got {len(rate_data)}"
    
    # Verify data structure
    assert isinstance(rate_data, dict), "Should return dict"
    
    # Check a few dates
    for date_str, rate in list(rate_data.items())[:10]:
        # Verify date format
        assert len(date_str) == 10, f"Date should be YYYY-MM-DD format: {date_str}"
        assert date_str[4] == '-' and date_str[7] == '-', f"Date format incorrect: {date_str}"
        
        # Verify rate is reasonable (GBP/USD typically 1.1 - 1.5)
        assert 1.0 < rate < 1.6, f"Unreasonable rate {rate} for {date_str}"
    
    print(f"✓ Fetched {len(rate_data)} days of GBP/USD historical rates")
    print(f"✓ Sample rates: {list(rate_data.items())[:3]}")


@pytest.mark.live
def test_fetch_historical_fx_rates_eur_usd():
    """
    Test fetching real historical FX rates for EUR/USD.
    """
    client = FXClient(debug=True)
    
    # Fetch 3 years of EUR/USD rates
    rate_data = client.fetch_historical_rates(
        'EUR',
        'USD',
        '2021-01-01',
        '2024-12-31'
    )
    
    # Verify data was fetched
    assert rate_data is not None
    assert len(rate_data) > 700, f"Should have ~750 trading days, got {len(rate_data)}"
    
    # Check that rates are reasonable (EUR/USD typically 1.0 - 1.3)
    for date_str, rate in list(rate_data.items())[:10]:
        assert 0.9 < rate < 1.4, f"Unreasonable rate {rate} for {date_str}"
    
    print(f"✓ Fetched {len(rate_data)} days of EUR/USD historical rates")


@pytest.mark.live
def test_match_fiscal_year_end_rates_with_real_data():
    """
    Test matching fiscal year ends to real historical FX data.
    """
    client = FXClient(debug=True)
    
    # Fetch historical rates
    rate_data = client.fetch_historical_rates(
        'GBP',
        'USD',
        '2020-01-01',
        '2024-12-31'
    )
    
    assert rate_data is not None
    
    # Define fiscal year ends (some may fall on weekends)
    fiscal_year_ends = [
        '2024-06-30',  # Sunday in 2024
        '2023-12-31',  # Sunday in 2023
        '2022-12-31',  # Saturday in 2022
        '2021-12-31',  # Friday in 2021
        '2020-12-31'   # Thursday in 2020
    ]
    
    # Match rates to fiscal year ends
    matched_rates = client.match_fiscal_year_end_rates(rate_data, fiscal_year_ends)
    
    # Verify all fiscal year ends have rates
    for fiscal_end in fiscal_year_ends:
        assert fiscal_end in matched_rates, f"Should have rate for {fiscal_end}"
        rate = matched_rates[fiscal_end]
        
        # Rate should be found (within 7-day window)
        assert rate is not None, f"Should find rate for {fiscal_end} within 7-day window"
        assert 1.0 < rate < 1.6, f"Rate {rate} for {fiscal_end} is unreasonable"
    
    print(f"✓ Matched rates to {len(matched_rates)} fiscal year ends")
    for fiscal_end, rate in matched_rates.items():
        print(f"  {fiscal_end}: {rate:.4f}")


@pytest.mark.live
def test_historical_fx_rates_caching():
    """
    Test that historical FX rates are cached across multiple calls.
    """
    client = FXClient(debug=True)
    
    # First call - should hit API
    rate_data_1 = client.fetch_historical_rates(
        'GBP',
        'USD',
        '2023-01-01',
        '2023-12-31'
    )
    
    assert rate_data_1 is not None
    assert len(rate_data_1) > 200
    
    # Second call with same parameters - should use cache
    rate_data_2 = client.fetch_historical_rates(
        'GBP',
        'USD',
        '2023-01-01',
        '2023-12-31'
    )
    
    assert rate_data_2 is not None
    
    # Results should be identical (same object from cache)
    assert rate_data_1 == rate_data_2
    assert id(rate_data_1) == id(rate_data_2), "Should return same cached object"
    
    print("✓ Historical FX rates are properly cached")


@pytest.mark.live
def test_same_currency_returns_empty_dict():
    """
    Test that fetching historical rates for same currency returns empty dict.
    """
    client = FXClient()
    
    result = client.fetch_historical_rates('USD', 'USD', '2023-01-01', '2023-12-31')
    
    assert result == {}, "Same currency should return empty dict"
    print("✓ Same currency returns empty dict (no conversion needed)")


@pytest.mark.live
def test_invalid_currency_pair_returns_none():
    """
    Test that invalid currency pairs return None gracefully.
    """
    client = FXClient(debug=True)
    
    # Try to fetch rates for invalid currency pair
    result = client.fetch_historical_rates('XYZ', 'ABC', '2023-01-01', '2023-12-31')
    
    # Should return None (not crash)
    assert result is None, "Invalid currency pair should return None"
    print("✓ Invalid currency pair handled gracefully")


@pytest.mark.live
def test_gbx_normalization_in_historical_fetch():
    """
    Test that GBX is normalized to GBP when fetching historical rates.
    """
    client = FXClient(debug=True)
    
    # Request GBX to USD historical rates (should normalize to GBP/USD)
    rate_data = client.fetch_historical_rates(
        'GBX',
        'USD',
        '2023-01-01',
        '2023-12-31'
    )
    
    # Should fetch GBP/USD rates (not fail)
    assert rate_data is not None
    assert len(rate_data) > 200
    
    # Rates should be in GBP/USD range (1.1 - 1.5), not GBX/USD range (110 - 150)
    for date_str, rate in list(rate_data.items())[:10]:
        assert 1.0 < rate < 1.6, f"Rate {rate} suggests GBX was not normalized to GBP"
    
    print("✓ GBX correctly normalized to GBP for historical rates")


@pytest.mark.live
def test_fiscal_year_end_on_weekend():
    """
    Test that fiscal year ends falling on weekends find the nearest trading day.
    """
    client = FXClient(debug=True)
    
    # Fetch rates for a period
    rate_data = client.fetch_historical_rates(
        'GBP',
        'USD',
        '2024-06-20',
        '2024-07-10'
    )
    
    assert rate_data is not None
    
    # 2024-06-30 is a Sunday (no trading)
    # Should find rate from Friday 2024-06-28 or earlier
    fiscal_year_ends = ['2024-06-30']
    
    matched_rates = client.match_fiscal_year_end_rates(rate_data, fiscal_year_ends)
    
    # Should find a rate within 7-day window
    assert matched_rates['2024-06-30'] is not None, "Should find rate for weekend fiscal year end"
    
    print(f"✓ Found rate for weekend fiscal year end: {matched_rates['2024-06-30']:.4f}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'live'])
