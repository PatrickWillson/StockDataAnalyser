"""Tests for Graham tests section generation.

This module tests the GrahamTestsSection class which generates both
defensive and enterprising investor test sections.
"""

import pytest
from output.sections.graham_tests import GrahamTestsSection


def test_defensive_tests_section_header():
    """Test that defensive tests section has correct header."""
    metrics = {
        'defensive_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS'
        },
        'enterprising_tests': {}
    }
    
    section = GrahamTestsSection(metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    assert "## SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS" in content


def test_defensive_tests_display_all_tests():
    """Test that all defensive tests are displayed."""
    metrics = {
        'defensive_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'FAIL',
            'debt_to_equity': 'PASS',
            'dividend_record': 'N/A',
            'earnings_growth': 'PASS',
            'pe_ratio': 'PASS',
            'price_to_book': 'PASS'
        },
        'enterprising_tests': {}
    }
    
    section = GrahamTestsSection(metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Check that all tests are present
    assert "Earnings Stability: PASS" in content
    assert "Current Ratio: FAIL" in content
    assert "Debt To Equity: PASS" in content
    assert "Dividend Record: N/A" in content
    assert "Earnings Growth: PASS" in content
    assert "Pe Ratio: PASS" in content
    assert "Price To Book: PASS" in content


def test_defensive_tests_pass_fail_formatting():
    """Test that PASS and FAIL results are formatted correctly."""
    metrics = {
        'defensive_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'FAIL',
            'debt_to_equity': 'N/A'
        },
        'enterprising_tests': {}
    }
    
    section = GrahamTestsSection(metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Check formatting
    assert "- Earnings Stability: PASS" in content
    assert "- Current Ratio: FAIL" in content
    assert "- Debt To Equity: N/A" in content


def test_enterprising_tests_section_header():
    """Test that enterprising tests section has correct header."""
    metrics = {
        'defensive_tests': {},
        'enterprising_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS'
        }
    }
    
    section = GrahamTestsSection(metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    assert "## SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS" in content


def test_enterprising_tests_display_all_tests():
    """Test that all enterprising tests are displayed."""
    metrics = {
        'defensive_tests': {},
        'enterprising_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_assets': 'FAIL',
            'dividend_record': 'PASS',
            'pe_ratio': 'PASS',
            'price_to_book': 'PASS'
        }
    }
    
    section = GrahamTestsSection(metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Check that all tests are present
    assert "Earnings Stability: PASS" in content
    assert "Current Ratio: PASS" in content
    assert "Debt To Assets: FAIL" in content
    assert "Dividend Record: PASS" in content
    assert "Pe Ratio: PASS" in content
    assert "Price To Book: PASS" in content


def test_enterprising_tests_includes_growth_note():
    """Test that enterprising tests section includes note about earnings growth."""
    metrics = {
        'defensive_tests': {},
        'enterprising_tests': {
            'earnings_stability': 'PASS'
        }
    }
    
    section = GrahamTestsSection(metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Check for the earnings growth note
    assert "Note on Earnings Growth:" in content
    assert "Earnings growth is intentionally not required for Enterprising Investors" in content
    assert "Graham's logic:" in content


def test_both_sections_generated():
    """Test that both defensive and enterprising sections are generated."""
    metrics = {
        'defensive_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS'
        },
        'enterprising_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS'
        }
    }
    
    section = GrahamTestsSection(metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Check both sections are present
    assert "## SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS" in content
    assert "## SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS" in content


def test_section_separators():
    """Test that sections are properly separated with horizontal rules."""
    metrics = {
        'defensive_tests': {
            'earnings_stability': 'PASS'
        },
        'enterprising_tests': {
            'earnings_stability': 'PASS'
        }
    }
    
    section = GrahamTestsSection(metrics)
    lines = section.generate()
    
    # Check for horizontal rules
    assert "---" in lines


def test_empty_enterprising_tests():
    """Test handling of empty enterprising tests dictionary."""
    metrics = {
        'defensive_tests': {
            'earnings_stability': 'PASS'
        },
        'enterprising_tests': {}
    }
    
    section = GrahamTestsSection(metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Should still have the section header
    assert "## SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS" in content
    # Should still have the note
    assert "Note on Earnings Growth:" in content


def test_test_name_formatting():
    """Test that test names are properly formatted from snake_case."""
    metrics = {
        'defensive_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_to_equity': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'PASS',
            'pe_ratio': 'PASS',
            'price_to_book': 'PASS'
        },
        'enterprising_tests': {}
    }
    
    section = GrahamTestsSection(metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Check that snake_case is converted to Title Case
    assert "Earnings Stability:" in content
    assert "Current Ratio:" in content
    assert "Debt To Equity:" in content
    assert "Dividend Record:" in content
    assert "Earnings Growth:" in content
    assert "Pe Ratio:" in content
    assert "Price To Book:" in content
