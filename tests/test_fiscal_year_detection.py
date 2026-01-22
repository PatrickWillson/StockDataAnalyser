"""
Test fiscal year end detection in merge_financial_data.

This test verifies that the system correctly detects a company's fiscal year end
from existing financial statements and uses it for dividend-only years.
"""

import pytest
from core.financial_data_processor import FinancialDataProcessor


class TestFiscalYearDetection:
    """Test fiscal year end detection for different companies."""
    
    def test_june_fiscal_year_end_msft(self):
        """Test that June 30 fiscal year end is detected (like MSFT)."""
        # Mock financial data with June 30 fiscal year end
        balance_sheet = {
            '2025-06-30': {'total_equity': 1000000},
            '2024-06-30': {'total_equity': 900000},
        }
        income_statement = {
            '2025-06-30': {'revenue': 5000000, 'net_income': 500000, 'eps': 5.0},
            '2024-06-30': {'revenue': 4500000, 'net_income': 450000, 'eps': 4.5},
        }
        dividend_history = {
            '2026': 1.0,  # Dividend declared for 2026 but no financial statements yet
            '2025': 0.9,
            '2024': 0.8,
        }
        
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet, income_statement, dividend_history, 100000
        )
        
        # Should create 2026-06-30 (not 2026-12-31) for dividend-only year
        assert '2026-06-30' in result
        assert '2026-12-31' not in result
        
        # Verify dividend is included
        assert result['2026-06-30']['dividend'] == 1.0
        
        # Verify financial data is missing (dividend-only year)
        assert result['2026-06-30']['revenue'] == 0.0
        assert result['2026-06-30']['net_income'] == 0.0
    
    def test_september_fiscal_year_end_aapl(self):
        """Test that September 30 fiscal year end is detected (like AAPL)."""
        balance_sheet = {
            '2025-09-30': {'total_equity': 2000000},
            '2024-09-30': {'total_equity': 1800000},
        }
        income_statement = {
            '2025-09-30': {'revenue': 10000000, 'net_income': 1000000, 'eps': 10.0},
            '2024-09-30': {'revenue': 9000000, 'net_income': 900000, 'eps': 9.0},
        }
        dividend_history = {
            '2026': 2.0,
            '2025': 1.8,
        }
        
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet, income_statement, dividend_history, 100000
        )
        
        # Should create 2026-09-30 (not 2026-12-31)
        assert '2026-09-30' in result
        assert '2026-12-31' not in result
        assert result['2026-09-30']['dividend'] == 2.0
    
    def test_december_fiscal_year_end_jnj(self):
        """Test that December 31 fiscal year end is detected (like JNJ)."""
        balance_sheet = {
            '2024-12-31': {'total_equity': 3000000},
            '2023-12-31': {'total_equity': 2800000},
        }
        income_statement = {
            '2024-12-31': {'revenue': 15000000, 'net_income': 1500000, 'eps': 15.0},
            '2023-12-31': {'revenue': 14000000, 'net_income': 1400000, 'eps': 14.0},
        }
        dividend_history = {
            '2025': 3.0,
            '2024': 2.8,
        }
        
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet, income_statement, dividend_history, 100000
        )
        
        # Should create 2025-12-31 (default behavior for December fiscal year)
        assert '2025-12-31' in result
        assert result['2025-12-31']['dividend'] == 3.0
    
    def test_mixed_sources_prefers_balance_sheet(self):
        """Test that fiscal year end is detected from either balance sheet or income statement."""
        # Only balance sheet has data
        balance_sheet = {
            '2025-03-31': {'total_equity': 1000000},
        }
        income_statement = {}
        dividend_history = {'2026': 1.0}
        
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet, income_statement, dividend_history, 100000
        )
        
        # Should use March 31 from balance sheet
        assert '2026-03-31' in result
        assert '2026-12-31' not in result
    
    def test_income_statement_only(self):
        """Test fiscal year end detection from income statement when balance sheet is empty."""
        balance_sheet = {}
        income_statement = {
            '2025-01-31': {'revenue': 5000000, 'net_income': 500000, 'eps': 5.0},
        }
        dividend_history = {'2026': 1.0}
        
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet, income_statement, dividend_history, 100000
        )
        
        # Should use January 31 from income statement
        assert '2026-01-31' in result
        assert '2026-12-31' not in result
    
    def test_no_financial_data_defaults_to_december(self):
        """Test that December 31 is used as default when no financial statements exist."""
        balance_sheet = {}
        income_statement = {}
        dividend_history = {'2026': 1.0}
        
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet, income_statement, dividend_history, 100000
        )
        
        # Should default to December 31
        assert '2026-12-31' in result
        assert result['2026-12-31']['dividend'] == 1.0
    
    def test_existing_date_format_preserved(self):
        """Test that dividend years with existing date format are not modified."""
        balance_sheet = {
            '2025-06-30': {'total_equity': 1000000},
        }
        income_statement = {
            '2025-06-30': {'revenue': 5000000, 'net_income': 500000, 'eps': 5.0},
        }
        # Dividend already has full date format
        dividend_history = {
            '2025': 0.9,
        }
        
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet, income_statement, dividend_history, 100000
        )
        
        # Should match existing financial statement date
        assert '2025-06-30' in result
        assert result['2025-06-30']['dividend'] == 0.9
        assert result['2025-06-30']['revenue'] == 5000000
