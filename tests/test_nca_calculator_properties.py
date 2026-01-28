"""
Property-Based Tests for Net Current Assets (NCA) Calculator

This module tests the NCA calculation methods using property-based testing with Hypothesis.
All tests run 100+ iterations with random valid inputs to verify universal correctness properties.

Feature: graham-metrics-enhancement
"""

import pytest
from decimal import Decimal
from hypothesis import given, settings
from hypothesis import strategies as st

from core.graham_math import GrahamCalculator
from tests.test_utils_decimal import (
    decimal_strategy,
    currency_strategy,
    to_decimal,
    assert_decimal_equal
)
from tests.fixtures_graham_metrics import (
    GrahamMetricsFixtures,
    EdgeCaseFixtures,
    SectorSpecificFixtures
)


class TestNCACalculationCorrectness:
    """
    Property 1: NCA Calculation Correctness
    
    For any balance sheet data with current_assets and total_liabilities,
    the calculated NCA should equal current_assets minus total_liabilities.
    
    Validates: Requirements 1.1
    """
    
    @given(
        current_assets=currency_strategy(min_value="0", max_value="1000000000000"),
        total_liabilities=currency_strategy(min_value="0", max_value="1000000000000"),
        long_term_debt=currency_strategy(min_value="0", max_value="1000000000000")
    )
    @settings(max_examples=100)
    def test_nca_equals_current_assets_minus_total_liabilities(
        self, current_assets, total_liabilities, long_term_debt
    ):
        """
        Property: NCA = Current Assets - Total Liabilities
        
        For any valid balance sheet data, the NCA calculation must equal
        the difference between current assets and total liabilities.
        """
        # Arrange
        financial_data = GrahamMetricsFixtures.get_nca_test_data(
            current_assets=current_assets,
            total_liabilities=total_liabilities,
            long_term_debt=long_term_debt
        )
        calculator = GrahamCalculator(financial_data)
        
        # Act
        result = calculator.compute_nca_details()
        
        # Assert
        assert result['current_assets'] == float(current_assets), \
            "Current assets should match input"
        assert result['total_liabilities'] == float(total_liabilities), \
            "Total liabilities should match input"
        
        # Verify NCA formula
        if result['nca'] != "N/A":
            expected_nca = current_assets - total_liabilities
            actual_nca = to_decimal(result['nca'])
            assert_decimal_equal(
                actual_nca,
                expected_nca,
                tolerance=Decimal('0.01'),
                message=f"NCA {actual_nca} should equal current_assets {current_assets} - total_liabilities {total_liabilities} = {expected_nca}"
            )
    
    def test_nca_calculation_with_known_values(self):
        """
        Unit test: Verify NCA calculation with known values.
        
        Example from requirements: DAC company
        """
        # Arrange
        financial_data = GrahamMetricsFixtures.get_nca_test_data(
            current_assets=Decimal('1234567000'),
            total_liabilities=Decimal('987654000'),
            long_term_debt=Decimal('699563000')
        )
        calculator = GrahamCalculator(financial_data)
        
        # Act
        result = calculator.compute_nca_details()
        
        # Assert
        expected_nca = Decimal('1234567000') - Decimal('987654000')  # 246913000
        actual_nca = to_decimal(result['nca'])
        
        assert_decimal_equal(
            actual_nca,
            expected_nca,
            tolerance=Decimal('1'),  # Allow 1 dollar rounding difference
            message=f"NCA should be {expected_nca}"
        )


