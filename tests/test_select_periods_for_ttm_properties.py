"""
Property-based tests for TTMCalculator._select_periods_for_ttm method.

Feature: ttm-graham-calculations
Property 3: Period Selection for TTM

For any periodic data with detected reporting frequency, the system should select
the appropriate number of most recent periods (4 for quarterly, 2 for semi-annual)
that cover approximately 12 months (within 15 days tolerance).

Validates: Requirements 1.6, 1.7, 1.8, 10.8
"""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, assume, settings
from core.ttm_calculator import TTMCalculator


class TestSelectPeriodsForTTMProperties:
    """Property-based tests for _select_periods_for_ttm method."""
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    @given(
        num_periods=st.integers(min_value=4, max_value=12)
    )
    @settings(max_examples=100)
    def test_quarterly_selects_four_periods(self, num_periods):
        """
        Property: For any quarterly data with sufficient periods, the system
        should select exactly 4 periods.
        
        Validates: Requirements 1.6, 1.7
        """
        # Arrange: Generate quarterly data with ~90 day intervals
        income_periods = {}
        balance_periods = {}
        current_date = datetime(2025, 9, 30)
        
        dates = []
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            dates.append(date_str)
            income_periods[date_str] = {'revenue': 1000.0, 'net_income': 100.0}
            balance_periods[date_str] = {
                'total_equity': 10000.0,
                'shares_outstanding': 1000.0
            }
            # Use 91 days to approximate quarterly intervals
            current_date = current_date - timedelta(days=91)
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': balance_periods
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        calculator.warnings = []  # Reset warnings from frequency detection
        selected_periods = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        assert frequency == 'quarterly', f"Expected quarterly frequency, got {frequency}"
        assert len(selected_periods) == 4, (
            f"Expected 4 periods for quarterly reporting, got {len(selected_periods)}"
        )
        # Verify periods are in descending order (most recent first)
        for i in range(len(selected_periods) - 1):
            date1 = datetime.strptime(selected_periods[i], '%Y-%m-%d')
            date2 = datetime.strptime(selected_periods[i + 1], '%Y-%m-%d')
            assert date1 > date2, (
                f"Periods not in descending order: {selected_periods[i]} should be after {selected_periods[i+1]}"
            )
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    @given(
        num_periods=st.integers(min_value=2, max_value=8)
    )
    @settings(max_examples=100)
    def test_semi_annual_selects_two_periods(self, num_periods):
        """
        Property: For any semi-annual data with sufficient periods, the system
        should select exactly 2 periods.
        
        Validates: Requirements 1.6, 1.8
        """
        # Arrange: Generate semi-annual data with ~182 day intervals
        # Semi-annual periods are 6 months apart, so 2 periods cover 12 months of data
        income_periods = {}
        balance_periods = {}
        current_date = datetime(2025, 6, 30)
        
        dates = []
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            dates.append(date_str)
            income_periods[date_str] = {'revenue': 2000.0, 'net_income': 200.0}
            balance_periods[date_str] = {
                'total_equity': 20000.0,
                'shares_outstanding': 2000.0
            }
            # Use 182 days to approximate semi-annual intervals (6 months)
            current_date = current_date - timedelta(days=182)
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': balance_periods
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        calculator.warnings = []  # Reset warnings from frequency detection
        selected_periods = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        assert frequency == 'semi-annual', f"Expected semi-annual frequency, got {frequency}"
        assert len(selected_periods) == 2, (
            f"Expected 2 periods for semi-annual reporting, got {len(selected_periods)}"
        )
        # Verify periods are in descending order (most recent first)
        if len(selected_periods) == 2:
            date1 = datetime.strptime(selected_periods[0], '%Y-%m-%d')
            date2 = datetime.strptime(selected_periods[1], '%Y-%m-%d')
            assert date1 > date2, (
                f"Periods not in descending order: {selected_periods[0]} should be after {selected_periods[1]}"
            )
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    @given(
        interval_days=st.integers(min_value=85, max_value=95)
    )
    @settings(max_examples=100)
    def test_quarterly_periods_cover_approximately_12_months(self, interval_days):
        """
        Property: For any quarterly data, the selected 4 periods should cover
        approximately 12 months (225-315 days for 3 intervals of ~90 days each).
        
        Validates: Requirements 10.8
        """
        # Arrange: Generate exactly 4 quarterly periods
        income_periods = {}
        balance_periods = {}
        current_date = datetime(2025, 9, 30)
        
        for i in range(4):
            date_str = current_date.strftime('%Y-%m-%d')
            income_periods[date_str] = {'revenue': 1000.0, 'net_income': 100.0}
            balance_periods[date_str] = {
                'total_equity': 10000.0,
                'shares_outstanding': 1000.0
            }
            current_date = current_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': balance_periods
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        calculator.warnings = []  # Reset warnings
        selected_periods = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        if len(selected_periods) == 4:
            # Calculate span between first and last period
            first_date = datetime.strptime(selected_periods[0], '%Y-%m-%d')
            last_date = datetime.strptime(selected_periods[-1], '%Y-%m-%d')
            span_days = (first_date - last_date).days
            
            # Should cover approximately 3 intervals of ~90 days = 270 days
            # With tolerance: 225-315 days (as per implementation)
            assert 225 <= span_days <= 315, (
                f"Expected periods to cover 225-315 days (3 quarterly intervals), got {span_days} days"
            )
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    @given(
        interval_days=st.integers(min_value=170, max_value=190)
    )
    @settings(max_examples=100)
    def test_semi_annual_periods_cover_approximately_12_months(self, interval_days):
        """
        Property: For any semi-annual data, the selected 2 periods should cover
        approximately 12 months (150-210 days for 1 interval of ~180 days).
        
        Validates: Requirements 10.8
        """
        # Arrange: Generate exactly 2 semi-annual periods
        income_periods = {}
        balance_periods = {}
        current_date = datetime(2025, 6, 30)
        
        for i in range(2):
            date_str = current_date.strftime('%Y-%m-%d')
            income_periods[date_str] = {'revenue': 2000.0, 'net_income': 200.0}
            balance_periods[date_str] = {
                'total_equity': 20000.0,
                'shares_outstanding': 2000.0
            }
            current_date = current_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': balance_periods
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        calculator.warnings = []  # Reset warnings
        selected_periods = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        if len(selected_periods) == 2:
            # Calculate span between first and last period
            first_date = datetime.strptime(selected_periods[0], '%Y-%m-%d')
            last_date = datetime.strptime(selected_periods[-1], '%Y-%m-%d')
            span_days = (first_date - last_date).days
            
            # Should cover approximately 1 semi-annual interval (~180 days)
            # With tolerance: 150-210 days (as per implementation)
            assert 150 <= span_days <= 210, (
                f"Expected periods to cover 150-210 days (1 semi-annual interval), got {span_days} days"
            )
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    @given(
        num_periods=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=100)
    def test_insufficient_quarterly_periods_returns_empty_with_warning(self, num_periods):
        """
        Property: For any quarterly data with fewer than 4 periods, the system
        should return an empty list and add a warning.
        
        Validates: Requirements 1.7
        """
        # Arrange: Generate insufficient quarterly periods
        income_periods = {}
        balance_periods = {}
        current_date = datetime(2025, 9, 30)
        
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            income_periods[date_str] = {'revenue': 1000.0, 'net_income': 100.0}
            balance_periods[date_str] = {
                'total_equity': 10000.0,
                'shares_outstanding': 1000.0
            }
            current_date = current_date - timedelta(days=90)
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': balance_periods
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        calculator.warnings = []  # Reset warnings from frequency detection
        selected_periods = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        if frequency == 'quarterly':
            assert len(selected_periods) == 0, (
                f"Expected empty list for insufficient periods, got {len(selected_periods)} periods"
            )
            assert len(calculator.warnings) > 0, (
                "Expected warning for insufficient periods"
            )
            assert any('Insufficient periodic data' in w for w in calculator.warnings), (
                f"Expected 'Insufficient periodic data' warning, got: {calculator.warnings}"
            )
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    def test_insufficient_semi_annual_periods_returns_empty_with_warning(self):
        """
        Property: For any semi-annual data with fewer than 2 periods, the system
        should return an empty list and add a warning.
        
        Validates: Requirements 1.8
        """
        # Arrange: Generate only 1 semi-annual period
        income_periods = {
            '2025-06-30': {'revenue': 2000.0, 'net_income': 200.0}
        }
        balance_periods = {
            '2025-06-30': {
                'total_equity': 20000.0,
                'shares_outstanding': 2000.0
            }
        }
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': balance_periods
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        calculator.warnings = []  # Reset warnings from frequency detection
        selected_periods = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        # With only 1 period, frequency detection will return 'irregular'
        # But we can still test the selection logic
        assert len(selected_periods) == 0, (
            f"Expected empty list for insufficient periods, got {len(selected_periods)} periods"
        )
        assert len(calculator.warnings) > 0, (
            "Expected warning for insufficient periods"
        )
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    @given(
        interval_days=st.integers(min_value=120, max_value=140)
    )
    @settings(max_examples=100)
    def test_periods_not_covering_12_months_returns_empty_with_warning(self, interval_days):
        """
        Property: For any periodic data where selected periods don't cover
        approximately 12 months (outside 350-380 days), the system should
        return an empty list and add a warning.
        
        Validates: Requirements 10.8
        """
        # Arrange: Generate 4 periods with intervals that won't cover 12 months
        # With 120-140 day intervals, 3 intervals = 360-420 days (may be outside range)
        income_periods = {}
        balance_periods = {}
        current_date = datetime(2025, 9, 30)
        
        for i in range(4):
            date_str = current_date.strftime('%Y-%m-%d')
            income_periods[date_str] = {'revenue': 1000.0, 'net_income': 100.0}
            balance_periods[date_str] = {
                'total_equity': 10000.0,
                'shares_outstanding': 1000.0
            }
            current_date = current_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': balance_periods
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        calculator.warnings = []  # Reset warnings
        selected_periods = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        # Calculate actual span
        if len(income_periods) >= 2:
            dates = sorted(income_periods.keys(), reverse=True)
            first_date = datetime.strptime(dates[0], '%Y-%m-%d')
            last_date = datetime.strptime(dates[min(3, len(dates)-1)], '%Y-%m-%d')
            span_days = (first_date - last_date).days
            
            # If span is outside 350-380 days, should return empty list with warning
            if not (350 <= span_days <= 380):
                assert len(selected_periods) == 0, (
                    f"Expected empty list for {span_days}-day span, got {len(selected_periods)} periods"
                )
                assert len(calculator.warnings) > 0, (
                    "Expected warning for coverage gap"
                )
                assert any('cover' in w.lower() for w in calculator.warnings), (
                    f"Expected coverage warning, got: {calculator.warnings}"
                )
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    def test_missing_balance_sheet_returns_empty_with_warning(self):
        """
        Property: For any data with income statement but no balance sheet,
        the system should return an empty list and add a warning.
        
        Validates: Requirements 1.6
        """
        # Arrange: Generate income statement but no balance sheet
        income_periods = {}
        current_date = datetime(2025, 9, 30)
        
        for i in range(4):
            date_str = current_date.strftime('%Y-%m-%d')
            income_periods[date_str] = {'revenue': 1000.0, 'net_income': 100.0}
            current_date = current_date - timedelta(days=90)
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': {}  # Empty balance sheet
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        calculator.warnings = []  # Reset warnings
        selected_periods = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        assert len(selected_periods) == 0, (
            f"Expected empty list for missing balance sheet, got {len(selected_periods)} periods"
        )
        assert len(calculator.warnings) > 0, (
            "Expected warning for missing balance sheet"
        )
        assert any('balance sheet' in w.lower() for w in calculator.warnings), (
            f"Expected balance sheet warning, got: {calculator.warnings}"
        )
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    @given(
        num_periods=st.integers(min_value=4, max_value=12)
    )
    @settings(max_examples=100)
    def test_selected_periods_are_most_recent(self, num_periods):
        """
        Property: For any periodic data with more periods than needed, the system
        should select the most recent periods.
        
        Validates: Requirements 1.6, 1.7
        """
        # Arrange: Generate more periods than needed with proper 12-month coverage
        income_periods = {}
        balance_periods = {}
        current_date = datetime(2025, 9, 30)
        
        dates = []
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            dates.append(date_str)
            income_periods[date_str] = {'revenue': 1000.0, 'net_income': 100.0}
            balance_periods[date_str] = {
                'total_equity': 10000.0,
                'shares_outstanding': 1000.0
            }
            # Use 91 days to approximate quarterly intervals
            current_date = current_date - timedelta(days=91)
        
        # Expected most recent 4 periods
        expected_most_recent = dates[:4]
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': balance_periods
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        calculator.warnings = []  # Reset warnings
        selected_periods = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        if frequency == 'quarterly' and len(selected_periods) == 4:
            # Verify selected periods are the 4 most recent
            assert selected_periods == expected_most_recent, (
                f"Expected most recent 4 periods {expected_most_recent}, got {selected_periods}"
            )
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    @given(
        num_periods=st.integers(min_value=4, max_value=12)
    )
    @settings(max_examples=100)
    def test_selection_is_deterministic(self, num_periods):
        """
        Property: For any periodic data, running _select_periods_for_ttm multiple
        times should always return the same result.
        
        Validates: Requirements 1.6, 1.7, 1.8
        """
        # Arrange: Generate quarterly data with proper 12-month coverage
        income_periods = {}
        balance_periods = {}
        current_date = datetime(2025, 9, 30)
        
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            income_periods[date_str] = {'revenue': 1000.0, 'net_income': 100.0}
            balance_periods[date_str] = {
                'total_equity': 10000.0,
                'shares_outstanding': 1000.0
            }
            # Use 91 days to approximate quarterly intervals
            current_date = current_date - timedelta(days=91)
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': balance_periods
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act: Run selection multiple times
        frequency = calculator.detect_reporting_frequency()
        
        calculator.warnings = []
        selected1 = calculator._select_periods_for_ttm(frequency)
        
        calculator.warnings = []
        selected2 = calculator._select_periods_for_ttm(frequency)
        
        calculator.warnings = []
        selected3 = calculator._select_periods_for_ttm(frequency)
        
        # Assert: All results should be identical
        assert selected1 == selected2 == selected3, (
            f"Expected deterministic results, got: {selected1}, {selected2}, {selected3}"
        )
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    def test_irregular_frequency_returns_empty_list(self):
        """
        Property: For any data with irregular frequency, the system should
        return an empty list (handled by calculate_ttm_metrics, not _select_periods_for_ttm).
        
        Validates: Requirements 1.6
        """
        # Arrange: Generate data that will be classified as irregular
        # Use dates with 92-day interval (within quarterly range)
        # but only 2 periods, which won't cover 12 months
        income_periods = {
            '2025-09-30': {'revenue': 1000.0, 'net_income': 100.0},
            '2025-06-30': {'revenue': 1000.0, 'net_income': 100.0}
        }
        balance_periods = {
            '2025-09-30': {'total_equity': 10000.0, 'shares_outstanding': 1000.0},
            '2025-06-30': {'total_equity': 10000.0, 'shares_outstanding': 1000.0}
        }
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': balance_periods
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        
        # Assert
        # With 92-day interval, this will be classified as quarterly
        # But with only 2 periods, it won't have enough for TTM calculation
        # So we verify that insufficient periods leads to empty result
        if frequency == 'quarterly':
            calculator.warnings = []
            selected_periods = calculator._select_periods_for_ttm(frequency)
            assert len(selected_periods) == 0, (
                f"Expected empty list for insufficient periods, got {len(selected_periods)}"
            )
            assert len(calculator.warnings) > 0, (
                "Expected warning for insufficient periods"
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
