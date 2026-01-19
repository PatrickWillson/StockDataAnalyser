#!/usr/bin/env python3
"""
Tests for year-specific shares outstanding fix.

This test ensures that EPS calculations use year-specific shares outstanding
rather than a single share count for all years.
"""

import pytest
from core.financial_data_processor import FinancialDataProcessor


def test_extract_shares_by_year():
    """Test extraction of year-specific shares from outstandingShares.annual."""
    # Mock API data with year-specific shares
    data = {
        'outstandingShares': {
            'annual': {
                '0': {'date': 2024, 'shares': 39531000},
                '1': {'date': 2023, 'shares': 39484000},
                '2': {'date': 2022, 'shares': 39437000}
            }
        }
    }
    
    processor = FinancialDataProcessor(debug=False)
    shares_by_year = processor.extract_shares_by_year(data)
    
    assert '2024' in shares_by_year
    assert '2023' in shares_by_year
    assert '2022' in shares_by_year
    
    assert shares_by_year['2024'] == 39531000
    assert shares_by_year['2023'] == 39484000
    assert shares_by_year['2022'] == 39437000


def test_extract_shares_by_year_empty():
    """Test handling of missing outstandingShares data."""
    data = {}
    
    processor = FinancialDataProcessor(debug=False)
    shares_by_year = processor.extract_shares_by_year(data)
    
    assert shares_by_year == {}


def test_merge_financial_data_uses_year_specific_shares():
    """Test that merge_financial_data uses year-specific shares for EPS calculation."""
    balance_sheet = {}
    income_statement = {
        '2024-12-31': {'net_income': 67612000, 'revenue': 372263000, 'eps': 0},
        '2023-12-31': {'net_income': 57638000, 'revenue': 370960000, 'eps': 0}
    }
    dividend_history = {}
    shares_outstanding = 38766696  # Default (old value)
    shares_by_year = {
        '2024': 39531000,  # Year-specific (correct value)
        '2023': 39484000
    }
    
    processor = FinancialDataProcessor(debug=False)
    result = processor.merge_financial_data(
        balance_sheet, 
        income_statement, 
        dividend_history, 
        shares_outstanding,
        outstanding_shares_by_year=shares_by_year
    )
    
    # Check that year-specific shares were used
    assert '2024-12-31' in result
    assert result['2024-12-31']['shares_outstanding'] == 39531000  # Not 38766696
    
    # Check that EPS was calculated with year-specific shares
    expected_eps_2024 = 67612000 / 39531000  # 1.7104
    assert result['2024-12-31']['eps'] == pytest.approx(expected_eps_2024, rel=0.0001)
    
    # Check 2023 as well
    assert result['2023-12-31']['shares_outstanding'] == 39484000
    expected_eps_2023 = 57638000 / 39484000  # 1.4596
    assert result['2023-12-31']['eps'] == pytest.approx(expected_eps_2023, rel=0.0001)


def test_merge_financial_data_falls_back_to_default_shares():
    """Test that merge_financial_data falls back to default shares when year-specific not available."""
    balance_sheet = {}
    income_statement = {
        '2024-12-31': {'net_income': 67612000, 'revenue': 372263000, 'eps': 0}
    }
    dividend_history = {}
    shares_outstanding = 38766696  # Default
    shares_by_year = {}  # No year-specific data
    
    processor = FinancialDataProcessor(debug=False)
    result = processor.merge_financial_data(
        balance_sheet, 
        income_statement, 
        dividend_history, 
        shares_outstanding,
        outstanding_shares_by_year=shares_by_year
    )
    
    # Should fall back to default shares
    assert result['2024-12-31']['shares_outstanding'] == 38766696
    
    # EPS should be calculated with default shares
    expected_eps = 67612000 / 38766696  # 1.7443
    assert result['2024-12-31']['eps'] == pytest.approx(expected_eps, rel=0.0001)


def test_aep_eps_correction():
    """
    Verify that AEP.LSE EPS is corrected with year-specific shares.
    
    Before fix: $1.744 (using 38,766,696 shares)
    After fix: $1.710 (using 39,531,000 shares)
    Peer review: $1.7088
    """
    # Read the AEP dossier
    import os
    dossier_path = 'data/AEP_LSE_DOSSIER.md'
    
    if not os.path.exists(dossier_path):
        pytest.skip("AEP dossier not found - run stock_data_analyser.py AEP.LSE first")
    
    with open(dossier_path, 'r') as f:
        content = f.read()
    
    # Check that EPS is now ~1.71 (not 1.744)
    # The exact value is 1.710353899471301
    assert '1.710' in content or '1.71' in content, \
        "EPS should be ~$1.71 after using year-specific shares"
    
    # Should NOT show the old incorrect value
    assert '1.744' not in content, \
        "Should not show old incorrect EPS of $1.744"
    
    # Check P/E ratio is updated (should be ~11.96, not 11.73)
    assert '11.96' in content or '11.9' in content or '12.0' in content, \
        "P/E ratio should be ~11.96 after EPS correction"
    
    print("✓ EPS correction verified")
    print("  - 2024 EPS: ~$1.71 (using 39,531,000 shares)")
    print("  - P/E Ratio: ~11.96")
    print("  - Within 0.09% of peer review's $1.7088")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
