"""Unit tests for Financial History section with WCPS and Payout Ratio columns.

Tests verify that WCPS and Payout Ratio columns are correctly displayed in the
financial history table with proper formatting and alignment.
"""

from output.sections.financial_history import FinancialHistorySection


def test_financial_history_with_wcps_and_payout_ratio():
    """Test that WCPS and Payout Ratio columns appear in financial history table."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'is_dividend_amounts': True,
        'history': {
            '2023-12-31': {
                'revenue': 1000000.0,
                'net_income': 100000.0,
                'eps': 5.0,
                'dividend': 2.0,
                'total_equity': 500000.0,
                'shares_outstanding': 20000.0,
                'wcps': 12.50,
                'payout_ratio': '40.0%',
                'total_debt': 200000.0,
                'year_end_price': 75.0
            }
        },
        'historical_fx_rates': {}
    }
    
    section = FinancialHistorySection(financial_data)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'WCPS' in content
    assert 'Payout Ratio' in content
    assert '12.50' in content
    assert '40.0%' in content
    assert 'WCPS (Working Capital Per Share)' in content
    assert 'Payout Ratio**: (Dividend / EPS) × 100' in content


def test_financial_history_table_alignment():
    """Test that table alignment row matches the number of columns."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'is_dividend_amounts': True,
        'history': {
            '2023-12-31': {
                'revenue': 1000000.0,
                'net_income': 100000.0,
                'eps': 5.0,
                'dividend': 2.0,
                'total_equity': 500000.0,
                'shares_outstanding': 20000.0,
                'wcps': 10.0,
                'payout_ratio': '40.0%',
                'total_debt': 200000.0,
                'year_end_price': 75.0
            }
        },
        'historical_fx_rates': {}
    }
    
    section = FinancialHistorySection(financial_data)
    
    # Act
    lines = section.generate()
    
    # Find header and alignment rows
    header_line = None
    alignment_line = None
    for i, line in enumerate(lines):
        if line.startswith('| Year |'):
            header_line = line
            if i + 1 < len(lines):
                alignment_line = lines[i + 1]
            break
    
    # Assert
    assert header_line is not None
    assert alignment_line is not None
    
    # Count columns (number of | characters minus 1)
    header_cols = header_line.count('|') - 1
    alignment_cols = alignment_line.count('|') - 1
    
    assert header_cols == alignment_cols, f"Header has {header_cols} columns but alignment has {alignment_cols}"
    assert header_cols == 13, f"Expected 13 columns, got {header_cols}"


def test_financial_history_negative_wcps_warning():
    """Test that negative WCPS values have warning indicator."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'is_dividend_amounts': True,
        'history': {
            '2023-12-31': {
                'revenue': 1000000.0,
                'net_income': 100000.0,
                'eps': 5.0,
                'dividend': 2.0,
                'total_equity': 500000.0,
                'shares_outstanding': 20000.0,
                'wcps': -5.25,  # Negative WCPS
                'payout_ratio': '40.0%',
                'total_debt': 200000.0,
                'year_end_price': 75.0
            }
        },
        'historical_fx_rates': {}
    }
    
    section = FinancialHistorySection(financial_data)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert '⚠️ -5.25' in content or '⚠️  -5.25' in content


def test_financial_history_na_wcps():
    """Test that N/A WCPS values are handled gracefully."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'is_dividend_amounts': True,
        'history': {
            '2023-12-31': {
                'revenue': 1000000.0,
                'net_income': 100000.0,
                'eps': 5.0,
                'dividend': 2.0,
                'total_equity': 500000.0,
                'shares_outstanding': 20000.0,
                'wcps': 'N/A',
                'payout_ratio': 'N/A',
                'total_debt': 200000.0,
                'year_end_price': 75.0
            }
        },
        'historical_fx_rates': {}
    }
    
    section = FinancialHistorySection(financial_data)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'N/A' in content


def test_financial_history_payout_ratio_over_100():
    """Test that payout ratio over 100% is displayed without capping."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'is_dividend_amounts': True,
        'history': {
            '2023-12-31': {
                'revenue': 1000000.0,
                'net_income': 50000.0,
                'eps': 2.5,
                'dividend': 3.0,
                'total_equity': 500000.0,
                'shares_outstanding': 20000.0,
                'wcps': 10.0,
                'payout_ratio': '120.0%',  # Over 100%
                'total_debt': 200000.0,
                'year_end_price': 50.0
            }
        },
        'historical_fx_rates': {}
    }
    
    section = FinancialHistorySection(financial_data)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert '120.0%' in content
    assert 'Values > 100% indicate unsustainable dividends' in content


def test_financial_history_column_explanations():
    """Test that column explanations are present for new columns."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'is_dividend_amounts': True,
        'history': {
            '2023-12-31': {
                'revenue': 1000000.0,
                'net_income': 100000.0,
                'eps': 5.0,
                'dividend': 2.0,
                'total_equity': 500000.0,
                'shares_outstanding': 20000.0,
                'wcps': 10.0,
                'payout_ratio': '40.0%',
                'total_debt': 200000.0,
                'year_end_price': 75.0
            }
        },
        'historical_fx_rates': {}
    }
    
    section = FinancialHistorySection(financial_data)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'WCPS (Working Capital Per Share)' in content
    assert 'Measures the company\'s liquid net worth per share' in content
    assert 'Positive values indicate financial strength' in content
    assert 'Negative values indicate current liabilities exceed current assets' in content
    assert 'Payout Ratio**: (Dividend / EPS) × 100' in content
    assert 'Percentage of earnings paid as dividends' in content
