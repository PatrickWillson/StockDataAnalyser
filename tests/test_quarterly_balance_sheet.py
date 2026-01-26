"""
Unit tests for parse_quarterly_balance_sheet method.

Tests the quarterly balance sheet extraction logic.
"""

import pytest
from core.financial_data_processor import FinancialDataProcessor


class TestParseQuarterlyBalanceSheet:
    """Test quarterly balance sheet parsing."""
    
    def test_parse_quarterly_balance_sheet_basic(self):
        """Test basic quarterly balance sheet parsing."""
        processor = FinancialDataProcessor(debug=False)
        
        # Create mock quarterly data
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'quarterly': {
                        '2025-09-30': {
                            'totalStockholderEquity': 363076000000.0,
                            'intangibleAssets': 21236000000.0,
                            'goodWill': 119497000000.0,
                            'totalCurrentAssets': 189066000000.0,
                            'totalCurrentLiabilities': 150000000000.0,
                            'totalLiab': 273275000000.0,
                            'longTermDebt': 100000000000.0,
                            'shortTermDebt': 10000000000.0,
                            'totalAssets': 636351000000.0,
                            'commonStockSharesOutstanding': 7466000000.0,
                        },
                        '2025-06-30': {
                            'totalStockholderEquity': 350000000000.0,
                            'intangibleAssets': 20000000000.0,
                            'goodWill': 115000000000.0,
                            'totalCurrentAssets': 180000000000.0,
                            'totalCurrentLiabilities': 145000000000.0,
                            'totalLiab': 260000000000.0,
                            'longTermDebt': 95000000000.0,
                            'shortTermDebt': 9000000000.0,
                            'totalAssets': 610000000000.0,
                            'commonStockSharesOutstanding': 7500000000.0,
                        },
                        '2025-03-31': {
                            'totalStockholderEquity': 340000000000.0,
                            'intangibleAssets': 19000000000.0,
                            'goodWill': 113000000000.0,
                            'totalCurrentAssets': 175000000000.0,
                            'totalCurrentLiabilities': 140000000000.0,
                            'totalLiab': 255000000000.0,
                            'longTermDebt': 92000000000.0,
                            'shortTermDebt': 8500000000.0,
                            'totalAssets': 595000000000.0,
                            'commonStockSharesOutstanding': 7550000000.0,
                        },
                        '2024-12-31': {
                            'totalStockholderEquity': 330000000000.0,
                            'intangibleAssets': 18500000000.0,
                            'goodWill': 111000000000.0,
                            'totalCurrentAssets': 170000000000.0,
                            'totalCurrentLiabilities': 135000000000.0,
                            'totalLiab': 250000000000.0,
                            'longTermDebt': 90000000000.0,
                            'shortTermDebt': 8000000000.0,
                            'totalAssets': 580000000000.0,
                            'commonStockSharesOutstanding': 7600000000.0,
                        },
                    }
                }
            }
        }
        
        result = processor.parse_quarterly_balance_sheet(mock_data)
        
        # Verify we got 4 quarters
        assert len(result) == 4
        
        # Verify periods are sorted descending (most recent first)
        periods = list(result.keys())
        assert periods == ['2025-09-30', '2025-06-30', '2025-03-31', '2024-12-31']
        
        # Verify data extraction for most recent quarter
        q3_2025 = result['2025-09-30']
        assert q3_2025['total_equity'] == 363076000000.0
        assert q3_2025['intangible_assets'] == 21236000000.0
        assert q3_2025['goodwill'] == 119497000000.0
        assert q3_2025['current_assets'] == 189066000000.0
        assert q3_2025['current_liabilities'] == 150000000000.0
        assert q3_2025['total_liabilities'] == 273275000000.0
        assert q3_2025['long_term_debt'] == 100000000000.0
        assert q3_2025['total_assets'] == 636351000000.0
        assert q3_2025['shares_outstanding'] == 7466000000.0
        
        # Verify total debt calculation (long_term + short_term)
        assert q3_2025['total_debt'] == 110000000000.0  # 100B + 10B
    
    def test_parse_quarterly_balance_sheet_sanitizes_na_values(self):
        """Test that 'NA' and null values are sanitized to 0.0."""
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'quarterly': {
                        '2025-09-30': {
                            'totalStockholderEquity': 'NA',
                            'intangibleAssets': None,
                            'goodWill': '',
                            'totalCurrentAssets': 100000.0,
                            'totalCurrentLiabilities': 'N/A',
                            'totalLiab': 50000.0,
                            'longTermDebt': 0,
                            'shortTermDebt': 0,
                            'totalAssets': 150000.0,
                            'commonStockSharesOutstanding': 1000.0,
                        }
                    }
                }
            }
        }
        
        result = processor.parse_quarterly_balance_sheet(mock_data)
        
        assert len(result) == 1
        q3_2025 = result['2025-09-30']
        
        # Verify NA values are converted to 0.0
        assert q3_2025['total_equity'] == 0.0
        assert q3_2025['intangible_assets'] == 0.0
        assert q3_2025['goodwill'] == 0.0
        assert q3_2025['current_liabilities'] == 0.0
        
        # Verify valid values are preserved
        assert q3_2025['current_assets'] == 100000.0
        assert q3_2025['total_liabilities'] == 50000.0
        assert q3_2025['total_assets'] == 150000.0
        assert q3_2025['shares_outstanding'] == 1000.0
    
    def test_parse_quarterly_balance_sheet_missing_data(self):
        """Test handling of missing quarterly data."""
        processor = FinancialDataProcessor(debug=False)
        
        # Test with no quarterly data
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'yearly': {
                        '2024-12-31': {
                            'totalStockholderEquity': 1000000.0,
                        }
                    }
                }
            }
        }
        
        result = processor.parse_quarterly_balance_sheet(mock_data)
        
        # Should return empty dict
        assert result == {}
    
    def test_parse_quarterly_balance_sheet_empty_quarterly(self):
        """Test handling of empty quarterly section."""
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'quarterly': {}
                }
            }
        }
        
        result = processor.parse_quarterly_balance_sheet(mock_data)
        
        # Should return empty dict
        assert result == {}
    
    def test_parse_quarterly_balance_sheet_shares_fallback(self):
        """Test shares outstanding fallback chain."""
        processor = FinancialDataProcessor(debug=False)
        
        # Test with alternative share field names
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'quarterly': {
                        '2025-09-30': {
                            'totalStockholderEquity': 1000000.0,
                            'weightedAverageShsOut': 5000.0,  # Should use this
                            'totalLiab': 500000.0,
                            'totalAssets': 1500000.0,
                        },
                        '2025-06-30': {
                            'totalStockholderEquity': 950000.0,
                            'weightedAverageShsOutDil': 4800.0,  # Should use this
                            'totalLiab': 480000.0,
                            'totalAssets': 1430000.0,
                        }
                    }
                }
            }
        }
        
        result = processor.parse_quarterly_balance_sheet(mock_data)
        
        assert result['2025-09-30']['shares_outstanding'] == 5000.0
        assert result['2025-06-30']['shares_outstanding'] == 4800.0
    
    def test_parse_quarterly_balance_sheet_total_debt_calculation(self):
        """Test total debt calculation logic."""
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Balance_Sheet': {
                    'quarterly': {
                        # Test with components
                        '2025-09-30': {
                            'totalStockholderEquity': 1000000.0,
                            'longTermDebt': 300000.0,
                            'shortTermDebt': 50000.0,
                            'totalLiab': 500000.0,
                            'totalAssets': 1500000.0,
                            'commonStockSharesOutstanding': 1000.0,
                        },
                        # Test with precalculated total
                        '2025-06-30': {
                            'totalStockholderEquity': 950000.0,
                            'shortLongTermDebtTotal': 320000.0,
                            'totalLiab': 480000.0,
                            'totalAssets': 1430000.0,
                            'commonStockSharesOutstanding': 1000.0,
                        },
                        # Test with no debt
                        '2025-03-31': {
                            'totalStockholderEquity': 900000.0,
                            'totalLiab': 450000.0,
                            'totalAssets': 1350000.0,
                            'commonStockSharesOutstanding': 1000.0,
                        }
                    }
                }
            }
        }
        
        result = processor.parse_quarterly_balance_sheet(mock_data)
        
        # Verify total debt from components
        assert result['2025-09-30']['total_debt'] == 350000.0  # 300k + 50k
        
        # Verify total debt from precalculated
        assert result['2025-06-30']['total_debt'] == 320000.0
        
        # Verify zero debt when missing
        assert result['2025-03-31']['total_debt'] == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
