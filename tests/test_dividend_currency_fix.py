#!/usr/bin/env python3
"""
Simple integration test to verify dividend currency conversion fix.

This test verifies that the fix for dividend currency conversion is working
by checking the actual AEP.LSE dossier output.
"""

import pytest
import os


def test_aep_dividend_currency_conversion():
    """
    Verify that AEP.LSE dividend is correctly converted from GBP to USD.
    
    Before fix: $0.12 USD (treating £0.11842 as $0.11842)
    After fix: $0.16 USD (£0.11842 × 1.3414)
    """
    # Read the AEP dossier
    dossier_path = 'data/AEP_LSE_DOSSIER.md'
    
    if not os.path.exists(dossier_path):
        pytest.skip("AEP dossier not found - run stock_data_analyser.py AEP.LSE first")
    
    with open(dossier_path, 'r') as f:
        content = f.read()
    
    # Check that dividend is correctly converted
    # Should show 0.16 USD (or 0.15-0.17 range due to rounding)
    assert '0.16 USD' in content or '0.15 USD' in content or '0.17 USD' in content, \
        "Dividend should be ~$0.16 USD after GBP→USD conversion"
    
    # Should NOT show the old incorrect value
    assert 'Trailing Dividend: 0.12 USD' not in content, \
        "Should not show old incorrect value of $0.12 USD"
    
    # Check yield is updated (should be ~0.78%, not 0.58%)
    assert '0.78%' in content or '0.77%' in content or '0.79%' in content, \
        "Yield should be ~0.78% after conversion"
    
    # Check that currency conversion is documented
    assert 'Dividends converted GBP → USD' in content or 'Dividends converted GBP' in content, \
        "Currency conversion should be documented in warnings"
    
    print("✓ Dividend currency conversion is working correctly")
    print("  - 2024 Dividend: ~$0.16 USD (converted from £0.11842 GBP)")
    print("  - Yield: ~0.78%")
    print("  - Conversion documented in warnings")


def test_dividend_conversion_calculation():
    """
    Verify the math: £0.11842 GBP × 1.3414 = $0.1588 USD ≈ $0.16 USD
    """
    gbp_value = 0.11842
    fx_rate = 1.3414
    expected_usd = gbp_value * fx_rate
    
    assert expected_usd == pytest.approx(0.1588, rel=0.01)
    assert round(expected_usd, 2) == 0.16
    
    print(f"✓ Conversion math verified: £{gbp_value} × {fx_rate} = ${expected_usd:.4f} ≈ $0.16")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
