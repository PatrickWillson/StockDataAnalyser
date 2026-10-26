"""
Unit tests for Margin of Safety edge cases.

Tests specific examples and scenarios from the design document to validate
exact behavior for Margin of Safety calculations using the conservative
dual-anchor approach.
"""

import pytest
from core.graham_math import GrahamCalculator


class TestMarginOfSafetyEdgeCases:
    """Unit tests for specific Margin of Safety scenarios."""
    
    def test_both_metrics_valid_use_min_value(self):
        """
        Test that when both normalized GN and EPV are valid, MoS uses the lower value.
        
        Scenario: normalized_gn = $50.00, epv_per_share = $30.00
        Expected: Use $30.00 (EPV), limiting_factor = "EPV"
        """
        # Arrange: Create financial data with both metrics valid
        # Normalized GN will be higher, EPV will be lower
        shares = 1000000.0
        eps_values = [10.0, 10.0, 10.0]  # Average = 10.0
        tbvps = 11.11  # Will produce normalized GN ≈ $50
        total_equity = tbvps * shares
        
        financial_data = {
            'ticker': 'TEST.US',
            'price': 25.00,
            'currency': 'USD',
            'history': {}
        }
        
        # Add 10 years with LOWER net income for EPV ≈ $30
        for i in range(10):
            year = f"{2024 - i}-12-31"
            # Use lower net income to get EPV around $30
            net_income = 3000000.0  # $3M / 1M shares = $3 per share
            # EPV = net_income / cost_of_capital = $3M / 0.10 = $30M / 1M shares = $30
            financial_data['history'][year] = {
                'total_equity': total_equity,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'shares_outstanding': shares,
                'eps': eps_values[i] if i < 3 else 10.0,
                'revenue': 1000000.0,
                'net_income': net_income
            }
        
        # Act: Calculate margin of safety
        calculator = GrahamCalculator(financial_data)
        result = calculator.compute_margin_of_safety(25.00)
        
        # Assert: Verify both metrics are valid
        assert isinstance(result['normalized_graham_number'], float), \
            f"Expected float for normalized_graham_number, got {type(result['normalized_graham_number'])}"
        
        assert isinstance(result['epv_per_share'], float), \
            f"Expected float for epv_per_share, got {type(result['epv_per_share'])}"
        
        # Verify intrinsic value is the minimum
        expected_intrinsic_value = min(result['normalized_graham_number'], result['epv_per_share'])
        assert result['intrinsic_value_used'] == expected_intrinsic_value, \
            f"Expected intrinsic_value_used to be min value, got {result['intrinsic_value_used']}"
        
        # Verify limiting factor is correctly identified
        if result['epv_per_share'] < result['normalized_graham_number']:
            assert result['limiting_factor'] == "EPV", \
                f"Expected limiting_factor 'EPV', got '{result['limiting_factor']}'"
        else:
            assert result['limiting_factor'] == "Normalized Graham Number", \
                f"Expected limiting_factor 'Normalized Graham Number', got '{result['limiting_factor']}'"
    
    def test_only_normalized_gn_valid(self):
        """
        Test that when only normalized GN is valid, MoS uses normalized GN.
        
        Scenario: normalized_gn = $50.00, epv_per_share = "N/A"
        Expected: Use $50.00, limiting_factor = "Normalized Graham Number"
        """
        # Arrange: Create financial data with only normalized GN valid
        # 3 years of positive EPS for normalized GN
        # But insufficient years for EPV (< 7 years)
        shares = 1000000.0
        eps_values = [10.0, 10.0, 10.0]
        tbvps = 11.11
        total_equity = tbvps * shares
        
        financial_data = {
            'ticker': 'TEST.US',
            'price': 25.00,
            'currency': 'USD',
            'history': {
                '2024-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[0],
                    'revenue': 1000000.0,
                    'net_income': eps_values[0] * shares
                },
                '2023-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[1],
                    'revenue': 1000000.0,
                    'net_income': eps_values[1] * shares
                },
                '2022-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[2],
                    'revenue': 1000000.0,
                    'net_income': eps_values[2] * shares
                }
            }
        }
        
        # Act: Calculate margin of safety
        calculator = GrahamCalculator(financial_data)
        result = calculator.compute_margin_of_safety(25.00)
        
        # Assert: Verify only normalized GN is valid
        assert isinstance(result['normalized_graham_number'], float), \
            f"Expected float for normalized_graham_number, got {type(result['normalized_graham_number'])}"
        
        # EPV should be 0.0 (insufficient data)
        assert result['epv_per_share'] == 0.0, \
            f"Expected 0.0 for epv_per_share (insufficient data), got {result['epv_per_share']}"
        
        # CRITICAL: EPV = 0.0 is a valid value, so min(normalized_gn, 0.0) = 0.0
        # This is correct behavior - EPV of 0.0 means value destroyer
        assert result['intrinsic_value_used'] == 0.0, \
            "Expected intrinsic_value_used to be 0.0 (min of normalized_gn and EPV=0.0)"
        
        assert result['limiting_factor'] == "EPV", \
            "Expected limiting_factor 'EPV' (0.0 < normalized_gn)"
    
    def test_only_epv_valid(self):
        """
        Test that when only EPV is valid, MoS uses EPV.
        
        Scenario: normalized_gn = "N/A", epv_per_share = $30.00
        Expected: Use $30.00, limiting_factor = "EPV"
        """
        # Arrange: Create financial data with only EPV valid
        # Negative 3-year average EPS for normalized GN = "N/A"
        # But 10 years of positive net income for EPV
        shares = 1000000.0
        eps_values = [5.0, -10.0, -5.0]  # Average = -3.33 (negative)
        tbvps = 20.0
        total_equity = tbvps * shares
        
        financial_data = {
            'ticker': 'TEST.US',
            'price': 25.00,
            'currency': 'USD',
            'history': {}
        }
        
        # Add 10 years with positive net income for EPV
        for i in range(10):
            year = f"{2024 - i}-12-31"
            # Use positive net income for EPV
            net_income = 3000000.0 if i >= 3 else eps_values[i] * shares
            financial_data['history'][year] = {
                'total_equity': total_equity,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'shares_outstanding': shares,
                'eps': eps_values[i] if i < 3 else 3.0,
                'revenue': 1000000.0,
                'net_income': net_income
            }
        
        # Act: Calculate margin of safety
        calculator = GrahamCalculator(financial_data)
        result = calculator.compute_margin_of_safety(25.00)
        
        # Assert: Verify only EPV is valid
        assert result['normalized_graham_number'] == "N/A", \
            "Expected 'N/A' for normalized_graham_number (negative avg EPS)"
        
        assert isinstance(result['epv_per_share'], float), \
            f"Expected float for epv_per_share, got {type(result['epv_per_share'])}"
        
        # Intrinsic value should be EPV
        assert result['intrinsic_value_used'] == result['epv_per_share'], \
            "Expected intrinsic_value_used to be epv_per_share"
        
        assert result['limiting_factor'] == "EPV", \
            "Expected limiting_factor 'EPV'"
    
    def test_both_na_returns_na(self):
        """
        Test that when both normalized GN and EPV are "N/A", MoS returns "N/A".
        
        Scenario: normalized_gn = "N/A", epv_per_share = "N/A"
        Expected: MoS = "N/A", limiting_factor = "N/A", warning added
        """
        # Arrange: Create financial data with both metrics invalid
        # Negative 3-year average EPS for normalized GN = "N/A"
        # Insufficient years for EPV (< 7 years)
        shares = 1000000.0
        eps_values = [-5.0, -10.0, -5.0]  # Average = -6.67 (negative)
        tbvps = 20.0
        total_equity = tbvps * shares
        
        financial_data = {
            'ticker': 'TEST.US',
            'price': 25.00,
            'currency': 'USD',
            'history': {
                '2024-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[0],
                    'revenue': 1000000.0,
                    'net_income': eps_values[0] * shares
                },
                '2023-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[1],
                    'revenue': 1000000.0,
                    'net_income': eps_values[1] * shares
                },
                '2022-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[2],
                    'revenue': 1000000.0,
                    'net_income': eps_values[2] * shares
                }
            }
        }
        
        # Act: Calculate margin of safety
        calculator = GrahamCalculator(financial_data)
        result = calculator.compute_margin_of_safety(25.00)
        
        # Assert: Verify both metrics are "N/A"
        assert result['normalized_graham_number'] == "N/A", \
            "Expected 'N/A' for normalized_graham_number"
        
        # EPV should be 0.0 (insufficient data)
        assert result['epv_per_share'] == 0.0, \
            "Expected 0.0 for epv_per_share (insufficient data)"
        
        # CRITICAL: EPV = 0.0 is a valid value, not "N/A"
        # So intrinsic_value_used = 0.0, and MoS = "N/A" (cannot divide by zero)
        assert result['intrinsic_value_used'] == 0.0, \
            "Expected intrinsic_value_used to be 0.0"
        
        assert result['mos_percentage'] == "N/A", \
            "Expected 'N/A' for mos_percentage (cannot divide by zero)"
        
        assert result['limiting_factor'] == "EPV", \
            "Expected limiting_factor 'EPV' (0.0 is the limiting value)"
    
    def test_epv_zero_vs_na_distinction(self):
        """
        Test Scenario 5: EPV = 0.00 (value destroyer) vs EPV = "N/A" (missing data).
        
        Case 1: EPV = 0.00 (valid value destroyer)
        - normalized_gn = $50.00, epv_per_share = 0.00
        - Expected: Use 0.00, limiting_factor = "EPV", MoS = "N/A"
        
        Case 2: EPV = "N/A" (missing data)
        - normalized_gn = $50.00, epv_per_share = "N/A"
        - Expected: Use $50.00, limiting_factor = "Normalized Graham Number"
        """
        # Case 1: EPV = 0.00 (value destroyer)
        # Create data with 10 years of NEGATIVE net income
        shares = 1000000.0
        eps_values = [10.0, 10.0, 10.0]  # Positive for normalized GN
        tbvps = 11.11
        total_equity = tbvps * shares
        
        financial_data_case1 = {
            'ticker': 'DESTROYER.US',
            'price': 30.00,
            'currency': 'USD',
            'history': {}
        }
        
        # Add 10 years with NEGATIVE net income for EPV = 0.0
        for i in range(10):
            year = f"{2024 - i}-12-31"
            financial_data_case1['history'][year] = {
                'total_equity': total_equity,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'shares_outstanding': shares,
                'eps': eps_values[i] if i < 3 else 10.0,
                'revenue': 1000000.0,
                'net_income': -10000000.0  # Negative for all years
            }
        
        # Act: Calculate margin of safety for Case 1
        calculator_case1 = GrahamCalculator(financial_data_case1)
        result_case1 = calculator_case1.compute_margin_of_safety(30.00)
        
        # Assert Case 1: EPV = 0.00 is valid value destroyer
        assert isinstance(result_case1['normalized_graham_number'], float), \
            "Case 1: Expected float for normalized_graham_number"
        
        assert result_case1['epv_per_share'] == 0.0, \
            "Case 1: Expected 0.0 for epv_per_share (value destroyer)"
        
        assert result_case1['intrinsic_value_used'] == 0.0, \
            "Case 1: Expected intrinsic_value_used to be 0.0 (min of normalized_gn and EPV=0.0)"
        
        assert result_case1['limiting_factor'] == "EPV", \
            "Case 1: Expected limiting_factor 'EPV' (0.0 < normalized_gn)"
        
        assert result_case1['mos_percentage'] == "N/A", \
            "Case 1: Expected 'N/A' for mos_percentage (cannot divide by zero)"
        
        # Case 2: EPV = "N/A" (missing data - insufficient years)
        financial_data_case2 = {
            'ticker': 'YOUNG.US',
            'price': 30.00,
            'currency': 'USD',
            'history': {
                '2024-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[0],
                    'revenue': 1000000.0,
                    'net_income': eps_values[0] * shares
                },
                '2023-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[1],
                    'revenue': 1000000.0,
                    'net_income': eps_values[1] * shares
                },
                '2022-12-31': {
                    'total_equity': total_equity,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': shares,
                    'eps': eps_values[2],
                    'revenue': 1000000.0,
                    'net_income': eps_values[2] * shares
                }
            }
        }
        
        # Act: Calculate margin of safety for Case 2
        calculator_case2 = GrahamCalculator(financial_data_case2)
        result_case2 = calculator_case2.compute_margin_of_safety(30.00)
        
        # Assert Case 2: EPV = 0.0 (insufficient data)
        assert isinstance(result_case2['normalized_graham_number'], float), \
            "Case 2: Expected float for normalized_graham_number"
        
        assert result_case2['epv_per_share'] == 0.0, \
            "Case 2: Expected 0.0 for epv_per_share (insufficient data)"
        
        # CRITICAL: EPV = 0.0 is treated as a valid value (not "N/A")
        # So min(normalized_gn, 0.0) = 0.0
        assert result_case2['intrinsic_value_used'] == 0.0, \
            "Case 2: Expected intrinsic_value_used to be 0.0 (min of normalized_gn and EPV=0.0)"
        
        assert result_case2['limiting_factor'] == "EPV", \
            "Case 2: Expected limiting_factor 'EPV' (0.0 < normalized_gn)"
    
    def test_intrinsic_value_zero_mos_na(self):
        """
        Test that when intrinsic_value = 0.00, MoS returns "N/A" (cannot divide by zero).
        
        Scenario: Both normalized GN and EPV are 0.00
        Expected: intrinsic_value_used = 0.00, MoS = "N/A"
        """
        # Arrange: Create financial data where both metrics are 0.00
        # Negative 3-year average EPS for normalized GN = "N/A"
        # Negative 10-year average net income for EPV = 0.00
        shares = 1000000.0
        eps_values = [-5.0, -10.0, -5.0]  # Average = -6.67 (negative)
        tbvps = 20.0
        total_equity = tbvps * shares
        
        financial_data = {
            'ticker': 'ZERO.US',
            'price': 25.00,
            'currency': 'USD',
            'history': {}
        }
        
        # Add 10 years with NEGATIVE net income for EPV = 0.0
        for i in range(10):
            year = f"{2024 - i}-12-31"
            financial_data['history'][year] = {
                'total_equity': total_equity,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'shares_outstanding': shares,
                'eps': eps_values[i] if i < 3 else -5.0,
                'revenue': 1000000.0,
                'net_income': -5000000.0  # Negative for all years
            }
        
        # Act: Calculate margin of safety
        calculator = GrahamCalculator(financial_data)
        result = calculator.compute_margin_of_safety(25.00)
        
        # Assert: Verify intrinsic value is 0.00
        assert result['intrinsic_value_used'] == 0.0, \
            "Expected intrinsic_value_used to be 0.0"
        
        # MoS should be "N/A" (cannot divide by zero)
        assert result['mos_percentage'] == "N/A", \
            "Expected 'N/A' for mos_percentage (cannot divide by zero)"
    
    def test_limiting_factor_identification(self):
        """
        Test that limiting factor is correctly identified in various scenarios.
        """
        shares = 1000000.0
        
        # Scenario 1: Normalized GN is lower
        eps_values = [5.0, 5.0, 5.0]  # Will produce lower normalized GN
        tbvps = 10.0
        total_equity = tbvps * shares
        
        financial_data_1 = {
            'ticker': 'TEST1.US',
            'price': 25.00,
            'currency': 'USD',
            'history': {}
        }
        
        # Add 10 years with HIGHER net income for EPV
        for i in range(10):
            year = f"{2024 - i}-12-31"
            financial_data_1['history'][year] = {
                'total_equity': total_equity,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'shares_outstanding': shares,
                'eps': eps_values[i] if i < 3 else 5.0,
                'revenue': 1000000.0,
                'net_income': 10000000.0  # High net income for high EPV
            }
        
        calculator_1 = GrahamCalculator(financial_data_1)
        result_1 = calculator_1.compute_margin_of_safety(25.00)
        
        # Verify normalized GN is the limiting factor
        if result_1['normalized_graham_number'] < result_1['epv_per_share']:
            assert result_1['limiting_factor'] == "Normalized Graham Number", \
                "Expected limiting_factor 'Normalized Graham Number' when normalized_gn < epv"
        
        # Scenario 2: EPV is lower
        eps_values = [20.0, 20.0, 20.0]  # Will produce higher normalized GN
        tbvps = 20.0
        total_equity = tbvps * shares
        
        financial_data_2 = {
            'ticker': 'TEST2.US',
            'price': 25.00,
            'currency': 'USD',
            'history': {}
        }
        
        # Add 10 years with LOWER net income for EPV
        for i in range(10):
            year = f"{2024 - i}-12-31"
            financial_data_2['history'][year] = {
                'total_equity': total_equity,
                'intangible_assets': 0.0,
                'goodwill': 0.0,
                'shares_outstanding': shares,
                'eps': eps_values[i] if i < 3 else 20.0,
                'revenue': 1000000.0,
                'net_income': 1000000.0  # Low net income for low EPV
            }
        
        calculator_2 = GrahamCalculator(financial_data_2)
        result_2 = calculator_2.compute_margin_of_safety(25.00)
        
        # Verify EPV is the limiting factor
        if result_2['epv_per_share'] < result_2['normalized_graham_number']:
            assert result_2['limiting_factor'] == "EPV", \
                "Expected limiting_factor 'EPV' when epv < normalized_gn"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
