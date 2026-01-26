"""
Unit tests for parse_quarterly_income_statement method.

Tests the quarterly income statement extraction logic.
"""

import pytest
from core.financial_data_processor import FinancialDataProcessor


class TestParseQuarterlyIncomeStatement:
    """Test quarterly income statement parsing."""
    
    def test_parse_quarterly_income_statement_basic(self):
        """Test basic quarterly income statement parsing."""
        processor = FinancialDataProcessor(debug=False)
        
        # Create mock quarterly data
        mock_data = {
            'Financials': {
                'Income_Statement': {
                    'quarterly': {
                        '2025-09-30': {
                            'totalRevenue': 77673000000.0,
                            'netIncome': 27747000000.0,
                            'eps': 3.72,
                        },
                        '2025-06-30': {
                            'totalRevenue': 75000000000.0,
                            'netIncome': 26000000000.0,
                            'eps': 3.47,
                        },
                        '2025-03-31': {
                            'totalRevenue': 72000000000.0,
                            'netIncome': 25000000000.0,
                            'eps': 3.31,
                        },
                        '2024-12-31': {
                            'totalRevenue': 69139000000.0,
                            'netIncome': 27804000000.0,
                            'eps': 3.66,
                        },
                    }
                }
            }
        }
        
        result = processor.parse_quarterly_income_statement(mock_data)
        
        # Verify we got 4 quarters
        assert len(result) == 4
        
        # Verify periods are sorted descending (most recent first)
        periods = list(result.keys())
        assert periods == ['2025-09-30', '2025-06-30', '2025-03-31', '2024-12-31']
        
        # Verify data extraction for most recent quarter
        q3_2025 = result['2025-09-30']
        assert q3_2025['revenue'] == 77673000000.0
        assert q3_2025['net_income'] == 27747000000.0
        assert q3_2025['eps'] == 3.72
        
        # Verify data for another quarter
        q4_2024 = result['2024-12-31']
        assert q4_2024['revenue'] == 69139000000.0
        assert q4_2024['net_income'] == 27804000000.0
        assert q4_2024['eps'] == 3.66
    
    def test_parse_quarterly_income_statement_sanitizes_na_values(self):
        """Test that 'NA' and null values are sanitized to 0.0."""
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Income_Statement': {
                    'quarterly': {
                        '2025-09-30': {
                            'totalRevenue': 'NA',
                            'netIncome': None,
                            'eps': '',
                        },
                        '2025-06-30': {
                            'totalRevenue': 100000.0,
                            'netIncome': 'N/A',
                            'eps': 1.5,
                        }
                    }
                }
            }
        }
        
        result = processor.parse_quarterly_income_statement(mock_data)
        
        assert len(result) == 2
        
        # Verify NA values are converted to 0.0
        q3_2025 = result['2025-09-30']
        assert q3_2025['revenue'] == 0.0
        assert q3_2025['net_income'] == 0.0
        assert q3_2025['eps'] == 0.0
        
        # Verify valid values are preserved
        q2_2025 = result['2025-06-30']
        assert q2_2025['revenue'] == 100000.0
        assert q2_2025['net_income'] == 0.0
        assert q2_2025['eps'] == 1.5
    
    def test_parse_quarterly_income_statement_missing_data(self):
        """Test handling of missing quarterly data."""
        processor = FinancialDataProcessor(debug=False)
        
        # Test with no quarterly data
        mock_data = {
            'Financials': {
                'Income_Statement': {
                    'yearly': {
                        '2024-12-31': {
                            'totalRevenue': 1000000.0,
                            'netIncome': 100000.0,
                        }
                    }
                }
            }
        }
        
        result = processor.parse_quarterly_income_statement(mock_data)
        
        # Should return empty dict
        assert result == {}
    
    def test_parse_quarterly_income_statement_empty_quarterly(self):
        """Test handling of empty quarterly section."""
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Income_Statement': {
                    'quarterly': {}
                }
            }
        }
        
        result = processor.parse_quarterly_income_statement(mock_data)
        
        # Should return empty dict
        assert result == {}
    
    def test_parse_quarterly_income_statement_eps_fallback(self):
        """Test EPS fallback to alternative field names."""
        processor = FinancialDataProcessor(debug=False)
        
        # Test with alternative EPS field names
        mock_data = {
            'Financials': {
                'Income_Statement': {
                    'quarterly': {
                        '2025-09-30': {
                            'totalRevenue': 100000.0,
                            'netIncome': 10000.0,
                            'basicEPS': 2.5,  # Should use this
                        },
                        '2025-06-30': {
                            'totalRevenue': 95000.0,
                            'netIncome': 9500.0,
                            'epsBasic': 2.4,  # Should use this
                        }
                    }
                }
            }
        }
        
        result = processor.parse_quarterly_income_statement(mock_data)
        
        assert result['2025-09-30']['eps'] == 2.5
        assert result['2025-06-30']['eps'] == 2.4
    
    def test_parse_quarterly_income_statement_net_income_from_continuing_ops(self):
        """Test preference for netIncomeFromContinuingOps over netIncome."""
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Income_Statement': {
                    'quarterly': {
                        '2025-09-30': {
                            'totalRevenue': 100000.0,
                            'netIncomeFromContinuingOps': 12000.0,  # Should use this
                            'netIncome': 10000.0,  # Should ignore this
                            'eps': 2.5,
                        },
                        '2025-06-30': {
                            'totalRevenue': 95000.0,
                            'netIncome': 9500.0,  # Should use this (no continuing ops)
                            'eps': 2.4,
                        }
                    }
                }
            }
        }
        
        result = processor.parse_quarterly_income_statement(mock_data)
        
        # Should prefer netIncomeFromContinuingOps when available
        assert result['2025-09-30']['net_income'] == 12000.0
        
        # Should fall back to netIncome when continuing ops not available
        assert result['2025-06-30']['net_income'] == 9500.0
    
    def test_parse_quarterly_income_statement_missing_fields(self):
        """Test handling of missing fields in quarterly data."""
        processor = FinancialDataProcessor(debug=False)
        
        mock_data = {
            'Financials': {
                'Income_Statement': {
                    'quarterly': {
                        '2025-09-30': {
                            # Only revenue, missing net_income and eps
                            'totalRevenue': 100000.0,
                        },
                        '2025-06-30': {
                            # Only net_income, missing revenue and eps
                            'netIncome': 9500.0,
                        }
                    }
                }
            }
        }
        
        result = processor.parse_quarterly_income_statement(mock_data)
        
        # Should handle missing fields gracefully
        q3_2025 = result['2025-09-30']
        assert q3_2025['revenue'] == 100000.0
        assert q3_2025['net_income'] == 0.0
        assert q3_2025['eps'] == 0.0
        
        q2_2025 = result['2025-06-30']
        assert q2_2025['revenue'] == 0.0
        assert q2_2025['net_income'] == 9500.0
        assert q2_2025['eps'] == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
