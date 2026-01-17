"""
Live FX Client Test (Optional - requires internet connection)

This test makes real API calls to frankfurter.app to verify the integration works.
Run manually with: pytest tests/test_fx_client_live.py -v
"""

import pytest
from core.fx_client import FXClient


@pytest.mark.skip(reason="Live API test - run manually when needed")
def test_live_fx_rate_eur_to_usd():
    """Test fetching live EUR to USD rate."""
    client = FXClient()
    rate = client.get_rate('EUR', 'USD')
    
    # Rate should be a positive number (typically between 1.0 and 1.3)
    assert rate is not None
    assert rate > 0
    assert 0.8 < rate < 1.5  # Reasonable range for EUR/USD
    print(f"Live EUR/USD rate: {rate}")


@pytest.mark.skip(reason="Live API test - run manually when needed")
def test_live_fx_rate_gbp_to_usd():
    """Test fetching live GBP to USD rate."""
    client = FXClient()
    rate = client.get_rate('GBP', 'USD')
    
    # Rate should be a positive number (typically between 1.2 and 1.4)
    assert rate is not None
    assert rate > 0
    assert 1.0 < rate < 1.6  # Reasonable range for GBP/USD
    print(f"Live GBP/USD rate: {rate}")


@pytest.mark.skip(reason="Live API test - run manually when needed")
def test_live_fx_caching():
    """Test that caching works with live API."""
    client = FXClient()
    
    # First call
    rate1 = client.get_rate('EUR', 'USD')
    
    # Second call should use cache (verify by checking it's the same)
    rate2 = client.get_rate('EUR', 'USD')
    
    assert rate1 == rate2
    print(f"Cached rate matches: {rate1}")


if __name__ == '__main__':
    # Run with: python tests/test_fx_client_live.py
    pytest.main([__file__, '-v', '-s', '--tb=short'])
