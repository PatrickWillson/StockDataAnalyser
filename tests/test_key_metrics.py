"""
Unit tests for Key Metrics section generator.

Tests profitability metrics display, ownership metrics display, and book value calculation.
"""

import pytest
from output.sections.key_metrics import KeyMetricsSection, format_price_display


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
    
    def test_large_number_formatting(self):
        """Test price formatting with large numbers includes commas."""
        result = format_price_display(1234567.89, "USD", "USD")
        assert result == "1,234,567.89 USD"


class TestKeyMetricsSection:
    """Tests for KeyMetricsSection class."""
    
    def create_test_financial_data(self):
        """Create test financial data dictionary."""
        return {
            'currency': 'USD',
            'original_stock_currency': 'USD',
            'roe': 0.1714,  # 17.14%
            'roa': 0.2296,  # 22.96%
            'profit_margin': 0.2530,  # 25.30%
            'insider_ownership': 0.07,  # 0.07%
            'institutional_ownership': 61.02,  # 61.02%
            'beta': 1.286,
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
                    'shares_outstanding': 16325800000.0
                }
            }
        }
    
    def test_section_generation_with_valid_data(self):
        """Test key metrics section generates correctly with valid data."""
        financial_data = self.create_test_financial_data()
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Check section header
        assert "## SECTION 2: KEY METRICS" in lines
        
        # Check section ends with separator
        assert "---" in lines
        
        # Check lines is a list
        assert isinstance(lines, list)
        
        # Check all lines are strings
        assert all(isinstance(line, str) for line in lines)
    
    def test_profitability_metrics_display(self):
        """Test profitability metrics (ROE, ROA, Profit Margin) are displayed correctly."""
        financial_data = self.create_test_financial_data()
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Check ROE
        roe_lines = [line for line in lines if "Return on Equity (ROE):" in line]
        assert len(roe_lines) == 1
        assert "17.14%" in roe_lines[0]
        
        # Check ROA
        roa_lines = [line for line in lines if "Return on Assets (ROA):" in line]
        assert len(roa_lines) == 1
        assert "22.96%" in roa_lines[0]
        
        # Check Profit Margin
        margin_lines = [line for line in lines if "Profit Margin:" in line]
        assert len(margin_lines) == 1
        assert "25.30%" in margin_lines[0]
    
    def test_profitability_metrics_missing(self):
        """Test profitability metrics when data is missing or zero."""
        financial_data = self.create_test_financial_data()
        financial_data['roe'] = 0
        financial_data['roa'] = 0
        financial_data['profit_margin'] = 0
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Should not include profitability lines
        roe_lines = [line for line in lines if "Return on Equity (ROE):" in line]
        assert len(roe_lines) == 0
        
        roa_lines = [line for line in lines if "Return on Assets (ROA):" in line]
        assert len(roa_lines) == 0
        
        margin_lines = [line for line in lines if "Profit Margin:" in line]
        assert len(margin_lines) == 0
    
    def test_profitability_metrics_negative_values(self):
        """Test profitability metrics with negative values (losses)."""
        financial_data = self.create_test_financial_data()
        financial_data['roe'] = -0.05  # -5%
        financial_data['roa'] = -0.02  # -2%
        financial_data['profit_margin'] = -0.10  # -10%
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Negative values should not be displayed (only positive > 0)
        roe_lines = [line for line in lines if "Return on Equity (ROE):" in line]
        assert len(roe_lines) == 0
        
        roa_lines = [line for line in lines if "Return on Assets (ROA):" in line]
        assert len(roa_lines) == 0
        
        margin_lines = [line for line in lines if "Profit Margin:" in line]
        assert len(margin_lines) == 0
    
    def test_book_value_calculation(self):
        """Test book value per share calculation from most recent data."""
        financial_data = self.create_test_financial_data()
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Calculate expected book value: 62146000000.0 / 15821900000.0 = 3.93
        bvps_lines = [line for line in lines if "Book Value Per Share:" in line]
        assert len(bvps_lines) == 1
        assert "3.93 USD" in bvps_lines[0]
    
    def test_book_value_uses_most_recent_year(self):
        """Test book value uses most recent year with financial data."""
        financial_data = self.create_test_financial_data()
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Should use 2023 data (most recent)
        # 2023: 62146000000.0 / 15821900000.0 = 3.93
        bvps_lines = [line for line in lines if "Book Value Per Share:" in line]
        assert len(bvps_lines) == 1
        assert "3.93 USD" in bvps_lines[0]
    
    def test_book_value_missing_data(self):
        """Test book value when equity or shares data is missing."""
        financial_data = self.create_test_financial_data()
        financial_data['history']['2023-12-31']['total_equity'] = 0
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Should not include book value line
        bvps_lines = [line for line in lines if "Book Value Per Share:" in line]
        assert len(bvps_lines) == 0
    
    def test_book_value_zero_shares(self):
        """Test book value when shares outstanding is zero."""
        financial_data = self.create_test_financial_data()
        financial_data['history']['2023-12-31']['shares_outstanding'] = 0
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Should not include book value line
        bvps_lines = [line for line in lines if "Book Value Per Share:" in line]
        assert len(bvps_lines) == 0
    
    def test_book_value_empty_history(self):
        """Test book value when history is empty."""
        financial_data = self.create_test_financial_data()
        financial_data['history'] = {}
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Should not include book value line
        bvps_lines = [line for line in lines if "Book Value Per Share:" in line]
        assert len(bvps_lines) == 0
    
    def test_book_value_skips_incomplete_years(self):
        """Test book value skips years without complete financial data."""
        financial_data = self.create_test_financial_data()
        # Add a more recent year with only dividend data (incomplete)
        financial_data['history']['2024-12-31'] = {
            'dividend': 1.00,
            'revenue': 0.0,
            'net_income': 0.0,
            'total_equity': 0.0,
            'shares_outstanding': 0.0
        }
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Should use 2023 data (most recent complete year)
        bvps_lines = [line for line in lines if "Book Value Per Share:" in line]
        assert len(bvps_lines) == 1
        assert "3.93 USD" in bvps_lines[0]
    
    def test_ownership_metrics_display(self):
        """Test ownership metrics (Insider, Institutional) are displayed correctly."""
        financial_data = self.create_test_financial_data()
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Check Insider Ownership
        insider_lines = [line for line in lines if "Insider Ownership:" in line]
        assert len(insider_lines) == 1
        assert "0.07%" in insider_lines[0]
        
        # Check Institutional Ownership
        institutional_lines = [line for line in lines if "Institutional Ownership:" in line]
        assert len(institutional_lines) == 1
        assert "61.02%" in institutional_lines[0]
    
    def test_ownership_metrics_missing(self):
        """Test ownership metrics when data is missing or zero."""
        financial_data = self.create_test_financial_data()
        financial_data['insider_ownership'] = 0
        financial_data['institutional_ownership'] = 0
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Should not include ownership lines
        insider_lines = [line for line in lines if "Insider Ownership:" in line]
        assert len(insider_lines) == 0
        
        institutional_lines = [line for line in lines if "Institutional Ownership:" in line]
        assert len(institutional_lines) == 0
    
    def test_ownership_metrics_high_values(self):
        """Test ownership metrics with high values."""
        financial_data = self.create_test_financial_data()
        financial_data['insider_ownership'] = 45.50
        financial_data['institutional_ownership'] = 85.25
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Check high insider ownership
        insider_lines = [line for line in lines if "Insider Ownership:" in line]
        assert len(insider_lines) == 1
        assert "45.50%" in insider_lines[0]
        
        # Check high institutional ownership
        institutional_lines = [line for line in lines if "Institutional Ownership:" in line]
        assert len(institutional_lines) == 1
        assert "85.25%" in institutional_lines[0]
    
    def test_risk_metrics_display(self):
        """Test risk metrics (Beta) are displayed correctly."""
        financial_data = self.create_test_financial_data()
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Check Beta
        beta_lines = [line for line in lines if "Beta (Volatility):" in line]
        assert len(beta_lines) == 1
        assert "1.286" in beta_lines[0]
    
    def test_risk_metrics_missing(self):
        """Test risk metrics when data is missing or zero."""
        financial_data = self.create_test_financial_data()
        financial_data['beta'] = 0
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Should not include beta line
        beta_lines = [line for line in lines if "Beta (Volatility):" in line]
        assert len(beta_lines) == 0
    
    def test_risk_metrics_low_beta(self):
        """Test risk metrics with low beta (defensive stock)."""
        financial_data = self.create_test_financial_data()
        financial_data['beta'] = 0.45
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Check low beta
        beta_lines = [line for line in lines if "Beta (Volatility):" in line]
        assert len(beta_lines) == 1
        assert "0.450" in beta_lines[0]
    
    def test_risk_metrics_high_beta(self):
        """Test risk metrics with high beta (volatile stock)."""
        financial_data = self.create_test_financial_data()
        financial_data['beta'] = 2.150
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Check high beta
        beta_lines = [line for line in lines if "Beta (Volatility):" in line]
        assert len(beta_lines) == 1
        assert "2.150" in beta_lines[0]
    
    def test_section_structure(self):
        """Test overall section structure."""
        financial_data = self.create_test_financial_data()
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Check starts with empty line
        assert lines[0] == ""
        
        # Check has header
        assert lines[1] == "## SECTION 2: KEY METRICS"
        
        # Check ends with separator
        assert lines[-1] == "---"
        assert lines[-2] == ""
    
    def test_section_with_minimal_data(self):
        """Test section generation with minimal data."""
        financial_data = {
            'currency': 'USD',
            'roe': 0.10,
            'history': {}
        }
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Should still generate without errors
        assert "## SECTION 2: KEY METRICS" in lines
        assert isinstance(lines, list)
        
        # Should have ROE
        roe_lines = [line for line in lines if "Return on Equity (ROE):" in line]
        assert len(roe_lines) == 1
    
    def test_section_with_all_metrics(self):
        """Test section generation with all metrics present."""
        financial_data = self.create_test_financial_data()
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Count metric lines (excluding header, empty lines, and separator)
        metric_lines = [line for line in lines if line.startswith("- ")]
        
        # Should have: ROE, ROA, Profit Margin, Book Value, Insider, Institutional, Beta = 7 lines
        assert len(metric_lines) == 7
    
    def test_section_ordering(self):
        """Test that metrics appear in correct order."""
        financial_data = self.create_test_financial_data()
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Get indices of key metrics
        roe_idx = next(i for i, line in enumerate(lines) if "Return on Equity (ROE):" in line)
        roa_idx = next(i for i, line in enumerate(lines) if "Return on Assets (ROA):" in line)
        margin_idx = next(i for i, line in enumerate(lines) if "Profit Margin:" in line)
        bvps_idx = next(i for i, line in enumerate(lines) if "Book Value Per Share:" in line)
        insider_idx = next(i for i, line in enumerate(lines) if "Insider Ownership:" in line)
        institutional_idx = next(i for i, line in enumerate(lines) if "Institutional Ownership:" in line)
        beta_idx = next(i for i, line in enumerate(lines) if "Beta (Volatility):" in line)
        
        # Check order: Profitability -> Book Value -> Ownership -> Risk
        assert roe_idx < roa_idx < margin_idx < bvps_idx < insider_idx < institutional_idx < beta_idx
    
    def test_currency_display_in_book_value(self):
        """Test that book value displays correct currency."""
        financial_data = self.create_test_financial_data()
        financial_data['currency'] = 'GBP'
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Check book value shows GBP
        bvps_lines = [line for line in lines if "Book Value Per Share:" in line]
        assert len(bvps_lines) == 1
        assert "GBP" in bvps_lines[0]
    
    def test_large_book_value_formatting(self):
        """Test book value formatting with large numbers."""
        financial_data = self.create_test_financial_data()
        # Set very high equity to create large book value
        financial_data['history']['2023-12-31']['total_equity'] = 1000000000000.0  # 1 trillion
        financial_data['history']['2023-12-31']['shares_outstanding'] = 1000000.0  # 1 million
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Book value should be 1,000,000.00
        bvps_lines = [line for line in lines if "Book Value Per Share:" in line]
        assert len(bvps_lines) == 1
        assert "1,000,000.00 USD" in bvps_lines[0]
    
    def test_small_book_value_formatting(self):
        """Test book value formatting with small numbers."""
        financial_data = self.create_test_financial_data()
        # Set low equity to create small book value
        financial_data['history']['2023-12-31']['total_equity'] = 1000000.0  # 1 million
        financial_data['history']['2023-12-31']['shares_outstanding'] = 10000000.0  # 10 million
        
        section = KeyMetricsSection(financial_data)
        lines = section.generate()
        
        # Book value should be 0.10
        bvps_lines = [line for line in lines if "Book Value Per Share:" in line]
        assert len(bvps_lines) == 1
        assert "0.10 USD" in bvps_lines[0]
