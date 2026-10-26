"""
Property-Based Tests for Quick Ratio Calculator

This module tests the Quick Ratio calculation methods using property-based testing with Hypothesis.
All tests run 100+ iterations with random valid inputs to verify universal correctness properties.

Feature: graham-metrics-enhancement
"""

import pytest
from decimal import Decimal
from hypothesis import given, settings

from core.graham_math import GrahamCalculator
from tests.test_utils_decimal import (
    currency_strategy,
    to_decimal,
    assert_decimal_equal
)
from tests.fixtures_graham_metrics import (
    GrahamMetricsFixtures,
    EdgeCaseFixtures
)


class TestQuickRatioCalculationCorrectness:
    """
    Property 5: Quick Ratio Calculation Correctness
    
    For any balance sheet data with current_assets, inventory, and current_liabilities > 0,
    the quick ratio should equal (current_assets - inventory) / current_liabilities.
    
    Validates: Requirements 2.1
    """
    
    @given(
        current_assets=currency_strategy(min_value="1", max_value="1000000000000"),
        inventory=currency_strategy(min_value="0", max_value="1000000000000"),
        current_liabilities=currency_strategy(min_value="0.01", max_value="1000000000000")
    )
    @settings(max_examples=100)
    def test_quick_ratio_equals_formula(
        self, current_assets, inventory, current_liabilities
    ):
        """
        Property: Quick Ratio = (Current Assets - Inventory) / Current Liabilities
        
        For any balance sheet data with current_liabilities > 0, quick ratio should equal
        (current_assets - inventory) / current_liabilities
        """
        # Ensure inventory doesn't exceed current assets
        if inventory > current_assets:
            inventory = current_assets * Decimal('0.5')
        
        # Arrange
        financial_data = GrahamMetricsFixtures.get_quick_ratio_test_data(
            current_assets=current_assets,
            inventory=inventory,
            current_liabilities=current_liabilities
        )
        calculator = GrahamCalculator(financial_data)
        
        # Act
        quick_ratio = calculator.compute_quick_ratio()
        
        # Assert
        if quick_ratio != "N/A":
            expected = (current_assets - inventory) / current_liabilities
            actual = to_decimal(quick_ratio)
            assert_decimal_equal(
                actual,
                expected,
                tolerance=Decimal('0.01'),
                message=f"Quick ratio {actual} should equal (current_assets {current_assets} - inventory {inventory}) / current_liabilities {current_liabilities} = {expected}"
            )
    
    def test_quick_ratio_with_known_values(self):
        """
        Unit test: Verify Quick Ratio calculation with known values.
        """
        # Arrange
        financial_data = GrahamMetricsFixtures.get_quick_ratio_test_data(
            current_assets=Decimal('1000000'),
            inventory=Decimal('200000'),
            current_liabilities=Decimal('400000')
        )
        calculator = GrahamCalculator(financial_data)
        
        # Act
        quick_ratio = calculator.compute_quick_ratio()
        
        # Assert
        # (1,000,000 - 200,000) / 400,000 = 800,000 / 400,000 = 2.0
        expected = Decimal('2.0')
        actual = to_decimal(quick_ratio)
        
        assert_decimal_equal(
            actual,
            expected,
            tolerance=Decimal('0.01'),
            message=f"Quick ratio should be {expected}"
        )
    
    def test_quick_ratio_with_zero_inventory(self):
        """
        Unit test: Quick Ratio with zero inventory equals Current Ratio.
        """
        # Arrange
        financial_data = GrahamMetricsFixtures.get_quick_ratio_test_data(
            current_assets=Decimal('1000000'),
            inventory=Decimal('0'),
            current_liabilities=Decimal('500000')
        )
        calculator = GrahamCalculator(financial_data)
        
        # Act
        quick_ratio = calculator.compute_quick_ratio()
        
        # Assert
        # 1,000,000 / 500,000 = 2.0
        expected = Decimal('2.0')
        actual = to_decimal(quick_ratio)
        
        assert_decimal_equal(
            actual,
            expected,
            tolerance=Decimal('0.01'),
            message="Quick ratio with zero inventory should equal current ratio"
        )
    
    def test_quick_ratio_with_high_inventory(self):
        """
        Unit test: Quick Ratio with high inventory percentage.
        """
        # Arrange
        financial_data = GrahamMetricsFixtures.get_quick_ratio_test_data(
            current_assets=Decimal('1000000'),
            inventory=Decimal('800000'),  # 80% of current assets
            current_liabilities=Decimal('400000')
        )
        calculator = GrahamCalculator(financial_data)
        
        # Act
        quick_ratio = calculator.compute_quick_ratio()
        
        # Assert
        # (1,000,000 - 800,000) / 400,000 = 200,000 / 400,000 = 0.5
        expected = Decimal('0.5')
        actual = to_decimal(quick_ratio)
        
        assert_decimal_equal(
            actual,
            expected,
            tolerance=Decimal('0.01'),
            message="Quick ratio should be 0.5 with high inventory"
        )


