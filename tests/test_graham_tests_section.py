"""Unit tests for Graham Tests section with combined P/E × P/B test.

Tests verify that the combined test and updated earnings stability text
are correctly displayed in the Graham tests sections.
"""

import pytest
from output.sections.graham_tests import GrahamTestsSection


def test_defensive_tests_with_combined_test():
    """Test that combined P/E × P/B test appears in defensive tests."""
    # Arrange
    metrics = {
        'defensive_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_assets': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'PASS',
            'pe_ratio': 'PASS',
            'pb_ratio': 'PASS'
        },
        'combined_pe_pb_test': {
            'pe_ratio': 12.5,
            'pb_ratio': 1.2,
            'product': 15.0,
            'result': 'PASS'
        },
        'enterprising_tests': {}
    }
    
    section = GrahamTestsSection(metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert '8. **Combined P/E × P/B Test**: PASS' in content
    assert 'P/E Ratio: 12.50' in content
    assert 'P/B Ratio: 1.20' in content
    assert 'Product: 15.00 (must be ≤ 22.5)' in content
    assert 'P/E × P/B should not exceed 22.5' in content


def test_defensive_tests_earnings_stability_text():
    """Test that earnings stability criterion text is updated for defensive tests."""
    # Arrange
    metrics = {
        'defensive_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_assets': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'PASS',
            'pe_ratio': 'PASS',
            'pb_ratio': 'PASS'
        },
        'enterprising_tests': {}
    }
    
    section = GrahamTestsSection(metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'Positive earnings in each of the past 10 years' in content


def test_enterprising_tests_earnings_stability_text():
    """Test that earnings stability criterion text is updated for enterprising tests."""
    # Arrange
    metrics = {
        'defensive_tests': {},
        'enterprising_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_assets': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'N/A - Not Required',
            'price_test': 'PASS'
        }
    }
    
    section = GrahamTestsSection(metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'Profitability in most recent year and 5 of past 7 years' in content


def test_combined_test_with_na_values():
    """Test that combined test handles N/A values gracefully."""
    # Arrange
    metrics = {
        'defensive_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_assets': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'PASS',
            'pe_ratio': 'PASS',
            'pb_ratio': 'PASS'
        },
        'combined_pe_pb_test': {
            'pe_ratio': 'N/A',
            'pb_ratio': 'N/A',
            'product': 'N/A',
            'result': 'N/A'
        },
        'enterprising_tests': {}
    }
    
    section = GrahamTestsSection(metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert '8. **Combined P/E × P/B Test**: N/A' in content
    assert 'Criterion: P/E × P/B ≤ 22.5' in content


def test_combined_test_fail():
    """Test that combined test shows FAIL when product exceeds 22.5."""
    # Arrange
    metrics = {
        'defensive_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_assets': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'PASS',
            'pe_ratio': 'FAIL',
            'pb_ratio': 'FAIL'
        },
        'combined_pe_pb_test': {
            'pe_ratio': 20.0,
            'pb_ratio': 2.0,
            'product': 40.0,
            'result': 'FAIL'
        },
        'enterprising_tests': {}
    }
    
    section = GrahamTestsSection(metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert '8. **Combined P/E × P/B Test**: FAIL' in content
    assert 'Product: 40.00 (must be ≤ 22.5)' in content


def test_all_test_criteria_present():
    """Test that all test criteria are displayed with proper formatting."""
    # Arrange
    metrics = {
        'defensive_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_assets': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'PASS',
            'pe_ratio': 'PASS',
            'pb_ratio': 'PASS'
        },
        'combined_pe_pb_test': {
            'pe_ratio': 10.0,
            'pb_ratio': 1.0,
            'product': 10.0,
            'result': 'PASS'
        },
        'enterprising_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_assets': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'N/A - Not Required',
            'price_test': 'PASS'
        }
    }
    
    section = GrahamTestsSection(metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - Defensive tests
    assert '1. **Earnings Stability**: PASS' in content
    assert '2. **Current Ratio**: PASS' in content
    assert '3. **Debt to Assets**: PASS' in content
    assert '4. **Dividend Record**: PASS' in content
    assert '5. **Earnings Growth**: PASS' in content
    assert '6. **P/E Ratio**: PASS' in content
    assert '7. **P/B Ratio**: PASS' in content
    assert '8. **Combined P/E × P/B Test**: PASS' in content
    
    # Assert - Enterprising tests
    assert 'SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS' in content
    assert 'Note on Earnings Growth' in content
