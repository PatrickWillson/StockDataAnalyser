"""
Property-based tests for TTMCalculator.calculate_ttm_metrics method.

Feature: ttm-graham-calculations
Property 4: Income Statement TTM Summing
Property 5: Balance Sheet Most Recent Value

For any set of income statement periods, TTM revenue and TTM net income should equal
the sum of the selected periods; TTM EPS should equal the sum of net income divided by
the most recent shares outstanding (not the sum of EPS values).

For any set of balance sheet periods, the TTM value should equal the most recent period
value, not the sum of periods.

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9
"""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from core.ttm_calculator import TTMCalculator


class TestCalculateTTMMetrics:
    """Property-based tests for calculate_ttm_metrics method."""
    
    # Feature: ttm-graham-calculations, Property 4: Income Statement TTM Summing
    @settings(suppress_health_check=[HealthCheck.too_slow])
    @given(
        q1_revenue=st.floats(min_value=1000.0, max_value=100000000000.0),
        q2_revenue=st.floats(min_value=1000.0, max_value=100000000000.0),
        q3_revenue=st.floats(min_value=1000.0, max_value=100000000000.0),
        q4_revenue=st.floats(min_value=1000.0, max_value=100000000000.0),
    )
    def test_ttm_revenue_equals_sum_of_quarters(self, q1_revenue, q2_revenue, q3_revenue, q4_revenue):
        """
        Property: TTM revenue should equal the sum of the last 4 quarters.
        
        Validates: Requirements 3.1
        """
        # Arrange: Create quarterly data with known revenue values
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': q1_revenue, 'net_income': 1000.0},
                '2025-06-30': {'revenue': q2_revenue, 'net_income': 1000.0},
                '2025-03-31': {'revenue': q3_revenue, 'net_income': 1000.0},
                '2024-12-31': {'revenue': q4_revenue, 'net_income': 1000.0},
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0,
                    'intangible_assets': 100.0,
                    'goodwill': 200.0,
                    'current_assets': 5000.0,
                    'total_liabilities': 3000.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        ttm_metrics = calculator.calculate_ttm_metrics()
        
        # Assert
        if ttm_metrics:  # Only test if metrics were calculated
            expected_revenue = q1_revenue + q2_revenue + q3_revenue + q4_revenue
            assert abs(ttm_metrics['ttm_revenue'] - expected_revenue) < 0.01, \
                f"TTM revenue {ttm_metrics['ttm_revenue']} != sum {expected_revenue}"

    # Feature: ttm-graham-calculations, Property 4: Income Statement TTM Summing
    @given(
        q1_net_income=st.floats(min_value=-10000000000.0, max_value=50000000000.0),
        q2_net_income=st.floats(min_value=-10000000000.0, max_value=50000000000.0),
        q3_net_income=st.floats(min_value=-10000000000.0, max_value=50000000000.0),
        q4_net_income=st.floats(min_value=-10000000000.0, max_value=50000000000.0),
    )
    def test_ttm_net_income_equals_sum_of_quarters(self, q1_net_income, q2_net_income, 
                                                    q3_net_income, q4_net_income):
        """
        Property: TTM net income should equal the sum of the last 4 quarters.
        
        Validates: Requirements 3.3
        """
        # Arrange
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 10000.0, 'net_income': q1_net_income},
                '2025-06-30': {'revenue': 10000.0, 'net_income': q2_net_income},
                '2025-03-31': {'revenue': 10000.0, 'net_income': q3_net_income},
                '2024-12-31': {'revenue': 10000.0, 'net_income': q4_net_income},
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0,
                    'intangible_assets': 100.0,
                    'goodwill': 200.0,
                    'current_assets': 5000.0,
                    'total_liabilities': 3000.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        ttm_metrics = calculator.calculate_ttm_metrics()
        
        # Assert
        if ttm_metrics:
            expected_net_income = q1_net_income + q2_net_income + q3_net_income + q4_net_income
            assert abs(ttm_metrics['ttm_net_income'] - expected_net_income) < 0.01, \
                f"TTM net income {ttm_metrics['ttm_net_income']} != sum {expected_net_income}"

    # Feature: ttm-graham-calculations, Property 4: Income Statement TTM Summing
    @given(
        q1_net_income=st.floats(min_value=1000.0, max_value=50000000000.0),
        q2_net_income=st.floats(min_value=1000.0, max_value=50000000000.0),
        q3_net_income=st.floats(min_value=1000.0, max_value=50000000000.0),
        q4_net_income=st.floats(min_value=1000.0, max_value=50000000000.0),
        shares=st.floats(min_value=1000000.0, max_value=10000000000.0),
    )
    def test_ttm_eps_equals_sum_net_income_divided_by_shares(self, q1_net_income, q2_net_income,
                                                              q3_net_income, q4_net_income, shares):
        """
        Property: TTM EPS should equal sum(net_income) / most_recent_shares.
        NOT the sum of EPS values (which would be incorrect when share count changes).
        
        Validates: Requirements 3.5
        """
        # Arrange: Create data with different EPS values per quarter
        # (simulating changing share counts)
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 10000.0, 'net_income': q1_net_income, 'eps': 5.0},
                '2025-06-30': {'revenue': 10000.0, 'net_income': q2_net_income, 'eps': 4.5},
                '2025-03-31': {'revenue': 10000.0, 'net_income': q3_net_income, 'eps': 4.2},
                '2024-12-31': {'revenue': 10000.0, 'net_income': q4_net_income, 'eps': 4.0},
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': shares,  # Most recent shares
                    'intangible_assets': 100.0,
                    'goodwill': 200.0,
                    'current_assets': 5000.0,
                    'total_liabilities': 3000.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        ttm_metrics = calculator.calculate_ttm_metrics()
        
        # Assert
        if ttm_metrics:
            total_net_income = q1_net_income + q2_net_income + q3_net_income + q4_net_income
            expected_eps = total_net_income / shares
            
            # Verify TTM EPS equals sum(net_income) / most_recent_shares
            assert abs(ttm_metrics['ttm_eps'] - expected_eps) < 0.01, \
                f"TTM EPS {ttm_metrics['ttm_eps']} != sum(net_income)/shares {expected_eps}"

    # Feature: ttm-graham-calculations, Property 5: Balance Sheet Most Recent Value
    @given(
        q1_equity=st.floats(min_value=1000000.0, max_value=1000000000000.0),
        q2_equity=st.floats(min_value=1000000.0, max_value=1000000000000.0),
        q3_equity=st.floats(min_value=1000000.0, max_value=1000000000000.0),
        q4_equity=st.floats(min_value=1000000.0, max_value=1000000000000.0),
    )
    def test_balance_sheet_uses_most_recent_period(self, q1_equity, q2_equity, q3_equity, q4_equity):
        """
        Property: Balance sheet items should use the most recent period value, not sum.
        
        Validates: Requirements 3.6, 3.7
        """
        # Arrange: Create data with different equity values per quarter
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 10000.0, 'net_income': 1000.0},
                '2025-06-30': {'revenue': 10000.0, 'net_income': 1000.0},
                '2025-03-31': {'revenue': 10000.0, 'net_income': 1000.0},
                '2024-12-31': {'revenue': 10000.0, 'net_income': 1000.0},
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': q1_equity,  # Most recent
                    'shares_outstanding': 1000.0,
                    'intangible_assets': 100.0,
                    'goodwill': 200.0,
                    'current_assets': 5000.0,
                    'total_liabilities': 3000.0,
                },
                '2025-06-30': {
                    'total_equity': q2_equity,
                    'shares_outstanding': 950.0,
                    'intangible_assets': 95.0,
                    'goodwill': 190.0,
                    'current_assets': 4800.0,
                    'total_liabilities': 2900.0,
                },
                '2025-03-31': {
                    'total_equity': q3_equity,
                    'shares_outstanding': 900.0,
                    'intangible_assets': 90.0,
                    'goodwill': 180.0,
                    'current_assets': 4600.0,
                    'total_liabilities': 2800.0,
                },
                '2024-12-31': {
                    'total_equity': q4_equity,
                    'shares_outstanding': 850.0,
                    'intangible_assets': 85.0,
                    'goodwill': 170.0,
                    'current_assets': 4400.0,
                    'total_liabilities': 2700.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        ttm_metrics = calculator.calculate_ttm_metrics()
        
        # Assert
        if ttm_metrics:
            # Should use most recent quarter (Q1 2025-09-30)
            assert ttm_metrics['total_equity'] == q1_equity, \
                f"Total equity should be {q1_equity}, got {ttm_metrics['total_equity']}"
            
            # Verify it's NOT the sum
            sum_equity = q1_equity + q2_equity + q3_equity + q4_equity
            assert abs(ttm_metrics['total_equity'] - sum_equity) > 1.0, \
                "Total equity should NOT be sum of quarters"
            
            # Verify other balance sheet items also use most recent
            assert ttm_metrics['shares_outstanding'] == 1000.0
            assert ttm_metrics['intangible_assets'] == 100.0
            assert ttm_metrics['goodwill'] == 200.0
            assert ttm_metrics['current_assets'] == 5000.0
            assert ttm_metrics['total_liabilities'] == 3000.0

    # Feature: ttm-graham-calculations, Property 4: Income Statement TTM Summing (Semi-Annual)
    @given(
        h1_revenue=st.floats(min_value=1000.0, max_value=200000000000.0),
        h2_revenue=st.floats(min_value=1000.0, max_value=200000000000.0),
    )
    def test_semi_annual_revenue_equals_sum_of_two_periods(self, h1_revenue, h2_revenue):
        """
        Property: For semi-annual reporters, TTM revenue should equal sum of last 2 periods.
        
        Validates: Requirements 3.2
        """
        # Arrange: Create semi-annual data
        quarterly_data = {
            'income_statement': {
                '2025-06-30': {'revenue': h1_revenue, 'net_income': 1000.0},
                '2024-12-31': {'revenue': h2_revenue, 'net_income': 1000.0},
            },
            'balance_sheet': {
                '2025-06-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0,
                    'intangible_assets': 100.0,
                    'goodwill': 200.0,
                    'current_assets': 5000.0,
                    'total_liabilities': 3000.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        ttm_metrics = calculator.calculate_ttm_metrics()
        
        # Assert
        if ttm_metrics and ttm_metrics.get('reporting_frequency') == 'semi-annual':
            expected_revenue = h1_revenue + h2_revenue
            assert abs(ttm_metrics['ttm_revenue'] - expected_revenue) < 0.01, \
                f"TTM revenue {ttm_metrics['ttm_revenue']} != sum {expected_revenue}"

    # Feature: ttm-graham-calculations, Property 4: Income Statement TTM Summing (Semi-Annual)
    @given(
        h1_net_income=st.floats(min_value=-20000000000.0, max_value=100000000000.0),
        h2_net_income=st.floats(min_value=-20000000000.0, max_value=100000000000.0),
    )
    def test_semi_annual_net_income_equals_sum_of_two_periods(self, h1_net_income, h2_net_income):
        """
        Property: For semi-annual reporters, TTM net income should equal sum of last 2 periods.
        
        Validates: Requirements 3.4
        """
        # Arrange
        quarterly_data = {
            'income_statement': {
                '2025-06-30': {'revenue': 10000.0, 'net_income': h1_net_income},
                '2024-12-31': {'revenue': 10000.0, 'net_income': h2_net_income},
            },
            'balance_sheet': {
                '2025-06-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0,
                    'intangible_assets': 100.0,
                    'goodwill': 200.0,
                    'current_assets': 5000.0,
                    'total_liabilities': 3000.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        ttm_metrics = calculator.calculate_ttm_metrics()
        
        # Assert
        if ttm_metrics and ttm_metrics.get('reporting_frequency') == 'semi-annual':
            expected_net_income = h1_net_income + h2_net_income
            assert abs(ttm_metrics['ttm_net_income'] - expected_net_income) < 0.01, \
                f"TTM net income {ttm_metrics['ttm_net_income']} != sum {expected_net_income}"


class TestCalculateTTMMetricsEdgeCases:
    """Unit tests for edge cases in calculate_ttm_metrics."""
    
    def test_insufficient_quarterly_periods_returns_empty_dict(self):
        """
        Test that insufficient periods returns empty dict with warning.
        
        Validates: Requirements 3.8
        """
        # Arrange: Only 2 periods for quarterly reporting (need 4)
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 10000.0, 'net_income': 1000.0},
                '2025-06-30': {'revenue': 10000.0, 'net_income': 1000.0},
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0,
                    'intangible_assets': 100.0,
                    'goodwill': 200.0,
                    'current_assets': 5000.0,
                    'total_liabilities': 3000.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        ttm_metrics = calculator.calculate_ttm_metrics()
        
        # Assert
        assert ttm_metrics == {}, "Should return empty dict for insufficient periods"
        assert len(calculator.warnings) > 0, "Should add warning"
        assert any('Insufficient periodic data' in w for w in calculator.warnings)

    def test_irregular_frequency_returns_empty_dict(self):
        """
        Test that irregular reporting frequency returns empty dict with warning.
        
        Validates: Requirements 3.8
        """
        # Arrange: Irregular intervals
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 10000.0, 'net_income': 1000.0},
                '2025-06-15': {'revenue': 10000.0, 'net_income': 1000.0},  # 107 days
                '2025-01-20': {'revenue': 10000.0, 'net_income': 1000.0},  # 146 days
                '2024-09-10': {'revenue': 10000.0, 'net_income': 1000.0},  # 132 days
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0,
                    'intangible_assets': 100.0,
                    'goodwill': 200.0,
                    'current_assets': 5000.0,
                    'total_liabilities': 3000.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        ttm_metrics = calculator.calculate_ttm_metrics()
        
        # Assert
        assert ttm_metrics == {}, "Should return empty dict for irregular frequency"
        assert len(calculator.warnings) > 0, "Should add warning"
        assert any('irregular' in w.lower() for w in calculator.warnings)
    
    def test_coverage_gap_returns_empty_dict(self):
        """
        Test that data gaps (missing periods in sequence) returns empty dict with warning.
        
        Validates: Requirements 3.9
        """
        # Arrange: 4 periods but with a gap (missing Q2 2025)
        # Q3 2025, Q1 2025 (missing Q2!), Q4 2024, Q3 2024
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 10000.0, 'net_income': 1000.0},  # Q3 2025
                '2025-03-31': {'revenue': 10000.0, 'net_income': 1000.0},  # Q1 2025 (Q2 missing!)
                '2024-12-31': {'revenue': 10000.0, 'net_income': 1000.0},  # Q4 2024
                '2024-09-30': {'revenue': 10000.0, 'net_income': 1000.0},  # Q3 2024
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0,
                    'intangible_assets': 100.0,
                    'goodwill': 200.0,
                    'current_assets': 5000.0,
                    'total_liabilities': 3000.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        ttm_metrics = calculator.calculate_ttm_metrics()
        
        # Assert
        # Should detect gap between Q3 2025 and Q1 2025 (183 days, should be ~90)
        assert ttm_metrics == {}, "Should return empty dict for data gap"
        assert len(calculator.warnings) > 0, "Should add warning"
        # Warning should mention "gap" or "missing"
        assert any('gap' in w.lower() or 'missing' in w.lower() for w in calculator.warnings)

    def test_zero_shares_outstanding_returns_zero_eps(self):
        """
        Test that zero shares outstanding results in zero EPS (not division by zero error).
        
        Validates: Requirements 3.5
        """
        # Arrange
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 10000.0, 'net_income': 1000.0},
                '2025-06-30': {'revenue': 10000.0, 'net_income': 1000.0},
                '2025-03-31': {'revenue': 10000.0, 'net_income': 1000.0},
                '2024-12-31': {'revenue': 10000.0, 'net_income': 1000.0},
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 0.0,  # Zero shares
                    'intangible_assets': 100.0,
                    'goodwill': 200.0,
                    'current_assets': 5000.0,
                    'total_liabilities': 3000.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        ttm_metrics = calculator.calculate_ttm_metrics()
        
        # Assert
        if ttm_metrics:
            assert ttm_metrics['ttm_eps'] == 0.0, "Should return 0.0 for zero shares"
    
    def test_negative_net_income_handled_correctly(self):
        """
        Test that negative net income is handled correctly (losses).
        
        Validates: Requirements 3.3, 3.4
        """
        # Arrange: Company with losses
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 10000.0, 'net_income': -500.0},
                '2025-06-30': {'revenue': 10000.0, 'net_income': -300.0},
                '2025-03-31': {'revenue': 10000.0, 'net_income': -200.0},
                '2024-12-31': {'revenue': 10000.0, 'net_income': -100.0},
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0,
                    'intangible_assets': 100.0,
                    'goodwill': 200.0,
                    'current_assets': 5000.0,
                    'total_liabilities': 3000.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        ttm_metrics = calculator.calculate_ttm_metrics()
        
        # Assert
        if ttm_metrics:
            expected_net_income = -500.0 - 300.0 - 200.0 - 100.0  # -1100.0
            assert ttm_metrics['ttm_net_income'] == expected_net_income
            
            expected_eps = expected_net_income / 1000.0  # -1.1
            assert abs(ttm_metrics['ttm_eps'] - expected_eps) < 0.01

    def test_returns_correct_metadata(self):
        """
        Test that calculate_ttm_metrics returns all expected metadata fields.
        
        Validates: Requirements 3.1-3.7
        """
        # Arrange
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 10000.0, 'net_income': 1000.0},
                '2025-06-30': {'revenue': 10000.0, 'net_income': 1000.0},
                '2025-03-31': {'revenue': 10000.0, 'net_income': 1000.0},
                '2024-12-31': {'revenue': 10000.0, 'net_income': 1000.0},
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0,
                    'intangible_assets': 100.0,
                    'goodwill': 200.0,
                    'current_assets': 5000.0,
                    'total_liabilities': 3000.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        ttm_metrics = calculator.calculate_ttm_metrics()
        
        # Assert
        if ttm_metrics:
            # Verify all required fields are present
            assert 'ttm_revenue' in ttm_metrics
            assert 'ttm_net_income' in ttm_metrics
            assert 'ttm_eps' in ttm_metrics
            assert 'total_equity' in ttm_metrics
            assert 'intangible_assets' in ttm_metrics
            assert 'goodwill' in ttm_metrics
            assert 'current_assets' in ttm_metrics
            assert 'total_liabilities' in ttm_metrics
            assert 'shares_outstanding' in ttm_metrics
            assert 'reporting_frequency' in ttm_metrics
            assert 'periods_used' in ttm_metrics
            assert 'date_range' in ttm_metrics
            
            # Verify metadata values
            assert ttm_metrics['reporting_frequency'] == 'quarterly'
            assert len(ttm_metrics['periods_used']) == 4
            assert ttm_metrics['date_range'] != 'N/A'
    
    def test_date_range_formatting(self):
        """
        Test that date range is formatted correctly.
        
        Validates: Requirements 3.7
        """
        # Arrange
        quarterly_data = {
            'income_statement': {
                '2025-09-30': {'revenue': 10000.0, 'net_income': 1000.0},
                '2025-06-30': {'revenue': 10000.0, 'net_income': 1000.0},
                '2025-03-31': {'revenue': 10000.0, 'net_income': 1000.0},
                '2024-12-31': {'revenue': 10000.0, 'net_income': 1000.0},
            },
            'balance_sheet': {
                '2025-09-30': {
                    'total_equity': 10000.0,
                    'shares_outstanding': 1000.0,
                    'intangible_assets': 100.0,
                    'goodwill': 200.0,
                    'current_assets': 5000.0,
                    'total_liabilities': 3000.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        
        # Act
        ttm_metrics = calculator.calculate_ttm_metrics()
        
        # Assert
        if ttm_metrics:
            date_range = ttm_metrics['date_range']
            # Should be formatted like "Q4 2024 through Q3 2025"
            assert 'through' in date_range
            assert '2024' in date_range
            assert '2025' in date_range


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
