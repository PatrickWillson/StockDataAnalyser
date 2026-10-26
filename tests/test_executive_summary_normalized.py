"""Unit tests for Executive Summary section with normalized Graham Number and MoS.

Tests verify that:
- Both Graham Numbers appear with correct labels (Examples 2, 3)
- Normalized MoS displayed as primary (Example 8)
- Limiting factor displayed correctly

Requirements: 3.3, 3.4, 3.5, 10.1
"""

from output.sections.executive_summary import ExecutiveSummarySection


def test_both_graham_numbers_with_correct_labels():
    """
    Test that both Graham Numbers appear with correct labels.
    
    Example 2: Legacy Label Format
    Example 3: Normalized Label Format
    
    Requirements: 3.3, 3.4, 3.5
    """
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
        'verdict': 'UNDERVALUED',
        'graham_number': 120.50,  # Legacy single-year
        'normalized_graham_number': 135.75,  # New 3-year average
        'epv': 110.0,
        'net_net_value': 'N/A',
        'margin_of_safety': 26.5,
        'margin_of_safety_details': {
            'mos_percentage': 26.5,
            'intrinsic_value_used': 110.0,
            'limiting_factor': 'EPV',
            'normalized_graham_number': 135.75,
            'epv_per_share': 110.0
        }
    }
    
    section = ExecutiveSummarySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - Requirement 3.4: Legacy label
    assert 'Graham Number (Single-Year EPS): 120.50 USD' in content
    
    # Assert - Requirement 3.5: Normalized label
    assert 'Graham Number (3-Year Avg EPS): 135.75 USD' in content
    
    # Assert - Both should appear in output
    assert content.count('Graham Number') == 2


def test_normalized_mos_displayed_as_primary():
    """
    Test that normalized MoS is displayed as primary value.
    
    Example 8: Executive Summary Display
    
    Requirements: 10.1
    """
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
        'verdict': 'UNDERVALUED',
        'graham_number': 120.0,
        'normalized_graham_number': 135.0,
        'epv': 110.0,
        'net_net_value': 'N/A',
        'margin_of_safety': 9.1,  # Legacy value (for backward compatibility)
        'margin_of_safety_details': {
            'mos_percentage': 9.1,
            'intrinsic_value_used': 110.0,
            'limiting_factor': 'EPV',
            'normalized_graham_number': 135.0,
            'epv_per_share': 110.0
        }
    }
    
    section = ExecutiveSummarySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - MoS should be displayed with percentage
    assert 'Margin of Safety: 9.1%' in content


def test_limiting_factor_displayed_correctly():
    """
    Test that limiting factor is displayed correctly in MoS.
    
    Requirements: 10.1
    """
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
        'verdict': 'UNDERVALUED',
        'graham_number': 120.0,
        'normalized_graham_number': 135.0,
        'epv': 110.0,
        'net_net_value': 'N/A',
        'margin_of_safety': 9.1,
        'margin_of_safety_details': {
            'mos_percentage': 9.1,
            'intrinsic_value_used': 110.0,
            'limiting_factor': 'EPV',
            'normalized_graham_number': 135.0,
            'epv_per_share': 110.0
        }
    }
    
    section = ExecutiveSummarySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - Limiting factor should be shown
    assert 'Margin of Safety: 9.1% (Capped by EPV)' in content
    assert 'Conservative Intrinsic Value: 110.00 USD' in content


def test_limiting_factor_normalized_graham_number():
    """
    Test that limiting factor shows correctly when normalized GN is lower.
    
    Requirements: 10.1
    """
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
        'verdict': 'UNDERVALUED',
        'graham_number': 120.0,
        'normalized_graham_number': 115.0,
        'epv': 140.0,
        'net_net_value': 'N/A',
        'margin_of_safety': 13.0,
        'margin_of_safety_details': {
            'mos_percentage': 13.0,
            'intrinsic_value_used': 115.0,
            'limiting_factor': 'Normalized Graham Number',
            'normalized_graham_number': 115.0,
            'epv_per_share': 140.0
        }
    }
    
    section = ExecutiveSummarySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - Limiting factor should show normalized GN
    assert 'Margin of Safety: 13.0% (Capped by Normalized Graham Number)' in content
    assert 'Conservative Intrinsic Value: 115.00 USD' in content


