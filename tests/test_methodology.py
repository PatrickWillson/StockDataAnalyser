"""
Unit tests for Methodology Notes section generator.

Tests valuation metrics explanation, EPV methodology explanation, and formula display.
"""

import pytest
from output.sections.methodology import MethodologySection, format_price_display


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


class TestMethodologySection:
    """Tests for MethodologySection class."""
    
    def create_test_financial_data(self):
        """Create test financial data dictionary."""
        return {
            'ticker': 'AAPL.US',
            'currency': 'USD',
            'original_stock_currency': 'USD',
            'exchange': 'US',
            'price': 150.50,
            'pe_ratio': 24.55,
            'history': {
                '2023-12-31': {
                    'revenue': 383285000000.0,
                    'net_income': 96995000000.0,
                    'eps': 6.13,
                    'total_equity': 62146000000.0,
                    'shares_outstanding': 15821900000.0
                },
                '2022-12-31': {
                    'revenue': 394328000000.0,
                    'net_income': 99803000000.0,
                    'eps': 6.15,
                    'total_equity': 50672000000.0,
                    'shares_outstanding': 16215963000.0
                }
            }
        }
    
    def create_test_metrics(self):
        """Create test Graham metrics dictionary."""
        return {
            'graham_number': 28.73,
            'epv': 497224000000.00,
            'net_net_value': -9.17,
            'margin_of_safety': 25.5,
            'epv_details': {
                'epv_per_share': 31.42,
                'normalized_earnings': 49722400000.0,
                'years_used': 10,
                'cost_of_capital': 0.10,
                'years_included': [
                    '2023-12-31', '2022-12-31', '2021-12-31', '2020-12-31',
                    '2019-12-31', '2018-12-31', '2017-12-31', '2016-12-31',
                    '2015-12-31', '2014-12-31'
                ],
                'net_incomes': [
                    96995000000.0, 99803000000.0, 94680000000.0, 57411000000.0,
                    55256000000.0, 59531000000.0, 48351000000.0, 45687000000.0,
                    53394000000.0, 39510000000.0
                ]
            }
        }
    
    def test_section_generation_with_valid_data(self):
        """Test methodology section generates correctly with valid data."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Check section header
        assert "## METHODOLOGY NOTES" in lines
        assert "*How key metrics are calculated*" in lines
        
        # Check subsection header
        assert "### Valuation Metrics:" in lines
        
        # Check section ends with separator
        assert "---" in lines
        
        # Check lines is a list
        assert isinstance(lines, list)
        
        # Check all lines are strings
        assert all(isinstance(line, str) for line in lines)
    
    def test_pe_ratio_explanation(self):
        """Test P/E ratio calculation explanation."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Find P/E ratio explanation
        pe_lines = [line for line in lines if "P/E Ratio" in line and "24.55" in line]
        assert len(pe_lines) == 1
        assert "Current Price / Most Recent Annual EPS" in pe_lines[0]
        
        # Check for EPS explanation
        eps_lines = [line for line in lines if "EPS:" in line and "6.13 USD" in line]
        assert len(eps_lines) == 1
        assert "Net Income / Shares Outstanding" in eps_lines[0]
        
        # Check for audited financials note
        audited_lines = [line for line in lines if "audited financials" in line]
        assert len(audited_lines) >= 1
    
    def test_pe_ratio_missing_data(self):
        """Test P/E ratio explanation when data is missing."""
        financial_data = self.create_test_financial_data()
        financial_data['pe_ratio'] = 0
        
        metrics = self.create_test_metrics()
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Should not include P/E ratio explanation
        pe_lines = [line for line in lines if "P/E Ratio" in line and "Current Price" in line]
        assert len(pe_lines) == 0
    
    def test_graham_number_explanation(self):
        """Test Graham Number formula explanation."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Find Graham Number explanation
        graham_lines = [line for line in lines if "Graham Number" in line and "28.73 USD" in line]
        assert len(graham_lines) == 1
        assert "√(22.5 × EPS × BVPS)" in graham_lines[0]
        
        # Check for conservative estimate note
        conservative_lines = [line for line in lines if "Conservative intrinsic value estimate" in line]
        assert len(conservative_lines) >= 1
        
        # Check for Benjamin Graham reference
        graham_ref_lines = [line for line in lines if "Benjamin Graham" in line and "Intelligent Investor" in line]
        assert len(graham_ref_lines) >= 1
    
    def test_graham_number_na(self):
        """Test Graham Number explanation when N/A."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        metrics['graham_number'] = 'N/A'
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Should not include Graham Number explanation
        graham_lines = [line for line in lines if "Graham Number" in line and "√(22.5" in line]
        assert len(graham_lines) == 0
    
    def test_epv_methodology_explanation(self):
        """Test EPV methodology explanation with full-cycle method."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Check for EPV header
        epv_header_lines = [line for line in lines if "EPV - Simplified Earnings Power Estimate" in line]
        assert len(epv_header_lines) >= 1
        
        # Check for Methodology section
        methodology_lines = [line for line in lines if "**Methodology:**" in line]
        assert len(methodology_lines) >= 1
        
        # Check for key methodology points
        assert any("7-10 year average" in line for line in lines)
        assert any("Includes ALL years" in line for line in lines)
        assert any("Loss years reduce the average" in line for line in lines)
        
        # Check for calculation details
        assert any("Years Used: 10" in line for line in lines)
        assert any("Normalized Earnings:" in line for line in lines)
        
        # Check for Graham's principle quote
        graham_quote_lines = [line for line in lines if "earning power" in line and "Graham's Principle" in line]
        assert len(graham_quote_lines) >= 1
    
    def test_epv_years_range_display(self):
        """Test EPV years range display."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Check for years range
        years_lines = [line for line in lines if "Years:" in line and "2014-2023" in line]
        assert len(years_lines) >= 1
    
    def test_epv_net_incomes_display(self):
        """Test EPV net incomes display."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Check for net incomes line
        net_income_lines = [line for line in lines if "Net Incomes:" in line]
        assert len(net_income_lines) >= 1
        
        # Should contain formatted currency values
        assert any("USD96,995,000,000" in line for line in lines)
    
    def test_epv_with_loss_years(self):
        """Test EPV explanation with loss years."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        # Add loss years to net incomes
        metrics['epv_details']['net_incomes'] = [
            96995000000.0, 99803000000.0, -5000000000.0, 57411000000.0,
            55256000000.0, 59531000000.0, 48351000000.0, 45687000000.0,
            53394000000.0, -2000000000.0
        ]
        metrics['epv_details']['years_included'] = [
            '2023-12-31', '2022-12-31', '2021-12-31', '2020-12-31',
            '2019-12-31', '2018-12-31', '2017-12-31', '2016-12-31',
            '2015-12-31', '2014-12-31'
        ]
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Check for loss year note
        loss_note_lines = [line for line in lines if "loss year" in line and "2021, 2014" in line]
        assert len(loss_note_lines) >= 1
        
        # Check for negative values in net incomes
        assert any("-USD5,000,000,000" in line for line in lines)
        assert any("-USD2,000,000,000" in line for line in lines)
    
    def test_epv_all_profitable_years(self):
        """Test EPV explanation when all years are profitable."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Check for profitable years note
        profitable_lines = [line for line in lines if "All 10 years were profitable" in line]
        assert len(profitable_lines) >= 1
        assert any("consistent earnings power" in line for line in lines)
    
    def test_epv_per_share_display(self):
        """Test EPV per share display."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Check for EPV per share
        epv_per_share_lines = [line for line in lines if "EPV Per Share:" in line and "31.42 USD" in line]
        assert len(epv_per_share_lines) >= 1
    
    def test_epv_formula_display(self):
        """Test EPV formula display."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Check for EPV formula
        formula_lines = [line for line in lines if "EPV:" in line and "/ 10%" in line]
        assert len(formula_lines) >= 1
        assert any("USD497,224,000,000" in line for line in lines)
    
    def test_epv_missing_data(self):
        """Test EPV explanation when EPV is not calculated."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        metrics['epv'] = 0
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Should not include EPV explanation
        epv_lines = [line for line in lines if "EPV - Simplified Earnings Power Estimate" in line]
        assert len(epv_lines) == 0
    
    def test_net_net_explanation(self):
        """Test Net-Net Value calculation explanation."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        metrics['net_net_value'] = 15.50  # Positive value for testing
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Find Net-Net explanation
        net_net_lines = [line for line in lines if "Net-Net Value" in line and "15.50 USD" in line]
        assert len(net_net_lines) >= 1
        assert any("(Current Assets - Total Liabilities) / Shares" in line for line in lines)
        
        # Check for liquidation value note
        liquidation_lines = [line for line in lines if "liquidation value" in line]
        assert len(liquidation_lines) >= 1
        
        # Check for cigar butt reference
        cigar_lines = [line for line in lines if "cigar butt" in line]
        assert len(cigar_lines) >= 1
    
    def test_net_net_negative_value(self):
        """Test Net-Net explanation with negative value."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        metrics['net_net_value'] = -9.17
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Should not include Net-Net explanation for negative values
        net_net_lines = [line for line in lines if "Net-Net Value" in line and "Current Assets" in line]
        assert len(net_net_lines) == 0
    
    def test_net_net_na(self):
        """Test Net-Net explanation when N/A."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        metrics['net_net_value'] = 'N/A'
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Should not include Net-Net explanation
        net_net_lines = [line for line in lines if "Net-Net Value" in line and "Current Assets" in line]
        assert len(net_net_lines) == 0
    
    def test_margin_of_safety_explanation(self):
        """Test Margin of Safety calculation explanation."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Find Margin of Safety explanation
        mos_lines = [line for line in lines if "Margin of Safety" in line and "25.5%" in line]
        assert len(mos_lines) >= 1
        assert any("(Graham Number - Price) / Graham Number × 100" in line for line in lines)
        
        # Check for percentage discount note
        discount_lines = [line for line in lines if "Percentage discount to intrinsic value" in line]
        assert len(discount_lines) >= 1
        
        # Check for Graham's recommendation
        graham_rec_lines = [line for line in lines if "20-30%" in line and "defensive investors" in line]
        assert len(graham_rec_lines) >= 1
    
    def test_margin_of_safety_negative(self):
        """Test Margin of Safety explanation with negative value."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        metrics['margin_of_safety'] = -15.3
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Should still include explanation
        mos_lines = [line for line in lines if "Margin of Safety" in line and "-15.3%" in line]
        assert len(mos_lines) >= 1
    
    def test_margin_of_safety_na(self):
        """Test Margin of Safety explanation when N/A."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        metrics['margin_of_safety'] = 'N/A'
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Should not include explanation for N/A
        mos_lines = [line for line in lines if "Margin of Safety" in line and "Graham Number" in line]
        assert len(mos_lines) == 0
    
    def test_section_structure(self):
        """Test overall section structure."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Check starts with empty line
        assert lines[0] == ""
        
        # Check has header
        assert lines[1] == "## METHODOLOGY NOTES"
        
        # Check ends with separator
        assert lines[-1] == "---"
        assert lines[-2] == ""
    
    def test_empty_history(self):
        """Test section generation with empty history."""
        financial_data = self.create_test_financial_data()
        financial_data['history'] = {}
        
        metrics = self.create_test_metrics()
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Should still generate without errors
        assert "## METHODOLOGY NOTES" in lines
        assert isinstance(lines, list)
    
    def test_minimal_metrics(self):
        """Test section generation with minimal metrics."""
        financial_data = self.create_test_financial_data()
        metrics = {
            'graham_number': 'N/A',
            'epv': 0,
            'net_net_value': 'N/A',
            'margin_of_safety': 'N/A',
            'epv_details': {}
        }
        
        section = MethodologySection(financial_data, metrics)
        lines = section.generate()
        
        # Should still generate section header
        assert "## METHODOLOGY NOTES" in lines
        assert "### Valuation Metrics:" in lines
        assert isinstance(lines, list)
