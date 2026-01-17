"""
Property-based tests for Dossier Generator functionality.
"""

import pytest
from hypothesis import given, strategies as st
from stock_data_analyser import generate_dossier_content


# Feature: stock-data-analyser, Property 11: Markdown table formatting
@given(
    ticker=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    years=st.lists(
        st.integers(min_value=2000, max_value=2024),
        min_size=1,
        max_size=10,
        unique=True
    ),
    revenue=st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False),
    net_income=st.floats(min_value=-1e12, max_value=1e12, allow_nan=False, allow_infinity=False),
    eps=st.floats(min_value=-100, max_value=1000, allow_nan=False, allow_infinity=False),
    dividend=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
    total_equity=st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False),
    shares_outstanding=st.floats(min_value=1e6, max_value=1e12, allow_nan=False, allow_infinity=False)
)
def test_markdown_table_formatting(ticker, years, revenue, net_income, eps, dividend, total_equity, shares_outstanding):
    """
    Property 11: Markdown table formatting
    Validates: Requirements 9.11
    
    For any financial history data, the output should contain valid Markdown table syntax
    with pipe separators, proper table header row, and proper table separator row.
    """
    # Build financial data with random history
    history = {}
    for year in years:
        history[str(year)] = {
            'revenue': revenue,
            'net_income': net_income,
            'eps': eps,
            'dividend': dividend,
            'total_equity': total_equity,
            'shares_outstanding': shares_outstanding
        }
    
    financial_data = {
        'ticker': ticker,
        'price': 100.0,
        'currency': 'USD',
        'ceo_name': 'Test CEO',
        'history': history,
        'warnings': []
    }
    
    metrics = {
        'verdict': 'TEST',
        'graham_number': 50.0,
        'epv': 60.0,
        'net_net_value': 40.0,
        'margin_of_safety': 10.0,
        'defensive_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS'
        },
        'enterprising_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS'
        },
        'warnings': []
    }
    
    anomalies = []
    
    # Generate dossier content
    output = generate_dossier_content(ticker, financial_data, metrics, anomalies)
    
    # Verify output contains pipe separators
    assert '|' in output, "Output should contain pipe separators for Markdown tables"
    
    # Verify output has proper table header row
    assert '| Year | Revenue | Net Income | EPS | Div | BVPS |' in output, \
        "Output should have proper Markdown table header row"
    
    # Verify output has proper table separator row
    assert '|------|---------|------------|-----|-----|------|' in output, \
        "Output should have proper Markdown table separator row"
    
    # Verify each year appears in a table row
    for year in years:
        # Check that the year appears in the output (it should be in a table row)
        assert str(year) in output, f"Year {year} should appear in the output"
