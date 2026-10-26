"""
Integration tests for historical price fetching in main workflow.

Tests verify that historical prices are correctly integrated into the
financial_data['history'] dict during the main analysis workflow.
"""

import pytest
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from clients.factory import ClientFactory

# Load environment variables
load_dotenv()
API_KEY = os.getenv("EODHD_API_KEY")


@pytest.mark.live
def test_historical_prices_integrated_into_history_msft():
    """
    Test that historical prices are correctly integrated into financial_data['history'].
    
    Verifies:
    - year_end_price field exists in history dict
    - Prices are present for most years (some gaps acceptable)
    - Prices are reasonable values (> 0)
    """
    if not API_KEY:
        pytest.skip("EODHD_API_KEY not available")
    
    ticker = "MSFT.US"
    
    # Fetch data using same workflow as main script
    client = ClientFactory.create_eodhd_client(API_KEY, debug=True)
    yf_client = ClientFactory.create_yfinance_client(debug=True)
    financial_data = client.fetch_all_data(ticker, yf_client=yf_client)
    
    # Get history keys
    history_keys = list(financial_data.get('history', {}).keys())
    assert len(history_keys) > 0, "No financial history available"
    
    # Fetch historical prices (simulating main workflow)
    oldest_date = min(history_keys)
    newest_date = max(history_keys)
    
    daily_prices = yf_client.fetch_historical_prices(
        ticker,
        start_date=oldest_date,
        end_date=newest_date
    )
    
    assert daily_prices is not None, "Historical prices should be available"
    assert len(daily_prices) > 0, "Should have at least some historical prices"
    
    # Match to fiscal year ends
    year_end_prices = yf_client.match_fiscal_year_end_prices(
        daily_prices,
        fiscal_year_ends=history_keys
    )
    
    # Merge into history (simulating main workflow)
    for date_key, price_value in year_end_prices.items():
        if date_key in financial_data['history']:
            financial_data['history'][date_key]['year_end_price'] = price_value
    
    # Verify integration
    history = financial_data['history']
    
    # Check that year_end_price field exists
    years_with_price = 0
    years_without_price = 0
    
    for year, data in history.items():
        assert 'year_end_price' in data, f"year_end_price field missing for {year}"
        
        price = data['year_end_price']
        if price is not None:
            years_with_price += 1
            assert price > 0, f"Price should be positive for {year}, got {price}"
        else:
            years_without_price += 1
    
    # Should have prices for most years (allow up to 20% gaps)
    total_years = len(history)
    coverage_ratio = years_with_price / total_years
    
    print("\nHistorical Price Coverage:")
    print(f"  Total years: {total_years}")
    print(f"  Years with price: {years_with_price}")
    print(f"  Years without price: {years_without_price}")
    print(f"  Coverage: {coverage_ratio*100:.1f}%")
    
    assert coverage_ratio >= 0.80, f"Should have prices for at least 80% of years, got {coverage_ratio*100:.1f}%"


