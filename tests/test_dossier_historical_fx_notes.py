"""
Unit Tests for Dossier Historical FX Rate Notes

Tests that the dossier correctly documents whether historical FX rates were used.
"""

import pytest
from output.sections.financial_history import FinancialHistorySection


def test_dossier_note_with_historical_rates():
    """
    **Feature: historical-fx-rates**
    **Validates: Requirements 4.1, 4.3, 4.4**
    
    Test that correct note is generated when historical rates are used.
    """
    # Create financial data with historical FX rates
    financial_data = {
        'currency': 'USD',
        'historical_fx_rates': {
            '2023-12-31': 1.30,
            '2022-12-31': 1.25,
            '2021-12-31': 1.20
        },
        'history': {
            '2023-12-31': {
                'revenue': 1000,
                'net_income': 100,
                'eps': 1.0,
                'dividend': 0.5,
                'total_equity': 500,
                'year_end_price': 130.0
            },
            '2022-12-31': {
                'revenue': 950,
                'net_income': 95,
                'eps': 0.95,
                'dividend': 0.48,
                'total_equity': 480,
                'year_end_price': 118.75
            }
        }
    }
    
    # Generate financial history section
    section = FinancialHistorySection(financial_data)
    lines = section.generate()
    
    # Join lines to search for note
    content = '\n'.join(lines)
    
    # Verify that the note indicates historical FX rates were used
    assert 'date-matched historical FX rates' in content, \
        "Should indicate that date-matched historical FX rates were used"
    assert 'accurate historical P/E and P/B ratios' in content, \
        "Should mention accuracy benefit"
    assert 'actual market conditions at the time' in content, \
        "Should mention market conditions"
    
    # Verify that the legacy warning is NOT present
    assert 'Historical FX rates not used' not in content, \
        "Should not show legacy warning when historical rates are used"
    
    print("✓ Dossier correctly indicates historical FX rates were used")


def test_dossier_note_without_historical_rates():
    """
    **Feature: historical-fx-rates**
    **Validates: Requirements 4.1, 4.3, 4.4**
    
    Test that legacy warning is shown when historical rates are not used.
    """
    # Create financial data WITHOUT historical FX rates
    financial_data = {
        'currency': 'USD',
        'historical_fx_rates': {},  # Empty dict (no historical rates)
        'history': {
            '2023-12-31': {
                'revenue': 1000,
                'net_income': 100,
                'eps': 1.0,
                'dividend': 0.5,
                'total_equity': 500,
                'year_end_price': 130.0
            }
        }
    }
    
    # Generate financial history section
    section = FinancialHistorySection(financial_data)
    lines = section.generate()
    
    # Join lines to search for note
    content = '\n'.join(lines)
    
    # Verify that the legacy warning is present
    assert 'current FX rates' in content, \
        "Should mention current FX rates when historical rates not used"
    assert 'Historical FX rates not used' in content, \
        "Should show legacy warning"
    assert 'actual historical valuations may differ due to FX fluctuations' in content, \
        "Should warn about FX fluctuations"
    
    # Verify that the new note is NOT present
    assert 'date-matched historical FX rates' not in content, \
        "Should not mention date-matched rates when they weren't used"
    
    print("✓ Dossier correctly shows legacy warning when historical rates not used")


def test_dossier_note_with_missing_historical_fx_rates_key():
    """
    Test that legacy warning is shown when historical_fx_rates key is missing entirely.
    """
    # Create financial data without historical_fx_rates key at all
    financial_data = {
        'currency': 'USD',
        # No 'historical_fx_rates' key
        'history': {
            '2023-12-31': {
                'revenue': 1000,
                'net_income': 100,
                'eps': 1.0
            }
        }
    }
    
    # Generate financial history section
    section = FinancialHistorySection(financial_data)
    lines = section.generate()
    
    # Join lines to search for note
    content = '\n'.join(lines)
    
    # Should show legacy warning (backward compatible)
    assert 'current FX rates' in content
    assert 'Historical FX rates not used' in content
    
    print("✓ Dossier handles missing historical_fx_rates key gracefully")


def test_dossier_note_with_partial_historical_rates():
    """
    Test that note is shown when some (but not all) historical rates are available.
    """
    # Create financial data with some historical FX rates
    financial_data = {
        'currency': 'USD',
        'historical_fx_rates': {
            '2023-12-31': 1.30,
            '2022-12-31': None,  # Missing rate for this year
            '2021-12-31': 1.20
        },
        'history': {
            '2023-12-31': {'revenue': 1000, 'eps': 1.0},
            '2022-12-31': {'revenue': 950, 'eps': 0.95},
            '2021-12-31': {'revenue': 900, 'eps': 0.90}
        }
    }
    
    # Generate financial history section
    section = FinancialHistorySection(financial_data)
    lines = section.generate()
    
    # Join lines to search for note
    content = '\n'.join(lines)
    
    # Should show the historical rates note (even with some missing)
    # The warning about fallback years is handled in stock_data_analyser.py, not here
    assert 'date-matched historical FX rates' in content, \
        "Should indicate historical rates were used (even if some are missing)"
    
    print("✓ Dossier correctly handles partial historical rates")


def test_dossier_note_formatting():
    """
    Test that the note is properly formatted as italic markdown.
    """
    financial_data = {
        'currency': 'USD',
        'historical_fx_rates': {'2023-12-31': 1.30},
        'history': {'2023-12-31': {'revenue': 1000}}
    }
    
    section = FinancialHistorySection(financial_data)
    lines = section.generate()
    
    # Find the note line
    note_lines = [line for line in lines if 'Historical prices converted' in line or 'date-matched' in line]
    
    assert len(note_lines) > 0, "Should have at least one note line"
    
    # Check that it's formatted as italic (starts with * and ends with *)
    for note_line in note_lines:
        assert note_line.startswith('*'), "Note should start with * (italic markdown)"
        assert note_line.endswith('*'), "Note should end with * (italic markdown)"
    
    print("✓ Dossier note is properly formatted as italic markdown")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
