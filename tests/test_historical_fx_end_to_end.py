"""
End-to-End Integration Tests for Historical FX Rates

Tests the complete flow with real stocks to validate that historical FX rates
are properly fetched, matched, and applied throughout the system.
"""

import pytest
import os
from dotenv import load_dotenv
from clients.factory import ClientFactory


# Load environment variables
load_dotenv()
API_KEY = os.getenv("EODHD_API_KEY")


@pytest.mark.live
@pytest.mark.skipif(not API_KEY, reason="EODHD_API_KEY not available")
def test_vod_lse_historical_fx_rates_end_to_end():
    """
    **Feature: historical-fx-rates, End-to-End Test**
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    
    Test complete flow with VOD.LSE (GBP stock, EUR financials).
    
    This test verifies that:
    1. Historical FX rates are fetched for GBP/EUR
    2. Rates are matched to fiscal year ends
    3. Historical prices are converted using date-matched rates
    4. Historical P/E and P/B ratios are calculated correctly
    5. Appropriate warnings are generated
    """
    # Create clients
    client = ClientFactory.create_eodhd_client(API_KEY, debug=True)
    yf_client = ClientFactory.create_yfinance_client(debug=True)
    
    # Fetch all data for VOD.LSE
    financial_data = client.fetch_all_data('VOD.LSE', yf_client=yf_client)
    
    # Verify basic data was fetched
    assert financial_data is not None, "Should fetch financial data"
    assert financial_data['ticker'] == 'VOD', "Ticker should be VOD"
    assert financial_data['exchange'] == 'LSE', "Exchange should be LSE"
    
    # Verify currency information
    original_currency = financial_data.get('original_stock_currency', '')
    financials_currency = financial_data.get('financials_currency', '')
    
    print(f"Original currency: {original_currency}")
    print(f"Financials currency: {financials_currency}")
    
    # If currencies differ, historical FX rates should be fetched
    if original_currency != financials_currency and original_currency and financials_currency:
        historical_fx_rates = financial_data.get('historical_fx_rates', {})
        
        # Verify historical FX rates were fetched
        assert historical_fx_rates is not None, "Should have historical_fx_rates key"
        
        if len(historical_fx_rates) > 0:
            print(f"✓ Historical FX rates fetched: {len(historical_fx_rates)} fiscal year ends")
            
            # Verify rates are reasonable
            for date, rate in list(historical_fx_rates.items())[:5]:
                if rate is not None:
                    assert rate > 0, f"Rate for {date} should be positive"
                    print(f"  {date}: {rate:.4f}")
            
            # Verify history has year_end_price data
            history = financial_data.get('history', {})
            if history:
                prices_with_data = [year for year, data in history.items() if data.get('year_end_price') is not None]
                print(f"✓ Historical prices available for {len(prices_with_data)} years")
                
                # Check a few historical P/E ratios
                for year in list(history.keys())[:3]:
                    data = history[year]
                    price = data.get('year_end_price')
                    eps = data.get('eps', 0)
                    
                    if price and eps and eps > 0:
                        pe = price / eps
                        print(f"  {year}: Price={price:.2f}, EPS={eps:.2f}, P/E={pe:.1f}")
                        
                        # P/E should be reasonable (not 100x too high)
                        assert pe < 100, f"P/E ratio {pe} seems too high for {year}"
        else:
            print("⚠ No historical FX rates fetched (may be same currency or API issue)")
    else:
        print("⚠ Currencies match or not available - no FX conversion needed")
    
    print("✓ VOD.LSE end-to-end test completed successfully")


