"""
Unit tests for Executive Summary section generator.

Tests section generation with valid data, verdict display, intrinsic value formatting,
and price display with currency conversion.
"""

import pytest
from output.sections.executive_summary import ExecutiveSummarySection, format_price_display


class TestFormatPriceDisplay:
    """Tests for format_price_display helper function."""
    
    def test_single_currency_format(self):
        """Test price formatting when trading and financials currencies match."""
        result = format_price_display(150.50, "USD", "USD")
        assert result == "150.50 USD"
    
    def test_dual_currency_format_with_conversion(self):
        """Test price formatting with currency conversion."""
        result = format_price_display(1650.0, "GBX", "GBP", 16.50)
        assert result == "1,650.00 GBX (16.50 GBP)"
    
    def test_dual_currency_format_without_conversion(self):
        """Test price formatting when currencies differ but no conversion provided."""
        result = format_price_display(1650.0, "GBX", "GBP")
        assert result == "1,650.00 GBX"
    
    def test_large_number_formatting(self):
        """Test price formatting with large numbers includes commas."""
        result = format_price_display(1234567.89, "USD", "USD")
        assert result == "1,234,567.89 USD"
    
    def test_small_number_formatting(self):
        """Test price formatting with small numbers."""
        result = format_price_display(0.50, "USD", "USD")
        assert result == "0.50 USD"


