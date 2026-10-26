"""Unit tests for TTM Analysis Section formatting.

Tests the TTMAnalysisSection class for correct markdown generation,
percentage difference calculation, date range formatting, and N/A handling.
"""

import pytest
from output.sections.ttm_analysis import TTMAnalysisSection


def create_minimal_financial_data():
    """Create minimal financial_data dict for testing."""
    return {
        'currency': 'USD',
        'price': 100.0,
        'ttm_dividend': 0.0,
        'ttm_dividend_payments': [],
        'history': {}
    }


class TestTTMAnalysisSectionGeneration:
    """Test TTM section generation with various data scenarios."""
    
    def test_section_header_generation(self):
        """Test that section header is correctly generated."""
        ttm_metrics = {
            'ttm_graham_number': 285.43,
            'ttm_tbvps': 29.87,
            'ttm_net_net': 15.23,
            'ttm_margin_of_safety': 12.5,
            'ttm_pe_ratio': 28.5,
            'ttm_pb_ratio': 13.6,
            'reporting_frequency': 'quarterly',
            'date_range': 'Q4 2024 through Q3 2025',
            'currency': 'USD'
        }
        
        annual_metrics = {
            'graham_number': 250.00,
            'tbvps': 28.00,
            'net_net_value': 14.00,
            'margin_of_safety': 10.0,
            'pe_ratio': 23.4,
            'pb_ratio': 12.0
        }
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        lines = section.generate()
        
        # Check header exists
        assert "## SECTION 1.5: TTM (TRAILING TWELVE MONTHS) ANALYSIS" in lines
        assert any("TTM calculations provide more current metrics" in line for line in lines)
    
    def test_reporting_frequency_display(self):
        """Test that reporting frequency is correctly displayed."""
        ttm_metrics = {
            'ttm_graham_number': 285.43,
            'reporting_frequency': 'quarterly',
            'date_range': 'Q4 2024 through Q3 2025',
            'currency': 'USD'
        }
        
        annual_metrics = {'graham_number': 250.00}
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        lines = section.generate()
        
        # Check frequency is displayed
        assert any("Reporting Frequency: Quarterly" in line for line in lines)
    
    def test_semi_annual_frequency_display(self):
        """Test that semi-annual frequency is correctly displayed."""
        ttm_metrics = {
            'ttm_graham_number': 285.43,
            'reporting_frequency': 'semi-annual',
            'date_range': 'H2 2024 through H1 2025',
            'currency': 'USD'
        }
        
        annual_metrics = {'graham_number': 250.00}
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        lines = section.generate()
        
        # Check frequency is displayed
        assert any("Reporting Frequency: Semi-Annual" in line for line in lines)
    
    def test_date_range_display(self):
        """Test that date range is correctly displayed."""
        ttm_metrics = {
            'ttm_graham_number': 285.43,
            'reporting_frequency': 'quarterly',
            'date_range': 'Q4 2024 through Q3 2025',
            'currency': 'USD'
        }
        
        annual_metrics = {'graham_number': 250.00}
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        lines = section.generate()
        
        # Check date range is displayed
        assert any("Period Covered: Q4 2024 through Q3 2025" in line for line in lines)
    
    def test_all_ttm_metrics_displayed(self):
        """Test that all TTM metrics are displayed."""
        ttm_metrics = {
            'ttm_graham_number': 285.43,
            'ttm_tbvps': 29.87,
            'ttm_net_net': 15.23,
            'ttm_margin_of_safety': 12.5,
            'ttm_pe_ratio': 28.5,
            'ttm_pb_ratio': 13.6,
            'reporting_frequency': 'quarterly',
            'date_range': 'Q4 2024 through Q3 2025',
            'currency': 'USD'
        }
        
        annual_metrics = {
            'graham_number': 250.00,
            'tbvps': 28.00,
            'net_net_value': 14.00,
            'margin_of_safety': 10.0,
            'pe_ratio': 23.4,
            'pb_ratio': 12.0
        }
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        lines = section.generate()
        
        # Check all metrics are present
        assert any("TTM Graham Number" in line for line in lines)
        assert any("TTM Tangible Book Value Per Share" in line for line in lines)
        assert any("TTM Net-Net Value" in line for line in lines)
        assert any("TTM Margin of Safety" in line for line in lines)
        assert any("TTM P/E Ratio" in line for line in lines)
        assert any("TTM P/B Ratio" in line for line in lines)


