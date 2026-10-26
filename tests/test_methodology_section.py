"""Unit tests for Methodology section with new metrics explanations.

Tests verify that all new metrics have proper methodology explanations
including formulas, Graham references, and context.
"""

from output.sections.methodology import MethodologySection


def test_methodology_with_all_new_metrics():
    """Test that all new metrics have methodology explanations."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'history': {
            '2023-12-31': {
                'wcps': 10.0,
                'payout_ratio': '40.0%'
            }
        }
    }
    
    metrics = {
        'three_year_avg_pe': {
            'three_year_avg_eps': 6.45,
            'pe_on_avg': 15.50,
            'years_used': ['2023-12-31', '2022-12-31', '2021-12-31']
        },
        'quick_ratio': 1.87,
        'nca_details': {
            'current_assets': 1000000.0,
            'total_liabilities': 800000.0,
            'nca': 200000.0,
            'long_term_debt': 150000.0,
            'debt_coverage_ratio': 0.75,
            'debt_coverage_pct': '75.00%'
        },
        'combined_pe_pb_test': {
            'pe_ratio': 12.5,
            'pb_ratio': 1.2,
            'product': 15.0,
            'result': 'PASS'
        },
        'margin_of_safety': 25.0
    }
    
    section = MethodologySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - Three-Year Average P/E
    assert 'P/E Ratio (3-Year Average)' in content
    assert "Graham's Defensive Criterion #6" in content
    assert 'including loss years (negative EPS)' in content
    assert 'P/E (3-Year Avg) = Current Price / ((EPS_Y1 + EPS_Y2 + EPS_Y3) / 3)' in content
    
    # Assert - Quick Ratio
    assert 'Quick Ratio (Acid Test)' in content
    assert 'Quick Ratio = (Current Assets - Inventory) / Current Liabilities' in content
    assert 'Services and Technology companies' in content
    
    # Assert - NCA and Debt Coverage
    assert 'Net Current Assets (NCA) and Debt Coverage' in content
    assert 'NCA = Current Assets - Total Liabilities' in content
    assert 'Debt Coverage Ratio** = Long-term Debt / NCA' in content
    assert 'ratio < 1.0' in content
    
    # Assert - Combined P/E × P/B Test
    assert 'Combined P/E × P/B Test' in content
    assert 'product of P/E and P/B ratios should not exceed 22.5' in content
    assert 'Combined Test = P/E Ratio × P/B Ratio ≤ 22.5' in content
    
    # Assert - WCPS and Payout Ratio
    assert 'Historical Trend Metrics' in content
    assert 'Working Capital Per Share (WCPS)' in content
    assert 'Payout Ratio**: (Dividend / EPS) × 100' in content


def test_methodology_three_year_pe_reference():
    """Test that three-year P/E includes Graham's Criterion #6 reference."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'history': {}
    }
    
    metrics = {
        'three_year_avg_pe': {
            'three_year_avg_eps': 6.45,
            'pe_on_avg': 15.50,
            'years_used': ['2023-12-31', '2022-12-31', '2021-12-31']
        }
    }
    
    section = MethodologySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert "Graham's Defensive Criterion #6" in content
    assert "Price should not exceed 15 times average earnings of the past three years" in content


def test_methodology_combined_test_examples():
    """Test that combined test includes flexibility examples."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'history': {}
    }
    
    metrics = {
        'combined_pe_pb_test': {
            'pe_ratio': 12.5,
            'pb_ratio': 1.2,
            'product': 15.0,
            'result': 'PASS'
        }
    }
    
    section = MethodologySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'P/E of 15 can have P/B up to 1.5 (15 × 1.5 = 22.5)' in content
    assert 'P/E of 10 can have P/B up to 2.25 (10 × 2.25 = 22.5)' in content
    assert 'P/B of 0.5 can have P/E up to 45 (45 × 0.5 = 22.5)' in content


def test_methodology_nca_sector_note():
    """Test that NCA explanation includes sector-specific note."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'history': {}
    }
    
    metrics = {
        'nca_details': {
            'current_assets': 1000000.0,
            'total_liabilities': 800000.0,
            'nca': 200000.0,
            'long_term_debt': 150000.0,
            'debt_coverage_ratio': 0.75,
            'debt_coverage_pct': '75.00%'
        }
    }
    
    section = MethodologySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'Financial and Utility companies' in content
    assert 'NCA analysis may not be applicable' in content


def test_methodology_payout_ratio_explanation():
    """Test that payout ratio explanation includes sustainability context."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'history': {
            '2023-12-31': {
                'payout_ratio': '40.0%'
            }
        }
    }
    
    metrics = {}
    
    section = MethodologySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'Payout Ratio**: (Dividend / EPS) × 100' in content
    assert 'Values > 100% indicate unsustainable dividends' in content
    assert 'Values < 50% indicate conservative dividend policy' in content
    assert "'N/A' shown for years with zero or negative earnings" in content


def test_methodology_without_new_metrics():
    """Test that methodology section works without new metrics (backward compatibility)."""
    # Arrange
    financial_data = {
        'currency': 'USD',
        'history': {}
    }
    
    metrics = {
        'margin_of_safety': 25.0
    }
    
    section = MethodologySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'METHODOLOGY NOTES' in content
    assert 'Margin of Safety' in content
    # Should not crash when new metrics are missing
