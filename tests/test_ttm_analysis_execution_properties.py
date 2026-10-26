"""
Property-based tests for TTM analysis execution with semi-annual data.

Feature: ttm-semi-annual-gap-fix
Property 6: TTM Analysis Execution for Valid Semi-Annual Data

For any semi-annual data with 2 valid consecutive periods, the calculate_ttm_metrics()
method should return a non-empty dictionary containing TTM metrics.

Validates: Requirements 1.3
"""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, HealthCheck
from core.ttm_calculator import TTMCalculator


class TestTTMAnalysisExecution:
    """Property-based tests for TTM analysis execution with semi-annual data."""
    
    # Feature: ttm-semi-annual-gap-fix, Property 6: TTM Analysis Execution for Valid Semi-Annual Data
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=100)
    @given(
        interval_days=st.integers(min_value=150, max_value=210),
        h1_revenue=st.floats(min_value=1000.0, max_value=100000000000.0),
        h2_revenue=st.floats(min_value=1000.0, max_value=100000000000.0),
        h1_net_income=st.floats(min_value=-10000000000.0, max_value=50000000000.0),
        h2_net_income=st.floats(min_value=-10000000000.0, max_value=50000000000.0),
        total_equity=st.floats(min_value=1000000.0, max_value=1000000000000.0),
        shares=st.floats(min_value=1000000.0, max_value=10000000000.0),
    )
    def test_valid_semi_annual_data_produces_ttm_metrics(
        self, interval_days, h1_revenue, h2_revenue, h1_net_income, h2_net_income,
        total_equity, shares
    ):
        """
        Property: For any semi-annual data with 2 valid consecutive periods (150-210 days apart),
        calculate_ttm_metrics() should return a non-empty dictionary with all expected keys.
        
        **Validates: Requirements 1.3**
        """
        # Arrange: Create semi-annual data with valid interval
        most_recent_date = datetime(2025, 6, 30)
        older_date = most_recent_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': {
                most_recent_date.strftime('%Y-%m-%d'): {
                    'revenue': h1_revenue,
                    'net_income': h1_net_income
                },
                older_date.strftime('%Y-%m-%d'): {
                    'revenue': h2_revenue,
                    'net_income': h2_net_income
                },
            },
            'balance_sheet': {
                most_recent_date.strftime('%Y-%m-%d'): {
                    'total_equity': total_equity,
                    'shares_outstanding': shares,
                    'intangible_assets': 100.0,
                    'goodwill': 200.0,
                    'current_assets': 5000.0,
                    'total_liabilities': 3000.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        ttm_metrics = calculator.calculate_ttm_metrics()
        
        # Assert: Should return non-empty dict with all expected keys
        assert ttm_metrics != {}, \
            f"TTM metrics should not be empty for valid semi-annual data (interval: {interval_days} days)"
        
        # Verify all required keys are present
        required_keys = [
            'ttm_revenue', 'ttm_net_income', 'ttm_eps',
            'total_equity', 'intangible_assets', 'goodwill',
            'current_assets', 'total_liabilities', 'shares_outstanding',
            'reporting_frequency', 'periods_used', 'date_range'
        ]
        
        for key in required_keys:
            assert key in ttm_metrics, \
                f"TTM metrics missing required key: {key}"
        
        # Verify frequency is detected as semi-annual
        assert ttm_metrics['reporting_frequency'] == 'semi-annual', \
            f"Frequency should be 'semi-annual', got '{ttm_metrics['reporting_frequency']}'"
        
        # Verify 2 periods were used
        assert len(ttm_metrics['periods_used']) == 2, \
            f"Should use 2 periods for semi-annual, got {len(ttm_metrics['periods_used'])}"
        
        # Verify TTM revenue is sum of both periods
        expected_revenue = h1_revenue + h2_revenue
        assert abs(ttm_metrics['ttm_revenue'] - expected_revenue) < 0.01, \
            f"TTM revenue {ttm_metrics['ttm_revenue']} != sum {expected_revenue}"
        
        # Verify TTM net income is sum of both periods
        expected_net_income = h1_net_income + h2_net_income
        assert abs(ttm_metrics['ttm_net_income'] - expected_net_income) < 0.01, \
            f"TTM net income {ttm_metrics['ttm_net_income']} != sum {expected_net_income}"
        
        # Verify TTM EPS is calculated correctly
        expected_eps = expected_net_income / shares
        assert abs(ttm_metrics['ttm_eps'] - expected_eps) < 0.01, \
            f"TTM EPS {ttm_metrics['ttm_eps']} != expected {expected_eps}"
    
    # Feature: ttm-semi-annual-gap-fix, Property 6: TTM Analysis Execution for Valid Semi-Annual Data
    @settings(max_examples=50)
    @given(
        interval_days=st.integers(min_value=150, max_value=210),
    )
    def test_semi_annual_data_within_detection_range_produces_metrics(self, interval_days):
        """
        Property: Semi-annual data with intervals within detection range (150-210 days)
        should produce TTM metrics without gap warnings.
        
        **Validates: Requirements 1.3**
        """
        # Arrange: Create semi-annual data with interval within tolerance
        most_recent_date = datetime(2025, 6, 30)
        older_date = most_recent_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': {
                most_recent_date.strftime('%Y-%m-%d'): {
                    'revenue': 50000000.0,
                    'net_income': 5000000.0
                },
                older_date.strftime('%Y-%m-%d'): {
                    'revenue': 55000000.0,
                    'net_income': 5500000.0
                },
            },
            'balance_sheet': {
                most_recent_date.strftime('%Y-%m-%d'): {
                    'total_equity': 100000000.0,
                    'shares_outstanding': 10000000.0,
                    'intangible_assets': 5000000.0,
                    'goodwill': 3000000.0,
                    'current_assets': 60000000.0,
                    'total_liabilities': 40000000.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        ttm_metrics = calculator.calculate_ttm_metrics()
        
        # Assert: Should return non-empty dict
        assert ttm_metrics != {}, \
            f"TTM metrics should not be empty for interval {interval_days} days (within tolerance)"
        
        # Verify no gap warnings
        gap_warnings = [w for w in calculator.warnings if 'gap' in w.lower() or 'missing' in w.lower()]
        assert len(gap_warnings) == 0, \
            f"Should not have gap warnings for interval {interval_days} days, but got: {gap_warnings}"
    
    def test_aep_lse_pattern_produces_metrics(self):
        """
        Unit test: Verify AEP.LSE pattern (actual semi-annual reporter) produces TTM metrics.
        
        **Validates: Requirements 1.3**
        """
        # Arrange: AEP.LSE pattern with actual reporting dates
        quarterly_data = {
            'income_statement': {
                '2025-06-30': {'revenue': 50000000.0, 'net_income': 5000000.0},  # H1 2025
                '2024-12-31': {'revenue': 55000000.0, 'net_income': 5500000.0},  # FY 2024
                '2024-06-30': {'revenue': 48000000.0, 'net_income': 4800000.0},  # H1 2024
                '2023-12-31': {'revenue': 52000000.0, 'net_income': 5200000.0},  # FY 2023
            },
            'balance_sheet': {
                '2025-06-30': {
                    'total_equity': 100000000.0,
                    'intangible_assets': 5000000.0,
                    'goodwill': 3000000.0,
                    'current_assets': 60000000.0,
                    'total_liabilities': 40000000.0,
                    'shares_outstanding': 10000000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        ttm_metrics = calculator.calculate_ttm_metrics()
        
        # Assert
        assert ttm_metrics != {}, "AEP.LSE pattern should produce TTM metrics"
        assert ttm_metrics['reporting_frequency'] == 'semi-annual'
        assert len(ttm_metrics['periods_used']) == 2
        assert ttm_metrics['periods_used'] == ['2025-06-30', '2024-12-31']
        
        # Verify calculations
        expected_revenue = 50000000.0 + 55000000.0
        assert abs(ttm_metrics['ttm_revenue'] - expected_revenue) < 0.01
        
        expected_net_income = 5000000.0 + 5500000.0
        assert abs(ttm_metrics['ttm_net_income'] - expected_net_income) < 0.01
        
        expected_eps = expected_net_income / 10000000.0
        assert abs(ttm_metrics['ttm_eps'] - expected_eps) < 0.01
    
    def test_mpe_lse_pattern_produces_metrics(self):
        """
        Unit test: Verify MPE.LSE pattern (actual semi-annual reporter) produces TTM metrics.
        
        **Validates: Requirements 1.3**
        """
        # Arrange: MPE.LSE pattern with actual reporting dates
        quarterly_data = {
            'income_statement': {
                '2025-06-30': {'revenue': 30000000.0, 'net_income': 3000000.0},  # H1 2025
                '2024-12-31': {'revenue': 35000000.0, 'net_income': 3500000.0},  # FY 2024
                '2024-06-30': {'revenue': 28000000.0, 'net_income': 2800000.0},  # H1 2024
            },
            'balance_sheet': {
                '2025-06-30': {
                    'total_equity': 80000000.0,
                    'intangible_assets': 4000000.0,
                    'goodwill': 2000000.0,
                    'current_assets': 50000000.0,
                    'total_liabilities': 30000000.0,
                    'shares_outstanding': 8000000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        ttm_metrics = calculator.calculate_ttm_metrics()
        
        # Assert
        assert ttm_metrics != {}, "MPE.LSE pattern should produce TTM metrics"
        assert ttm_metrics['reporting_frequency'] == 'semi-annual'
        assert len(ttm_metrics['periods_used']) == 2
        assert ttm_metrics['periods_used'] == ['2025-06-30', '2024-12-31']
        
        # Verify calculations
        expected_revenue = 30000000.0 + 35000000.0
        assert abs(ttm_metrics['ttm_revenue'] - expected_revenue) < 0.01
        
        expected_net_income = 3000000.0 + 3500000.0
        assert abs(ttm_metrics['ttm_net_income'] - expected_net_income) < 0.01
        
        expected_eps = expected_net_income / 8000000.0
        assert abs(ttm_metrics['ttm_eps'] - expected_eps) < 0.01


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