class TestPercentageDifferenceCalculation:
    """Test percentage difference calculation between TTM and annual values."""
    
    def test_positive_difference(self):
        """Test calculation of positive percentage difference."""
        ttm_metrics = {'ttm_graham_number': 300.00, 'currency': 'USD'}
        annual_metrics = {'graham_number': 250.00}
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        diff = section._calculate_percentage_difference(300.00, 250.00)
        
        assert diff == "+20.0%"
    
    def test_negative_difference(self):
        """Test calculation of negative percentage difference."""
        ttm_metrics = {'ttm_graham_number': 200.00, 'currency': 'USD'}
        annual_metrics = {'graham_number': 250.00}
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        diff = section._calculate_percentage_difference(200.00, 250.00)
        
        assert diff == "-20.0%"
    
    def test_zero_difference(self):
        """Test calculation when values are equal."""
        ttm_metrics = {'ttm_graham_number': 250.00, 'currency': 'USD'}
        annual_metrics = {'graham_number': 250.00}
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        diff = section._calculate_percentage_difference(250.00, 250.00)
        
        assert diff == "0.0%"
    
    def test_na_ttm_value(self):
        """Test handling of N/A TTM value."""
        ttm_metrics = {'ttm_graham_number': 'N/A', 'currency': 'USD'}
        annual_metrics = {'graham_number': 250.00}
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        diff = section._calculate_percentage_difference('N/A', 250.00)
        
        assert diff == ""
    
    def test_na_annual_value(self):
        """Test handling of N/A annual value."""
        ttm_metrics = {'ttm_graham_number': 300.00, 'currency': 'USD'}
        annual_metrics = {'graham_number': 'N/A'}
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        diff = section._calculate_percentage_difference(300.00, 'N/A')
        
        assert diff == ""
    
    def test_zero_annual_value(self):
        """Test handling of zero annual value (avoid division by zero)."""
        ttm_metrics = {'ttm_graham_number': 300.00, 'currency': 'USD'}
        annual_metrics = {'graham_number': 0.0}
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        diff = section._calculate_percentage_difference(300.00, 0.0)
        
        assert diff == ""
    
    def test_large_difference(self):
        """Test calculation of large percentage difference."""
        ttm_metrics = {'ttm_graham_number': 500.00, 'currency': 'USD'}
        annual_metrics = {'graham_number': 100.00}
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        diff = section._calculate_percentage_difference(500.00, 100.00)
        
        assert diff == "+400.0%"


