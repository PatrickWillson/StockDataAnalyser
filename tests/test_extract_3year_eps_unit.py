"""
Unit tests for extract_3year_eps_data() function.

Tests specific examples and edge cases for 3-year EPS data extraction
used in normalized Graham Number calculations.
"""

import pytest
from core.financial_data_processor import FinancialDataProcessor


class TestExtract3YearEPSData:
    """Unit tests for extract_3year_eps_data() function."""
    
    def test_valid_3year_eps_data(self):
        """Test extraction with valid 3 years of EPS data."""
        history = {
            '2024-12-31': {'eps': 4.85, 'revenue': 1000},
            '2023-12-31': {'eps': 25.51, 'revenue': 1100},
            '2022-12-31': {'eps': 14.40, 'revenue': 1200},
            '2021-12-31': {'eps': 10.00, 'revenue': 1300},
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        assert result['valid'] is True
        assert result['warning'] is None
        assert result['eps_values'] == [4.85, 25.51, 14.40]
        assert result['years'] == ['2024-12-31', '2023-12-31', '2022-12-31']
    
    def test_exactly_3_years(self):
        """Test extraction with exactly 3 years of data."""
        history = {
            '2024-12-31': {'eps': 5.00},
            '2023-12-31': {'eps': 4.50},
            '2022-12-31': {'eps': 4.00},
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        assert result['valid'] is True
        assert result['warning'] is None
        assert result['eps_values'] == [5.00, 4.50, 4.00]
        assert len(result['years']) == 3
    
    def test_insufficient_data_2_years(self):
        """Test with only 2 years of data (young company)."""
        history = {
            '2024-12-31': {'eps': 5.00},
            '2023-12-31': {'eps': 4.50},
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        assert result['valid'] is False
        assert result['warning'] == "Insufficient data: Only 2 years available, need 3 for normalized calculation"
        assert result['eps_values'] == []
        assert result['years'] == []
    
    def test_insufficient_data_1_year(self):
        """Test with only 1 year of data."""
        history = {
            '2024-12-31': {'eps': 5.00},
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        assert result['valid'] is False
        assert result['warning'] == "Insufficient data: Only 1 years available, need 3 for normalized calculation"
        assert result['eps_values'] == []
        assert result['years'] == []
    
    def test_insufficient_data_0_years(self):
        """Test with empty history."""
        history = {}
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        assert result['valid'] is False
        assert result['warning'] == "No financial history available"
        assert result['eps_values'] == []
        assert result['years'] == []
    
    def test_null_eps_in_one_year(self):
        """Test with null EPS in one of the 3 years."""
        history = {
            '2024-12-31': {'eps': 5.00},
            '2023-12-31': {'eps': None},  # Null EPS
            '2022-12-31': {'eps': 4.00},
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        assert result['valid'] is False
        assert "Missing EPS data for years: 2023-12-31" in result['warning']
        assert result['eps_values'] == [5.00, None, 4.00]
        assert result['years'] == ['2024-12-31', '2023-12-31', '2022-12-31']
    
    def test_na_string_eps(self):
        """Test with 'NA' string as EPS value."""
        history = {
            '2024-12-31': {'eps': 5.00},
            '2023-12-31': {'eps': 'NA'},  # NA string
            '2022-12-31': {'eps': 4.00},
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        assert result['valid'] is False
        assert "Missing EPS data for years: 2023-12-31" in result['warning']
    
    def test_n_slash_a_string_eps(self):
        """Test with 'N/A' string as EPS value."""
        history = {
            '2024-12-31': {'eps': 5.00},
            '2023-12-31': {'eps': 'N/A'},  # N/A string
            '2022-12-31': {'eps': 4.00},
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        assert result['valid'] is False
        assert "Missing EPS data for years: 2023-12-31" in result['warning']
    
    def test_empty_string_eps(self):
        """Test with empty string as EPS value."""
        history = {
            '2024-12-31': {'eps': 5.00},
            '2023-12-31': {'eps': ''},  # Empty string
            '2022-12-31': {'eps': 4.00},
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        assert result['valid'] is False
        assert "Missing EPS data for years: 2023-12-31" in result['warning']
    
    def test_multiple_missing_years(self):
        """Test with multiple years having missing EPS."""
        history = {
            '2024-12-31': {'eps': None},
            '2023-12-31': {'eps': 5.00},
            '2022-12-31': {'eps': 'NA'},
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        assert result['valid'] is False
        assert "Missing EPS data for years:" in result['warning']
        assert "2024-12-31" in result['warning']
        assert "2022-12-31" in result['warning']
    
    def test_missing_eps_key(self):
        """Test when 'eps' key is missing from year data."""
        history = {
            '2024-12-31': {'eps': 5.00},
            '2023-12-31': {'revenue': 1000},  # No 'eps' key
            '2022-12-31': {'eps': 4.00},
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        assert result['valid'] is False
        assert "Missing EPS data for years: 2023-12-31" in result['warning']
    
    def test_negative_eps_values(self):
        """Test with negative EPS values (losses) - should still be valid."""
        history = {
            '2024-12-31': {'eps': 5.00},
            '2023-12-31': {'eps': -2.00},  # Loss
            '2022-12-31': {'eps': -1.00},  # Loss
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        # Negative EPS is valid data (company had losses)
        # The normalized Graham Number calculation will handle negative average
        assert result['valid'] is True
        assert result['warning'] is None
        assert result['eps_values'] == [5.00, -2.00, -1.00]
    
    def test_zero_eps_value(self):
        """Test with zero EPS value - should be valid."""
        history = {
            '2024-12-31': {'eps': 5.00},
            '2023-12-31': {'eps': 0.00},  # Break-even
            '2022-12-31': {'eps': 4.00},
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        # Zero EPS is valid data (company broke even)
        assert result['valid'] is True
        assert result['warning'] is None
        assert result['eps_values'] == [5.00, 0.00, 4.00]
    
    def test_non_numeric_eps(self):
        """Test with non-numeric EPS value."""
        history = {
            '2024-12-31': {'eps': 5.00},
            '2023-12-31': {'eps': 'invalid'},  # Non-numeric
            '2022-12-31': {'eps': 4.00},
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        assert result['valid'] is False
        assert "Missing EPS data for years: 2023-12-31" in result['warning']
    
    def test_most_recent_3_years_selected(self):
        """Test that only the 3 most recent years are selected from 10+ years."""
        history = {
            '2024-12-31': {'eps': 10.00},
            '2023-12-31': {'eps': 9.00},
            '2022-12-31': {'eps': 8.00},
            '2021-12-31': {'eps': 7.00},
            '2020-12-31': {'eps': 6.00},
            '2019-12-31': {'eps': 5.00},
            '2018-12-31': {'eps': 4.00},
            '2017-12-31': {'eps': 3.00},
            '2016-12-31': {'eps': 2.00},
            '2015-12-31': {'eps': 1.00},
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        assert result['valid'] is True
        assert result['eps_values'] == [10.00, 9.00, 8.00]
        assert result['years'] == ['2024-12-31', '2023-12-31', '2022-12-31']
    
    def test_non_december_fiscal_year(self):
        """Test with non-December fiscal year end (e.g., Microsoft uses June 30)."""
        history = {
            '2024-06-30': {'eps': 11.00},
            '2023-06-30': {'eps': 10.00},
            '2022-06-30': {'eps': 9.00},
            '2021-06-30': {'eps': 8.00},
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        assert result['valid'] is True
        assert result['eps_values'] == [11.00, 10.00, 9.00]
        assert result['years'] == ['2024-06-30', '2023-06-30', '2022-06-30']
    
    def test_unsorted_history_input(self):
        """Test that function handles unsorted history correctly."""
        # Provide history in random order
        history = {
            '2022-12-31': {'eps': 8.00},
            '2024-12-31': {'eps': 10.00},
            '2021-12-31': {'eps': 7.00},
            '2023-12-31': {'eps': 9.00},
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        # Should still select most recent 3 years in correct order
        assert result['valid'] is True
        assert result['eps_values'] == [10.00, 9.00, 8.00]
        assert result['years'] == ['2024-12-31', '2023-12-31', '2022-12-31']
    
    def test_string_numeric_eps(self):
        """Test with EPS as string that can be converted to float."""
        history = {
            '2024-12-31': {'eps': '5.00'},  # String but numeric
            '2023-12-31': {'eps': '4.50'},
            '2022-12-31': {'eps': '4.00'},
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        # Should convert string to float successfully
        assert result['valid'] is True
        assert result['eps_values'] == [5.00, 4.50, 4.00]
    
    def test_untc_example_scenario(self):
        """Test UNTC example from design doc: cyclical earnings."""
        history = {
            '2024-12-31': {'eps': 4.85},   # Depressed
            '2023-12-31': {'eps': 25.51},  # Peak
            '2022-12-31': {'eps': 14.40},  # Normal
            '2021-12-31': {'eps': 10.00},
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        assert result['valid'] is True
        assert result['eps_values'] == [4.85, 25.51, 14.40]
        
        # Calculate 3-year average
        avg_eps = sum(result['eps_values']) / 3
        assert avg_eps == pytest.approx(14.92, abs=0.01)
    
    def test_bull_trap_scenario(self):
        """Test bull trap scenario: one peak year masking chronic losses."""
        history = {
            '2024-12-31': {'eps': 5.00},   # Peak year
            '2023-12-31': {'eps': -2.00},  # Loss
            '2022-12-31': {'eps': -1.00},  # Loss
        }
        
        result = FinancialDataProcessor.extract_3year_eps_data(history)
        
        assert result['valid'] is True
        assert result['eps_values'] == [5.00, -2.00, -1.00]
        
        # Calculate 3-year average (should be low)
        avg_eps = sum(result['eps_values']) / 3
        assert avg_eps == pytest.approx(0.67, abs=0.01)


class TestDividendOnlyYearsAreSkipped:
    """
    merge_financial_data adds dividend-only years (dividend data but no statements) with
    revenue, net income, equity and EPS all 0.0. They must not count as one of the 3 EPS years.
    """

    @staticmethod
    def _year(eps, revenue=1000.0, net_income=100.0, total_equity=500.0):
        return {'eps': eps, 'revenue': revenue, 'net_income': net_income, 'total_equity': total_equity}

    DIVIDEND_ONLY = {'eps': 0.0, 'revenue': 0.0, 'net_income': 0.0, 'total_equity': 0.0, 'dividend': 0.96}

    def test_dividend_only_year_is_skipped(self):
        history = {
            '2024-09-30': self.DIVIDEND_ONLY,
            '2023-09-30': self._year(6.24),
            '2022-09-30': self.DIVIDEND_ONLY,
            '2022-09-24': self._year(6.26),
            '2021-09-25': self._year(5.76),
        }

        result = FinancialDataProcessor.extract_3year_eps_data(history)

        assert result['valid'] is True
        assert result['years'] == ['2023-09-30', '2022-09-24', '2021-09-25']
        assert result['eps_values'] == [6.24, 6.26, 5.76]

    def test_fewer_than_three_statement_years_is_insufficient(self):
        history = {'2024-09-30': self.DIVIDEND_ONLY, '2023-09-30': self._year(6.24),
                   '2022-09-24': self._year(6.26)}

        result = FinancialDataProcessor.extract_3year_eps_data(history)

        assert result['valid'] is False
        assert result['warning'] == "Insufficient data: Only 2 years available, need 3 for normalized calculation"

    def test_break_even_year_with_revenue_is_kept(self):
        history = {'2023-12-31': self._year(5.0),
                   '2022-12-31': self._year(0.0, net_income=0.0),
                   '2021-12-31': self._year(4.0)}

        result = FinancialDataProcessor.extract_3year_eps_data(history)

        assert result['valid'] is True
        assert result['eps_values'] == [5.0, 0.0, 4.0]

    def test_loss_year_is_kept(self):
        history = {'2023-12-31': self._year(5.0),
                   '2022-12-31': self._year(-2.0, net_income=-40.0),
                   '2021-12-31': self._year(4.0)}

        result = FinancialDataProcessor.extract_3year_eps_data(history)

        assert result['eps_values'] == [5.0, -2.0, 4.0]

    def test_uses_same_years_as_three_year_average_pe(self):
        from core.graham_math import GrahamCalculator
        history = {
            '2024-09-30': self.DIVIDEND_ONLY,
            '2023-09-30': self._year(6.24),
            '2022-09-30': self.DIVIDEND_ONLY,
            '2022-09-24': self._year(6.26),
            '2021-09-25': self._year(5.76),
            '2020-09-26': self._year(3.28),
        }

        eps_years = FinancialDataProcessor.extract_3year_eps_data(history)['years']
        pe_years = GrahamCalculator({'history': history, 'price': 150.0}).compute_three_year_avg_pe()['years_used']

        assert eps_years == pe_years


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
