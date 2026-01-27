"""
Property-based tests for semi-annual gap detection in TTMCalculator.

Feature: ttm-semi-annual-gap-fix
Property 2: Semi-Annual Gap Detection Tolerance
Property 3: Actual Gap Detection for Semi-Annual

For any sequence of semi-annual periods where all consecutive intervals are within
135-225 days (180 ± 45 days tolerance), gap detection should return False.
For sequences where at least one interval exceeds 270 days, gap detection should
return True and identify the specific gap location.

Validates: Requirements 2.1, 2.2, 2.3, 2.4
"""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, assume, settings
from core.ttm_calculator import TTMCalculator


class TestSemiAnnualGapDetectionProperties:
    """Property-based tests for semi-annual gap detection."""
    
    # Feature: ttm-semi-annual-gap-fix, Property 2: Semi-Annual Gap Detection Tolerance
    @given(
        num_periods=st.integers(min_value=2, max_value=6),
        interval_days=st.integers(min_value=135, max_value=225)
    )
    @settings(max_examples=100)
    def test_valid_semi_annual_intervals_no_gaps(self, num_periods, interval_days):
        """
        Property 2: Semi-Annual Gap Detection Tolerance
        
        For any sequence of semi-annual periods where all consecutive intervals
        are within 135-225 days (180 ± 45 days tolerance), gap detection should
        return False and not flag any gaps.
        
        **Validates: Requirements 2.1, 2.2, 2.4**
        """
        # Arrange: Generate periods with valid semi-annual intervals
        periods = {}
        current_date = datetime(2025, 6, 30)
        
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            periods[date_str] = {'revenue': 2000.0, 'net_income': 200.0}
            # Move back by interval_days for next period
            current_date = current_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {
                '2025-06-30': {
                    'total_equity': 100000.0,
                    'intangible_assets': 5000.0,
                    'goodwill': 3000.0,
                    'current_assets': 60000.0,
                    'total_liabilities': 40000.0,
                    'shares_outstanding': 10000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Get sorted periods for gap detection
        sorted_periods = sorted(periods.keys(), reverse=True)
        
        # Act: Run gap detection with semi-annual frequency
        gaps_detected = calculator._detect_data_gaps(sorted_periods, 'semi-annual')
        
        # Assert: No gaps should be detected for valid intervals
        assert gaps_detected is False, (
            f"Expected no gaps for {interval_days}-day intervals (within 135-225 range), "
            f"but gaps were detected. Periods: {sorted_periods}, Warnings: {calculator.warnings}"
        )
        
        # Should not have gap warnings
        gap_warnings = [w for w in calculator.warnings if 'gaps' in w.lower()]
        assert len(gap_warnings) == 0, (
            f"Expected no gap warnings for valid semi-annual intervals, got: {gap_warnings}"
        )
    
    # Feature: ttm-semi-annual-gap-fix, Property 2: Semi-Annual Gap Detection Tolerance
    @given(
        num_periods=st.integers(min_value=2, max_value=6),
        base_interval=st.integers(min_value=150, max_value=210)
    )
    @settings(max_examples=100)
    def test_consistent_semi_annual_intervals_no_gaps(self, num_periods, base_interval):
        """
        Property 2: Semi-Annual Gap Detection Tolerance (variant)
        
        For any sequence of semi-annual periods with consistent intervals in the
        150-210 day range (typical semi-annual), gap detection should return False.
        
        **Validates: Requirements 2.1, 2.2, 2.4**
        """
        # Arrange: Generate periods with consistent semi-annual intervals
        periods = {}
        current_date = datetime(2025, 6, 30)
        
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            periods[date_str] = {'revenue': 2000.0, 'net_income': 200.0}
            # Move back by base_interval for next period
            current_date = current_date - timedelta(days=base_interval)
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {
                '2025-06-30': {
                    'total_equity': 100000.0,
                    'intangible_assets': 5000.0,
                    'goodwill': 3000.0,
                    'current_assets': 60000.0,
                    'total_liabilities': 40000.0,
                    'shares_outstanding': 10000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Get sorted periods for gap detection
        sorted_periods = sorted(periods.keys(), reverse=True)
        
        # Act: Run gap detection with semi-annual frequency
        gaps_detected = calculator._detect_data_gaps(sorted_periods, 'semi-annual')
        
        # Assert: No gaps should be detected
        assert gaps_detected is False, (
            f"Expected no gaps for consistent {base_interval}-day intervals, "
            f"but gaps were detected. Periods: {sorted_periods}"
        )
    
    # Feature: ttm-semi-annual-gap-fix, Property 3: Actual Gap Detection for Semi-Annual
    @given(
        gap_interval=st.integers(min_value=270, max_value=400),
        before_gap_interval=st.integers(min_value=150, max_value=210),
        after_gap_interval=st.integers(min_value=150, max_value=210)
    )
    @settings(max_examples=100)
    def test_actual_gap_detected_for_semi_annual(self, gap_interval, before_gap_interval, after_gap_interval):
        """
        Property 3: Actual Gap Detection for Semi-Annual
        
        For any sequence of semi-annual periods where at least one interval exceeds
        270 days (indicating a missing period), gap detection should return True
        and identify the specific gap location.
        
        **Validates: Requirements 2.3**
        """
        # Arrange: Generate periods with an actual gap
        periods = {}
        current_date = datetime(2025, 6, 30)
        
        # Add first period
        periods[current_date.strftime('%Y-%m-%d')] = {'revenue': 2000.0, 'net_income': 200.0}
        
        # Add second period (normal interval)
        current_date = current_date - timedelta(days=before_gap_interval)
        periods[current_date.strftime('%Y-%m-%d')] = {'revenue': 2000.0, 'net_income': 200.0}
        
        # Add third period (with gap - large interval)
        current_date = current_date - timedelta(days=gap_interval)
        periods[current_date.strftime('%Y-%m-%d')] = {'revenue': 2000.0, 'net_income': 200.0}
        
        # Add fourth period (normal interval)
        current_date = current_date - timedelta(days=after_gap_interval)
        periods[current_date.strftime('%Y-%m-%d')] = {'revenue': 2000.0, 'net_income': 200.0}
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {
                '2025-06-30': {
                    'total_equity': 100000.0,
                    'intangible_assets': 5000.0,
                    'goodwill': 3000.0,
                    'current_assets': 60000.0,
                    'total_liabilities': 40000.0,
                    'shares_outstanding': 10000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Get sorted periods for gap detection
        sorted_periods = sorted(periods.keys(), reverse=True)
        
        # Act: Run gap detection with semi-annual frequency
        gaps_detected = calculator._detect_data_gaps(sorted_periods, 'semi-annual')
        
        # Assert: Gap should be detected
        assert gaps_detected is True, (
            f"Expected gap to be detected for {gap_interval}-day interval (> 270 days), "
            f"but no gap was detected. Periods: {sorted_periods}"
        )
        
        # Should have gap warning
        gap_warnings = [w for w in calculator.warnings if 'gaps' in w.lower() or 'missing' in w.lower()]
        assert len(gap_warnings) > 0, (
            f"Expected gap warning for {gap_interval}-day interval, but got no warnings. "
            f"All warnings: {calculator.warnings}"
        )
    
    # Feature: ttm-semi-annual-gap-fix, Property 3: Actual Gap Detection for Semi-Annual
    @given(
        num_valid_periods=st.integers(min_value=2, max_value=4),
        valid_interval=st.integers(min_value=150, max_value=210),
        gap_interval=st.integers(min_value=300, max_value=500)
    )
    @settings(max_examples=100)
    def test_gap_detection_with_multiple_valid_periods(self, num_valid_periods, valid_interval, gap_interval):
        """
        Property 3: Actual Gap Detection for Semi-Annual (variant)
        
        For any sequence with multiple valid semi-annual periods followed by a gap,
        gap detection should correctly identify the gap while not flagging the
        valid periods.
        
        **Validates: Requirements 2.3**
        """
        # Arrange: Generate periods with valid intervals followed by a gap
        periods = {}
        current_date = datetime(2025, 6, 30)
        
        # Add valid periods
        for i in range(num_valid_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            periods[date_str] = {'revenue': 2000.0, 'net_income': 200.0}
            current_date = current_date - timedelta(days=valid_interval)
        
        # Add period after gap
        current_date = current_date - timedelta(days=gap_interval)
        periods[current_date.strftime('%Y-%m-%d')] = {'revenue': 2000.0, 'net_income': 200.0}
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {
                '2025-06-30': {
                    'total_equity': 100000.0,
                    'intangible_assets': 5000.0,
                    'goodwill': 3000.0,
                    'current_assets': 60000.0,
                    'total_liabilities': 40000.0,
                    'shares_outstanding': 10000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Get sorted periods for gap detection
        sorted_periods = sorted(periods.keys(), reverse=True)
        
        # Act: Run gap detection with semi-annual frequency
        gaps_detected = calculator._detect_data_gaps(sorted_periods, 'semi-annual')
        
        # Assert: Gap should be detected
        assert gaps_detected is True, (
            f"Expected gap to be detected for {gap_interval}-day interval, "
            f"but no gap was detected. Periods: {sorted_periods}"
        )
    
    # Feature: ttm-semi-annual-gap-fix, Property 2: Semi-Annual Gap Detection Tolerance
    @given(
        interval_days=st.integers(min_value=135, max_value=225)
    )
    @settings(max_examples=100)
    def test_edge_case_two_periods_no_gap(self, interval_days):
        """
        Property 2: Semi-Annual Gap Detection Tolerance (edge case)
        
        For exactly 2 semi-annual periods with interval within tolerance,
        gap detection should return False.
        
        **Validates: Requirements 2.1, 2.2, 2.4**
        """
        # Arrange: Generate exactly 2 periods
        periods = {
            '2025-06-30': {'revenue': 2000.0, 'net_income': 200.0},
            (datetime(2025, 6, 30) - timedelta(days=interval_days)).strftime('%Y-%m-%d'): 
                {'revenue': 2000.0, 'net_income': 200.0}
        }
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {
                '2025-06-30': {
                    'total_equity': 100000.0,
                    'intangible_assets': 5000.0,
                    'goodwill': 3000.0,
                    'current_assets': 60000.0,
                    'total_liabilities': 40000.0,
                    'shares_outstanding': 10000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Get sorted periods for gap detection
        sorted_periods = sorted(periods.keys(), reverse=True)
        
        # Act: Run gap detection with semi-annual frequency
        gaps_detected = calculator._detect_data_gaps(sorted_periods, 'semi-annual')
        
        # Assert: No gaps should be detected
        assert gaps_detected is False, (
            f"Expected no gaps for 2 periods with {interval_days}-day interval, "
            f"but gaps were detected. Periods: {sorted_periods}"
        )
    
    # Feature: ttm-semi-annual-gap-fix, Property 2: Semi-Annual Gap Detection Tolerance
    def test_boundary_135_days_no_gap(self):
        """
        Property 2: Semi-Annual Gap Detection Tolerance (boundary test)
        
        For exactly 135 days interval (lower tolerance boundary),
        gap detection should return False.
        
        **Validates: Requirements 2.1, 2.2, 2.4**
        """
        # Arrange: Generate periods with exactly 135 days interval
        periods = {
            '2025-06-30': {'revenue': 2000.0, 'net_income': 200.0},
            '2025-02-15': {'revenue': 2000.0, 'net_income': 200.0}  # 135 days before
        }
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {
                '2025-06-30': {
                    'total_equity': 100000.0,
                    'intangible_assets': 5000.0,
                    'goodwill': 3000.0,
                    'current_assets': 60000.0,
                    'total_liabilities': 40000.0,
                    'shares_outstanding': 10000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        sorted_periods = sorted(periods.keys(), reverse=True)
        
        # Act
        gaps_detected = calculator._detect_data_gaps(sorted_periods, 'semi-annual')
        
        # Assert
        assert gaps_detected is False, (
            f"Expected no gaps for 135-day interval (lower boundary), "
            f"but gaps were detected"
        )
    
    # Feature: ttm-semi-annual-gap-fix, Property 2: Semi-Annual Gap Detection Tolerance
    def test_boundary_225_days_no_gap(self):
        """
        Property 2: Semi-Annual Gap Detection Tolerance (boundary test)
        
        For exactly 225 days interval (upper tolerance boundary),
        gap detection should return False.
        
        **Validates: Requirements 2.1, 2.2, 2.4**
        """
        # Arrange: Generate periods with exactly 225 days interval
        periods = {
            '2025-06-30': {'revenue': 2000.0, 'net_income': 200.0},
            '2024-11-18': {'revenue': 2000.0, 'net_income': 200.0}  # 225 days before
        }
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {
                '2025-06-30': {
                    'total_equity': 100000.0,
                    'intangible_assets': 5000.0,
                    'goodwill': 3000.0,
                    'current_assets': 60000.0,
                    'total_liabilities': 40000.0,
                    'shares_outstanding': 10000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        sorted_periods = sorted(periods.keys(), reverse=True)
        
        # Act
        gaps_detected = calculator._detect_data_gaps(sorted_periods, 'semi-annual')
        
        # Assert
        assert gaps_detected is False, (
            f"Expected no gaps for 225-day interval (upper boundary), "
            f"but gaps were detected"
        )
    
    # Feature: ttm-semi-annual-gap-fix, Property 3: Actual Gap Detection for Semi-Annual
    def test_boundary_270_days_gap_detected(self):
        """
        Property 3: Actual Gap Detection for Semi-Annual (boundary test)
        
        For 300+ days interval (clearly indicating a missing period),
        gap detection should return True.
        
        **Validates: Requirements 2.3**
        """
        # Arrange: Generate periods with 300 days interval (clearly a gap)
        periods = {
            '2025-06-30': {'revenue': 2000.0, 'net_income': 200.0},
            '2024-09-04': {'revenue': 2000.0, 'net_income': 200.0}  # 300 days before
        }
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {
                '2025-06-30': {
                    'total_equity': 100000.0,
                    'intangible_assets': 5000.0,
                    'goodwill': 3000.0,
                    'current_assets': 60000.0,
                    'total_liabilities': 40000.0,
                    'shares_outstanding': 10000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        sorted_periods = sorted(periods.keys(), reverse=True)
        
        # Act
        gaps_detected = calculator._detect_data_gaps(sorted_periods, 'semi-annual')
        
        # Assert
        assert gaps_detected is True, (
            f"Expected gap to be detected for 270-day interval (gap threshold), "
            f"but no gap was detected"
        )