class TestNAHandling:
    """Test handling of N/A values in TTM metrics."""
    
    def test_na_graham_number(self):
        """Test display of N/A Graham Number."""
        ttm_metrics = {
            'ttm_graham_number': 'N/A',
            'ttm_tbvps': 29.87,
            'reporting_frequency': 'quarterly',
            'date_range': 'Q4 2024 through Q3 2025',
            'currency': 'USD'
        }
        
        annual_metrics = {'graham_number': 250.00, 'tbvps': 28.00}
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        lines = section.generate()
        
        # Check N/A is displayed
        assert any("TTM Graham Number: N/A" in line for line in lines)
    
    def test_all_na_metrics(self):
        """Test display when all TTM metrics are N/A."""
        ttm_metrics = {
            'ttm_graham_number': 'N/A',
            'ttm_tbvps': 'N/A',
            'ttm_net_net': 'N/A',
            'ttm_margin_of_safety': 'N/A',
            'ttm_pe_ratio': 'N/A',
            'ttm_pb_ratio': 'N/A',
            'reporting_frequency': 'irregular',
            'date_range': 'N/A',
            'currency': 'USD'
        }
        
        annual_metrics = {
            'graham_number': 250.00,
            'tbvps': 28.00,
            'net_net_value': 14.00,
            'margin_of_safety': 10.0,
            'pe_ratio': 23.4,
            'pb_ratio': 12.0
        }
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        lines = section.generate()
        
        # Check all metrics show N/A
        na_count = sum(1 for line in lines if ": N/A" in line)
        assert na_count >= 6  # At least 6 N/A values
    
    def test_mixed_na_and_values(self):
        """Test display with mix of N/A and valid values."""
        ttm_metrics = {
            'ttm_graham_number': 285.43,
            'ttm_tbvps': 'N/A',
            'ttm_net_net': 15.23,
            'ttm_margin_of_safety': 'N/A',
            'ttm_pe_ratio': 28.5,
            'ttm_pb_ratio': 'N/A',
            'reporting_frequency': 'quarterly',
            'date_range': 'Q4 2024 through Q3 2025',
            'currency': 'USD'
        }
        
        annual_metrics = {
            'graham_number': 250.00,
            'tbvps': 28.00,
            'net_net_value': 14.00,
            'margin_of_safety': 10.0,
            'pe_ratio': 23.4,
            'pb_ratio': 12.0
        }
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        lines = section.generate()
        
        # Check mix of values and N/A
        assert any("TTM Graham Number: 285.43 USD" in line for line in lines)
        assert any("TTM Tangible Book Value Per Share: N/A" in line for line in lines)
        assert any("TTM Net-Net Value: 15.23 USD" in line for line in lines)


class TestCurrencyFormatting:
    """Test currency formatting in TTM metrics display."""
    
    def test_usd_currency_display(self):
        """Test USD currency formatting."""
        ttm_metrics = {
            'ttm_graham_number': 285.43,
            'ttm_tbvps': 29.87,
            'currency': 'USD'
        }
        
        annual_metrics = {'graham_number': 250.00, 'tbvps': 28.00}
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        lines = section.generate()
        
        # Check USD is displayed
        assert any("USD" in line for line in lines)
    
    def test_gbp_currency_display(self):
        """Test GBP currency formatting."""
        ttm_metrics = {
            'ttm_graham_number': 285.43,
            'ttm_tbvps': 29.87,
            'currency': 'GBP'
        }
        
        annual_metrics = {'graham_number': 250.00, 'tbvps': 28.00}
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        lines = section.generate()
        
        # Check GBP is displayed
        assert any("GBP" in line for line in lines)
    
    def test_large_numbers_with_commas(self):
        """Test that large numbers are formatted with commas."""
        ttm_metrics = {
            'ttm_graham_number': 1285.43,
            'ttm_tbvps': 1029.87,
            'currency': 'USD'
        }
        
        annual_metrics = {'graham_number': 1250.00, 'tbvps': 1028.00}
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        lines = section.generate()
        
        # Check comma formatting
        assert any("1,285.43" in line for line in lines)
        assert any("1,029.87" in line for line in lines)


class TestComparisonDisplay:
    """Test display of TTM vs Annual comparisons."""
    
    def test_comparison_with_percentage_difference(self):
        """Test that comparisons include percentage differences."""
        ttm_metrics = {
            'ttm_graham_number': 300.00,
            'ttm_pe_ratio': 28.5,
            'currency': 'USD'
        }
        
        annual_metrics = {
            'graham_number': 250.00,
            'pe_ratio': 23.4
        }
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        lines = section.generate()
        
        # Check comparison format includes Annual and Diff
        assert any("Annual:" in line and "Diff:" in line for line in lines)
    
    def test_no_comparison_when_annual_na(self):
        """Test that no comparison shown when annual value is N/A."""
        ttm_metrics = {
            'ttm_graham_number': 300.00,
            'currency': 'USD'
        }
        
        annual_metrics = {
            'graham_number': 'N/A'
        }
        
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, create_minimal_financial_data())
        lines = section.generate()
        
        # Check no comparison shown
        graham_line = [line for line in lines if "TTM Graham Number" in line][0]
        assert "Annual:" not in graham_line or "Diff:" not in graham_line
