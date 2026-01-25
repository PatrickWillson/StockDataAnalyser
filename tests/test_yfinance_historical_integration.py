"""
Integration tests for yfinance historical price fetching.

These tests use real yfinance API calls and are marked with @pytest.mark.live.
Run with: pytest tests/test_yfinance_historical_integration.py -v -m live
"""

import pytest
from datetime import datetime, timedelta
from clients.yfinance_client import YFinanceClient


@pytest.mark.live
class TestHistoricalPriceFetching:
    """Integration tests for fetch_historical_prices()."""
    
    def test_fetch_historical_prices_msft(self):
        """Test fetching real historical data for MSFT.US."""
        client = YFinanceClient(debug=True)
        
        # Fetch 5 years of data
        prices = client.fetch_historical_prices(
            'MSFT.US',
            '2020-01-01',
            '2024-12-31'
        )
        
        assert prices is not None, "Should return price data"
        assert len(prices) > 1000, "Should have ~1250 trading days (250/year × 5 years)"
        assert isinstance(prices, dict), "Should return dict"
        
        # Check data structure
        for date_str, price in list(prices.items())[:5]:
            assert isinstance(date_str, str), "Keys should be strings"
            assert isinstance(price, float), "Values should be floats"
            assert price > 0, "Prices should be positive"
            # Verify date format
            datetime.strptime(date_str, '%Y-%m-%d')
    
    def test_fetch_historical_prices_lse_stock(self):
        """Test fetching historical data for LSE stock (VOD.LSE)."""
        client = YFinanceClient(debug=True)
        
        prices = client.fetch_historical_prices(
            'VOD.LSE',
            '2022-01-01',
            '2023-12-31'
        )
        
        assert prices is not None, "Should return price data for LSE stock"
        assert len(prices) > 400, "Should have ~500 trading days (250/year × 2 years)"
        
        # Verify prices are reasonable for Vodafone (in pence)
        sample_price = list(prices.values())[0]
        assert 50 < sample_price < 200, "VOD price should be in reasonable range (50-200 pence)"
    
    def test_fetch_historical_prices_toronto_stock(self):
        """Test fetching historical data for Toronto stock (RY.TO)."""
        client = YFinanceClient(debug=True)
        
        prices = client.fetch_historical_prices(
            'RY.TO',
            '2023-01-01',
            '2023-12-31'
        )
        
        assert prices is not None, "Should return price data for Toronto stock"
        assert len(prices) > 200, "Should have ~250 trading days"
    
    def test_fetch_historical_prices_invalid_ticker(self):
        """Test handling of invalid ticker."""
        client = YFinanceClient(debug=False)
        
        prices = client.fetch_historical_prices(
            'INVALID.XX',
            '2023-01-01',
            '2023-12-31'
        )
        
        assert prices is None, "Should return None for invalid ticker"
    
    def test_fetch_historical_prices_no_data_for_range(self):
        """Test handling when no data available for date range."""
        client = YFinanceClient(debug=False)
        
        # Try to fetch data from the future
        future_start = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        future_end = (datetime.now() + timedelta(days=730)).strftime('%Y-%m-%d')
        
        prices = client.fetch_historical_prices(
            'MSFT.US',
            future_start,
            future_end
        )
        
        assert prices is None, "Should return None when no data available"
    
    def test_fetch_historical_prices_split_adjusted(self):
        """Test that prices are split-adjusted."""
        client = YFinanceClient(debug=True)
        
        # Fetch data spanning a known stock split
        # AAPL had a 4-for-1 split on 2020-08-31
        prices = client.fetch_historical_prices(
            'AAPL.US',
            '2020-08-01',
            '2020-09-30'
        )
        
        assert prices is not None, "Should return price data"
        
        # Get prices before and after split
        pre_split = prices.get('2020-08-28')  # Friday before split
        post_split = prices.get('2020-08-31')  # Split date
        
        if pre_split and post_split:
            # Prices should be comparable (split-adjusted)
            # They should be in similar range, not 4x different
            ratio = pre_split / post_split
            assert 0.8 < ratio < 1.2, "Split-adjusted prices should be comparable"


