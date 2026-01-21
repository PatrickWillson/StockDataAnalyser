"""Integration tests for Graham tests section.

This module tests that the GrahamTestsSection integrates correctly
with the rest of the dossier generation system.
"""

import pytest
from output.sections.graham_tests import GrahamTestsSection


def test_graham_tests_section_integration():
    """Test that Graham tests section generates output matching expected format."""
    # Sample metrics matching the structure from GrahamCalculator
    metrics = {
        'defensive_tests': {
            'earnings_stability': 'FAIL',
            'current_ratio': 'FAIL',
            'debt_to_assets': 'FAIL',
            'dividend_record': 'PASS',
            'earnings_growth': 'PASS',
            'pe_ratio': 'FAIL',
            'pb_ratio': 'FAIL'
        },
        'enterprising_tests': {
            'earnings_stability': 'FAIL',
            'current_ratio': 'FAIL',
            'debt_to_assets': 'FAIL',
            'dividend_record': 'PASS',
            'earnings_growth': 'N/A - Not Required',
            'price_test': 'FAIL'
        }
    }
    
    section = GrahamTestsSection(metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Verify defensive tests section
    assert "## SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS" in content
    assert "- Earnings Stability: FAIL" in content
    assert "- Current Ratio: FAIL" in content
    assert "- Debt To Assets: FAIL" in content
    assert "- Dividend Record: PASS" in content
    assert "- Earnings Growth: PASS" in content
    assert "- Pe Ratio: FAIL" in content
    assert "- Pb Ratio: FAIL" in content
    
    # Verify enterprising tests section
    assert "## SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS" in content
    assert "- Earnings Stability: FAIL" in content
    assert "- Current Ratio: FAIL" in content
    assert "- Debt To Assets: FAIL" in content
    assert "- Dividend Record: PASS" in content
    assert "- Earnings Growth: N/A - Not Required" in content
    assert "- Price Test: FAIL" in content
    
    # Verify note is present
    assert "**Note on Earnings Growth:**" in content
    assert "Earnings growth is intentionally not required for Enterprising Investors" in content
    
    # Verify separators
    assert content.count("---") >= 2


def test_graham_tests_section_with_all_pass():
    """Test Graham tests section when all tests pass."""
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
    lines = section.generate()
    content = '\n'.join(lines)
    
    # All tests should show PASS
    assert content.count("PASS") >= 12  # 7 defensive + 5 enterprising


def test_graham_tests_section_output_structure():
    """Test that the output structure matches expected format."""
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
    
    # Find section positions
    defensive_pos = None
    enterprising_pos = None
    
    for i, line in enumerate(lines):
        if "SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS" in line:
            defensive_pos = i
        if "SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS" in line:
            enterprising_pos = i
    
    # Both sections should be present
    assert defensive_pos is not None
    assert enterprising_pos is not None
    
    # Defensive should come before enterprising
    assert defensive_pos < enterprising_pos
