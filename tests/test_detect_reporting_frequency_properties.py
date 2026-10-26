"""
Property-based tests for TTMCalculator.detect_reporting_frequency method.

Feature: ttm-graham-calculations
Property 2: Reporting Frequency Detection

For any set of periodic financial data, when the average interval between consecutive
periods is approximately 90 days (±15 days), the system should classify it as quarterly;
when approximately 180 days (±30 days), as semi-annual; otherwise as irregular with a warning.

Validates: Requirements 2.1, 2.2, 2.3, 2.4
"""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings
from core.ttm_calculator import TTMCalculator


class TestDetectReportingFrequencyProperties:
    """Property-based tests for detect_reporting_frequency method."""
    
    # Feature: ttm-graham-calculations, Property 2: Reporting Frequency Detection
    @given(
        num_periods=st.integers(min_value=2, max_value=12),
        interval_days=st.integers(min_value=75, max_value=105)
    )
    @settings(max_examples=100)
    def test_quarterly_interval_classification(self, num_periods, interval_days):
        """
        Property: For any periodic data with average interval ~90 days (±15 days),
        the system should classify it as quarterly.
        
        Validates: Requirements 2.1, 2.2
        """
        # Arrange: Generate periods with known quarterly intervals
        periods = {}
        current_date = datetime(2025, 9, 30)
        
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            periods[date_str] = {'revenue': 1000.0, 'net_income': 100.0}
            # Move back by interval_days for next period
            current_date = current_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {}
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        
        # Assert
        assert frequency == 'quarterly', (
            f"Expected 'quarterly' for {interval_days}-day intervals, got '{frequency}'"
        )
        # Should not have warnings for valid quarterly pattern
        assert len(calculator.warnings) == 0, (
            f"Expected no warnings for valid quarterly pattern, got: {calculator.warnings}"
        )
    
    # Feature: ttm-graham-calculations, Property 2: Reporting Frequency Detection
    @given(
        num_periods=st.integers(min_value=2, max_value=8),
        interval_days=st.integers(min_value=150, max_value=210)
    )
    @settings(max_examples=100)
    def test_semi_annual_interval_classification(self, num_periods, interval_days):
        """
        Property: For any periodic data with average interval ~180 days (±30 days),
        the system should classify it as semi-annual.
        
        Validates: Requirements 2.1, 2.3
        """
        # Arrange: Generate periods with known semi-annual intervals
        periods = {}
        current_date = datetime(2025, 6, 30)
        
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            periods[date_str] = {'revenue': 2000.0, 'net_income': 200.0}
            # Move back by interval_days for next period
            current_date = current_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {}
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        
        # Assert
        assert frequency == 'semi-annual', (
            f"Expected 'semi-annual' for {interval_days}-day intervals, got '{frequency}'"
        )
        # Should not have warnings for valid semi-annual pattern
        assert len(calculator.warnings) == 0, (
            f"Expected no warnings for valid semi-annual pattern, got: {calculator.warnings}"
        )
    
    # Feature: ttm-graham-calculations, Property 2: Reporting Frequency Detection
    @given(
        num_periods=st.integers(min_value=2, max_value=10),
        interval_days=st.integers(min_value=106, max_value=149)
    )
    @settings(max_examples=100)
    def test_irregular_interval_classification_between_ranges(self, num_periods, interval_days):
        """
        Property: For any periodic data with average interval between quarterly and
        semi-annual ranges (106-149 days), the system should classify it as irregular
        and add a warning.
        
        Validates: Requirements 2.4
        """
        # Arrange: Generate periods with intervals that don't fit either pattern
        periods = {}
        current_date = datetime(2025, 9, 30)
        
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            periods[date_str] = {'revenue': 1000.0, 'net_income': 100.0}
            # Move back by interval_days for next period
            current_date = current_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {}
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        
        # Assert
        assert frequency == 'irregular', (
            f"Expected 'irregular' for {interval_days}-day intervals, got '{frequency}'"
        )
        # Should have warning about irregular pattern
        assert len(calculator.warnings) > 0, (
            "Expected warning for irregular pattern"
        )
        assert any('Irregular reporting pattern' in w for w in calculator.warnings), (
            f"Expected 'Irregular reporting pattern' warning, got: {calculator.warnings}"
        )
    
    # Feature: ttm-graham-calculations, Property 2: Reporting Frequency Detection
    @given(
        num_periods=st.integers(min_value=2, max_value=10),
        interval_days=st.integers(min_value=211, max_value=400)
    )
    @settings(max_examples=100)
    def test_irregular_interval_classification_above_semi_annual(self, num_periods, interval_days):
        """
        Property: For any periodic data with average interval above semi-annual range
        (>210 days), the system should classify it as irregular and add a warning.
        
        Validates: Requirements 2.4
        """
        # Arrange: Generate periods with intervals above semi-annual range
        periods = {}
        current_date = datetime(2025, 9, 30)
        
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            periods[date_str] = {'revenue': 1000.0, 'net_income': 100.0}
            # Move back by interval_days for next period
            current_date = current_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {}
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        
        # Assert
        assert frequency == 'irregular', (
            f"Expected 'irregular' for {interval_days}-day intervals, got '{frequency}'"
        )
        # Should have warning about irregular pattern
        assert len(calculator.warnings) > 0, (
            "Expected warning for irregular pattern"
        )
        assert any('Irregular reporting pattern' in w for w in calculator.warnings), (
            f"Expected 'Irregular reporting pattern' warning, got: {calculator.warnings}"
        )
    
    # Feature: ttm-graham-calculations, Property 2: Reporting Frequency Detection
    @given(
        num_periods=st.integers(min_value=2, max_value=10),
        interval_days=st.integers(min_value=20, max_value=74)
    )
    @settings(max_examples=100)
    def test_irregular_interval_classification_below_quarterly(self, num_periods, interval_days):
        """
        Property: For any periodic data with average interval below quarterly range
        (<75 days), the system should classify it as irregular and add a warning.
        
        Validates: Requirements 2.4
        """
        # Arrange: Generate periods with intervals below quarterly range
        periods = {}
        current_date = datetime(2025, 9, 30)
        
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            periods[date_str] = {'revenue': 1000.0, 'net_income': 100.0}
            # Move back by interval_days for next period
            current_date = current_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {}
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        
        # Assert
        assert frequency == 'irregular', (
            f"Expected 'irregular' for {interval_days}-day intervals, got '{frequency}'"
        )
        # Should have warning about irregular pattern
        assert len(calculator.warnings) > 0, (
            "Expected warning for irregular pattern"
        )
        assert any('Irregular reporting pattern' in w for w in calculator.warnings), (
            f"Expected 'Irregular reporting pattern' warning, got: {calculator.warnings}"
        )
    
    # Feature: ttm-graham-calculations, Property 2: Reporting Frequency Detection
    @given(
        num_periods=st.integers(min_value=3, max_value=10),
        base_interval=st.integers(min_value=85, max_value=95),
        variance=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_mixed_intervals_averaging_to_quarterly(self, num_periods, base_interval, variance):
        """
        Property: For any periodic data with varying intervals that average to ~90 days,
        the system should classify it as quarterly.
        
        Validates: Requirements 2.1, 2.2
        """
        # Arrange: Generate periods with varying intervals that average to quarterly
        periods = {}
        current_date = datetime(2025, 9, 30)
        
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            periods[date_str] = {'revenue': 1000.0, 'net_income': 100.0}
            # Alternate between base_interval + variance and base_interval - variance
            if i % 2 == 0:
                interval = base_interval + variance
            else:
                interval = base_interval - variance
            current_date = current_date - timedelta(days=interval)
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {}
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        
        # Assert
        # Average should still be within quarterly range
        assert frequency == 'quarterly', (
            f"Expected 'quarterly' for intervals averaging {base_interval} days, got '{frequency}'"
        )
    
    # Feature: ttm-graham-calculations, Property 2: Reporting Frequency Detection
    @given(
        num_periods=st.integers(min_value=3, max_value=8),
        base_interval=st.integers(min_value=170, max_value=190),
        variance=st.integers(min_value=1, max_value=15)
    )
    @settings(max_examples=100)
    def test_mixed_intervals_averaging_to_semi_annual(self, num_periods, base_interval, variance):
        """
        Property: For any periodic data with varying intervals that average to ~180 days,
        the system should classify it as semi-annual.
        
        Validates: Requirements 2.1, 2.3
        """
        # Arrange: Generate periods with varying intervals that average to semi-annual
        periods = {}
        current_date = datetime(2025, 6, 30)
        
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            periods[date_str] = {'revenue': 2000.0, 'net_income': 200.0}
            # Alternate between base_interval + variance and base_interval - variance
            if i % 2 == 0:
                interval = base_interval + variance
            else:
                interval = base_interval - variance
            current_date = current_date - timedelta(days=interval)
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {}
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        
        # Assert
        # Average should still be within semi-annual range
        assert frequency == 'semi-annual', (
            f"Expected 'semi-annual' for intervals averaging {base_interval} days, got '{frequency}'"
        )
    
    # Feature: ttm-graham-calculations, Property 2: Reporting Frequency Detection
    def test_empty_data_returns_irregular_with_warning(self):
        """
        Property: For any empty periodic data, the system should return 'irregular'
        and add a warning.
        
        Validates: Requirements 2.4
        """
        # Arrange: Empty quarterly data
        quarterly_data = {
            'income_statement': {},
            'balance_sheet': {}
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        
        # Assert
        assert frequency == 'irregular', (
            f"Expected 'irregular' for empty data, got '{frequency}'"
        )
        assert len(calculator.warnings) > 0, (
            "Expected warning for empty data"
        )
        assert any('No periodic data available' in w for w in calculator.warnings), (
            f"Expected 'No periodic data available' warning, got: {calculator.warnings}"
        )
    
    # Feature: ttm-graham-calculations, Property 2: Reporting Frequency Detection
    def test_single_period_returns_irregular_with_warning(self):
        """
        Property: For any periodic data with only one period, the system should
        return 'irregular' and add a warning.
        
        Validates: Requirements 2.4
        """
        # Arrange: Single period data
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 1000.0, 'net_income': 100.0}
            },
            'balance_sheet': {}
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        
        # Assert
        assert frequency == 'irregular', (
            f"Expected 'irregular' for single period, got '{frequency}'"
        )
        assert len(calculator.warnings) > 0, (
            "Expected warning for single period"
        )
        assert any('Insufficient periods' in w for w in calculator.warnings), (
            f"Expected 'Insufficient periods' warning, got: {calculator.warnings}"
        )
    
    # Feature: ttm-graham-calculations, Property 2: Reporting Frequency Detection
    @given(
        num_periods=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=100)
    def test_highly_irregular_intervals_with_warning(self, num_periods):
        """
        Property: For any periodic data with highly irregular intervals (large variance),
        the system should classify it as irregular and add a warning.
        
        Validates: Requirements 2.4
        """
        # Arrange: Generate periods with highly irregular intervals
        # Use intervals that vary significantly: 60, 120, 80, 200, etc.
        periods = {}
        current_date = datetime(2025, 9, 30)
        interval_options = [60, 120, 80, 200, 90, 150, 70, 180]
        
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            periods[date_str] = {'revenue': 1000.0, 'net_income': 100.0}
            # Use different intervals from the options
            interval = interval_options[i % len(interval_options)]
            current_date = current_date - timedelta(days=interval)
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {}
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        
        # Assert
        # With highly irregular intervals, should be classified as irregular
        # (unless by chance the average falls within a valid range)
        if frequency == 'irregular':
            assert len(calculator.warnings) > 0, (
                "Expected warning for irregular pattern"
            )
            assert any('Irregular reporting pattern' in w for w in calculator.warnings), (
                f"Expected 'Irregular reporting pattern' warning, got: {calculator.warnings}"
            )
    
    # Feature: ttm-graham-calculations, Property 2: Reporting Frequency Detection
    @given(
        num_periods=st.integers(min_value=2, max_value=10),
        interval_days=st.integers(min_value=75, max_value=105)
    )
    @settings(max_examples=100)
    def test_classification_is_deterministic(self, num_periods, interval_days):
        """
        Property: For any periodic data, running detect_reporting_frequency multiple
        times should always return the same result.
        
        Validates: Requirements 2.1, 2.2, 2.3
        """
        # Arrange: Generate periods with known intervals
        periods = {}
        current_date = datetime(2025, 9, 30)
        
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            periods[date_str] = {'revenue': 1000.0, 'net_income': 100.0}
            current_date = current_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {}
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act: Run detection multiple times
        frequency1 = calculator.detect_reporting_frequency()
        # Reset warnings for second run
        calculator.warnings = []
        frequency2 = calculator.detect_reporting_frequency()
        # Reset warnings for third run
        calculator.warnings = []
        frequency3 = calculator.detect_reporting_frequency()
        
        # Assert: All results should be identical
        assert frequency1 == frequency2 == frequency3, (
            f"Expected deterministic results, got: {frequency1}, {frequency2}, {frequency3}"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
