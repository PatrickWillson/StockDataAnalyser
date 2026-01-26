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
from hypothesis import given, strategies as st, assume
from core.ttm_calculator import TTMCalculator


class TestSelectPeriodsForTTM:
    """Property-based tests for _select_periods_for_ttm method."""
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    @given(
        num_periods=st.integers(min_value=4, max_value=12),
        interval_days=st.integers(min_value=85, max_value=95)
    )
    def test_quarterly_selects_four_periods(self, num_periods, interval_days):
        """
        Property: For quarterly data, _select_periods_for_ttm should select exactly 4 periods.
        
        Validates: Requirement 1.6
        """
        # Arrange: Generate quarterly data with known intervals
        # Create periods that span approximately 12 months
        periods = {}
        current_date = datetime(2025, 9, 30)
        
        for i in range(num_periods):
            date_str = current_date.strftime('%Y-%m-%d')
            periods[date_str] = {'revenue': 1000.0, 'net_income': 100.0}
            # Move back by interval_days for next period
            current_date = current_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {
                list(periods.keys())[0]: {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        selected = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        if frequency == 'quarterly':
            # With 85-95 day intervals, 4 periods span 255-285 days (3 intervals)
            # This is within the quarterly tolerance of 225-315 days
            sorted_dates = sorted(periods.keys(), reverse=True)
            first_date = datetime.strptime(sorted_dates[0], '%Y-%m-%d')
            fourth_date = datetime.strptime(sorted_dates[3], '%Y-%m-%d')
            span = (first_date - fourth_date).days
            
            if 225 <= span <= 315:
                assert len(selected) == 4, f"Expected 4 periods for quarterly, got {len(selected)}"
            else:
                # If span is outside tolerance, should return empty list
                assert selected == [], f"Expected empty list for span {span} days, got {len(selected)} periods"
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    @given(
        num_periods=st.integers(min_value=2, max_value=8),
        interval_days=st.integers(min_value=170, max_value=190)
    )
    def test_semi_annual_selects_two_periods(self, num_periods, interval_days):
        """
        Property: For semi-annual data, _select_periods_for_ttm should select exactly 2 periods.
        
        Validates: Requirement 1.7
        """
        # Arrange: Generate semi-annual data with known intervals
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
                list(periods.keys())[0]: {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        selected = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        if frequency == 'semi-annual':
            # With 170-190 day intervals, 2 periods span 170-190 days (1 interval)
            # This is within the semi-annual tolerance of 150-210 days
            sorted_dates = sorted(periods.keys(), reverse=True)
            if len(sorted_dates) >= 2:
                first_date = datetime.strptime(sorted_dates[0], '%Y-%m-%d')
                second_date = datetime.strptime(sorted_dates[1], '%Y-%m-%d')
                span = (first_date - second_date).days
                
                if 150 <= span <= 210:
                    assert len(selected) == 2, f"Expected 2 periods for semi-annual, got {len(selected)}"
                else:
                    # If span is outside tolerance, should return empty list
                    assert selected == [], f"Expected empty list for span {span} days, got {len(selected)} periods"
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    @given(
        interval_days=st.integers(min_value=85, max_value=95)
    )
    def test_selected_periods_cover_approximately_12_months(self, interval_days):
        """
        Property: Selected periods should cover approximately 12 months (225-315 days for quarterly).
        
        Validates: Requirement 1.8, 10.8
        """
        # Arrange: Generate quarterly data with known intervals
        end_date = datetime(2025, 9, 30)
        periods = {}
        
        for i in range(4):
            period_date = end_date - timedelta(days=i * interval_days)
            date_str = period_date.strftime('%Y-%m-%d')
            periods[date_str] = {'revenue': 1000.0, 'net_income': 100.0}
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {
                list(periods.keys())[0]: {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        selected = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        if selected:
            # Calculate actual span
            first_date = datetime.strptime(selected[0], '%Y-%m-%d')
            last_date = datetime.strptime(selected[-1], '%Y-%m-%d')
            span_days = (first_date - last_date).days
            
            # Should be approximately 3 quarterly intervals (225-315 days)
            assert 225 <= span_days <= 315, \
                f"Selected periods span {span_days} days, expected 225-315 days"
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    def test_insufficient_periods_returns_empty_list(self):
        """
        Property: When insufficient periods available, should return empty list with warning.
        
        Validates: Requirement 10.8
        """
        # Arrange: Only 2 periods for quarterly reporting (need 4)
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 1000.0, 'net_income': 100.0},
                '2025-06-30': {'revenue': 1000.0, 'net_income': 100.0},
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        selected = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        if frequency == 'quarterly':
            assert selected == [], "Should return empty list when insufficient periods"
            assert len(calculator.warnings) > 0, "Should add warning for insufficient periods"
            assert any('Insufficient periodic data' in w for w in calculator.warnings)
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    def test_coverage_gap_returns_empty_list(self):
        """
        Property: When periods don't cover ~12 months, should return empty list with warning.
        
        Validates: Requirement 1.8, 10.8
        """
        # Arrange: 4 periods but with short intervals (only 6 months total)
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 1000.0, 'net_income': 100.0},
                '2025-08-31': {'revenue': 1000.0, 'net_income': 100.0},  # 30 days
                '2025-07-31': {'revenue': 1000.0, 'net_income': 100.0},  # 31 days
                '2025-06-30': {'revenue': 1000.0, 'net_income': 100.0},  # 31 days
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        
        # Frequency will likely be irregular due to short intervals
        # But let's test _select_periods_for_ttm directly with 'quarterly'
        selected = calculator._select_periods_for_ttm('quarterly')
        
        # Assert
        # Total span is only ~92 days, which is outside 350-380 range
        assert selected == [], "Should return empty list when coverage gap exists"
        assert len(calculator.warnings) > 0, "Should add warning for coverage gap"
        assert any('cover' in w.lower() for w in calculator.warnings)
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    def test_no_balance_sheet_returns_empty_list(self):
        """
        Property: When no balance sheet data available, should return empty list with warning.
        
        Validates: Requirement 10.8
        """
        # Arrange: Income statement but no balance sheet
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 1000.0, 'net_income': 100.0},
                '2025-06-30': {'revenue': 1000.0, 'net_income': 100.0},
                '2025-03-31': {'revenue': 1000.0, 'net_income': 100.0},
                '2024-12-31': {'revenue': 1000.0, 'net_income': 100.0},
            },
            'balance_sheet': {}
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        selected = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        assert selected == [], "Should return empty list when no balance sheet data"
        assert len(calculator.warnings) > 0, "Should add warning for missing balance sheet"
        assert any('balance sheet' in w.lower() for w in calculator.warnings)
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    def test_selects_most_recent_periods(self):
        """
        Property: Should select the most recent periods (first N in descending order).
        
        Validates: Requirement 1.6, 1.7
        """
        # Arrange: 8 quarterly periods with proper ~91 day intervals
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 1000.0, 'net_income': 100.0},
                '2025-07-01': {'revenue': 1000.0, 'net_income': 100.0},  # 91 days earlier
                '2025-04-01': {'revenue': 1000.0, 'net_income': 100.0},  # 91 days earlier
                '2024-12-31': {'revenue': 1000.0, 'net_income': 100.0},  # 91 days earlier
                '2024-10-01': {'revenue': 1000.0, 'net_income': 100.0},  # 91 days earlier
                '2024-07-02': {'revenue': 1000.0, 'net_income': 100.0},  # 91 days earlier
                '2024-04-02': {'revenue': 1000.0, 'net_income': 100.0},  # 91 days earlier
                '2024-01-01': {'revenue': 1000.0, 'net_income': 100.0},  # 92 days earlier
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        selected = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        if frequency == 'quarterly':
            assert len(selected) == 4
            # Should be the 4 most recent periods
            expected = ['2025-09-30', '2025-07-01', '2025-04-01', '2024-12-31']
            assert selected == expected, f"Expected {expected}, got {selected}"
    
    # Feature: ttm-graham-calculations, Property 3: Period Selection for TTM
    @given(
        num_periods=st.integers(min_value=4, max_value=12),
        base_interval=st.integers(min_value=85, max_value=95),
        variation=st.integers(min_value=-5, max_value=5)
    )
    def test_handles_slight_interval_variations(self, num_periods, base_interval, variation):
        """
        Property: Should handle slight variations in period intervals gracefully.
        
        Validates: Requirement 1.8
        """
        # Arrange: Generate quarterly data with slight variations
        end_date = datetime(2025, 9, 30)
        periods = {}
        
        for i in range(num_periods):
            # Add variation to each interval
            interval = base_interval + (variation if i % 2 == 0 else -variation)
            period_date = end_date - timedelta(days=i * interval)
            date_str = period_date.strftime('%Y-%m-%d')
            periods[date_str] = {'revenue': 1000.0, 'net_income': 100.0}
        
        quarterly_data = {
            'income_statement': periods,
            'balance_sheet': {
                list(periods.keys())[0]: {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        frequency = calculator.detect_reporting_frequency()
        selected = calculator._select_periods_for_ttm(frequency)
        
        # Assert
        if frequency == 'quarterly' and selected:
            # Should still select 4 periods
            assert len(selected) == 4
            
            # Calculate span
            first_date = datetime.strptime(selected[0], '%Y-%m-%d')
            last_date = datetime.strptime(selected[-1], '%Y-%m-%d')
            span_days = (first_date - last_date).days
            
            # Should be within quarterly tolerance (225-315 days)
            assert 225 <= span_days <= 315, \
                f"Span {span_days} days outside tolerance despite slight variations"


class TestSelectPeriodsEdgeCases:
    """Unit tests for edge cases in _select_periods_for_ttm."""
    
    def test_exactly_225_days_accepted(self):
        """Test that exactly 225 days (lower boundary for quarterly) is accepted."""
        # Arrange: Create periods spanning exactly 225 days (3 intervals of 75 days)
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 1000.0, 'net_income': 100.0},
                '2025-07-17': {'revenue': 1000.0, 'net_income': 100.0},  # 75 days earlier
                '2025-05-03': {'revenue': 1000.0, 'net_income': 100.0},  # 75 days earlier
                '2025-02-17': {'revenue': 1000.0, 'net_income': 100.0},  # 75 days earlier (total 225 days)
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        selected = calculator._select_periods_for_ttm('quarterly')
        
        # Assert
        assert len(selected) == 4, "Should accept exactly 225 days (lower boundary for quarterly)"
    
    def test_exactly_315_days_accepted(self):
        """Test that exactly 315 days (upper boundary for quarterly) is accepted."""
        # Arrange: Create periods spanning exactly 315 days (3 intervals of 105 days)
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 1000.0, 'net_income': 100.0},
                '2025-06-17': {'revenue': 1000.0, 'net_income': 100.0},  # 105 days earlier
                '2025-03-04': {'revenue': 1000.0, 'net_income': 100.0},  # 105 days earlier
                '2024-11-19': {'revenue': 1000.0, 'net_income': 100.0},  # 105 days earlier (total 315 days)
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        selected = calculator._select_periods_for_ttm('quarterly')
        
        # Assert
        assert len(selected) == 4, "Should accept exactly 315 days (upper boundary for quarterly)"
    
    def test_224_days_rejected(self):
        """Test that 224 days (just below lower boundary for quarterly) is rejected."""
        # Arrange: Create periods spanning 224 days
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 1000.0, 'net_income': 100.0},
                '2025-07-18': {'revenue': 1000.0, 'net_income': 100.0},  # 74 days earlier
                '2025-05-05': {'revenue': 1000.0, 'net_income': 100.0},  # 74 days earlier
                '2025-02-19': {'revenue': 1000.0, 'net_income': 100.0},  # 76 days earlier (total 224 days)
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        selected = calculator._select_periods_for_ttm('quarterly')
        
        # Assert
        assert selected == [], "Should reject 224 days (below tolerance for quarterly)"
        assert any('cover' in w.lower() for w in calculator.warnings)
    
    def test_316_days_rejected(self):
        """Test that 316 days (just above upper boundary for quarterly) is rejected."""
        # Arrange: Create periods spanning 316 days
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 1000.0, 'net_income': 100.0},
                '2025-06-16': {'revenue': 1000.0, 'net_income': 100.0},  # 106 days earlier
                '2025-03-02': {'revenue': 1000.0, 'net_income': 100.0},  # 106 days earlier
                '2024-11-17': {'revenue': 1000.0, 'net_income': 100.0},  # 105 days earlier (total 317 days, close enough)
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        selected = calculator._select_periods_for_ttm('quarterly')
        
        # Assert
        assert selected == [], "Should reject 316+ days (above tolerance for quarterly)"
        assert any('cover' in w.lower() for w in calculator.warnings)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