class TestNCADisplayCompleteness:
    """
    Property 2: NCA Display Completeness
    
    For any valid NCA calculation result, the output should contain
    current_assets, total_liabilities, nca, and debt_coverage_ratio
    (or "N/A") as separate displayable values.
    
    Validates: Requirements 1.2, 1.4
    """
    
    @given(
        current_assets=currency_strategy(min_value="1", max_value="1000000000000"),
        total_liabilities=currency_strategy(min_value="1", max_value="1000000000000"),
        long_term_debt=currency_strategy(min_value="0", max_value="1000000000000")
    )
    @settings(max_examples=100)
    def test_nca_result_contains_all_required_fields(
        self, current_assets, total_liabilities, long_term_debt
    ):
        """
        Property: NCA result must contain all required display fields.
        
        Every NCA calculation result must include:
        - current_assets
        - total_liabilities
        - nca
        - long_term_debt
        - debt_coverage_ratio
        - debt_coverage_pct
        - warnings
        """
        # Arrange
        financial_data = GrahamMetricsFixtures.get_nca_test_data(
            current_assets=current_assets,
            total_liabilities=total_liabilities,
            long_term_debt=long_term_debt
        )
        calculator = GrahamCalculator(financial_data)
        
        # Act
        result = calculator.compute_nca_details()
        
        # Assert - all required fields must be present
        required_fields = [
            'current_assets',
            'total_liabilities',
            'nca',
            'long_term_debt',
            'debt_coverage_ratio',
            'debt_coverage_pct',
            'warnings'
        ]
        
        for field in required_fields:
            assert field in result, f"Result must contain '{field}' field"
        
        # Verify warnings is a list
        assert isinstance(result['warnings'], list), "Warnings must be a list"
    
    def test_nca_display_with_valid_data(self):
        """
        Unit test: Verify all fields are populated with valid data.
        """
        # Arrange
        financial_data = GrahamMetricsFixtures.get_nca_test_data(
            current_assets=Decimal('1000000'),
            total_liabilities=Decimal('600000'),
            long_term_debt=Decimal('300000')
        )
        calculator = GrahamCalculator(financial_data)
        
        # Act
        result = calculator.compute_nca_details()
        
        # Assert
        assert result['current_assets'] == 1000000.0
        assert result['total_liabilities'] == 600000.0
        assert result['nca'] == 400000.0
        assert result['long_term_debt'] == 300000.0
        assert result['debt_coverage_ratio'] != "N/A"
        assert result['debt_coverage_pct'] != "N/A"
        assert isinstance(result['warnings'], list)