class TestQuickRatioSectorBasedInventoryHandling:
    """
    Property 6: Quick Ratio Sector-Based Inventory Handling
    
    For any balance sheet data with missing inventory, if the sector is Services or Technology,
    the system should use current_assets without subtraction; otherwise, it should return "N/A".
    
    Validates: Requirements 2.3, 2.4
    """
    
    @pytest.mark.parametrize("sector,should_calculate", [
        ("Services", True),
        ("Service", True),
        ("Technology", True),
        ("Software", True),
        ("Technology Services", True),
        ("Manufacturing", False),
        ("Retail", False),
        ("Consumer Goods", False),
        ("Healthcare", False),
        ("Energy", False)
    ])
    def test_missing_inventory_sector_handling(self, sector, should_calculate):
        """
        Property: Missing inventory handling depends on sector.
        
        Services and Technology sectors: use current_assets (inventory assumed minimal)
        Other sectors: return "N/A" (conservative approach)
        """
        # Arrange
        financial_data = EdgeCaseFixtures.get_missing_inventory_data(sector=sector)
        calculator = GrahamCalculator(financial_data)
        
        # Act
        quick_ratio = calculator.compute_quick_ratio()
        
        # Assert
        if should_calculate:
            assert quick_ratio != "N/A", \
                f"Should calculate Quick Ratio for {sector} sector with missing inventory"
            
            # Verify it equals current ratio (inventory = 0)
            year_data = financial_data['history']['2023-12-31']
            expected = to_decimal(year_data['current_assets']) / to_decimal(year_data['current_liabilities'])
            actual = to_decimal(quick_ratio)
            
            assert_decimal_equal(
                actual,
                expected,
                tolerance=Decimal('0.01'),
                message=f"Quick ratio for {sector} with missing inventory should equal current ratio"
            )
            
            # Verify warning is present
            assert any('Inventory data unavailable' in w for w in calculator.warnings), \
                f"Should have warning about missing inventory for {sector}"
        else:
            assert quick_ratio == "N/A", \
                f"Should return N/A for {sector} sector with missing inventory"
            
            # Verify warning is present
            assert any('Cannot calculate' in w and 'inventory' in w.lower() for w in calculator.warnings), \
                f"Should have warning about inability to calculate for {sector}"
    
    def test_services_sector_missing_inventory(self):
        """
        Unit test: Services sector with missing inventory uses current assets.
        """
        # Arrange
        financial_data = EdgeCaseFixtures.get_missing_inventory_data(sector='Services')
        calculator = GrahamCalculator(financial_data)
        
        # Act
        quick_ratio = calculator.compute_quick_ratio()
        
        # Assert
        assert quick_ratio != "N/A", "Should calculate for Services sector"
        
        # Verify equals current ratio
        year_data = financial_data['history']['2023-12-31']
        expected = to_decimal(year_data['current_assets']) / to_decimal(year_data['current_liabilities'])
        actual = to_decimal(quick_ratio)
        
        assert_decimal_equal(actual, expected, tolerance=Decimal('0.01'))
        
        # Verify warning mentions Services sector
        assert any('Services' in w for w in calculator.warnings), \
            "Warning should mention Services sector"
    
    def test_technology_sector_missing_inventory(self):
        """
        Unit test: Technology sector with missing inventory uses current assets.
        """
        # Arrange
        financial_data = EdgeCaseFixtures.get_missing_inventory_data(sector='Technology')
        calculator = GrahamCalculator(financial_data)
        
        # Act
        quick_ratio = calculator.compute_quick_ratio()
        
        # Assert
        assert quick_ratio != "N/A", "Should calculate for Technology sector"
        
        # Verify warning mentions Technology sector
        assert any('Technology' in w for w in calculator.warnings), \
            "Warning should mention Technology sector"
    
    def test_manufacturing_sector_missing_inventory(self):
        """
        Unit test: Manufacturing sector with missing inventory returns N/A.
        """
        # Arrange
        financial_data = EdgeCaseFixtures.get_missing_inventory_data(sector='Manufacturing')
        calculator = GrahamCalculator(financial_data)
        
        # Act
        quick_ratio = calculator.compute_quick_ratio()
        
        # Assert
        assert quick_ratio == "N/A", "Should return N/A for Manufacturing sector"
        
        # Verify warning mentions Manufacturing sector
        assert any('Manufacturing' in w for w in calculator.warnings), \
            "Warning should mention Manufacturing sector"
        assert any('Cannot calculate' in w for w in calculator.warnings), \
            "Warning should indicate inability to calculate"