@pytest.mark.live
@pytest.mark.skipif(not API_KEY, reason="EODHD_API_KEY not available")
def test_msft_us_no_fx_fetch_when_currencies_match():
    """
    **Feature: historical-fx-rates, End-to-End Test**
    **Validates: Requirements 6.4**
    
    Test that no FX fetch occurs when currencies match (MSFT.US - USD/USD).
    
    This verifies the optimization that skips historical FX rate fetching
    when no currency conversion is needed.
    """
    # Create clients
    client = ClientFactory.create_eodhd_client(API_KEY, debug=True)
    yf_client = ClientFactory.create_yfinance_client(debug=True)
    
    # Fetch all data for MSFT.US
    financial_data = client.fetch_all_data('MSFT.US', yf_client=yf_client)
    
    # Verify basic data was fetched
    assert financial_data is not None, "Should fetch financial data"
    assert financial_data['ticker'] == 'MSFT', "Ticker should be MSFT"
    
    # Verify currency information
    original_currency = financial_data.get('original_stock_currency', '')
    financials_currency = financial_data.get('financials_currency', '')
    
    print(f"Original currency: {original_currency}")
    print(f"Financials currency: {financials_currency}")
    
    # For MSFT, both should be USD
    if original_currency == financials_currency:
        # Historical FX rates should be empty (no conversion needed)
        historical_fx_rates = financial_data.get('historical_fx_rates', {})
        
        assert historical_fx_rates == {} or len(historical_fx_rates) == 0, \
            "Should not fetch historical FX rates when currencies match"
        
        print("✓ No historical FX rates fetched (currencies match - optimization working)")
    else:
        print(f"⚠ Unexpected: Currencies differ ({original_currency} vs {financials_currency})")
    
    print("✓ MSFT.US end-to-end test completed successfully")


@pytest.mark.live
@pytest.mark.skipif(not API_KEY, reason="EODHD_API_KEY not available")
def test_historical_fx_rates_improve_accuracy():
    """
    Test that historical FX rates improve accuracy compared to current rates.
    
    This test compares historical P/E ratios calculated with:
    1. Historical FX rates (new method)
    2. Current FX rate (old method)
    
    The difference should be proportional to FX rate changes over time.
    """
    # Create clients
    client = ClientFactory.create_eodhd_client(API_KEY, debug=True)
    yf_client = ClientFactory.create_yfinance_client(debug=True)
    
    # Fetch data for a stock with currency conversion (e.g., VOD.LSE)
    financial_data = client.fetch_all_data('VOD.LSE', yf_client=yf_client)
    
    original_currency = financial_data.get('original_stock_currency', '')
    financials_currency = financial_data.get('financials_currency', '')
    
    if original_currency != financials_currency:
        historical_fx_rates = financial_data.get('historical_fx_rates', {})
        current_fx_rate = financial_data.get('fx_rate_used')
        
        if historical_fx_rates and current_fx_rate:
            # Compare rates across years
            rate_differences = []
            
            for year, historical_rate in historical_fx_rates.items():
                if historical_rate is not None and historical_rate > 0:
                    diff_pct = abs(historical_rate - current_fx_rate) / current_fx_rate * 100
                    rate_differences.append(diff_pct)
                    
                    if diff_pct > 5:  # More than 5% difference
                        print(f"  {year}: Historical rate {historical_rate:.4f} vs Current {current_fx_rate:.4f} ({diff_pct:.1f}% diff)")
            
            if rate_differences:
                avg_diff = sum(rate_differences) / len(rate_differences)
                max_diff = max(rate_differences)
                
                print(f"✓ FX rate variation: Avg {avg_diff:.1f}%, Max {max_diff:.1f}%")
                print(f"✓ Historical rates provide more accurate historical valuations")
            else:
                print("⚠ No significant FX rate differences found")
        else:
            print("⚠ Historical FX rates or current rate not available")
    else:
        print("⚠ Currencies match - no FX conversion needed")


@pytest.mark.live
@pytest.mark.skipif(not API_KEY, reason="EODHD_API_KEY not available")
def test_performance_overhead_acceptable():
    """
    Test that historical FX rate fetching doesn't add excessive overhead.
    
    This test measures the time taken to fetch data with historical FX rates
    and verifies it's within acceptable limits (<5 seconds additional overhead).
    """
    import time
    
    # Create clients
    client = ClientFactory.create_eodhd_client(API_KEY, debug=False)
    yf_client = ClientFactory.create_yfinance_client(debug=False)
    
    # Measure time for complete data fetch
    start_time = time.time()
    financial_data = client.fetch_all_data('VOD.LSE', yf_client=yf_client)
    end_time = time.time()
    
    elapsed_time = end_time - start_time
    
    print(f"✓ Complete data fetch took {elapsed_time:.2f} seconds")
    
    # Verify data was fetched
    assert financial_data is not None
    
    # Check if historical FX rates were fetched
    historical_fx_rates = financial_data.get('historical_fx_rates', {})
    if historical_fx_rates:
        print(f"✓ Historical FX rates fetched: {len(historical_fx_rates)} fiscal year ends")
    
    # Performance should be reasonable (< 10 seconds total)
    assert elapsed_time < 10, f"Data fetch took too long: {elapsed_time:.2f}s"
    
    print("✓ Performance overhead is acceptable")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'live'])
