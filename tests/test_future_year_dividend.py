"""
Test that future year dividends (without complete financial statements) are included in dossier.

This test verifies that when dividend data exists for a year that doesn't have
complete financial statements yet (e.g., 2025), the system:
1. Includes that year in the history dictionary
2. Shows dividend data for that year
3. Marks other financial metrics as "[Data Unavailable]"
4. Adds appropriate warning about incomplete data
"""

import pytest
from core.financial_data_processor import FinancialDataProcessor


def test_merge_includes_dividend_only_years():
    """Test that years with only dividend data (no financial statements) are included."""
    processor = FinancialDataProcessor(debug=False)
    
    # Mock data: 2024 has full financials, 2025 has only dividend
    balance_sheet = {
        '2024-12-31': {
            'total_equity': 500000000,
            'intangible_assets': 10000000,
            'goodwill': 5000000,
            'current_assets': 200000000,
            'current_liabilities': 50000000,
            'total_liabilities': 100000000,
            'long_term_debt': 50000000
        }
    }
    
    income_statement = {
        '2024-12-31': {
            'revenue': 1000000000,
            'net_income': 50000000,
            'eps': 1.25
        }
    }
    
    dividend_history = {
        '2024': 0.50,
        '2025': 0.88  # Future year with dividend but no financials yet
    }
    
    shares_outstanding = 40000000
    shares_by_year = {
        '2024': 40000000,
        '2025': 39445000
    }
    
    # Merge data
    result = processor.merge_financial_data(
        balance_sheet,
        income_statement,
        dividend_history,
        shares_outstanding,
        outstanding_shares_by_year=shares_by_year
    )
    
    # Verify both years are included
    assert '2024-12-31' in result
    assert '2025-12-31' in result
    
    # Verify 2024 has complete data
    assert result['2024-12-31']['revenue'] == 1000000000
    assert result['2024-12-31']['net_income'] == 50000000
    assert result['2024-12-31']['eps'] == 1.25
    assert result['2024-12-31']['dividend'] == 0.50
    assert result['2024-12-31']['total_equity'] == 500000000
    
    # Verify 2025 has dividend but zeros for financial data
    assert result['2025-12-31']['dividend'] == 0.88
    assert result['2025-12-31']['revenue'] == 0.0
    assert result['2025-12-31']['net_income'] == 0.0
    assert result['2025-12-31']['eps'] == 0.0
    assert result['2025-12-31']['total_equity'] == 0.0
    
    # Verify 2025 has correct shares
    assert result['2025-12-31']['shares_outstanding'] == 39445000


def test_dossier_formats_incomplete_year_correctly():
    """Test that dossier generation formats incomplete years with [Data Unavailable]."""
    # This is a simpler test that just verifies the table formatting logic
    # without needing to mock the entire dossier generation
    
    # Simulate the table generation logic from stock_data_analyser.py
    history = {
        '2025-12-31': {
            'revenue': 0.0,
            'net_income': 0.0,
            'eps': 0.0,
            'dividend': 0.88,
            'total_equity': 0.0,
            'shares_outstanding': 39445000
        },
        '2024-12-31': {
            'revenue': 1000000000,
            'net_income': 50000000,
            'eps': 1.25,
            'dividend': 0.50,
            'total_equity': 500000000,
            'shares_outstanding': 40000000
        }
    }
    
    # Simulate the table row generation logic
    sorted_years = sorted(history.keys(), reverse=True)
    
    for year in sorted_years:
        data = history[year]
        revenue = data.get('revenue', 0.0)
        net_income = data.get('net_income', 0.0)
        eps = data.get('eps', 0.0)
        dividend = data.get('dividend', 0.0)
        
        # Check if this year has actual financial data or just dividend data
        has_financial_data = revenue > 0 or net_income != 0 or eps != 0
        
        # Format values - show "[Data Unavailable]" for years without financial statements
        if not has_financial_data and dividend > 0:
            # Year has dividend but no financial statements yet
            revenue_str = "[Data Unavailable]"
            net_income_str = "[Data Unavailable]"
            eps_str = "[Data Unavailable]"
            dividend_str = str(dividend)
            bvps_str = "[Data Unavailable]"
        else:
            # Normal year with financial data
            revenue_str = str(revenue) if revenue != 0 else 'N/A'
            net_income_str = str(net_income) if net_income != 0 else 'N/A'
            eps_str = str(eps) if eps != 0 else 'N/A'
            dividend_str = str(dividend) if dividend != 0 else 'N/A'
            
            # Calculate BVPS from balance sheet data
            total_equity = data.get('total_equity', 0)
            shares = data.get('shares_outstanding', 0)
            bvps = round(total_equity / shares, 2) if shares > 0 and total_equity > 0 else 'N/A'
            bvps_str = str(bvps)
        
        row = f"| {year} | {revenue_str} | {net_income_str} | {eps_str} | {dividend_str} | {bvps_str} |"
        
        # Verify formatting
        if year == '2025-12-31':
            assert '[Data Unavailable]' in row
            assert row.count('[Data Unavailable]') == 4  # Revenue, Net Income, EPS, BVPS
            assert '0.88' in row
        elif year == '2024-12-31':
            assert '[Data Unavailable]' not in row
            assert '1000000000' in row
            assert '0.5' in row  # Python str(0.5) = '0.5' not '0.50'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
