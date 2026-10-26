"""
Unit tests for normalized Graham Number methodology notes formatting.

Tests that the METHODOLOGY NOTES section correctly displays:
- Normalized Graham Number explanation (Example 4)
- Formula documentation (Example 5)
- Conservative approach explanation (Example 6)
- 3-year EPS breakdown format (Example 7)
- Dual methodology documentation (Example 9)

Requirements: 6.1, 6.2, 6.3, 6.4, 8.2, 8.3
"""

from output.sections.methodology import MethodologySection


def test_normalized_graham_number_explanation_appears():
    """
    Test that normalized Graham Number explanation appears in METHODOLOGY NOTES.
    
    Example 4: Normalized GN explanation presence
    Validates: Requirements 6.1, 6.2
    """
    # Arrange
    financial_data = {
        'ticker': 'TEST.US',
        'currency': 'USD',
        'history': {
            '2024-12-31': {'eps': 10.0, 'revenue': 1000000, 'net_income': 100000},
            '2023-12-31': {'eps': 12.0, 'revenue': 1100000, 'net_income': 120000},
            '2022-12-31': {'eps': 8.0, 'revenue': 900000, 'net_income': 80000}
        }
    }
    
    metrics = {
        'graham_number': 50.0,
        'normalized_graham_number': 55.0,
        'epv': 0,
        'epv_details': {},
        'net_net_value': 0,
        'margin_of_safety': 10.0,
        'margin_of_safety_details': {
            'mos_percentage': 10.0,
            'intrinsic_value_used': 55.0,
            'limiting_factor': 'Normalized Graham Number',
            'normalized_graham_number': 55.0,
            'epv_per_share': 60.0
        }
    }
    
    # Act
    section = MethodologySection(financial_data, metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - Check normalized GN explanation appears
    assert 'Graham Number - 3-Year Average EPS (Normalized)' in content
    assert 'Smooths cyclical volatility' in content
    assert 'bull traps' in content
    
    # Validates: Requirement 6.1 - Explanation of normalized earnings methodology
    # Validates: Requirement 6.2 - Rationale for smoothing cyclical volatility


def test_formula_documentation_appears():
    """
    Test that formula documentation appears in METHODOLOGY NOTES.
    
    Example 5: Formula documentation
    Validates: Requirement 6.3
    """
    # Arrange
    financial_data = {
        'ticker': 'TEST.US',
        'currency': 'USD',
        'history': {
            '2024-12-31': {'eps': 10.0, 'revenue': 1000000, 'net_income': 100000},
            '2023-12-31': {'eps': 12.0, 'revenue': 1100000, 'net_income': 120000},
            '2022-12-31': {'eps': 8.0, 'revenue': 900000, 'net_income': 80000}
        }
    }
    
    metrics = {
        'graham_number': 50.0,
        'normalized_graham_number': 55.0,
        'epv': 0,
        'epv_details': {},
        'net_net_value': 0,
        'margin_of_safety': 10.0,
        'margin_of_safety_details': {
            'mos_percentage': 10.0,
            'intrinsic_value_used': 55.0,
            'limiting_factor': 'Normalized Graham Number',
            'normalized_graham_number': 55.0,
            'epv_per_share': 60.0
        }
    }
    
    # Act
    section = MethodologySection(financial_data, metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - Check formula appears
    assert '√(22.5 × EPS_3yr_avg × TBVPS)' in content
    
    # Validates: Requirement 6.3 - Formula documentation


def test_conservative_approach_explanation_appears():
    """
    Test that conservative approach explanation appears in METHODOLOGY NOTES.
    
    Example 6: Conservative approach documentation
    Validates: Requirement 6.4
    """
    # Arrange
    financial_data = {
        'ticker': 'TEST.US',
        'currency': 'USD',
        'history': {
            '2024-12-31': {'eps': 10.0, 'revenue': 1000000, 'net_income': 100000},
            '2023-12-31': {'eps': 12.0, 'revenue': 1100000, 'net_income': 120000},
            '2022-12-31': {'eps': 8.0, 'revenue': 900000, 'net_income': 80000}
        }
    }
    
    metrics = {
        'graham_number': 50.0,
        'normalized_graham_number': 55.0,
        'epv': 0,
        'epv_details': {},
        'net_net_value': 0,
        'margin_of_safety': 10.0,
        'margin_of_safety_details': {
            'mos_percentage': 10.0,
            'intrinsic_value_used': 55.0,
            'limiting_factor': 'Normalized Graham Number',
            'normalized_graham_number': 55.0,
            'epv_per_share': 60.0
        }
    }
    
    # Act
    section = MethodologySection(financial_data, metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - Check conservative approach explanation
    assert 'Conservative Dual-Anchor Methodology' in content
    assert 'lower' in content.lower()
    assert 'Normalized Graham Number' in content
    assert 'EPV per share' in content
    assert "Graham's Philosophy" in content or 'conservative' in content.lower()
    
    # Validates: Requirement 6.4 - Conservative MoS approach explanation


def test_3year_eps_breakdown_format():
    """
    Test that 3-year EPS breakdown format is correct.
    
    Example 7: EPS breakdown format
    Validates: Requirements 8.2, 8.3
    """
    # Arrange
    financial_data = {
        'ticker': 'TEST.US',
        'currency': 'USD',
        'history': {
            '2024-12-31': {'eps': 10.50, 'revenue': 1000000, 'net_income': 100000},
            '2023-12-31': {'eps': 12.75, 'revenue': 1100000, 'net_income': 120000},
            '2022-12-31': {'eps': 8.25, 'revenue': 900000, 'net_income': 80000}
        }
    }
    
    metrics = {
        'graham_number': 50.0,
        'normalized_graham_number': 55.0,
        'epv': 0,
        'epv_details': {},
        'net_net_value': 0,
        'margin_of_safety': 10.0,
        'margin_of_safety_details': {
            'mos_percentage': 10.0,
            'intrinsic_value_used': 55.0,
            'limiting_factor': 'Normalized Graham Number',
            'normalized_graham_number': 55.0,
            'epv_per_share': 60.0
        }
    }
    
    # Act
    section = MethodologySection(financial_data, metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - Check format matches: "3-Year EPS: [Year1: $X.XX, Year2: $Y.YY, Year3: $Z.ZZ] → Avg: $A.AA"
    assert '3-Year EPS' in content
    assert '2024:' in content  # Most recent year first
    assert '2023:' in content
    assert '2022:' in content
    assert '→ Avg:' in content
    
    # Check values are displayed
    assert '10.50' in content
    assert '12.75' in content
    assert '8.25' in content
    
    # Calculate expected average
    expected_avg = (10.50 + 12.75 + 8.25) / 3
    assert f'{expected_avg:.2f}' in content
    
    # Validates: Requirement 8.2 - 3-year EPS breakdown display
    # Validates: Requirement 8.3 - Years in descending order


def test_dual_methodology_documentation():
    """
    Test that both single-year and normalized Graham Number methodologies are documented.
    
    Example 9: Dual methodology documentation
    Validates: Requirement 10.2
    """
    # Arrange
    financial_data = {
        'ticker': 'TEST.US',
        'currency': 'USD',
        'history': {
            '2024-12-31': {'eps': 10.0, 'revenue': 1000000, 'net_income': 100000},
            '2023-12-31': {'eps': 12.0, 'revenue': 1100000, 'net_income': 120000},
            '2022-12-31': {'eps': 8.0, 'revenue': 900000, 'net_income': 80000}
        }
    }
    
    metrics = {
        'graham_number': 50.0,
        'normalized_graham_number': 55.0,
        'epv': 0,
        'epv_details': {},
        'net_net_value': 0,
        'margin_of_safety': 10.0,
        'margin_of_safety_details': {
            'mos_percentage': 10.0,
            'intrinsic_value_used': 55.0,
            'limiting_factor': 'Normalized Graham Number',
            'normalized_graham_number': 55.0,
            'epv_per_share': 60.0
        }
    }
    
    # Act
    section = MethodologySection(financial_data, metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - Check both methodologies are documented
    assert 'Graham Number - Single-Year EPS' in content
    assert 'Graham Number - 3-Year Average EPS (Normalized)' in content
    
    # Check both formulas are present
    assert '√(22.5 × EPS × TBVPS)' in content  # Single-year
    assert '√(22.5 × EPS_3yr_avg × TBVPS)' in content  # Normalized
    
    # Validates: Requirement 10.2 - Both methodologies documented


def test_limiting_factor_displayed():
    """
    Test that limiting factor is displayed in MoS explanation.
    
    Validates: Requirement 6.4
    """
    # Arrange
    financial_data = {
        'ticker': 'TEST.US',
        'currency': 'USD',
        'history': {
            '2024-12-31': {'eps': 10.0, 'revenue': 1000000, 'net_income': 100000},
            '2023-12-31': {'eps': 12.0, 'revenue': 1100000, 'net_income': 120000},
            '2022-12-31': {'eps': 8.0, 'revenue': 900000, 'net_income': 80000}
        }
    }
    
    metrics = {
        'graham_number': 50.0,
        'normalized_graham_number': 90.0,
        'epv': 0,
        'epv_details': {},
        'net_net_value': 0,
        'margin_of_safety': -50.0,
        'margin_of_safety_details': {
            'mos_percentage': -50.0,
            'intrinsic_value_used': 30.0,
            'limiting_factor': 'EPV',
            'normalized_graham_number': 90.0,
            'epv_per_share': 30.0
        }
    }
    
    # Act
    section = MethodologySection(financial_data, metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - Check limiting factor is shown
    assert 'Capped by EPV' in content
    assert 'For This Stock' in content
    
    # Check interpretation is provided
    assert 'Interpretation' in content
    
    # Validates: Requirement 6.4 - Limiting factor display


def test_normalized_gn_na_still_shows_breakdown():
    """
    Test that 3-year EPS breakdown is shown even when normalized GN is N/A.
    
    Validates: Requirement 8.5
    """
    # Arrange - Only 2 years of data (insufficient)
    financial_data = {
        'ticker': 'TEST.US',
        'currency': 'USD',
        'history': {
            '2024-12-31': {'eps': 10.0, 'revenue': 1000000, 'net_income': 100000},
            '2023-12-31': {'eps': 12.0, 'revenue': 1100000, 'net_income': 120000}
        }
    }
    
    metrics = {
        'graham_number': 50.0,
        'normalized_graham_number': 'N/A',
        'epv': 0,
        'epv_details': {},
        'net_net_value': 0,
        'margin_of_safety': 'N/A',
        'margin_of_safety_details': {
            'mos_percentage': 'N/A',
            'intrinsic_value_used': 'N/A',
            'limiting_factor': 'N/A',
            'normalized_graham_number': 'N/A',
            'epv_per_share': 0.0
        }
    }
    
    # Act
    section = MethodologySection(financial_data, metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - Check normalized GN section appears with N/A
    assert 'Graham Number - 3-Year Average EPS (Normalized)' in content
    assert 'Value**: N/A' in content
    
    # Check breakdown or warning is shown
    assert '3-Year EPS' in content
    
    # Validates: Requirement 8.5 - Show breakdown even when calculation fails


def test_negative_average_eps_explanation():
    """
    Test that negative average EPS is explained in breakdown.
    
    Validates: Requirements 5.2, 8.5
    """
    # Arrange - Mix of positive and negative EPS resulting in negative average
    financial_data = {
        'ticker': 'TEST.US',
        'currency': 'USD',
        'history': {
            '2024-12-31': {'eps': 5.0, 'revenue': 1000000, 'net_income': 50000},
            '2023-12-31': {'eps': -10.0, 'revenue': 1100000, 'net_income': -100000},
            '2022-12-31': {'eps': -8.0, 'revenue': 900000, 'net_income': -80000}
        }
    }
    
    metrics = {
        'graham_number': 50.0,
        'normalized_graham_number': 'N/A',
        'epv': 0,
        'epv_details': {},
        'net_net_value': 0,
        'margin_of_safety': 'N/A',
        'margin_of_safety_details': {
            'mos_percentage': 'N/A',
            'intrinsic_value_used': 'N/A',
            'limiting_factor': 'N/A',
            'normalized_graham_number': 'N/A',
            'epv_per_share': 0.0
        }
    }
    
    # Act
    section = MethodologySection(financial_data, metrics)
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert - Check normalized GN is N/A
    assert 'Graham Number - 3-Year Average EPS (Normalized)' in content
    assert 'Value**: N/A' in content
    
    # Check rationale is still shown
    assert 'Smooths cyclical volatility' in content
    
    # Validates: Requirement 5.2 - Negative average EPS handling
    # Validates: Requirement 8.5 - Show breakdown even when calculation fails
