"""Unit tests for Key Metrics section with NCA and Quick Ratio.

Tests verify that NCA details and Quick Ratio are correctly displayed in the
key metrics section when available.
"""

import pytest
from output.sections.key_metrics import KeyMetricsSection


def test_key_metrics_with_nca_and_quick_ratio():
    """Test that NCA details and Quick Ratio appear in key metrics."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'current_ratio': 2.15,
        'history': {}
    }
    
    metrics = {
        'current_ratio': {'ratio': 2.15, 'fiscal_year_end': '2023-12-31'},
        'quick_ratio': 1.87,
        'nca_details': {
            'current_assets': 1234567000.0,
            'total_liabilities': 987654000.0,
            'nca': 246913000.0,
            'long_term_debt': 699563000.0,
            'debt_coverage_ratio': 2.83,
            'debt_coverage_pct': '283.00%',
            'warnings': []
        }
    }
    
    section = KeyMetricsSection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'Liquidity Analysis' in content
    assert 'Current Ratio**: 2.15 (Current Assets / Current Liabilities, fiscal year ending 2023-12-31)' in content
    assert 'Quick Ratio**: 1.87' in content
    assert 'Net Current Assets (NCA) Analysis' in content
    assert 'Current Assets**: 1,234,567,000.00 USD' in content
    assert 'Total Liabilities**: 987,654,000.00 USD' in content
    assert 'Net Current Assets**: 246,913,000.00 USD' in content
    assert 'Long-term Debt**: 699,563,000.00 USD' in content
    assert 'Debt Coverage Ratio**: 2.83 (283.00%)' in content
    assert "Graham's defensive test requires long-term debt < NCA" in content


def test_key_metrics_with_na_quick_ratio():
    """Test that key metrics handles N/A Quick Ratio gracefully."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'current_ratio': 2.15,
        'history': {}
    }
    
    metrics = {
        'quick_ratio': 'N/A',
        'nca_details': {
            'current_assets': 1000000.0,
            'total_liabilities': 800000.0,
            'nca': 200000.0,
            'long_term_debt': 150000.0,
            'debt_coverage_ratio': 0.75,
            'debt_coverage_pct': '75.00%',
            'warnings': []
        }
    }
    
    section = KeyMetricsSection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'Quick Ratio**: N/A' in content
    assert 'Net Current Assets (NCA) Analysis' in content


def test_key_metrics_with_na_nca():
    """Test that key metrics handles N/A NCA gracefully."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'current_ratio': 1.5,
        'history': {}
    }
    
    metrics = {
        'quick_ratio': 1.2,
        'nca_details': {
            'current_assets': 'N/A',
            'total_liabilities': 'N/A',
            'nca': 'N/A',
            'long_term_debt': 'N/A',
            'debt_coverage_ratio': 'N/A',
            'debt_coverage_pct': 'N/A',
            'warnings': ['Missing balance sheet data']
        }
    }
    
    section = KeyMetricsSection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'Quick Ratio**: 1.20' in content
    assert 'Debt Coverage Ratio**: N/A' in content


def test_key_metrics_without_metrics_dict():
    """Test that key metrics works without metrics dict (backward compatibility)."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'current_ratio': 2.0,
        'history': {}
    }
    
    section = KeyMetricsSection(financial_data)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'SECTION 2: KEY METRICS' in content
    assert 'Liquidity Analysis' in content
    # Current ratio comes from core metrics, never from financial_data
    assert 'Current Ratio' not in content
    # Should not crash when metrics dict is missing


def test_key_metrics_formatting():
    """Test that NCA values are formatted correctly with commas and currency."""
    # Arrange
    financial_data = {
        'currency': 'GBP',
        'current_ratio': 1.8,
        'history': {}
    }
    
    metrics = {
        'quick_ratio': 1.5,
        'nca_details': {
            'current_assets': 5432100.50,
            'total_liabilities': 3210987.25,
            'nca': 2221113.25,
            'long_term_debt': 1500000.00,
            'debt_coverage_ratio': 0.675,
            'debt_coverage_pct': '67.50%',
            'warnings': []
        }
    }
    
    section = KeyMetricsSection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert '5,432,100.50 GBP' in content
    assert '3,210,987.25 GBP' in content
    assert '2,221,113.25 GBP' in content
    assert '1,500,000.00 GBP' in content
    assert 'Debt Coverage Ratio**: 0.68' in content  # Rounded to 2 decimals


def test_current_ratio_unavailable_shows_na_with_reason():
    section = KeyMetricsSection({'currency': 'USD', 'history': {}},
                                {'current_ratio': {'ratio': 'N/A', 'fiscal_year_end': '2023-12-31'}})

    content = '\n'.join(section.generate())

    assert '- **Current Ratio**: N/A (current liabilities not reported)' in content
