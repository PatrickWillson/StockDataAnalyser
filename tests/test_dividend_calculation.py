"""
Unit tests for dividend calculation logic in FinancialDataProcessor.

Tests Requirements 2.1, 2.2, 2.3, 2.4:
- Prioritize Cash Flow dividendsPaid over ForwardAnnualDividendRate
- Use ForwardAnnualDividendRate for most recent year only if cash flow missing
- Do NOT use ForwardAnnualDividendRate for historical years
- Source indicators correctly identify data source
"""

import pytest
from core.financial_data_processor import FinancialDataProcessor


class TestDividendCalculation:
    """Test dividend calculation logic per Graham's methodology."""
    
    def test_prioritizes_cash_flow_over_forward_rate(self):
        """
        Test that cash flow dividendsPaid is prioritized over ForwardAnnualDividendRate.
        Requirements: 2.1, 2.2
        """
        processor = FinancialDataProcessor(debug=False)
        
        # Mock data with both cash flow and forward rate
        data = {
            'General': {'CurrencyCode': 'USD'},
            'SplitsDividends': {
                'ForwardAnnualDividendRate': 2.50  # Forward rate available
            },
            'Financials': {
                'Cash_Flow': {
                    'currency_symbol': 'USD',
                    'yearly': {
                        '2024-12-31': {'dividendsPaid': -1000000},  # Negative (cash outflow)
                        '2023-12-31': {'dividendsPaid': -900000},
                        '2022-12-31': {'dividendsPaid': -800000}
                    }
                }
            },
            'outstandingShares': {
                'annual': {
                    '0': {'date': '2024', 'shares': 500000},
                    '1': {'date': '2023', 'shares': 500000},
                    '2': {'date': '2022', 'shares': 500000}
                }
            }
        }
        
        result, forward_rate, is_amount, currency, sources = processor.parse_dividend_history(data)
        
        # Should use cash flow for all years, not forward rate
        assert '2024' in result
        assert '2023' in result
        assert '2022' in result
        
        # Verify cash flow values are used (dividendsPaid / shares)
        assert result['2024'] == pytest.approx(2.0, rel=0.01)  # 1000000 / 500000
        assert result['2023'] == pytest.approx(1.8, rel=0.01)  # 900000 / 500000
        assert result['2022'] == pytest.approx(1.6, rel=0.01)  # 800000 / 500000
        
        # All should be marked as cash_flow source
        assert sources['2024'] == 'cash_flow'
        assert sources['2023'] == 'cash_flow'
        assert sources['2022'] == 'cash_flow'
    
    def test_uses_forward_rate_for_most_recent_year_only(self):
        """
        Test that ForwardAnnualDividendRate is used for most recent year if cash flow missing.
        Requirements: 2.3
        """
        processor = FinancialDataProcessor(debug=False)
        
        # Mock data with forward rate but NO cash flow for most recent year
        data = {
            'General': {'CurrencyCode': 'USD'},
            'SplitsDividends': {
                'ForwardAnnualDividendRate': 2.50
            },
            'Financials': {
                'Cash_Flow': {
                    'currency_symbol': 'USD',
                    'yearly': {
                        '2024-12-31': {},  # No dividendsPaid for 2024
                        '2023-12-31': {'dividendsPaid': -900000},
                        '2022-12-31': {'dividendsPaid': -800000}
                    }
                }
            },
            'outstandingShares': {
                'annual': {
                    '0': {'date': '2024', 'shares': 500000},
                    '1': {'date': '2023', 'shares': 500000},
                    '2': {'date': '2022', 'shares': 500000}
                }
            }
        }
        
        result, forward_rate, is_amount, currency, sources = processor.parse_dividend_history(data)
        
        # Most recent year (2024) should use forward rate
        assert '2024' in result
        assert result['2024'] == 2.50
        assert sources['2024'] == 'forward_rate'
        
        # Historical years should use cash flow
        assert '2023' in result
        assert result['2023'] == pytest.approx(1.8, rel=0.01)
        assert sources['2023'] == 'cash_flow'
        
        assert '2022' in result
        assert result['2022'] == pytest.approx(1.6, rel=0.01)
        assert sources['2022'] == 'cash_flow'
    
    def test_does_not_use_forward_rate_for_historical_years(self):
        """
        Test that ForwardAnnualDividendRate is NOT used for historical years.
        Requirements: 2.4
        """
        processor = FinancialDataProcessor(debug=False)
        
        # Mock data with forward rate but NO cash flow for any year
        data = {
            'General': {'CurrencyCode': 'USD'},
            'SplitsDividends': {
                'ForwardAnnualDividendRate': 2.50
            },
            'Financials': {
                'Cash_Flow': {
                    'currency_symbol': 'USD',
                    'yearly': {
                        '2024-12-31': {},  # No dividendsPaid
                        '2023-12-31': {},  # No dividendsPaid
                        '2022-12-31': {}   # No dividendsPaid
                    }
                }
            },
            'outstandingShares': {
                'annual': {
                    '0': {'date': '2024', 'shares': 500000},
                    '1': {'date': '2023', 'shares': 500000},
                    '2': {'date': '2022', 'shares': 500000}
                }
            }
        }
        
        result, forward_rate, is_amount, currency, sources = processor.parse_dividend_history(data)
        
        # Only most recent year (2024) should have forward rate
        assert '2024' in result
        assert result['2024'] == 2.50
        assert sources['2024'] == 'forward_rate'
        
        # Historical years should NOT be in result (left as zero/missing)
        assert '2023' not in result
        assert '2022' not in result
    
    def test_source_indicator_correctly_identifies_data_source(self):
        """
        Test that source indicators correctly identify whether data comes from
        cash_flow or forward_rate.
        Requirements: 2.1, 2.2, 2.3, 2.4
        """
        processor = FinancialDataProcessor(debug=False)
        
        # Mock data with mixed sources
        data = {
            'General': {'CurrencyCode': 'USD'},
            'SplitsDividends': {
                'ForwardAnnualDividendRate': 3.00
            },
            'Financials': {
                'Cash_Flow': {
                    'currency_symbol': 'USD',
                    'yearly': {
                        '2024-12-31': {},  # Missing - should use forward rate
                        '2023-12-31': {'dividendsPaid': -1500000},  # Present - use cash flow
                        '2022-12-31': {'dividendsPaid': -1400000},  # Present - use cash flow
                        '2021-12-31': {}   # Missing - should be omitted (historical)
                    }
                }
            },
            'outstandingShares': {
                'annual': {
                    '0': {'date': '2024', 'shares': 500000},
                    '1': {'date': '2023', 'shares': 500000},
                    '2': {'date': '2022', 'shares': 500000},
                    '3': {'date': '2021', 'shares': 500000}
                }
            }
        }
        
        result, forward_rate, is_amount, currency, sources = processor.parse_dividend_history(data)
        
        # Verify source indicators
        assert sources['2024'] == 'forward_rate'  # Most recent, missing cash flow
        assert sources['2023'] == 'cash_flow'     # Has cash flow
        assert sources['2022'] == 'cash_flow'     # Has cash flow
        assert '2021' not in sources              # Historical, missing cash flow
        
        # Verify values
        assert result['2024'] == 3.00
        assert result['2023'] == pytest.approx(3.0, rel=0.01)  # 1500000 / 500000
        assert result['2022'] == pytest.approx(2.8, rel=0.01)  # 1400000 / 500000
        assert '2021' not in result
    
    def test_handles_zero_forward_rate(self):
        """
        Test that zero or missing forward rate doesn't cause issues.
        """
        processor = FinancialDataProcessor(debug=False)
        
        data = {
            'General': {'CurrencyCode': 'USD'},
            'SplitsDividends': {
                'ForwardAnnualDividendRate': 0.0  # Zero forward rate
            },
            'Financials': {
                'Cash_Flow': {
                    'currency_symbol': 'USD',
                    'yearly': {
                        '2024-12-31': {},  # No cash flow
                    }
                }
            },
            'outstandingShares': {
                'annual': {
                    '0': {'date': '2024', 'shares': 500000}
                }
            }
        }
        
        result, forward_rate, is_amount, currency, sources = processor.parse_dividend_history(data)
        
        # Should not add forward rate if it's zero
        assert '2024' not in result or result['2024'] == 0.0
    
    def test_handles_missing_shares_data(self):
        """
        Test that missing shares data is handled gracefully.
        """
        processor = FinancialDataProcessor(debug=False)
        
        data = {
            'General': {'CurrencyCode': 'USD'},
            'SplitsDividends': {
                'ForwardAnnualDividendRate': 2.50
            },
            'Financials': {
                'Cash_Flow': {
                    'currency_symbol': 'USD',
                    'yearly': {
                        '2024-12-31': {'dividendsPaid': -1000000}
                    }
                }
            },
            'outstandingShares': {
                'annual': {}  # No shares data
            }
        }
        
        result, forward_rate, is_amount, currency, sources = processor.parse_dividend_history(data)
        
        # Should fall back to forward rate for most recent year
        assert '2024' in result
        assert result['2024'] == 2.50
        assert sources['2024'] == 'forward_rate'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
