"""
Unit tests for Calculation Details section generator.

Tests share count disclosure, BVPS calculation display, and Graham Number calculation display.
"""

import pytest
from output.sections.calculation_details import CalculationDetailsSection, format_price_display


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


class TestCalculationDetailsSection:
    """Tests for CalculationDetailsSection class."""
    
    def create_test_financial_data(self):
        """Create test financial data dictionary."""
        return {
            'ticker': 'AAPL.US',
            'currency': 'USD',
            'original_stock_currency': 'USD',
            'exchange': 'US',
            'price': 150.50,
            'book_value_per_share': 3.93,
            'fx_rate_used': 1.0,
            'history': {
                '2023-12-31': {
                    'revenue': 383285000000.0,
                    'net_income': 96995000000.0,
                    'eps': 6.13,
                    'total_equity': 62146000000.0,
                    'intangible_assets': 0.0,
                    'goodwill': 0.0,
                    'shares_outstanding': 15821900000.0,
                    'current_assets': 143566000000.0,
                    'total_liabilities': 290437000000.0
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
        """Test calculation details section generates correctly with valid data."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Check section header
        assert "## CALCULATION DETAILS" in lines
        assert "*Detailed breakdown of key calculations for transparency and verification*" in lines
        
        # Check section ends with separator
        assert "---" in lines
        
        # Check lines is a list
        assert isinstance(lines, list)
        
        # Check all lines are strings
        assert all(isinstance(line, str) for line in lines)
    
    def test_share_count_disclosure(self):
        """Test share count disclosure section."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Check for share count header
        assert "### Share Count Used:" in lines
        
        # Check for shares outstanding
        shares_lines = [line for line in lines if "Shares Outstanding" in line and "15,821,900,000" in line]
        assert len(shares_lines) >= 1
        
        # Check for source
        source_lines = [line for line in lines if "Source" in line and "Financial statements" in line and "2023" in line]
        assert len(source_lines) >= 1
        
        # Check for note about year-specific share count
        note_lines = [line for line in lines if "year-specific share count" in line and "audited financials" in line]
        assert len(note_lines) >= 1
        
        # Check for "Why This Matters" explanation
        why_lines = [line for line in lines if "Why This Matters" in line]
        assert len(why_lines) >= 1
        
        # Check for Graham methodology note
        graham_lines = [line for line in lines if "Graham methodology" in line and "same period" in line]
        assert len(graham_lines) >= 1
    
    def test_bvps_calculation_display(self):
        """Test Book Value Per Share calculation display."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Check for BVPS header
        assert "### Book Value Per Share (BVPS) Calculation:" in lines
        
        # Check for total equity
        equity_lines = [line for line in lines if "Total Stockholder Equity" in line and "USD62,146,000,000" in line]
        assert len(equity_lines) >= 1
        
        # Check for intangibles
        intangibles_lines = [line for line in lines if "Less: Intangible Assets" in line]
        assert len(intangibles_lines) >= 1
        
        # Check for goodwill
        goodwill_lines = [line for line in lines if "Less: Goodwill" in line]
        assert len(goodwill_lines) >= 1
        
        # Check for tangible book value
        tbv_lines = [line for line in lines if "**Tangible Book Value**:" in line and "USD62,146,000,000" in line]
        assert len(tbv_lines) >= 1
        
        # Check for divided by shares
        divided_lines = [line for line in lines if "Divided by Shares" in line and "15,821,900,000" in line]
        assert len(divided_lines) >= 1
        
        # Check for TBVPS result
        tbvps_lines = [line for line in lines if "Tangible Book Value Per Share (TBVPS)" in line and "USD3.93" in line]
        assert len(tbvps_lines) >= 1
        
        # Check for BVPS result
        bvps_lines = [line for line in lines if "Book Value Per Share (BVPS)" in line and "USD3.93" in line and "without subtracting intangibles" in line]
        assert len(bvps_lines) >= 1
    
    def test_bvps_with_intangibles(self):
        """Test BVPS calculation with intangibles and goodwill."""
        financial_data = self.create_test_financial_data()
        financial_data['history']['2023-12-31']['intangible_assets'] = 5000000000.0
        financial_data['history']['2023-12-31']['goodwill'] = 3000000000.0
        
        metrics = self.create_test_metrics()
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Check for intangibles value
        intangibles_lines = [line for line in lines if "Less: Intangible Assets" in line and "USD5,000,000,000" in line]
        assert len(intangibles_lines) >= 1
        
        # Check for goodwill value
        goodwill_lines = [line for line in lines if "Less: Goodwill" in line and "USD3,000,000,000" in line]
        assert len(goodwill_lines) >= 1
        
        # Check tangible book value is reduced
        tbv_lines = [line for line in lines if "**Tangible Book Value**:" in line and "USD54,146,000,000" in line]
        assert len(tbv_lines) >= 1
    
    def test_bvps_api_comparison(self):
        """Test BVPS comparison with API value when difference is significant."""
        financial_data = self.create_test_financial_data()
        financial_data['book_value_per_share'] = 4.80  # 22% difference from calculated 3.93
        
        metrics = self.create_test_metrics()
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Check for API book value comparison
        api_lines = [line for line in lines if "API Book Value" in line and "USD4.80" in line]
        assert len(api_lines) >= 1
        
        # Check for explanation of differences
        explanation_lines = [line for line in lines if "Explanation" in line and "Differences may be due to" in line]
        assert len(explanation_lines) >= 1
        
        # Check for specific reasons
        assert any("Different share count" in line for line in lines)
        assert any("Different accounting treatment" in line for line in lines)
        assert any("Timing differences" in line for line in lines)
        assert any("audited financial statement data per Graham methodology" in line for line in lines)
    
    def test_bvps_api_comparison_small_difference(self):
        """Test BVPS comparison when API difference is small (< 15%)."""
        financial_data = self.create_test_financial_data()
        financial_data['book_value_per_share'] = 4.00  # Only 1.8% difference from calculated 3.93
        
        metrics = self.create_test_metrics()
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Should not show API comparison for small differences
        api_lines = [line for line in lines if "API Book Value" in line and "difference" in line]
        assert len(api_lines) == 0
    
    def test_graham_number_calculation_display(self):
        """Test Graham Number calculation display."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Check for Graham Number header
        assert "### Graham Number Calculation:" in lines
        
        # Check for formula
        formula_lines = [line for line in lines if "Formula" in line and "√(22.5 × EPS × TBVPS)" in line]
        assert len(formula_lines) >= 1
        
        # Check for EPS value
        eps_lines = [line for line in lines if "EPS" in line and "USD6.13" in line]
        assert len(eps_lines) >= 1
        
        # Check for TBVPS value
        tbvps_lines = [line for line in lines if "TBVPS" in line and "USD3.93" in line]
        assert len(tbvps_lines) >= 1
        
        # Check for calculation steps
        calc_lines = [line for line in lines if "Calculation" in line and "√(22.5 ×" in line]
        assert len(calc_lines) >= 1
        
        # Check for Graham Number result
        result_lines = [line for line in lines if "Graham Number" in line and "USD28.73" in line]
        assert len(result_lines) >= 1
        
        # Check for precision note
        precision_lines = [line for line in lines if "unrounded intermediate values" in line and "precision" in line]
        assert len(precision_lines) >= 1
    
    def test_graham_number_na(self):
        """Test Graham Number calculation when N/A."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        metrics['graham_number'] = 'N/A'
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Should not include Graham Number calculation
        graham_lines = [line for line in lines if "### Graham Number Calculation:" in line]
        assert len(graham_lines) == 0
    
    def test_net_net_calculation_display(self):
        """Test Net-Net Value calculation display."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        metrics['net_net_value'] = 15.50  # Positive value for testing
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Check for Net-Net header
        assert "### Net-Net Value Calculation:" in lines
        
        # Check for current assets
        assets_lines = [line for line in lines if "Current Assets" in line and "USD143,566,000,000" in line]
        assert len(assets_lines) >= 1
        
        # Check for total liabilities
        liabilities_lines = [line for line in lines if "Total Liabilities" in line and "USD290,437,000,000" in line]
        assert len(liabilities_lines) >= 1
        
        # Check for net current assets
        nca_lines = [line for line in lines if "Net Current Assets" in line]
        assert len(nca_lines) >= 1
        
        # Check for divided by shares
        divided_lines = [line for line in lines if "Divided by Shares" in line and "15,821,900,000" in line]
        assert len(divided_lines) >= 1
        
        # Check for Net-Net result
        result_lines = [line for line in lines if "Net-Net Value Per Share" in line and "USD15.50" in line]
        assert len(result_lines) >= 1
        
        # Check for formula explanation
        formula_lines = [line for line in lines if "Formula Used" in line and "NCAV" in line]
        assert len(formula_lines) >= 1
        
        # Check for alternative formula note
        alternative_lines = [line for line in lines if "Alternative" in line and "NNWC" in line]
        assert len(alternative_lines) >= 1
        assert any("0.75×AR" in line for line in lines)
        assert any("0.5×Inventory" in line for line in lines)
    
    def test_net_net_negative_value(self):
        """Test Net-Net calculation when value is negative."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        metrics['net_net_value'] = -9.17
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Should not include Net-Net calculation for negative values
        net_net_lines = [line for line in lines if "### Net-Net Value Calculation:" in line]
        assert len(net_net_lines) == 0
    
    def test_currency_conversion_details_no_conversion(self):
        """Test currency conversion details when no conversion needed."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Should not include currency conversion section
        currency_lines = [line for line in lines if "### Currency Conversion Details:" in line]
        assert len(currency_lines) == 0
    
    def test_currency_conversion_details_with_london_fix(self):
        """Test currency conversion details with London Fix applied."""
        financial_data = self.create_test_financial_data()
        financial_data['original_stock_currency'] = 'GBX'
        financial_data['currency'] = 'GBP'
        financial_data['exchange'] = 'LSE'
        financial_data['fx_rate_used'] = 0.01
        
        metrics = self.create_test_metrics()
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Check for currency conversion header
        assert "### Currency Conversion Details:" in lines
        
        # Check for stock trading currency
        trading_lines = [line for line in lines if "Stock Trading Currency" in line and "GBX" in line and "pence" in line]
        assert len(trading_lines) >= 1
        
        # Check for financial statements currency
        financials_lines = [line for line in lines if "Financial Statements Currency" in line and "GBP" in line]
        assert len(financials_lines) >= 1
        
        # Check for London Fix applied
        london_lines = [line for line in lines if "London Fix Applied" in line and "Yes" in line]
        assert len(london_lines) >= 1
        
        # Check for explanation
        assert any("LSE stocks trade in pence" in line for line in lines)
        assert any("Price divided by 100" in line for line in lines)
        assert any("1,650 GBX = 16.50 GBP" in line for line in lines)
    
    def test_currency_conversion_details_with_fx_rate(self):
        """Test currency conversion details with FX rate conversion."""
        financial_data = self.create_test_financial_data()
        financial_data['original_stock_currency'] = 'GBP'
        financial_data['currency'] = 'USD'
        financial_data['fx_rate_used'] = 1.2650
        
        metrics = self.create_test_metrics()
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Check for FX conversion rate
        fx_lines = [line for line in lines if "FX Conversion Rate" in line and "1.2650" in line and "GBP → USD" in line]
        assert len(fx_lines) >= 1
        
        # Check for source
        source_lines = [line for line in lines if "Source" in line and "Frankfurter API" in line and "ECB" in line]
        assert len(source_lines) >= 1
        
        # Check for what was converted
        converted_lines = [line for line in lines if "What Was Converted" in line]
        assert len(converted_lines) >= 1
        assert any("Current stock price" in line for line in lines)
        assert any("Dividend amounts" in line for line in lines)
        
        # Check for why it matters
        why_lines = [line for line in lines if "Why Currency Unification Matters" in line]
        assert len(why_lines) >= 1
        assert any("Ensures all per-share calculations use the same currency" in line for line in lines)
        assert any("Prevents mixing GBX prices with GBP financials" in line for line in lines)
    
    def test_epv_methodology_clarification(self):
        """Test EPV methodology clarification section."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Check for EPV methodology header
        assert "### EPV Methodology Clarification:" in lines
        
        # Check for approach used
        approach_lines = [line for line in lines if "Approach Used" in line and "Graham's EPV" in line and "1949" in line]
        assert len(approach_lines) >= 1
        
        # Check for cost of capital
        cost_lines = [line for line in lines if "Cost of Capital" in line and "10%" in line]
        assert len(cost_lines) >= 1
        
        # Check for formula
        formula_lines = [line for line in lines if "Formula" in line and "Average Net Income" in line and "7-10 years" in line]
        assert len(formula_lines) >= 1
        
        # Check for includes loss years
        loss_lines = [line for line in lines if "Includes Loss Years" in line and "Yes" in line]
        assert len(loss_lines) >= 1
        
        # Check for modern EPV differences
        modern_lines = [line for line in lines if "This Differs From Modern EPV" in line and "Greenwald, 2001" in line]
        assert len(modern_lines) >= 1
        assert any("company-specific WACC" in line for line in lines)
        assert any("normalized EBIT" in line for line in lines)
        assert any("maintenance CapEx" in line for line in lines)
        
        # Check for why we use Graham's approach
        why_lines = [line for line in lines if "Why We Use Graham's Approach" in line]
        assert len(why_lines) >= 1
        assert any("Simpler and more deterministic" in line for line in lines)
        assert any("Consistent with other Graham metrics" in line for line in lines)
        assert any("10% is a reasonable conservative discount rate" in line for line in lines)
    
    def test_epv_methodology_not_shown_when_epv_zero(self):
        """Test EPV methodology clarification not shown when EPV is zero."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        metrics['epv'] = 0
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Should not include EPV methodology
        epv_lines = [line for line in lines if "### EPV Methodology Clarification:" in line]
        assert len(epv_lines) == 0
    
    def test_section_structure(self):
        """Test overall section structure."""
        financial_data = self.create_test_financial_data()
        metrics = self.create_test_metrics()
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Check starts with empty line
        assert lines[0] == ""
        
        # Check has header
        assert lines[1] == "## CALCULATION DETAILS"
        
        # Check ends with separator
        assert lines[-1] == "---"
        assert lines[-2] == ""
    
    def test_empty_history(self):
        """Test section generation with empty history."""
        financial_data = self.create_test_financial_data()
        financial_data['history'] = {}
        
        metrics = self.create_test_metrics()
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Should still generate header without errors
        assert "## CALCULATION DETAILS" in lines
        assert isinstance(lines, list)
        
        # Should not have subsections
        assert "### Share Count Used:" not in lines
        assert "### Book Value Per Share (BVPS) Calculation:" not in lines
    
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
        
        section = CalculationDetailsSection(financial_data, metrics)
        lines = section.generate()
        
        # Should still generate section header
        assert "## CALCULATION DETAILS" in lines
        assert isinstance(lines, list)
        
        # Should have share count and BVPS sections
        assert "### Share Count Used:" in lines
        assert "### Book Value Per Share (BVPS) Calculation:" in lines
        
        # Should not have Graham Number or Net-Net sections
        assert "### Graham Number Calculation:" not in lines
        assert "### Net-Net Value Calculation:" not in lines