class TestDebtCoverageCalculation:
    """
    Property 3: Debt Coverage Calculation
    
    For any balance sheet data where NCA > 0 and long_term_debt is available,
    the debt coverage ratio should equal long_term_debt divided by NCA.
    
    Validates: Requirements 1.3
    """
    
    @given(
        current_assets=currency_strategy(min_value="1000000", max_value="1000000000000"),
        total_liabilities=currency_strategy(min_value="1", max_value="500000000000"),
        long_term_debt=currency_strategy(min_value="1", max_value="1000000000000")
    )
    @settings(max_examples=100)
    def test_debt_coverage_ratio_formula(
        self, current_assets, total_liabilities, long_term_debt
    ):
        """
        Property: Debt Coverage Ratio = Long-term Debt / NCA (when NCA > 0)
        
        For any balance sheet where NCA is positive, the debt coverage ratio
        must equal long_term_debt divided by NCA.
        """
        # Ensure NCA will be positive
        if current_assets <= total_liabilities:
            current_assets = total_liabilities + Decimal('1000000')
        
        # Arrange
        financial_data = GrahamMetricsFixtures.get_nca_test_data(
            current_assets=current_assets,
            total_liabilities=total_liabilities,
            long_term_debt=long_term_debt
        )
        calculator = GrahamCalculator(financial_data)
        
        # Act
        result = calculator.compute_nca_details()
        
        # Assert
        nca = to_decimal(result['nca'])
        
        if nca > 0:
            # Debt coverage ratio should be calculated
            assert result['debt_coverage_ratio'] != "N/A", \
                "Debt coverage ratio should be calculated when NCA > 0"
            
            # Verify formula
            expected_ratio = long_term_debt / nca
            actual_ratio = to_decimal(result['debt_coverage_ratio'])
            
            assert_decimal_equal(
                actual_ratio,
                expected_ratio,
                tolerance=Decimal('0.01'),
                message=f"Debt coverage ratio {actual_ratio} should equal long_term_debt {long_term_debt} / NCA {nca} = {expected_ratio}"
            )
            
            # Verify percentage format
            assert result['debt_coverage_pct'].endswith('%'), \
                "Debt coverage percentage should end with '%'"
            
            # Verify percentage value matches ratio
            pct_value = Decimal(result['debt_coverage_pct'].rstrip('%'))
            expected_pct = expected_ratio * 100
            assert_decimal_equal(
                pct_value,
                expected_pct,
                tolerance=Decimal('0.01'),
                message=f"Debt coverage percentage {pct_value}% should equal ratio {expected_ratio} * 100"
            )
    
    def test_debt_coverage_with_negative_nca(self):
        """
        Unit test: Debt coverage should be N/A when NCA is negative.
        """
        # Arrange
        financial_data = EdgeCaseFixtures.get_negative_nca_data()
        calculator = GrahamCalculator(financial_data)
        
        # Act
        result = calculator.compute_nca_details()
        
        # Assert
        assert result['nca'] < 0, "NCA should be negative"
        assert result['debt_coverage_ratio'] == "N/A", \
            "Debt coverage ratio should be N/A when NCA is negative"
        assert result['debt_coverage_pct'] == "N/A", \
            "Debt coverage percentage should be N/A when NCA is negative"
        
        # Verify warning is present
        assert any('negative' in w.lower() for w in result['warnings']), \
            "Should have warning about negative NCA"
    
    def test_debt_coverage_with_zero_nca(self):
        """
        Unit test: Debt coverage should be N/A when NCA is zero.
        """
        # Arrange
        financial_data = GrahamMetricsFixtures.get_nca_test_data(
            current_assets=Decimal('600000'),
            total_liabilities=Decimal('600000'),
            long_term_debt=Decimal('300000')
        )
        calculator = GrahamCalculator(financial_data)
        
        # Act
        result = calculator.compute_nca_details()
        
        # Assert
        assert result['nca'] == 0.0, "NCA should be zero"
        assert result['debt_coverage_ratio'] == "N/A", \
            "Debt coverage ratio should be N/A when NCA is zero"
        assert result['debt_coverage_pct'] == "N/A", \
            "Debt coverage percentage should be N/A when NCA is zero"


class TestSectorSpecificNCAWarnings:
    """
    Property 4: Sector-Specific NCA Warnings
    
    For any company in the Financials or Utilities sector, the NCA calculation
    should include a warning about balance sheet structure applicability.
    
    Validates: Requirements 1.6
    """
    
    @pytest.mark.parametrize("sector,should_warn", [
        ("Financials", True),
        ("Financial Services", True),
        ("Banking", True),
        ("Utilities", True),
        ("Utility", True),
        ("Technology", False),
        ("Services", False),
        ("Manufacturing", False),
        ("Healthcare", False),
        ("Consumer Goods", False)
    ])
    def test_sector_specific_warnings(self, sector, should_warn):
        """
        Property: Financials and Utilities sectors should trigger warnings.
        
        NCA analysis may not be applicable for Financial and Utility companies
        due to their unique balance sheet structures.
        """
        # Arrange
        financial_data = GrahamMetricsFixtures.get_nca_test_data(sector=sector)
        calculator = GrahamCalculator(financial_data)
        
        # Act
        result = calculator.compute_nca_details()
        
        # Assert
        has_sector_warning = any(
            'not be applicable' in w and (
                'Financial' in w or 'Utility' in w or 'Utilities' in w
            )
            for w in result['warnings']
        )
        
        if should_warn:
            assert has_sector_warning, \
                f"Should have sector warning for {sector} companies"
        else:
            assert not has_sector_warning, \
                f"Should not have sector warning for {sector} companies"
    
    def test_financial_sector_warning_content(self):
        """
        Unit test: Verify Financial sector warning message.
        """
        # Arrange
        financial_data = SectorSpecificFixtures.get_financial_sector_data()
        calculator = GrahamCalculator(financial_data)
        
        # Act
        result = calculator.compute_nca_details()
        
        # Assert
        assert any('Financial' in w for w in result['warnings']), \
            "Should mention Financial sector in warning"
        assert any('balance sheet structure' in w for w in result['warnings']), \
            "Should mention balance sheet structure in warning"
    
    def test_utility_sector_warning_content(self):
        """
        Unit test: Verify Utility sector warning message.
        """
        # Arrange
        financial_data = SectorSpecificFixtures.get_utility_sector_data()
        calculator = GrahamCalculator(financial_data)
        
        # Act
        result = calculator.compute_nca_details()
        
        # Assert
        assert any('Utility' in w or 'Utilities' in w for w in result['warnings']), \
            "Should mention Utility sector in warning"
        assert any('balance sheet structure' in w for w in result['warnings']), \
            "Should mention balance sheet structure in warning"


