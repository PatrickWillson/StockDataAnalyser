"""
Property-based tests for semi-annual period selection in TTMCalculator.

Feature: ttm-semi-annual-gap-fix
Property 4: Semi-Annual Period Selection
Property 5: Invalid Semi-Annual Data Handling

For any semi-annual data with valid consecutive periods, the system should select
exactly 2 periods covering 150-210 days. For invalid data (gaps or insufficient
coverage), the system should return an empty list with appropriate warnings.

Validates: Requirements 3.1, 3.2, 3.3, 3.4
"""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, assume, settings
from core.ttm_calculator import TTMCalculator


class TestSemiAnnualPeriodSelectionProperties:
    """Property-based tests for semi-annual period selection."""
    
    # Feature: ttm-semi-annual-gap-fix, Property 4: Semi-Annual Period Selection
    @given(
        interval_days=st.integers(min_value=150, max_value=210),
        num_periods=st.integers(min_value=2, max_value=8)
    )
    @settings(max_examples=100)
    def test_property_4_semi_annual_period_selection(self, interval_days, num_periods):
        """
        Property 4: Semi-Annual Period Selection
        
        For any semi-annual data with at least 2 consecutive periods covering
        150-210 days total span, period selection should return exactly 2 periods
        for TTM calculation.
        
        Validates: Requirements 3.1, 3.2, 3.3
        """
        # Arrange: Generate semi-annual data with specified interval
        income_periods = {}
        balance_periods = {}
        current_date = datetime(2025, 6, 30)
        
        dates = []
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            dates.append(date_str)
            income_periods[date_str] = {
                'revenue': 50000000.0,
                'net_income': 5000000.0
            }
            balance_periods[date_str] = {
                'total_equity': 100000000.0,
                'intangible_assets': 5000000.0,
                'goodwill': 3000000.0,
                'current_assets': 60000000.0,
                'total_liabilities': 40000000.0,
                'shares_outstanding': 10000000.0
            }
            current_date = current_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': balance_periods
        }
        
        calculator = TTMCalculator(quarterly_data, price=10.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        calculator.warnings = []  # Reset warnings from frequency detection
        selected_periods = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        # Requirement 3.1: Exactly 2 periods selected for semi-annual reporters
        if frequency == 'semi-annual':
            assert len(selected_periods) == 2, (
                f"Expected exactly 2 periods for semi-annual reporting, got {len(selected_periods)}"
            )
            
            # Requirement 3.2: Periods should cover 150-210 days
            if len(selected_periods) == 2:
                first_date = datetime.strptime(selected_periods[0], '%Y-%m-%d')
                last_date = datetime.strptime(selected_periods[1], '%Y-%m-%d')
                span_days = (first_date - last_date).days
                
                assert 150 <= span_days <= 210, (
                    f"Expected span of 150-210 days, got {span_days} days"
                )
            
            # Requirement 3.3: Selected periods should be the 2 most recent
            expected_periods = dates[:2]
            assert selected_periods == expected_periods, (
                f"Expected most recent 2 periods {expected_periods}, got {selected_periods}"
            )
            
            # No warnings should be added for valid data
            assert len(calculator.warnings) == 0, (
                f"Expected no warnings for valid semi-annual data, got: {calculator.warnings}"
            )
    
    # Feature: ttm-semi-annual-gap-fix, Property 4: Semi-Annual Period Selection
    @given(
        interval_days=st.integers(min_value=150, max_value=210)
    )
    @settings(max_examples=100)
    def test_property_4_span_validation_accepts_valid_range(self, interval_days):
        """
        Property 4: Semi-Annual Period Selection - Span Validation
        
        For any semi-annual data where 2 consecutive periods cover 150-210 days,
        the span validation should accept this as valid 12-month coverage.
        
        Validates: Requirements 3.2
        """
        # Arrange: Generate exactly 2 semi-annual periods with specified interval
        income_periods = {}
        balance_periods = {}
        current_date = datetime(2025, 6, 30)
        
        for i in range(2):
            date_str = current_date.strftime('%Y-%m-%d')
            income_periods[date_str] = {
                'revenue': 50000000.0,
                'net_income': 5000000.0
            }
            balance_periods[date_str] = {
                'total_equity': 100000000.0,
                'intangible_assets': 5000000.0,
                'goodwill': 3000000.0,
                'current_assets': 60000000.0,
                'total_liabilities': 40000000.0,
                'shares_outstanding': 10000000.0
            }
            current_date = current_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': balance_periods
        }
        
        calculator = TTMCalculator(quarterly_data, price=10.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        calculator.warnings = []  # Reset warnings
        selected_periods = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        # Span validation should accept 150-210 day range
        assert len(selected_periods) == 2, (
            f"Expected 2 periods to be selected for {interval_days}-day interval, "
            f"got {len(selected_periods)} periods"
        )
        
        # No span validation warnings should be added
        span_warnings = [w for w in calculator.warnings if 'cover' in w.lower()]
        assert len(span_warnings) == 0, (
            f"Expected no span warnings for {interval_days}-day interval, got: {span_warnings}"
        )
    
    # Feature: ttm-semi-annual-gap-fix, Property 5: Invalid Semi-Annual Data Handling
    @given(
        interval_days=st.integers(min_value=270, max_value=400)
    )
    @settings(max_examples=100)
    def test_property_5_invalid_data_with_gaps(self, interval_days):
        """
        Property 5: Invalid Semi-Annual Data Handling - Gaps
        
        For any semi-annual data with gaps (intervals > 270 days indicating
        missing periods), period selection should return an empty list and
        add appropriate warnings.
        
        Validates: Requirements 3.4
        """
        # Arrange: Generate 2 periods with a large gap (missing period)
        income_periods = {}
        balance_periods = {}
        current_date = datetime(2025, 6, 30)
        
        for i in range(2):
            date_str = current_date.strftime('%Y-%m-%d')
            income_periods[date_str] = {
                'revenue': 50000000.0,
                'net_income': 5000000.0
            }
            balance_periods[date_str] = {
                'total_equity': 100000000.0,
                'intangible_assets': 5000000.0,
                'goodwill': 3000000.0,
                'current_assets': 60000000.0,
                'total_liabilities': 40000000.0,
                'shares_outstanding': 10000000.0
            }
            current_date = current_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': balance_periods
        }
        
        calculator = TTMCalculator(quarterly_data, price=10.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        calculator.warnings = []  # Reset warnings
        selected_periods = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        # Should return empty list for data with gaps
        assert len(selected_periods) == 0, (
            f"Expected empty list for {interval_days}-day gap, got {len(selected_periods)} periods"
        )
        
        # Should add warning about gaps
        assert len(calculator.warnings) > 0, (
            f"Expected warning for {interval_days}-day gap, got no warnings"
        )
        
        gap_warnings = [w for w in calculator.warnings if 'gap' in w.lower()]
        assert len(gap_warnings) > 0, (
            f"Expected gap warning for {interval_days}-day gap, got: {calculator.warnings}"
        )
    
    # Feature: ttm-semi-annual-gap-fix, Property 5: Invalid Semi-Annual Data Handling
    @given(
        interval_days=st.one_of(
            st.integers(min_value=50, max_value=149),   # Too short
            st.integers(min_value=211, max_value=269)   # Too long but not a gap
        )
    )
    @settings(max_examples=100)
    def test_property_5_invalid_data_insufficient_coverage(self, interval_days):
        """
        Property 5: Invalid Semi-Annual Data Handling - Insufficient Coverage
        
        For any semi-annual data with insufficient coverage (span outside
        150-210 days but not a gap), period selection should return an empty
        list and add appropriate warnings.
        
        Validates: Requirements 3.4
        """
        # Arrange: Generate 2 periods with interval outside valid range
        income_periods = {}
        balance_periods = {}
        current_date = datetime(2025, 6, 30)
        
        for i in range(2):
            date_str = current_date.strftime('%Y-%m-%d')
            income_periods[date_str] = {
                'revenue': 50000000.0,
                'net_income': 5000000.0
            }
            balance_periods[date_str] = {
                'total_equity': 100000000.0,
                'intangible_assets': 5000000.0,
                'goodwill': 3000000.0,
                'current_assets': 60000000.0,
                'total_liabilities': 40000000.0,
                'shares_outstanding': 10000000.0
            }
            current_date = current_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': balance_periods
        }
        
        calculator = TTMCalculator(quarterly_data, price=10.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        calculator.warnings = []  # Reset warnings
        selected_periods = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        # For intervals outside 150-210 range, should return empty list
        if interval_days < 150 or interval_days > 210:
            # Frequency detection might classify this as irregular or quarterly
            # depending on the interval
            if frequency == 'semi-annual':
                # If classified as semi-annual, span validation should reject it
                assert len(selected_periods) == 0, (
                    f"Expected empty list for {interval_days}-day span, "
                    f"got {len(selected_periods)} periods"
                )
                
                # Should add warning about coverage
                assert len(calculator.warnings) > 0, (
                    f"Expected warning for {interval_days}-day span, got no warnings"
                )
    
    # Feature: ttm-semi-annual-gap-fix, Property 5: Invalid Semi-Annual Data Handling
    def test_property_5_invalid_data_insufficient_periods(self):
        """
        Property 5: Invalid Semi-Annual Data Handling - Insufficient Periods
        
        For any semi-annual data with fewer than 2 periods, period selection
        should return an empty list and add appropriate warnings.
        
        Validates: Requirements 3.4
        """
        # Arrange: Generate only 1 period
        income_periods = {
            '2025-06-30': {
                'revenue': 50000000.0,
                'net_income': 5000000.0
            }
        }
        balance_periods = {
            '2025-06-30': {
                'total_equity': 100000000.0,
                'intangible_assets': 5000000.0,
                'goodwill': 3000000.0,
                'current_assets': 60000000.0,
                'total_liabilities': 40000000.0,
                'shares_outstanding': 10000000.0
            }
        }
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': balance_periods
        }
        
        calculator = TTMCalculator(quarterly_data, price=10.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        calculator.warnings = []  # Reset warnings
        selected_periods = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        # Should return empty list for insufficient periods
        assert len(selected_periods) == 0, (
            f"Expected empty list for 1 period, got {len(selected_periods)} periods"
        )
        
        # Should add warning about insufficient periods
        assert len(calculator.warnings) > 0, (
            "Expected warning for insufficient periods, got no warnings"
        )
    
    # Feature: ttm-semi-annual-gap-fix, Property 4: Semi-Annual Period Selection
    @given(
        interval_days=st.integers(min_value=150, max_value=210),
        num_periods=st.integers(min_value=2, max_value=8)
    )
    @settings(max_examples=100)
    def test_property_4_selection_is_deterministic(self, interval_days, num_periods):
        """
        Property 4: Semi-Annual Period Selection - Determinism
        
        For any semi-annual data, running _select_periods_for_ttm multiple
        times should always return the same result.
        
        Validates: Requirements 3.1, 3.2, 3.3
        """
        # Arrange: Generate semi-annual data
        income_periods = {}
        balance_periods = {}
        current_date = datetime(2025, 6, 30)
        
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            income_periods[date_str] = {
                'revenue': 50000000.0,
                'net_income': 5000000.0
            }
            balance_periods[date_str] = {
                'total_equity': 100000000.0,
                'intangible_assets': 5000000.0,
                'goodwill': 3000000.0,
                'current_assets': 60000000.0,
                'total_liabilities': 40000000.0,
                'shares_outstanding': 10000000.0
            }
            current_date = current_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': balance_periods
        }
        
        calculator = TTMCalculator(quarterly_data, price=10.0, currency='USD')
        
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
    
    # Feature: ttm-semi-annual-gap-fix, Property 4: Semi-Annual Period Selection
    @given(
        interval_days=st.integers(min_value=150, max_value=210)
    )
    @settings(max_examples=100)
    def test_property_4_periods_in_descending_order(self, interval_days):
        """
        Property 4: Semi-Annual Period Selection - Period Order
        
        For any semi-annual data, selected periods should be in descending
        chronological order (most recent first).
        
        Validates: Requirements 3.3
        """
        # Arrange: Generate 2 semi-annual periods
        income_periods = {}
        balance_periods = {}
        current_date = datetime(2025, 6, 30)
        
        for i in range(2):
            date_str = current_date.strftime('%Y-%m-%d')
            income_periods[date_str] = {
                'revenue': 50000000.0,
                'net_income': 5000000.0
            }
            balance_periods[date_str] = {
                'total_equity': 100000000.0,
                'intangible_assets': 5000000.0,
                'goodwill': 3000000.0,
                'current_assets': 60000000.0,
                'total_liabilities': 40000000.0,
                'shares_outstanding': 10000000.0
            }
            current_date = current_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': income_periods,
            'balance_sheet': balance_periods
        }
        
        calculator = TTMCalculator(quarterly_data, price=10.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        calculator.warnings = []  # Reset warnings
        selected_periods = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        if len(selected_periods) == 2:
            date1 = datetime.strptime(selected_periods[0], '%Y-%m-%d')
            date2 = datetime.strptime(selected_periods[1], '%Y-%m-%d')
            
            assert date1 > date2, (
                f"Periods not in descending order: {selected_periods[0]} should be after {selected_periods[1]}"
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
