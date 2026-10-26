"""
Property-based tests for FinancialDataProcessor.

Tests the new balance sheet extraction logic for total debt and shares outstanding.
"""

from hypothesis import given, strategies as st
from core.financial_data_processor import FinancialDataProcessor


class TestTotalDebtCalculation:
    """Test total debt calculation logic."""
    
    @given(
        long_term=st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False),
        short_term=st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False)
    )
    def test_total_debt_from_components(self, long_term, short_term):
        """
        Property: When both longTermDebt and shortTermDebt are available,
        total_debt should equal their sum.
        """
        processor = FinancialDataProcessor(debug=False)
        
        # Create mock balance sheet data
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'yearly': {
                        '2024-12-31': {
                            'longTermDebt': long_term,
                            'shortTermDebt': short_term,
                            'totalStockholderEquity': 1000000,
                        }
                    }
                }
            }
        }
        
        result = processor.parse_balance_sheet(mock_data)
        
        assert '2024-12-31' in result
        calculated_total = result['2024-12-31']['total_debt']
        expected_total = long_term + short_term
        
        # Allow small floating point differences
        assert abs(calculated_total - expected_total) < 0.01, \
            f"Expected {expected_total}, got {calculated_total}"
    
    @given(
        precalc_total=st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False)
    )
    def test_total_debt_fallback_to_precalculated(self, precalc_total):
        """
        Property: When longTermDebt and shortTermDebt are missing,
        should fall back to shortLongTermDebtTotal.
        """
        processor = FinancialDataProcessor(debug=False)
        
        # Create mock data with only precalculated total
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'yearly': {
                        '2024-12-31': {
                            'shortLongTermDebtTotal': precalc_total,
                            'totalStockholderEquity': 1000000,
                        }
                    }
                }
            }
        }
        
        result = processor.parse_balance_sheet(mock_data)
        
        assert '2024-12-31' in result
        calculated_total = result['2024-12-31']['total_debt']
        
        assert abs(calculated_total - precalc_total) < 0.01, \
            f"Expected {precalc_total}, got {calculated_total}"
    
    def test_total_debt_all_missing_returns_zero(self):
        """
        Property: When all debt fields are missing, total_debt should be 0.
        """
        processor = FinancialDataProcessor(debug=False)
        
        # Create mock data with no debt fields
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'yearly': {
                        '2024-12-31': {
                            'totalStockholderEquity': 1000000,
                        }
                    }
                }
            }
        }
        
        result = processor.parse_balance_sheet(mock_data)
        
        assert '2024-12-31' in result
        assert result['2024-12-31']['total_debt'] == 0.0
    
    def test_total_debt_prefers_components_over_precalculated(self):
        """
        Property: When both components and precalculated total are available,
        should prefer components (more accurate).
        """
        processor = FinancialDataProcessor(debug=False)
        
        # Create mock data with both
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'yearly': {
                        '2024-12-31': {
                            'longTermDebt': 100000000,
                            'shortTermDebt': 50000000,
                            'shortLongTermDebtTotal': 200000000,  # Different value
                            'totalStockholderEquity': 1000000,
                        }
                    }
                }
            }
        }
        
        result = processor.parse_balance_sheet(mock_data)
        
        assert '2024-12-31' in result
        # Should use components (150M), not precalculated (200M)
        assert result['2024-12-31']['total_debt'] == 150000000.0