class TestNCAEdgeCases:
    """
    Unit tests for NCA edge cases.
    
    Tests specific scenarios that should be handled gracefully.
    """
    
    def test_missing_balance_sheet_data(self):
        """
        Edge case: Missing balance sheet data should return N/A.
        """
        # Arrange
        financial_data = {
            'ticker': 'TEST.US',
            'price': 100.0,
            'currency': 'USD',
            'sector': 'Technology',
            'history': {
                '2023-12-31': {
                    'revenue': 1000000.0,
                    'net_income': 100000.0
                    # Missing balance sheet fields
                }
            }
        }
        calculator = GrahamCalculator(financial_data)
        
        # Act
        result = calculator.compute_nca_details()
        
        # Assert
        assert result['nca'] == "N/A", "NCA should be N/A when balance sheet data is missing"
        assert result['debt_coverage_ratio'] == "N/A"
        assert any('unavailable' in w.lower() for w in result['warnings'])
    
    def test_no_financial_history(self):
        """
        Edge case: No financial history should return N/A.
        """
        # Arrange
        financial_data = {
            'ticker': 'TEST.US',
            'price': 100.0,
            'currency': 'USD',
            'sector': 'Technology',
            'history': {}
        }
        calculator = GrahamCalculator(financial_data)
        
        # Act
        result = calculator.compute_nca_details()
        
        # Assert
        assert result['nca'] == "N/A"
        assert result['debt_coverage_ratio'] == "N/A"
        assert len(result['warnings']) > 0
    
    def test_zero_long_term_debt(self):
        """
        Edge case: Zero long-term debt should still calculate debt coverage.
        """
        # Arrange
        financial_data = GrahamMetricsFixtures.get_nca_test_data(
            current_assets=Decimal('1000000'),
            total_liabilities=Decimal('600000'),
            long_term_debt=Decimal('0')
        )
        calculator = GrahamCalculator(financial_data)
        
        # Act
        result = calculator.compute_nca_details()
        
        # Assert
        assert result['long_term_debt'] == 0.0
        assert result['debt_coverage_ratio'] == 0.0, \
            "Debt coverage ratio should be 0 when long-term debt is 0"
        assert result['debt_coverage_pct'] == "0.0%"
    
    def test_very_large_values(self):
        """
        Edge case: Very large values should be handled correctly.
        """
        # Arrange
        financial_data = GrahamMetricsFixtures.get_nca_test_data(
            current_assets=Decimal('999999999999'),  # ~1 trillion
            total_liabilities=Decimal('500000000000'),  # 500 billion
            long_term_debt=Decimal('300000000000')  # 300 billion
        )
        calculator = GrahamCalculator(financial_data)
        
        # Act
        result = calculator.compute_nca_details()
        
        # Assert
        assert result['nca'] != "N/A", "Should handle large values"
        assert result['debt_coverage_ratio'] != "N/A"
        
        # Verify calculation is correct
        expected_nca = Decimal('999999999999') - Decimal('500000000000')
        actual_nca = to_decimal(result['nca'])
        assert_decimal_equal(actual_nca, expected_nca, tolerance=Decimal('1'))