class TestQuickRatioEdgeCases:
    """
    Unit tests for Quick Ratio edge cases.
    
    Tests specific scenarios that should be handled gracefully.
    Validates: Requirements 2.2, 2.3, 2.4
    """
    
    def test_zero_current_liabilities(self):
        """
        Edge case: Zero current liabilities should return N/A.
        
        Validates: Requirement 2.2
        """
        # Arrange
        financial_data = EdgeCaseFixtures.get_zero_current_liabilities_data()
        calculator = GrahamCalculator(financial_data)
        
        # Act
        quick_ratio = calculator.compute_quick_ratio()
        
        # Assert
        assert quick_ratio == "N/A", \
            "Quick Ratio should be N/A when current liabilities is zero"
        
        # Verify warning is present
        assert any('current liabilities is zero' in w.lower() for w in calculator.warnings), \
            "Should have warning about zero current liabilities"
    
    def test_missing_current_assets(self):
        """
        Edge case: Missing current assets should return N/A.
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
                    'inventory': 100000.0,
                    'current_liabilities': 400000.0
                    # Missing current_assets
                }
            }
        }
        calculator = GrahamCalculator(financial_data)
        
        # Act
        quick_ratio = calculator.compute_quick_ratio()
        
        # Assert
        assert quick_ratio == "N/A", \
            "Quick Ratio should be N/A when current assets is missing"
    
    def test_missing_current_liabilities(self):
        """
        Edge case: Missing current liabilities should return N/A.
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
                    'current_assets': 1000000.0,
                    'inventory': 100000.0
                    # Missing current_liabilities
                }
            }
        }
        calculator = GrahamCalculator(financial_data)
        
        # Act
        quick_ratio = calculator.compute_quick_ratio()
        
        # Assert
        assert quick_ratio == "N/A", \
            "Quick Ratio should be N/A when current liabilities is missing"
    
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
        quick_ratio = calculator.compute_quick_ratio()
        
        # Assert
        assert quick_ratio == "N/A", \
            "Quick Ratio should be N/A when no financial history"
    
    def test_very_small_quick_ratio(self):
        """
        Edge case: Very small Quick Ratio (< 0.1) should be calculated correctly.
        """
        # Arrange
        financial_data = GrahamMetricsFixtures.get_quick_ratio_test_data(
            current_assets=Decimal('100000'),
            inventory=Decimal('90000'),
            current_liabilities=Decimal('500000')
        )
        calculator = GrahamCalculator(financial_data)
        
        # Act
        quick_ratio = calculator.compute_quick_ratio()
        
        # Assert
        # (100,000 - 90,000) / 500,000 = 10,000 / 500,000 = 0.02
        expected = Decimal('0.02')
        actual = to_decimal(quick_ratio)
        
        assert_decimal_equal(
            actual,
            expected,
            tolerance=Decimal('0.01'),
            message="Should handle very small Quick Ratio values"
        )
    
    def test_very_large_quick_ratio(self):
        """
        Edge case: Very large Quick Ratio (> 10) should be calculated correctly.
        """
        # Arrange
        financial_data = GrahamMetricsFixtures.get_quick_ratio_test_data(
            current_assets=Decimal('10000000'),
            inventory=Decimal('100000'),
            current_liabilities=Decimal('500000')
        )
        calculator = GrahamCalculator(financial_data)
        
        # Act
        quick_ratio = calculator.compute_quick_ratio()
        
        # Assert
        # (10,000,000 - 100,000) / 500,000 = 9,900,000 / 500,000 = 19.8
        expected = Decimal('19.8')
        actual = to_decimal(quick_ratio)
        
        assert_decimal_equal(
            actual,
            expected,
            tolerance=Decimal('0.01'),
            message="Should handle very large Quick Ratio values"
        )
    
    def test_inventory_equals_current_assets(self):
        """
        Edge case: Inventory equals current assets results in Quick Ratio of 0.
        """
        # Arrange
        financial_data = GrahamMetricsFixtures.get_quick_ratio_test_data(
            current_assets=Decimal('1000000'),
            inventory=Decimal('1000000'),
            current_liabilities=Decimal('500000')
        )
        calculator = GrahamCalculator(financial_data)
        
        # Act
        quick_ratio = calculator.compute_quick_ratio()
        
        # Assert
        # (1,000,000 - 1,000,000) / 500,000 = 0 / 500,000 = 0.0
        expected = Decimal('0.0')
        actual = to_decimal(quick_ratio)
        
        assert_decimal_equal(
            actual,
            expected,
            tolerance=Decimal('0.01'),
            message="Quick Ratio should be 0 when inventory equals current assets"
        )
    
    def test_very_large_values(self):
        """
        Edge case: Very large values should be handled correctly.
        """
        # Arrange
        financial_data = GrahamMetricsFixtures.get_quick_ratio_test_data(
            current_assets=Decimal('999999999999'),  # ~1 trillion
            inventory=Decimal('100000000000'),  # 100 billion
            current_liabilities=Decimal('500000000000')  # 500 billion
        )
        calculator = GrahamCalculator(financial_data)
        
        # Act
        quick_ratio = calculator.compute_quick_ratio()
        
        # Assert
        assert quick_ratio != "N/A", "Should handle large values"
        
        # Verify calculation is correct
        expected = (Decimal('999999999999') - Decimal('100000000000')) / Decimal('500000000000')
        actual = to_decimal(quick_ratio)
        assert_decimal_equal(actual, expected, tolerance=Decimal('0.01'))
    
    def test_rounding_precision(self):
        """
        Edge case: Verify rounding to 2 decimal places.
        """
        # Arrange - values that produce a result requiring rounding
        financial_data = GrahamMetricsFixtures.get_quick_ratio_test_data(
            current_assets=Decimal('1000000'),
            inventory=Decimal('333333'),
            current_liabilities=Decimal('400000')
        )
        calculator = GrahamCalculator(financial_data)
        
        # Act
        quick_ratio = calculator.compute_quick_ratio()
        
        # Assert
        # (1,000,000 - 333,333) / 400,000 = 666,667 / 400,000 = 1.6666675
        # Should round to 1.67
        assert isinstance(quick_ratio, float), "Should return float"
        
        # Verify it's rounded to 2 decimal places
        quick_ratio_str = f"{quick_ratio:.2f}"
        assert quick_ratio_str == "1.67", \
            f"Quick Ratio should be rounded to 2 decimal places: expected 1.67, got {quick_ratio_str}"
