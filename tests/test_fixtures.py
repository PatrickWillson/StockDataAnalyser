"""
Tests for the fixtures module itself.

Verifies that all fixtures are properly structured and usable.
"""

import pytest
from tests.fixtures import (
    EODHDFixtures,
    YFinanceFixtures,
    FXFixtures,
    create_mock_http_response,
    create_financial_data_dict
)


class TestEODHDFixtures:
    """Test EODHD fixtures."""
    
    def test_aapl_fundamentals_structure(self):
        """Test AAPL fundamentals fixture has correct structure."""
        data = EODHDFixtures.get_aapl_fundamentals()
        
        # Verify top-level keys
        assert 'General' in data
        assert 'SharesStats' in data
        assert 'Highlights' in data
        assert 'Financials' in data
        assert 'SplitsDividends' in data
        assert 'outstandingShares' in data
        
        # Verify General section
        assert data['General']['Code'] == 'AAPL'
        assert data['General']['Exchange'] == 'NASDAQ'
        assert data['General']['CurrencyCode'] == 'USD'
        assert 'Officers' in data['General']
        
        # Verify Financials structure
        assert 'Balance_Sheet' in data['Financials']
        assert 'Income_Statement' in data['Financials']
        assert 'Cash_Flow' in data['Financials']
        
        # Verify yearly data exists
        assert 'yearly' in data['Financials']['Balance_Sheet']
        assert len(data['Financials']['Balance_Sheet']['yearly']) >= 3
    
    def test_lse_stock_fundamentals_structure(self):
        """Test LSE stock fixture has correct structure."""
        data = EODHDFixtures.get_lse_stock_fundamentals()
        
        # Verify LSE-specific fields
        assert data['General']['Exchange'] == 'LSE'
        assert data['General']['CurrencyCode'] == 'GBX'  # Pence
        assert data['Financials']['Balance_Sheet']['currency_symbol'] == 'GBP'  # Pounds
        
        # Verify price is in pence (should be > 100)
        assert data['Highlights']['SharePrice'] > 100
    
    def test_dividend_api_response_structure(self):
        """Test dividend API response fixture."""
        data = EODHDFixtures.get_dividend_api_response()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify first dividend record structure
        dividend = data[0]
        assert 'date' in dividend
        assert 'value' in dividend
        assert 'currency' in dividend
        assert dividend['value'] > 0


class TestYFinanceFixtures:
    """Test yfinance fixtures."""
    
    def test_ticker_fast_info(self):
        """Test fast_info fixture."""
        fast_info = YFinanceFixtures.get_ticker_fast_info(price=150.0)
        
        assert hasattr(fast_info, 'last_price')
        assert fast_info.last_price == 150.0
    
    def test_ticker_mock(self):
        """Test complete ticker mock."""
        ticker = YFinanceFixtures.get_ticker_mock(price=200.0)
        
        assert hasattr(ticker, 'fast_info')
        assert ticker.fast_info.last_price == 200.0
    
    def test_ticker_mock_custom_price(self):
        """Test ticker mock with custom price."""
        ticker = YFinanceFixtures.get_ticker_mock(price=99.99)
        
        assert ticker.fast_info.last_price == 99.99


class TestFXFixtures:
    """Test FX fixtures."""
    
    def test_fx_rate_response_structure(self):
        """Test FX rate response fixture."""
        response = FXFixtures.get_fx_rate_response('EUR', 'USD', 1.10)
        
        assert 'amount' in response
        assert 'base' in response
        assert 'date' in response
        assert 'rates' in response
        
        assert response['base'] == 'EUR'
        assert response['rates']['USD'] == 1.10
    
    def test_common_rates(self):
        """Test common rates fixture."""
        rates = FXFixtures.get_common_rates()
        
        assert isinstance(rates, dict)
        assert len(rates) > 0
        
        # Verify some common pairs exist
        assert ('EUR', 'USD') in rates
        assert ('GBP', 'USD') in rates
        assert ('USD', 'EUR') in rates
        
        # Verify rates are positive
        for rate in rates.values():
            assert rate > 0


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_create_mock_http_response_success(self):
        """Test creating successful HTTP response."""
        response = create_mock_http_response(200, {'key': 'value'})
        
        assert response.status_code == 200
        assert response.json() == {'key': 'value'}
    
    def test_create_mock_http_response_error(self):
        """Test creating error HTTP response."""
        response = create_mock_http_response(404)
        
        assert response.status_code == 404
        
        # Should raise error when calling json()
        with pytest.raises(ValueError):
            response.json()
    
    def test_create_financial_data_dict_defaults(self):
        """Test creating financial data dict with defaults."""
        data = create_financial_data_dict()
        
        # Verify structure
        assert 'ticker' in data
        assert 'exchange' in data
        assert 'currency' in data
        assert 'price' in data
        assert 'history' in data
        
        # Verify defaults
        assert data['ticker'] == 'TEST.US'
        assert data['exchange'] == 'NASDAQ'
        assert data['currency'] == 'USD'
        assert data['price'] == 100.0
        
        # Verify history has 10 years by default
        assert len(data['history']) == 10
    
    def test_create_financial_data_dict_custom(self):
        """Test creating financial data dict with custom values."""
        data = create_financial_data_dict(
            ticker='MSFT.US',
            exchange='NASDAQ',
            currency='USD',
            price=350.0,
            years_of_history=5
        )
        
        assert data['ticker'] == 'MSFT.US'
        assert data['price'] == 350.0
        assert len(data['history']) == 5
    
    def test_create_financial_data_dict_history_structure(self):
        """Test that generated history has correct structure."""
        data = create_financial_data_dict(years_of_history=3)
        
        # Verify each year has required fields
        for year_key, year_data in data['history'].items():
            assert 'revenue' in year_data
            assert 'net_income' in year_data
            assert 'eps' in year_data
            assert 'dividend' in year_data
            assert 'total_equity' in year_data
            assert 'shares_outstanding' in year_data
            assert 'current_assets' in year_data
            assert 'current_liabilities' in year_data
            
            # Verify all values are positive
            assert year_data['revenue'] > 0
            assert year_data['net_income'] > 0
            assert year_data['eps'] > 0


class TestFixturesIntegration:
    """Test using fixtures together."""
    
    def test_eodhd_fixture_with_mock_response(self):
        """Test using EODHD fixture with mock HTTP response."""
        mock_data = EODHDFixtures.get_aapl_fundamentals()
        response = create_mock_http_response(200, mock_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['General']['Code'] == 'AAPL'
    
    def test_multiple_fixtures_together(self):
        """Test using multiple fixtures in combination."""
        # EODHD data
        eodhd_data = EODHDFixtures.get_aapl_fundamentals()
        
        # yfinance price
        yf_ticker = YFinanceFixtures.get_ticker_mock(price=187.45)
        
        # FX rate
        fx_response = FXFixtures.get_fx_rate_response('EUR', 'USD', 1.10)
        
        # Verify all work together
        assert eodhd_data['General']['Code'] == 'AAPL'
        assert yf_ticker.fast_info.last_price == 187.45
        assert fx_response['rates']['USD'] == 1.10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
