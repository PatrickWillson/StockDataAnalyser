"""
Unit tests for Financial History section generator.

Tests table generation, data formatting, and year sorting.
"""

import pytest
from output.sections.financial_history import FinancialHistorySection


class TestFinancialHistorySection:
    """Tests for FinancialHistorySection class."""
    
    def create_test_financial_data(self):
        """Create test financial data dictionary with multiple years."""
        return {
            'currency': 'USD',
            'is_dividend_amounts': True,
            'history': {
                '2023-12-31': {
                    'revenue': 383285000000.0,
                    'net_income': 96995000000.0,
                    'eps': 6.13,
                    'dividend': 0.96,
                    'total_equity': 62146000000.0,
                    'shares_outstanding': 15821900000.0
                },
                '2022-12-31': {
                    'revenue': 394328000000.0,
                    'net_income': 99803000000.0,
                    'eps': 6.15,
                    'dividend': 0.92,
                    'total_equity': 50672000000.0,
                    'shares_outstanding': 16325800000.0
                },
                '2021-12-31': {
                    'revenue': 365817000000.0,
                    'net_income': 94680000000.0,
                    'eps': 5.67,
                    'dividend': 0.88,
                    'total_equity': 63090000000.0,
                    'shares_outstanding': 16701300000.0
                },
                '2020-12-31': {
                    'revenue': 274515000000.0,
                    'net_income': 57411000000.0,
                    'eps': 3.31,
                    'dividend': 0.82,
                    'total_equity': 65339000000.0,
                    'shares_outstanding': 17352100000.0
                }
            }
        }
    
    def test_section_generation_with_valid_data(self):
        """Test financial history section generates correctly with valid data."""
        financial_data = self.create_test_financial_data()
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Check section header
        assert "## SECTION 6: 20-YEAR FINANCIALS (STANDARDIZED)" in lines
        
        # Check currency note
        assert "*All values in USD*" in lines
        
        # Check lines is a list
        assert isinstance(lines, list)
        
        # Check all lines are strings
        assert all(isinstance(line, str) for line in lines)
    
    def test_table_header_with_dividend_amounts(self):
        """Test table header shows 'Div/Share' when dividend amounts are available."""
        financial_data = self.create_test_financial_data()
        financial_data['is_dividend_amounts'] = True
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Find header line
        header_lines = [line for line in lines if "| Year |" in line and "Revenue" in line]
        assert len(header_lines) == 1
        assert "Div/Share" in header_lines[0]
    
    def test_table_header_with_dividend_counts(self):
        """Test table header shows 'Div Count' when only dividend counts are available."""
        financial_data = self.create_test_financial_data()
        financial_data['is_dividend_amounts'] = False
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Find header line
        header_lines = [line for line in lines if "| Year |" in line and "Revenue" in line]
        assert len(header_lines) == 1
        assert "Div Count" in header_lines[0]
    
    def test_table_structure(self):
        """Test table has proper markdown structure."""
        financial_data = self.create_test_financial_data()
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Find table header and separator
        header_idx = next(i for i, line in enumerate(lines) if "| Year |" in line and "Revenue" in line)
        separator_idx = header_idx + 1
        
        # Check separator line
        assert lines[separator_idx].startswith("|------|")
        assert "------|" in lines[separator_idx]
    
    def test_year_sorting_descending(self):
        """Test years are sorted in descending order (most recent first)."""
        financial_data = self.create_test_financial_data()
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Extract year rows
        year_rows = [line for line in lines if line.startswith("| 20")]
        
        # Extract years from rows
        years = [row.split("|")[1].strip() for row in year_rows]
        
        # Check descending order
        assert years == sorted(years, reverse=True)
        
        # Check most recent year is first (now displays just year, not full date)
        assert years[0] == "2023"
    
    def test_data_formatting_complete_year(self):
        """Test data formatting for a complete year with all financial data."""
        financial_data = self.create_test_financial_data()
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Find 2023 row (now displays just year)
        row_2023 = next(line for line in lines if line.startswith("| 2023 |"))
        
        # Check all values are present
        assert "383285000000.0" in row_2023  # Revenue
        assert "96995000000.0" in row_2023  # Net Income
        assert "6.13" in row_2023  # EPS
        assert "0.96" in row_2023  # Dividend
        
        # Check BVPS is calculated: 62146000000.0 / 15821900000.0 = 3.93
        assert "3.93" in row_2023
    
    def test_data_formatting_zero_values(self):
        """Test data formatting when values are zero."""
        financial_data = self.create_test_financial_data()
        financial_data['history']['2020-12-31']['revenue'] = 0.0
        financial_data['history']['2020-12-31']['net_income'] = 0.0
        financial_data['history']['2020-12-31']['eps'] = 0.0
        financial_data['history']['2020-12-31']['dividend'] = 0.0
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Find 2020 row (now displays just year)
        row_2020 = next(line for line in lines if line.startswith("| 2020 |"))
        
        # Check zero values show as N/A
        parts = row_2020.split("|")
        assert "N/A" in parts[2]  # Revenue
        assert "N/A" in parts[3]  # Net Income
        assert "N/A" in parts[4]  # EPS
        assert "N/A" in parts[5]  # Dividend
    
    def test_incomplete_year_handling(self):
        """Test handling of incomplete years (dividend only, no financial statements)."""
        financial_data = self.create_test_financial_data()
        # Add incomplete year with only dividend
        financial_data['history']['2024-12-31'] = {
            'revenue': 0.0,
            'net_income': 0.0,
            'eps': 0.0,
            'dividend': 1.00,
            'total_equity': 0.0,
            'shares_outstanding': 0.0
        }
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Find 2024 row (now displays just year)
        row_2024 = next(line for line in lines if line.startswith("| 2024 |"))
        
        # Check incomplete year shows [Data Unavailable]
        assert "[Data Unavailable]" in row_2024
        
        # Check dividend is still shown
        assert "1.0" in row_2024
    
    def test_incomplete_year_note(self):
        """Test note about incomplete years is added when applicable."""
        financial_data = self.create_test_financial_data()
        # Add incomplete year
        financial_data['history']['2024-12-31'] = {
            'revenue': 0.0,
            'net_income': 0.0,
            'eps': 0.0,
            'dividend': 1.00,
            'total_equity': 0.0,
            'shares_outstanding': 0.0
        }
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Check note is present
        note_lines = [line for line in lines if "Data Unavailable" in line and "2024" in line]
        assert len(note_lines) > 0
        
        # Check Graham's principle is mentioned
        graham_lines = [line for line in lines if "Graham's Principle" in line]
        assert len(graham_lines) > 0
    
    def test_no_incomplete_year_note_when_all_complete(self):
        """Test no incomplete year note when all years have complete data."""
        financial_data = self.create_test_financial_data()
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Check no incomplete year note
        incomplete_note_lines = [line for line in lines if "Data Unavailable" in line and "show declared dividends" in line]
        assert len(incomplete_note_lines) == 0
    
    def test_bvps_calculation(self):
        """Test BVPS (Book Value Per Share) calculation."""
        financial_data = self.create_test_financial_data()
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Find 2023 row (now displays just year)
        row_2023 = next(line for line in lines if line.startswith("| 2023 |"))
        
        # Calculate expected BVPS: 62146000000.0 / 15821900000.0 = 3.93
        assert "3.93" in row_2023
    
    def test_bvps_zero_shares(self):
        """Test BVPS when shares outstanding is zero."""
        financial_data = self.create_test_financial_data()
        financial_data['history']['2023-12-31']['shares_outstanding'] = 0
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Find 2023 row (now displays just year)
        row_2023 = next(line for line in lines if line.startswith("| 2023 |"))
        
        # Check BVPS shows as N/A
        parts = row_2023.split("|")
        assert "N/A" in parts[6]  # BVPS column
    
    def test_bvps_zero_equity(self):
        """Test BVPS when total equity is zero."""
        financial_data = self.create_test_financial_data()
        financial_data['history']['2023-12-31']['total_equity'] = 0
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Find 2023 row (now displays just year)
        row_2023 = next(line for line in lines if line.startswith("| 2023 |"))
        
        # Check BVPS shows as N/A
        parts = row_2023.split("|")
        assert "N/A" in parts[6]  # BVPS column
    
    def test_twenty_year_limit(self):
        """Test that only 20 most recent years are shown."""
        financial_data = self.create_test_financial_data()
        
        # Add 25 years of data
        for year in range(1999, 2024):
            financial_data['history'][f'{year}-12-31'] = {
                'revenue': 100000000.0,
                'net_income': 10000000.0,
                'eps': 1.0,
                'dividend': 0.5,
                'total_equity': 50000000.0,
                'shares_outstanding': 10000000.0
            }
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Count year rows
        year_rows = [line for line in lines if line.startswith("| 20") and "-12-31" not in line]
        
        # Should have exactly 20 rows
        assert len(year_rows) == 20
        
        # Check most recent years are included (now displays just year)
        assert any("| 2023 |" in row for row in year_rows)
        assert any("| 2004 |" in row for row in year_rows)
        
        # Check oldest years are excluded
        assert not any("2003-12-31" in row for row in year_rows)
        assert not any("1999-12-31" in row for row in year_rows)
    
    def test_dividend_count_note(self):
        """Test note about dividend counts is added when applicable."""
        financial_data = self.create_test_financial_data()
        financial_data['is_dividend_amounts'] = False
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Check note is present
        note_lines = [line for line in lines if "number of payments per year" in line]
        assert len(note_lines) == 1
    
    def test_no_dividend_count_note_when_amounts_available(self):
        """Test no dividend count note when amounts are available."""
        financial_data = self.create_test_financial_data()
        financial_data['is_dividend_amounts'] = True
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Check note is not present
        note_lines = [line for line in lines if "number of payments per year" in line]
        assert len(note_lines) == 0
    
    def test_currency_display(self):
        """Test currency is displayed correctly in header."""
        financial_data = self.create_test_financial_data()
        financial_data['currency'] = 'GBP'
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Check currency note
        currency_lines = [line for line in lines if "*All values in GBP*" in line]
        assert len(currency_lines) == 1
    
    def test_empty_history(self):
        """Test section generation with empty history."""
        financial_data = {
            'currency': 'USD',
            'is_dividend_amounts': True,
            'history': {}
        }
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Should still generate header and table structure
        assert "## SECTION 6: 20-YEAR FINANCIALS (STANDARDIZED)" in lines
        assert "| Year |" in " ".join(lines)
        
        # Should have no data rows
        year_rows = [line for line in lines if line.startswith("| 20")]
        assert len(year_rows) == 0
    
    def test_section_structure(self):
        """Test overall section structure."""
        financial_data = self.create_test_financial_data()
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Check starts with empty line
        assert lines[0] == ""
        
        # Check has header
        assert lines[1] == "## SECTION 6: 20-YEAR FINANCIALS (STANDARDIZED)"
        
        # Check has currency note
        assert "*All values in USD*" in lines[2]
    
    def test_negative_values_handling(self):
        """Test handling of negative values (losses)."""
        financial_data = self.create_test_financial_data()
        financial_data['history']['2020-12-31']['net_income'] = -5000000000.0
        financial_data['history']['2020-12-31']['eps'] = -0.29
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Find 2020 row (now displays just year)
        row_2020 = next(line for line in lines if line.startswith("| 2020 |"))
        
        # Check negative values are shown
        assert "-5000000000.0" in row_2020
        assert "-0.29" in row_2020
    
    def test_mixed_complete_and_incomplete_years(self):
        """Test handling of mix of complete and incomplete years."""
        financial_data = self.create_test_financial_data()
        
        # Add incomplete year
        financial_data['history']['2024-12-31'] = {
            'revenue': 0.0,
            'net_income': 0.0,
            'eps': 0.0,
            'dividend': 1.00,
            'total_equity': 0.0,
            'shares_outstanding': 0.0
        }
        
        # Add another incomplete year
        financial_data['history']['2019-12-31'] = {
            'revenue': 0.0,
            'net_income': 0.0,
            'eps': 0.0,
            'dividend': 0.75,
            'total_equity': 0.0,
            'shares_outstanding': 0.0
        }
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Check both incomplete years are noted
        note_lines = [line for line in lines if "2024" in line and "2019" in line and "Data Unavailable" in line]
        assert len(note_lines) > 0
    
    def test_data_completeness_note_structure(self):
        """Test structure of data completeness note."""
        financial_data = self.create_test_financial_data()
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Check note header is present
        note_header_lines = [line for line in lines if "**Note on Data Completeness:**" in line]
        assert len(note_header_lines) == 1
    
    def test_large_numbers_formatting(self):
        """Test formatting of large numbers in table."""
        financial_data = self.create_test_financial_data()
        # Set very large revenue
        financial_data['history']['2023-12-31']['revenue'] = 1234567890123.0
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Find 2023 row (now displays just year)
        row_2023 = next(line for line in lines if line.startswith("| 2023 |"))
        
        # Check large number is shown (as string, no special formatting in table)
        assert "1234567890123.0" in row_2023
    
    def test_small_numbers_formatting(self):
        """Test formatting of small numbers in table."""
        financial_data = self.create_test_financial_data()
        # Set small EPS
        financial_data['history']['2023-12-31']['eps'] = 0.01
        
        section = FinancialHistorySection(financial_data)
        lines = section.generate()
        
        # Find 2023 row (now displays just year)
        row_2023 = next(line for line in lines if line.startswith("| 2023 |"))
        
        # Check small number is shown
        assert "0.01" in row_2023
