"""
Unit tests for merge_quarterly_data method.

Tests the merging of quarterly balance sheet and income statement data.
"""

import pytest
from core.financial_data_processor import FinancialDataProcessor


class TestMergeQuarterlyData:
    """Test quarterly data merging."""
    
    def test_merge_quarterly_data_basic(self):
        """Test basic merging of quarterly balance sheet and income statement."""
        processor = FinancialDataProcessor(debug=False)
        
        # Create mock balance sheet data
        balance_sheet = {
            '2025-09-30': {
                'total_equity': 363076000000.0,
                'intangible_assets': 21236000000.0,
                'goodwill': 119497000000.0,
                'current_assets': 189066000000.0,
                'total_liabilities': 273275000000.0,
                'shares_outstanding': 7466000000.0,
            },
            '2025-06-30': {
                'total_equity': 350000000000.0,
                'intangible_assets': 20000000000.0,
                'goodwill': 115000000000.0,
                'current_assets': 180000000000.0,
                'total_liabilities': 260000000000.0,
                'shares_outstanding': 7500000000.0,
            }
        }
        
        # Create mock income statement data
        income_statement = {
            '2025-09-30': {
                'revenue': 77673000000.0,
                'net_income': 27747000000.0,
                'eps': 3.72,
            },
            '2025-06-30': {
                'revenue': 75000000000.0,
                'net_income': 26000000000.0,
                'eps': 3.47,
            }
        }
        
        result = processor.merge_quarterly_data(balance_sheet, income_statement)
        
        # Verify structure
        assert 'balance_sheet' in result
        assert 'income_statement' in result
        
        # Verify balance sheet data is preserved
        assert result['balance_sheet'] == balance_sheet
        assert len(result['balance_sheet']) == 2
        assert result['balance_sheet']['2025-09-30']['total_equity'] == 363076000000.0
        
        # Verify income statement data is preserved
        assert result['income_statement'] == income_statement
        assert len(result['income_statement']) == 2
        assert result['income_statement']['2025-09-30']['revenue'] == 77673000000.0
    
    def test_merge_quarterly_data_empty_balance_sheet(self):
        """Test merging with empty balance sheet."""
        processor = FinancialDataProcessor(debug=False)
        
        balance_sheet = {}
        income_statement = {
            '2025-09-30': {
                'revenue': 77673000000.0,
                'net_income': 27747000000.0,
                'eps': 3.72,
            }
        }
        
        result = processor.merge_quarterly_data(balance_sheet, income_statement)
        
        # Should return empty dict for balance sheet
        assert result['balance_sheet'] == {}
        assert result['income_statement'] == income_statement
    
    def test_merge_quarterly_data_empty_income_statement(self):
        """Test merging with empty income statement."""
        processor = FinancialDataProcessor(debug=False)
        
        balance_sheet = {
            '2025-09-30': {
                'total_equity': 363076000000.0,
                'shares_outstanding': 7466000000.0,
            }
        }
        income_statement = {}
        
        result = processor.merge_quarterly_data(balance_sheet, income_statement)
        
        # Should return empty dict for income statement
        assert result['balance_sheet'] == balance_sheet
        assert result['income_statement'] == {}
    
    def test_merge_quarterly_data_both_empty(self):
        """Test merging with both empty."""
        processor = FinancialDataProcessor(debug=False)
        
        balance_sheet = {}
        income_statement = {}
        
        result = processor.merge_quarterly_data(balance_sheet, income_statement)
        
        # Should return empty dicts for both
        assert result['balance_sheet'] == {}
        assert result['income_statement'] == {}
    
    def test_merge_quarterly_data_none_inputs(self):
        """Test merging with None inputs (graceful handling)."""
        processor = FinancialDataProcessor(debug=False)
        
        result = processor.merge_quarterly_data(None, None)
        
        # Should handle None gracefully and return empty dicts
        assert result['balance_sheet'] == {}
        assert result['income_statement'] == {}
    
    def test_merge_quarterly_data_mismatched_periods(self):
        """Test merging with different periods in balance sheet vs income statement."""
        processor = FinancialDataProcessor(debug=False)
        
        # Balance sheet has 4 quarters
        balance_sheet = {
            '2025-09-30': {'total_equity': 363076000000.0},
            '2025-06-30': {'total_equity': 350000000000.0},
            '2025-03-31': {'total_equity': 340000000000.0},
            '2024-12-31': {'total_equity': 330000000000.0},
        }
        
        # Income statement has only 2 quarters
        income_statement = {
            '2025-09-30': {'revenue': 77673000000.0},
            '2025-06-30': {'revenue': 75000000000.0},
        }
        
        result = processor.merge_quarterly_data(balance_sheet, income_statement)
        
        # Should preserve both as-is (TTMCalculator will handle mismatches)
        assert len(result['balance_sheet']) == 4
        assert len(result['income_statement']) == 2
        assert '2025-03-31' in result['balance_sheet']
        assert '2025-03-31' not in result['income_statement']
    
    def test_merge_quarterly_data_preserves_all_fields(self):
        """Test that all fields are preserved during merge."""
        processor = FinancialDataProcessor(debug=False)
        
        balance_sheet = {
            '2025-09-30': {
                'total_equity': 363076000000.0,
                'intangible_assets': 21236000000.0,
                'goodwill': 119497000000.0,
                'current_assets': 189066000000.0,
                'current_liabilities': 150000000000.0,
                'total_liabilities': 273275000000.0,
                'long_term_debt': 100000000000.0,
                'total_assets': 636351000000.0,
                'total_debt': 110000000000.0,
                'shares_outstanding': 7466000000.0,
            }
        }
        
        income_statement = {
            '2025-09-30': {
                'revenue': 77673000000.0,
                'net_income': 27747000000.0,
                'eps': 3.72,
            }
        }
        
        result = processor.merge_quarterly_data(balance_sheet, income_statement)
        
        # Verify all balance sheet fields are preserved
        bs_q3 = result['balance_sheet']['2025-09-30']
        assert bs_q3['total_equity'] == 363076000000.0
        assert bs_q3['intangible_assets'] == 21236000000.0
        assert bs_q3['goodwill'] == 119497000000.0
        assert bs_q3['current_assets'] == 189066000000.0
        assert bs_q3['current_liabilities'] == 150000000000.0
        assert bs_q3['total_liabilities'] == 273275000000.0
        assert bs_q3['long_term_debt'] == 100000000000.0
        assert bs_q3['total_assets'] == 636351000000.0
        assert bs_q3['total_debt'] == 110000000000.0
        assert bs_q3['shares_outstanding'] == 7466000000.0
        
        # Verify all income statement fields are preserved
        is_q3 = result['income_statement']['2025-09-30']
        assert is_q3['revenue'] == 77673000000.0
        assert is_q3['net_income'] == 27747000000.0
        assert is_q3['eps'] == 3.72


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
