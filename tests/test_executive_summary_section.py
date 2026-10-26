"""Unit tests for Executive Summary section with three-year average P/E.

Tests verify that the three-year average P/E is correctly displayed in the
executive summary section when available.
"""

from output.sections.executive_summary import ExecutiveSummarySection


def test_executive_summary_with_three_year_pe():
    """Test that three-year average P/E appears in executive summary."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'price': 100.0,
        'pe_ratio': 15.5,
        'price_to_book': 2.0,
        'exchange': 'US',
        'history': {}
    }
    
    metrics = {
        'verdict': 'FAIRLY VALUED',
        'graham_number': 120.0,
        'epv': 110.0,
        'net_net_value': 'N/A',
        'margin_of_safety': 16.7,
        'three_year_avg_pe': {
            'three_year_avg_eps': 6.45,
            'pe_on_avg': 15.50,
            'years_used': ['2023-12-31', '2022-12-31', '2021-12-31']
        }
    }
    
    section = ExecutiveSummarySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'P/E Ratio (Current Year): 15.50' in content
    assert 'P/E Ratio (3-Year Avg): 15.50' in content
    assert 'based on avg EPS of 6.45 from 2021-2023' in content


def test_executive_summary_without_three_year_pe():
    """Test that executive summary works when three-year P/E is N/A."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'price': 100.0,
        'pe_ratio': 15.5,
        'price_to_book': 2.0,
        'exchange': 'US',
        'history': {}
    }
    
    metrics = {
        'verdict': 'FAIRLY VALUED',
        'graham_number': 120.0,
        'epv': 110.0,
        'net_net_value': 'N/A',
        'margin_of_safety': 16.7,
        'three_year_avg_pe': {
            'three_year_avg_eps': 'N/A',
            'pe_on_avg': 'N/A',
            'years_used': []
        }
    }
    
    section = ExecutiveSummarySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'P/E Ratio (Current Year): 15.50' in content
    assert 'P/E Ratio (3-Year Avg)' not in content  # Should not appear when N/A


def test_executive_summary_three_year_pe_formatting():
    """Test that three-year P/E is formatted correctly with 2 decimal places."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'price': 100.0,
        'pe_ratio': 12.34,
        'price_to_book': 1.5,
        'exchange': 'US',
        'history': {}
    }
    
    metrics = {
        'verdict': 'UNDERVALUED',
        'graham_number': 150.0,
        'epv': 140.0,
        'net_net_value': 'N/A',
        'margin_of_safety': 33.3,
        'three_year_avg_pe': {
            'three_year_avg_eps': 8.123456,
            'pe_on_avg': 12.3456789,
            'years_used': ['2023-12-31', '2022-12-31', '2021-12-31']
        }
    }
    
    section = ExecutiveSummarySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'P/E Ratio (3-Year Avg): 12.35' in content  # Rounded to 2 decimals
    assert 'based on avg EPS of 8.12' in content  # Rounded to 2 decimals