@pytest.mark.live
def test_historical_prices_currency_conversion_lse():
    """
    Test that historical prices are correctly converted when currencies differ.
    
    Uses VOD.LSE which trades in GBX but reports financials in GBP.
    """
    if not API_KEY:
        pytest.skip("EODHD_API_KEY not available")
    
    ticker = "VOD.LSE"
    
    # Fetch data
    client = ClientFactory.create_eodhd_client(API_KEY, debug=True)
    yf_client = ClientFactory.create_yfinance_client(debug=True)
    financial_data = client.fetch_all_data(ticker, yf_client=yf_client)
    
    # Get currencies
    stock_currency = financial_data.get('original_stock_currency', '')
    financials_currency = financial_data.get('financials_currency', '')
    
    print("\nCurrency Info:")
    print(f"  Stock Currency: {stock_currency}")
    print(f"  Financials Currency: {financials_currency}")
    
    # Get history keys
    history_keys = list(financial_data.get('history', {}).keys())
    if len(history_keys) == 0:
        pytest.skip("No financial history available for VOD.LSE")
    
    # Fetch historical prices
    oldest_date = min(history_keys)
    newest_date = max(history_keys)
    
    daily_prices = yf_client.fetch_historical_prices(
        ticker,
        start_date=oldest_date,
        end_date=newest_date
    )
    
    if daily_prices is None:
        pytest.skip("Historical prices unavailable for VOD.LSE")
    
    # Match to fiscal year ends
    year_end_prices = yf_client.match_fiscal_year_end_prices(
        daily_prices,
        fiscal_year_ends=history_keys
    )
    
    # Apply currency conversion if needed (simulating main workflow)
    exchange = financial_data.get('exchange', '')
    
    # For LSE stocks, yfinance returns prices in GBX (pence), not GBP
    # We need to convert GBX → GBP first, then GBP → financials_currency (if needed)
    if exchange == "LSE" and stock_currency == "GBX":
        print("  Converting historical prices from GBX (pence) to GBP (pounds)")
        gbp_prices = {}
        for date_key, price_value in year_end_prices.items():
            if price_value is not None:
                gbp_prices[date_key] = price_value / 100  # GBX → GBP
            else:
                gbp_prices[date_key] = None
        year_end_prices = gbp_prices
        # Update currency for next conversion step
        stock_currency = "GBP"
        print(f"  Converted {len([p for p in gbp_prices.values() if p is not None])} prices from GBX to GBP")
    
    if stock_currency and financials_currency and stock_currency != financials_currency:
        fx_rate = financial_data.get('fx_rate_used')
        
        if fx_rate and fx_rate > 0:
            print(f"  FX Rate Used: {fx_rate:.4f}")
            
            # Convert all prices
            converted_prices = {}
            for date_key, price_value in year_end_prices.items():
                if price_value is not None:
                    converted_prices[date_key] = price_value * fx_rate
                else:
                    converted_prices[date_key] = None
            
            year_end_prices = converted_prices
    
    # Merge into history
    for date_key, price_value in year_end_prices.items():
        if date_key in financial_data['history']:
            financial_data['history'][date_key]['year_end_price'] = price_value
    
    # Verify prices are in financials currency (should be reasonable GBP values)
    history = financial_data['history']
    
    prices_found = []
    for year, data in history.items():
        price = data.get('year_end_price')
        if price is not None:
            prices_found.append(price)
    
    if len(prices_found) > 0:
        avg_price = sum(prices_found) / len(prices_found)
        print(f"  Average historical price: {avg_price:.2f} {financials_currency}")
        
        # VOD.LSE prices should be in reasonable range after conversion
        # yfinance returns GBX (pence), we convert to GBP, then to financials_currency
        # After GBX→GBP conversion, prices should be 0.50 to 5.00 GBP typically
        # After GBP→EUR conversion (rate ~1.15), prices should be 0.60 to 6.00 EUR typically
        # If we see values > 100, it means GBX→GBP conversion wasn't applied
        assert avg_price < 100, f"Prices seem unconverted from GBX (avg={avg_price:.2f}), expected {financials_currency} values after GBX→GBP→{financials_currency} conversion"


@pytest.mark.live
def test_graceful_degradation_invalid_ticker():
    """
    Test that workflow continues gracefully when historical prices unavailable.
    
    Uses an invalid ticker to simulate yfinance failure.
    """
    if not API_KEY:
        pytest.skip("EODHD_API_KEY not available")
    
    # Use a ticker that might not have yfinance data
    ticker = "INVALID.US"
    
    yf_client = ClientFactory.create_yfinance_client(debug=True)
    
    # Try to fetch historical prices
    daily_prices = yf_client.fetch_historical_prices(
        ticker,
        start_date="2020-01-01",
        end_date="2024-12-31"
    )
    
    # Should return None, not crash
    assert daily_prices is None, "Should return None for invalid ticker"
    
    # Workflow should continue with year_end_price = None for all years
    # This is tested implicitly by the main workflow's graceful degradation


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