def test_divergent_graham_numbers_with_note():
    """
    Test that a note appears when single-year and normalized values diverge significantly.
    
    Requirements: 3.3
    """
    # Arrange - Normalized is 30% higher (earnings decline scenario)
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
        'verdict': 'UNDERVALUED',
        'graham_number': 100.0,  # Based on depressed recent EPS
        'normalized_graham_number': 130.0,  # 30% higher - smooths decline
        'epv': 110.0,
        'net_net_value': 'N/A',
        'margin_of_safety': 9.1,
        'margin_of_safety_details': {
            'mos_percentage': 9.1,
            'intrinsic_value_used': 110.0,
            'limiting_factor': 'EPV',
            'normalized_graham_number': 130.0,
            'epv_per_share': 110.0
        }
    }
    
    section = ExecutiveSummarySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - Note should appear explaining divergence
    assert '⚠️ Note: 3-year average (30% higher) smooths recent earnings decline' in content


def test_divergent_graham_numbers_peak_year():
    """
    Test that a note appears when normalized is lower (peak year scenario).
    
    Requirements: 3.3
    """
    # Arrange - Normalized is 25% lower (peak year scenario)
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
        'verdict': 'OVERVALUED',
        'graham_number': 120.0,  # Based on peak recent EPS
        'normalized_graham_number': 90.0,  # 25% lower - reveals peak
        'epv': 85.0,
        'net_net_value': 'N/A',
        'margin_of_safety': -15.0,
        'margin_of_safety_details': {
            'mos_percentage': -15.0,
            'intrinsic_value_used': 85.0,
            'limiting_factor': 'EPV',
            'normalized_graham_number': 90.0,
            'epv_per_share': 85.0
        }
    }
    
    section = ExecutiveSummarySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - Note should appear explaining peak year
    assert '⚠️ Note: 3-year average (25% lower) reveals earnings peaked in recent year' in content


def test_no_note_when_values_similar():
    """
    Test that no note appears when values are within 20% of each other.
    
    Requirements: 3.3
    """
    # Arrange - Only 10% difference (below 20% threshold)
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
        'verdict': 'UNDERVALUED',
        'graham_number': 120.0,
        'normalized_graham_number': 132.0,  # Only 10% higher
        'epv': 110.0,
        'net_net_value': 'N/A',
        'margin_of_safety': 9.1,
        'margin_of_safety_details': {
            'mos_percentage': 9.1,
            'intrinsic_value_used': 110.0,
            'limiting_factor': 'EPV',
            'normalized_graham_number': 132.0,
            'epv_per_share': 110.0
        }
    }
    
    section = ExecutiveSummarySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - No note should appear
    assert '⚠️ Note:' not in content


def test_na_values_handled_correctly():
    """
    Test that N/A values are handled correctly in display.
    
    Requirements: 3.3, 3.4, 3.5, 10.1
    """
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
        'verdict': 'PENDING',
        'graham_number': 'N/A',
        'normalized_graham_number': 'N/A',
        'epv': 'N/A',
        'net_net_value': 'N/A',
        'margin_of_safety': 'N/A',
        'margin_of_safety_details': {
            'mos_percentage': 'N/A',
            'intrinsic_value_used': 'N/A',
            'limiting_factor': 'N/A',
            'normalized_graham_number': 'N/A',
            'epv_per_share': 'N/A'
        }
    }
    
    section = ExecutiveSummarySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - All N/A values should be displayed
    assert 'Graham Number (Single-Year EPS): N/A' in content
    assert 'Graham Number (3-Year Avg EPS): N/A' in content
    assert 'Margin of Safety: N/A' in content
    
    # Assert - No note should appear when both are N/A
    assert '⚠️ Note:' not in content