class TestSharesOutstandingExtraction:
    """Test shares outstanding extraction with fallback chain."""
    
    @given(
        shares=st.floats(min_value=1, max_value=1e12, allow_nan=False, allow_infinity=False)
    )
    def test_shares_from_common_stock(self, shares):
        """
        Property: When commonStockSharesOutstanding is available,
        should use it as primary source.
        """
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'yearly': {
                        '2024-12-31': {
                            'commonStockSharesOutstanding': shares,
                            'totalStockholderEquity': 1000000,
                        }
                    }
                }
            }
        }
        
        result = processor.parse_balance_sheet(mock_data)
        
        assert '2024-12-31' in result
        assert abs(result['2024-12-31']['shares_outstanding'] - shares) < 0.01
    
    def test_shares_fallback_to_weighted_average(self):
        """
        Property: When commonStockSharesOutstanding is missing,
        should fall back to weightedAverageShsOut.
        """
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'yearly': {
                        '2024-12-31': {
                            'weightedAverageShsOut': 5000000000,
                            'totalStockholderEquity': 1000000,
                        }
                    }
                }
            }
        }
        
        result = processor.parse_balance_sheet(mock_data)
        
        assert '2024-12-31' in result
        assert result['2024-12-31']['shares_outstanding'] == 5000000000.0
    
    def test_shares_fallback_to_diluted(self):
        """
        Property: When commonStockSharesOutstanding and weightedAverageShsOut are missing,
        should fall back to weightedAverageShsOutDil.
        """
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'yearly': {
                        '2024-12-31': {
                            'weightedAverageShsOutDil': 5500000000,
                            'totalStockholderEquity': 1000000,
                        }
                    }
                }
            }
        }
        
        result = processor.parse_balance_sheet(mock_data)
        
        assert '2024-12-31' in result
        assert result['2024-12-31']['shares_outstanding'] == 5500000000.0
    
    def test_shares_all_missing_returns_zero(self):
        """
        Property: When all share fields are missing, shares_outstanding should be 0.
        """
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'yearly': {
                        '2024-12-31': {
                            'totalStockholderEquity': 1000000,
                        }
                    }
                }
            }
        }
        
        result = processor.parse_balance_sheet(mock_data)
        
        assert '2024-12-31' in result
        assert result['2024-12-31']['shares_outstanding'] == 0.0
    
    def test_shares_prefers_common_stock_over_weighted(self):
        """
        Property: When multiple share fields are available,
        should prefer commonStockSharesOutstanding.
        """
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'yearly': {
                        '2024-12-31': {
                            'commonStockSharesOutstanding': 7000000000,
                            'weightedAverageShsOut': 6500000000,
                            'weightedAverageShsOutDil': 6800000000,
                            'totalStockholderEquity': 1000000,
                        }
                    }
                }
            }
        }
        
        result = processor.parse_balance_sheet(mock_data)
        
        assert '2024-12-31' in result
        # Should use commonStockSharesOutstanding (7B), not others
        assert result['2024-12-31']['shares_outstanding'] == 7000000000.0


class TestMergeFinancialData:
    """Test that merge_financial_data includes new fields."""
    
    def test_total_debt_included_in_merged_result(self):
        """
        Property: total_debt from balance sheet should appear in merged result.
        """
        balance_sheet = {
            '2024-12-31': {
                'total_equity': 1000000,
                'total_debt': 500000,
                'shares_outstanding': 1000000,
            }
        }
        income_statement = {
            '2024-12-31': {
                'revenue': 5000000,
                'net_income': 500000,
                'eps': 0.50,
            }
        }
        dividend_history = {}
        
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet, income_statement, dividend_history, shares_outstanding=1000000
        )
        
        assert '2024-12-31' in result
        assert 'total_debt' in result['2024-12-31']
        assert result['2024-12-31']['total_debt'] == 500000
    
    def test_shares_outstanding_included_in_merged_result(self):
        """
        Property: shares_outstanding from balance sheet should appear in merged result.
        """
        balance_sheet = {
            '2024-12-31': {
                'total_equity': 1000000,
                'total_debt': 500000,
                'shares_outstanding': 7500000,
            }
        }
        income_statement = {
            '2024-12-31': {
                'revenue': 5000000,
                'net_income': 500000,
                'eps': 0.067,
            }
        }
        dividend_history = {}
        
        result = FinancialDataProcessor.merge_financial_data(
            balance_sheet, income_statement, dividend_history, shares_outstanding=1000000
        )
        
        assert '2024-12-31' in result
        assert 'shares_outstanding' in result['2024-12-31']
        # Should use balance sheet shares (7.5M), not fallback (1M)
        assert result['2024-12-31']['shares_outstanding'] == 7500000