@pytest.mark.live
class TestFiscalYearEndMatching:
    """Integration tests for match_fiscal_year_end_prices()."""
    
    def test_match_exact_dates(self):
        """Test matching when fiscal year ends fall on trading days."""
        client = YFinanceClient(debug=True)
        
        # Fetch data
        prices = client.fetch_historical_prices(
            'MSFT.US',
            '2023-01-01',
            '2024-12-31'
        )
        
        assert prices is not None
        
        # MSFT fiscal year ends on June 30
        fiscal_year_ends = ['2024-06-30', '2023-06-30']
        
        matched = client.match_fiscal_year_end_prices(prices, fiscal_year_ends)
        
        assert len(matched) == 2, "Should match both fiscal year ends"
        assert '2024-06-30' in matched
        assert '2023-06-30' in matched
        
        # At least one should have a price (June 30 might be weekend)
        prices_found = sum(1 for p in matched.values() if p is not None)
        assert prices_found >= 1, "Should find at least one price"
    
    def test_match_weekend_fiscal_year_end(self):
        """Test matching when fiscal year end falls on weekend."""
        client = YFinanceClient(debug=True)
        
        prices = client.fetch_historical_prices(
            'AAPL.US',
            '2023-09-01',
            '2023-10-31'
        )
        
        assert prices is not None
        
        # AAPL fiscal year ends on last Saturday of September
        # 2023-09-30 was a Saturday
        fiscal_year_ends = ['2023-09-30']
        
        matched = client.match_fiscal_year_end_prices(prices, fiscal_year_ends)
        
        assert '2023-09-30' in matched
        # Should find price from Friday 2023-09-29
        assert matched['2023-09-30'] is not None, "Should find price from last trading day"
    
    def test_match_multiple_years(self):
        """Test matching multiple fiscal year ends."""
        client = YFinanceClient(debug=True)
        
        prices = client.fetch_historical_prices(
            'MSFT.US',
            '2020-01-01',
            '2024-12-31'
        )
        
        assert prices is not None
        
        # MSFT fiscal years (June 30)
        fiscal_year_ends = [
            '2024-06-30',
            '2023-06-30',
            '2022-06-30',
            '2021-06-30',
            '2020-06-30'
        ]
        
        matched = client.match_fiscal_year_end_prices(prices, fiscal_year_ends)
        
        assert len(matched) == 5, "Should match all 5 fiscal year ends"
        
        # Most should have prices
        prices_found = sum(1 for p in matched.values() if p is not None)
        assert prices_found >= 4, "Should find prices for most years"
    
    def test_match_no_data_within_window(self):
        """Test handling when no data within 7-day window."""
        client = YFinanceClient(debug=True)
        
        # Create sparse price data
        prices = {
            '2023-06-15': 350.0,
            '2023-07-10': 360.0,
        }
        
        # Fiscal year end with no data within 7 days
        fiscal_year_ends = ['2023-06-30']
        
        matched = client.match_fiscal_year_end_prices(prices, fiscal_year_ends)
        
        assert '2023-06-30' in matched
        assert matched['2023-06-30'] is None, "Should return None when no data in window"
    
    def test_match_uses_last_trading_day(self):
        """Test that matching uses last trading day before fiscal year end."""
        client = YFinanceClient(debug=True)
        
        # Create price data with specific dates
        prices = {
            '2023-06-26': 340.0,  # Monday
            '2023-06-27': 345.0,  # Tuesday
            '2023-06-28': 350.0,  # Wednesday
            '2023-06-29': 355.0,  # Thursday
            # June 30 is Friday (trading day)
            '2023-06-30': 360.0,  # Friday
        }
        
        fiscal_year_ends = ['2023-06-30']
        
        matched = client.match_fiscal_year_end_prices(prices, fiscal_year_ends)
        
        # Should use exact match (June 30)
        assert matched['2023-06-30'] == 360.0, "Should use exact match when available"
    
    def test_match_searches_backwards_not_forwards(self):
        """Test that matching searches backwards, not forwards."""
        client = YFinanceClient(debug=True)
        
        # Create price data with gap
        prices = {
            '2023-06-28': 350.0,  # 2 days before
            # June 29-30 missing (weekend)
            '2023-07-03': 360.0,  # 3 days after
        }
        
        fiscal_year_ends = ['2023-06-30']
        
        matched = client.match_fiscal_year_end_prices(prices, fiscal_year_ends)
        
        # Should use June 28 (backwards), not July 3 (forwards)
        assert matched['2023-06-30'] == 350.0, "Should search backwards, not forwards"
    
    def test_match_empty_price_data(self):
        """Test handling of empty price data."""
        client = YFinanceClient(debug=False)
        
        prices = {}
        fiscal_year_ends = ['2023-06-30']
        
        matched = client.match_fiscal_year_end_prices(prices, fiscal_year_ends)
        
        assert '2023-06-30' in matched
        assert matched['2023-06-30'] is None
    
    def test_match_invalid_date_format(self):
        """Test handling of invalid date format in fiscal year ends."""
        client = YFinanceClient(debug=False)
        
        prices = {'2023-06-30': 350.0}
        fiscal_year_ends = ['invalid-date']
        
        matched = client.match_fiscal_year_end_prices(prices, fiscal_year_ends)
        
        assert 'invalid-date' in matched
        assert matched['invalid-date'] is None, "Should return None for invalid date"


@pytest.mark.live
class TestEndToEndHistoricalPrices:
    """End-to-end tests combining fetch and match."""
    
    def test_full_workflow_msft(self):
        """Test complete workflow: fetch → match for MSFT."""
        client = YFinanceClient(debug=True)
        
        # Fetch historical prices
        prices = client.fetch_historical_prices(
            'MSFT.US',
            '2020-06-01',
            '2024-07-31'
        )
        
        assert prices is not None
        
        # Match to MSFT fiscal year ends (June 30)
        fiscal_year_ends = [
            '2024-06-30',
            '2023-06-30',
            '2022-06-30',
            '2021-06-30',
            '2020-06-30'
        ]
        
        matched = client.match_fiscal_year_end_prices(prices, fiscal_year_ends)
        
        # Verify all years matched
        assert len(matched) == 5
        
        # Verify prices are reasonable for MSFT
        for year, price in matched.items():
            if price is not None:
                assert 50 < price < 500, f"MSFT price for {year} should be reasonable: {price}"
    
    def test_full_workflow_lse_stock(self):
        """Test complete workflow for LSE stock with non-December fiscal year."""
        client = YFinanceClient(debug=True)
        
        # Fetch for VOD.LSE
        prices = client.fetch_historical_prices(
            'VOD.LSE',
            '2022-01-01',
            '2024-12-31'
        )
        
        assert prices is not None
        
        # Vodafone fiscal year ends March 31
        fiscal_year_ends = [
            '2024-03-31',
            '2023-03-31',
            '2022-03-31'
        ]
        
        matched = client.match_fiscal_year_end_prices(prices, fiscal_year_ends)
        
        assert len(matched) == 3
        
        # At least 2 should have prices
        prices_found = sum(1 for p in matched.values() if p is not None)
        assert prices_found >= 2, "Should find prices for most years"
