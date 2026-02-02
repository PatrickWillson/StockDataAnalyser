"""
Unit tests for check_data_staleness() function.

Tests specific examples and edge cases for data staleness detection.
Validates Requirements 7.6, 7.7 from normalized-margin-of-safety spec.
"""

import pytest
from datetime import datetime, timedelta
from core.financial_data_processor import FinancialDataProcessor


class TestCheckDataStaleness:
    """Unit tests for check_data_staleness() function."""
    
    def test_fresh_data_within_9_months(self):
        """Test that data within 9 months returns None (no warning)."""
        # Data from 6 months ago
        current_date = datetime(2025, 6, 1)
        report_date = datetime(2024, 12, 31)
        
        history = {
            '2024-12-31': {'eps': 4.85, 'revenue': 1000000}
        }
        
        result = FinancialDataProcessor.check_data_staleness(history, current_date)
        
        assert result is None  # No warning for fresh data
    
    def test_stale_data_exactly_9_months(self):
        """Test that data exactly 9 months old returns None (boundary case)."""
        # Data from exactly 9 months ago (9 * 30.44 = 273.96 days)
        current_date = datetime(2025, 9, 30)
        report_date = datetime(2024, 12, 31)
        
        history = {
            '2024-12-31': {'eps': 4.85}
        }
        
        result = FinancialDataProcessor.check_data_staleness(history, current_date)
        
        # 9 months exactly should not trigger warning (> 9 months required)
        assert result is None
    
    def test_stale_data_over_9_months(self):
        """Test that data older than 9 months returns warning."""
        # Data from 10 months ago (304 days = 9.98 months using 30.44 days/month)
        current_date = datetime(2025, 10, 31)
        report_date = datetime(2024, 12, 31)
        
        history = {
            '2024-12-31': {'eps': 4.85}
        }
        
        result = FinancialDataProcessor.check_data_staleness(history, current_date)
        
        assert result is not None
        assert "Potentially Stale Data" in result
        assert "2024-12-31" in result
        # 304 days / 30.44 = 9.98 months, rounds to 9
        assert "9 months old" in result
    
    def test_stale_data_over_12_months(self):
        """Test that data older than 12 months returns warning with correct age."""
        # Data from 15 months ago (455 days = 14.95 months using 30.44 days/month)
        current_date = datetime(2026, 3, 31)
        report_date = datetime(2024, 12, 31)
        
        history = {
            '2024-12-31': {'eps': 4.85}
        }
        
        result = FinancialDataProcessor.check_data_staleness(history, current_date)
        
        assert result is not None
        assert "Potentially Stale Data" in result
        assert "2024-12-31" in result
        # 455 days / 30.44 = 14.95 months, rounds to 14
        assert "14 months old" in result
    
    def test_empty_history(self):
        """Test that empty history returns appropriate warning."""
        current_date = datetime(2025, 6, 1)
        history = {}
        
        result = FinancialDataProcessor.check_data_staleness(history, current_date)
        
        assert result is not None
        assert "No financial history available" in result
    
    def test_future_date_clock_skew(self):
        """Test that future report date returns warning (clock skew)."""
        current_date = datetime(2025, 6, 1)
        # Report date is in the future
        history = {
            '2025-12-31': {'eps': 4.85}
        }
        
        result = FinancialDataProcessor.check_data_staleness(history, current_date)
        
        assert result is not None
        assert "Data date is in the future" in result
        assert "2025-12-31" in result
    
    def test_invalid_date_format(self):
        """Test that invalid date format returns None (graceful degradation)."""
        current_date = datetime(2025, 6, 1)
        history = {
            'invalid-date': {'eps': 4.85}
        }
        
        result = FinancialDataProcessor.check_data_staleness(history, current_date)
        
        # Should return None and log error (graceful degradation)
        assert result is None
    
    def test_default_current_date(self):
        """Test that function uses datetime.now() when current_date not provided."""
        # Create history with old data
        old_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        history = {
            old_date: {'eps': 4.85}
        }
        
        result = FinancialDataProcessor.check_data_staleness(history)
        
        # Should detect staleness using current date
        assert result is not None
        assert "Potentially Stale Data" in result
    
    def test_multiple_years_uses_most_recent(self):
        """Test that function uses most recent year when multiple years present."""
        current_date = datetime(2025, 6, 1)
        
        history = {
            '2024-12-31': {'eps': 4.85},  # 5 months old (fresh)
            '2023-12-31': {'eps': 25.51},  # 17 months old (stale)
            '2022-12-31': {'eps': 14.40}   # 29 months old (very stale)
        }
        
        result = FinancialDataProcessor.check_data_staleness(history, current_date)
        
        # Should use most recent year (2024-12-31) which is fresh
        assert result is None
    
    def test_non_december_fiscal_year_end(self):
        """Test with non-December fiscal year end (e.g., June 30)."""
        current_date = datetime(2025, 10, 1)
        
        # Microsoft-style June 30 fiscal year end
        history = {
            '2024-06-30': {'eps': 10.00}  # 15 months old
        }
        
        result = FinancialDataProcessor.check_data_staleness(history, current_date)
        
        assert result is not None
        assert "Potentially Stale Data" in result
        assert "2024-06-30" in result
        assert "15 months old" in result
    
    def test_boundary_case_9_months_plus_one_day(self):
        """Test that 9 months + 1 day triggers staleness warning."""
        # 9 months = 274 days (using 30.44 days/month)
        # 9 months + 1 day = 275 days
        current_date = datetime(2025, 10, 1)
        report_date = datetime(2024, 12, 17)  # Approximately 9 months + 1 day ago
        
        history = {
            '2024-12-17': {'eps': 4.85}
        }
        
        result = FinancialDataProcessor.check_data_staleness(history, current_date)
        
        # Should trigger warning (just over 9 months)
        assert result is not None
        assert "Potentially Stale Data" in result
    
    def test_warning_message_format(self):
        """Test that warning message has correct format."""
        current_date = datetime(2025, 10, 1)
        
        history = {
            '2024-12-31': {'eps': 4.85}
        }
        
        result = FinancialDataProcessor.check_data_staleness(history, current_date)
        
        # Verify message format
        assert result is not None
        assert result.startswith("Potentially Stale Data:")
        assert "Most recent annual report is from" in result
        assert "months old" in result
        # Verify date is included
        assert "2024-12-31" in result
    
    def test_leap_year_handling(self):
        """Test that leap years are handled correctly in date calculations."""
        # 2024 is a leap year
        current_date = datetime(2025, 2, 28)
        report_date = datetime(2024, 5, 31)  # 9 months ago in leap year
        
        history = {
            '2024-05-31': {'eps': 4.85}
        }
        
        result = FinancialDataProcessor.check_data_staleness(history, current_date)
        
        # Should handle leap year correctly
        # 273 days / 30.44 = 8.97 months (just under 9 months)
        assert result is None
    
    def test_very_old_data_multiple_years(self):
        """Test that very old data (2+ years) is correctly flagged."""
        current_date = datetime(2027, 1, 1)
        
        history = {
            '2024-12-31': {'eps': 4.85}  # 24 months old
        }
        
        result = FinancialDataProcessor.check_data_staleness(history, current_date)
        
        assert result is not None
        assert "Potentially Stale Data" in result
        assert "24 months old" in result