class TestExecutiveSummarySection:
    """Tests for ExecutiveSummarySection class."""
    
    def create_test_financial_data(self):
        """Create test financial data dictionary."""
        return {
            'currency': 'USD',
            'original_stock_currency': 'USD',
            'exchange': 'US',
            'price': 150.50,
            'price_source': 'yfinance',
            'week_52_high': 199.62,
            'week_52_low': 124.17,
            'forward_dividend_rate': 1.00,
            'dividend_source': 'cash_flow',
            'dividend_sources': {'2023': 'cash_flow'},
            'pe_ratio': 24.55,
            'price_to_book': 6.25,
            'history': {
                '2023-12-31': {
                    'revenue': 383285000000.0,
                    'net_income': 96995000000.0,
                    'eps': 6.13,
                    'dividend': 0.96,
                    'total_equity': 62146000000.0,
                    'shares_outstanding': 15821900000.0
                }
            }
        }
    
    def create_test_metrics(self):
        """Create test Graham metrics dictionary."""
        return {
            'verdict': 'UNDERVALUED',
            'graham_number': 28.73,
            'epv': 497224000000.00,
            'net_net_value': -9.17,
            'margin_of_safety': 25.5
        }
    
    def test_section_generation_with_valid_data(self):
        """Test executive summary section generates correctly with valid data."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        # Check section header
        assert "## SECTION 1: EXECUTIVE SUMMARY" in lines
        assert "*Current metrics (P/E, Price) reflect most recent available data*" in lines
        
        # Check verdict
        assert "- Verdict: **UNDERVALUED**" in lines
        
        # Check section ends with separator
        assert "---" in lines
        
        # Check lines is a list
        assert isinstance(lines, list)
        
        # Check all lines are strings
        assert all(isinstance(line, str) for line in lines)
    
    def test_verdict_display(self):
        """Test verdict is displayed correctly."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        # Find verdict line
        verdict_lines = [line for line in lines if "Verdict:" in line]
        assert len(verdict_lines) == 1
        assert "**UNDERVALUED**" in verdict_lines[0]
    
    def test_verdict_display_overvalued(self):
        """Test verdict display for overvalued stock."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        metrics['verdict'] = 'OVERVALUED'
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        verdict_lines = [line for line in lines if "Verdict:" in line]
        assert "**OVERVALUED**" in verdict_lines[0]
    
    def test_intrinsic_value_formatting_numeric(self):
        """Test intrinsic value formatting with numeric values."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        # Check Graham Number
        graham_lines = [line for line in lines if "Intrinsic Value (Graham):" in line]
        assert len(graham_lines) == 1
        assert "28.73 USD" in graham_lines[0]
        
        # Check EPV
        epv_lines = [line for line in lines if "Intrinsic Value (EPV):" in line]
        assert len(epv_lines) == 1
        assert "497,224,000,000.00 USD" in epv_lines[0]
        
        # Check Net-Net (negative value)
        net_net_lines = [line for line in lines if "Net-Net Value:" in line]
        assert len(net_net_lines) == 1
        # Negative values should still be formatted
        assert "-9.17 USD" in net_net_lines[0]
    
    def test_intrinsic_value_formatting_na(self):
        """Test intrinsic value formatting with N/A values."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        metrics['graham_number'] = 'N/A'
        metrics['epv'] = 'N/A'
        metrics['net_net_value'] = 'N/A'
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        # Check all show N/A
        graham_lines = [line for line in lines if "Intrinsic Value (Graham):" in line]
        assert "N/A" in graham_lines[0]
        
        epv_lines = [line for line in lines if "Intrinsic Value (EPV):" in line]
        assert "N/A" in epv_lines[0]
        
        net_net_lines = [line for line in lines if "Net-Net Value:" in line]
        assert "N/A" in net_net_lines[0]
    
    def test_price_display_single_currency(self):
        """Test current price display with single currency."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        price_lines = [line for line in lines if "Current Price:" in line]
        assert len(price_lines) == 1
        assert "150.50 USD" in price_lines[0]
    
    def test_price_display_lse_special_case(self):
        """Test current price display for LSE stocks (GBP with pence)."""
        financial_data = self.create_test_financial_data()
        financial_data['exchange'] = 'LSE'
        financial_data['currency'] = 'GBP'
        financial_data['original_stock_currency'] = 'GBP'
        financial_data['price'] = 16.50
        
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        price_lines = [line for line in lines if "Current Price:" in line]
        assert len(price_lines) == 1
        # Should show both GBP and pence
        assert "16.50 GBP" in price_lines[0]
        assert "1,650 pence" in price_lines[0]
    
    def test_52_week_range_display(self):
        """Test 52-week range display."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        range_lines = [line for line in lines if "52-Week Range:" in line]
        assert len(range_lines) == 1
        assert "124.17 USD" in range_lines[0]
        assert "199.62 USD" in range_lines[0]
    
    def test_52_week_range_missing_data(self):
        """Test 52-week range when data is missing."""
        financial_data = self.create_test_financial_data()
        financial_data['week_52_high'] = 0
        financial_data['week_52_low'] = 0
        
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        # Should not include 52-week range line
        range_lines = [line for line in lines if "52-Week Range:" in line]
        assert len(range_lines) == 0
    
    def test_dividend_display_cash_flow_source(self):
        """Test dividend display with cash flow source."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        dividend_lines = [line for line in lines if "Trailing Dividend:" in line]
        assert len(dividend_lines) == 1
        # When cash_flow source, uses actual dividend from history (0.96)
        assert "0.96 USD" in dividend_lines[0]
        assert "Yield:" in dividend_lines[0]
        assert "Paid (Cash Flow)" in dividend_lines[0]
    
    def test_dividend_display_dividend_api_source(self):
        """Test dividend display with dividend API source."""
        financial_data = self.create_test_financial_data()
        financial_data['dividend_sources'] = {'2023': 'dividend_api'}
        
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        dividend_lines = [line for line in lines if "Trailing Dividend:" in line]
        assert len(dividend_lines) == 1
        assert "Declared (Dividend API)" in dividend_lines[0]
    
    def test_dividend_display_forward_rate_source(self):
        """Test dividend display with forward rate source and warning."""
        financial_data = self.create_test_financial_data()
        financial_data['dividend_sources'] = {'2023': 'forward_rate'}
        
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        dividend_lines = [line for line in lines if "Trailing Dividend:" in line]
        assert len(dividend_lines) == 1
        assert "Declared (Forward Rate)" in dividend_lines[0]
        
        # Check for warning
        warning_lines = [line for line in lines if "⚠️" in line and "forward declared rate" in line]
        assert len(warning_lines) == 1
    
    def test_dividend_display_incomplete_year(self):
        """Test dividend display with incomplete year flag."""
        financial_data = self.create_test_financial_data()
        financial_data['dividend_sources'] = {'2023': 'dividend_api'}
        # Make year incomplete by removing financial data
        financial_data['history']['2023-12-31'] = {
            'dividend': 0.96,
            'revenue': 0.0,
            'net_income': 0.0,
            'total_equity': 0.0
        }
        
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        dividend_lines = [line for line in lines if "Trailing Dividend:" in line]
        assert len(dividend_lines) == 1
        assert "[2023 - Incomplete Year]" in dividend_lines[0]
    
    def test_dividend_display_both_sources(self):
        """Test dividend display when both cash flow and forward rate available."""
        financial_data = self.create_test_financial_data()
        financial_data['forward_dividend_rate'] = 1.04
        financial_data['history']['2023-12-31']['dividend'] = 1.00
        
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        # Should show both trailing and forward
        dividend_lines = [line for line in lines if "Trailing Dividend:" in line or "Forward Rate:" in line]
        assert len(dividend_lines) == 2
        
        # Check trailing
        trailing = [line for line in dividend_lines if "Trailing Dividend:" in line]
        assert "1.00 USD" in trailing[0]
        
        # Check forward
        forward = [line for line in dividend_lines if "Forward Rate:" in line]
        assert "1.04 USD" in forward[0]
    
    def test_dividend_display_no_dividend(self):
        """Test dividend display when no dividend is paid."""
        financial_data = self.create_test_financial_data()
        financial_data['forward_dividend_rate'] = None
        
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        # Should not include dividend line
        dividend_lines = [line for line in lines if "Trailing Dividend:" in line]
        assert len(dividend_lines) == 0
    
    def test_valuation_ratios_display(self):
        """Test P/E and Price/Book ratio display."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        # Check P/E ratio
        pe_lines = [line for line in lines if "P/E Ratio:" in line]
        assert len(pe_lines) == 1
        assert "24.55" in pe_lines[0]
        
        # Check Price/Book
        pb_lines = [line for line in lines if "Price/Book:" in line]
        assert len(pb_lines) == 1
        assert "6.25" in pb_lines[0]
    
    def test_valuation_ratios_missing(self):
        """Test valuation ratios when data is missing."""
        financial_data = self.create_test_financial_data()
        financial_data['pe_ratio'] = 0
        financial_data['price_to_book'] = 0
        
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        # Should not include ratio lines
        pe_lines = [line for line in lines if "P/E Ratio:" in line]
        assert len(pe_lines) == 0
        
        pb_lines = [line for line in lines if "Price/Book:" in line]
        assert len(pb_lines) == 0
    
    def test_margin_of_safety_display(self):
        """Test margin of safety display."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        mos_lines = [line for line in lines if "Margin of Safety:" in line]
        assert len(mos_lines) == 1
        assert "25.5" in mos_lines[0]
    
    def test_margin_of_safety_na(self):
        """Test margin of safety display when N/A."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        metrics['margin_of_safety'] = 'N/A'
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        mos_lines = [line for line in lines if "Margin of Safety:" in line]
        assert len(mos_lines) == 1
        assert "N/A" in mos_lines[0]
    
    def test_section_structure(self):
        """Test overall section structure."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        # Check starts with empty line
        assert lines[0] == ""
        
        # Check has header
        assert lines[1] == "## SECTION 1: EXECUTIVE SUMMARY"
        
        # Check ends with separator
        assert lines[-1] == "---"
        assert lines[-2] == ""
    
    def test_empty_history(self):
        """Test section generation with empty history."""
        financial_data = self.create_test_financial_data()
        financial_data['history'] = {}
        
        metrics = self.create_test_metrics()
        
        section = ExecutiveSummarySection(financial_data, metrics)
        lines = section.generate()
        
        # Should still generate without errors
        assert "## SECTION 1: EXECUTIVE SUMMARY" in lines
        assert isinstance(lines, list)
