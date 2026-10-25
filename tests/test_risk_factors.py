"""Unit tests for Risk Factors section generator.

Tests the RiskFactorsSection class to ensure it generates correct markdown
output for risk assessments based on financial data and Graham metrics.
"""

import pytest
from output.sections.risk_factors import RiskFactorsSection


def create_test_financial_data():
    """Create test financial data for risk factors testing."""
    return {
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'price': 150.0,
        'beta': 0.85,
        'average_volume': 50000000,
        'pe_ratio': 12.5,
        'roe': 0.15,
        'institutional_ownership': 25.5,
        'price_source': 'yfinance',
        'forward_dividend_rate': 2.50,
        'history': {
            '2023-12-31': {
                'revenue': 100000000,
                'net_income': 10000000,
                'eps': 5.00,
                'dividend': 2.50,
                'total_equity': 50000000,
                'shares_outstanding': 2000000,
                'current_assets': 30000000,
                'current_liabilities': 10000000,
                'long_term_debt': 5000000,
                'total_assets': 80000000,
                'operating_cash_flow': 12000000
            },
            '2022-12-31': {
                'revenue': 95000000,
                'net_income': 9500000,
                'eps': 4.75,
                'dividend': 2.40,
                'total_equity': 48000000,
                'shares_outstanding': 2000000,
                'current_assets': 28000000,
                'current_liabilities': 9500000,
                'long_term_debt': 5500000,
                'total_assets': 78000000,
                'operating_cash_flow': 11000000
            },
            '2021-12-31': {
                'revenue': 90000000,
                'net_income': 9000000,
                'eps': 4.50,
                'dividend': 2.30,
                'total_equity': 46000000,
                'shares_outstanding': 2000000,
                'current_assets': 26000000,
                'current_liabilities': 9000000,
                'long_term_debt': 6000000,
                'total_assets': 76000000,
                'operating_cash_flow': 10500000
            }
        }
    }


def create_test_metrics():
    """Create test Graham metrics for risk factors testing."""
    return {
        'graham_number': 100.0,
        'epv': 110.0,
        'net_net_value': 90.0,
        'margin_of_safety': 25.5,
        'verdict': 'UNDERVALUED'
    }


def test_risk_factors_section_generates_both_sections():
    """Test that risk factors section generates risk assessment."""
    financial_data = create_test_financial_data()
    metrics = create_test_metrics()
    
    section = RiskFactorsSection(financial_data, metrics)
    lines = section.generate()
    
    # Should have one risk factors section
    risk_headers = [line for line in lines if line == "## RISK FACTORS"]
    assert len(risk_headers) == 1, "Should generate one RISK FACTORS section"
    
    # Section subtitle
    assert "*Quantifiable risks based on Graham's investment criteria*" in lines


def test_market_risk_calculations():
    """Test market risk calculations (beta and liquidity)."""
    financial_data = create_test_financial_data()
    metrics = create_test_metrics()
    
    section = RiskFactorsSection(financial_data, metrics)
    lines = section.generate()
    
    # Check beta is displayed
    beta_lines = [line for line in lines if 'Beta' in line or 'Volatility' in line]
    assert len(beta_lines) > 0, "Should display beta/volatility information"
    
    # Check liquidity assessment
    liquidity_lines = [line for line in lines if 'Liquidity' in line or 'liquidity' in line]
    assert len(liquidity_lines) > 0, "Should display liquidity information"


def test_financial_strength_risk_calculations():
    """Test financial strength risk calculations (current ratio, debt)."""
    financial_data = create_test_financial_data()
    metrics = create_test_metrics()
    
    section = RiskFactorsSection(financial_data, metrics)
    lines = section.generate()
    
    # Check current ratio is calculated and displayed
    current_ratio_lines = [line for line in lines if 'Current Ratio' in line or 'current ratio' in line]
    assert len(current_ratio_lines) > 0, "Should display current ratio"
    
    # Verify current ratio calculation (30M / 10M = 3.0x)
    assert any('3.00x' in line for line in current_ratio_lines), "Should calculate current ratio correctly"
    
    # Check debt assessment
    debt_lines = [line for line in lines if 'Debt' in line or 'debt' in line]
    assert len(debt_lines) > 0, "Should display debt information"


def test_operational_stability_risk_calculations():
    """Test operational stability risk calculations (earnings volatility, ROE)."""
    financial_data = create_test_financial_data()
    metrics = create_test_metrics()
    
    section = RiskFactorsSection(financial_data, metrics)
    lines = section.generate()
    
    # Check earnings volatility/stability
    earnings_lines = [line for line in lines if 'Earnings' in line or 'Profit Margin' in line]
    assert len(earnings_lines) > 0, "Should display earnings stability information"
    
    # Check ROE assessment
    roe_lines = [line for line in lines if 'Return on Equity' in line or 'ROE' in line]
    assert len(roe_lines) > 0, "Should display ROE information"
    
    # Verify ROE is displayed as percentage (15%)
    assert any('15.0%' in line for line in roe_lines), "Should display ROE as percentage"


def test_dividend_risk_when_dividend_present():
    """Test dividend risk assessment when company pays dividends."""
    financial_data = create_test_financial_data()
    metrics = create_test_metrics()
    
    section = RiskFactorsSection(financial_data, metrics)
    lines = section.generate()
    
    # Check dividend risk sections are present
    dividend_headers = [line for line in lines if 'Dividend' in line and ('Risk' in line or 'Sustainability' in line)]
    assert len(dividend_headers) > 0, "Should have dividend risk sections"
    
    # Check payout ratio is calculated
    payout_lines = [line for line in lines if 'Payout Ratio' in line or 'payout ratio' in line]
    assert len(payout_lines) > 0, "Should display payout ratio"
    
    # Verify payout ratio calculation (2.50 / 5.00 = 50%)
    assert any('50.0%' in line for line in payout_lines), "Should calculate payout ratio correctly"


def test_dividend_risk_when_no_dividend():
    """Test that dividend risk section is omitted when no dividend."""
    financial_data = create_test_financial_data()
    financial_data['forward_dividend_rate'] = 0  # No dividend
    metrics = create_test_metrics()
    
    section = RiskFactorsSection(financial_data, metrics)
    lines = section.generate()
    
    # Dividend risk sections should not be present
    dividend_headers = [line for line in lines if 'Dividend Risk' in line or 'Dividend Sustainability Risk' in line]
    assert len(dividend_headers) == 0, "Should not have dividend risk sections when no dividend"


def test_valuation_risk_with_positive_margin():
    """Test valuation risk assessment with positive margin of safety."""
    financial_data = create_test_financial_data()
    metrics = create_test_metrics()
    metrics['margin_of_safety'] = 25.5  # Positive margin
    
    section = RiskFactorsSection(financial_data, metrics)
    lines = section.generate()
    
    # Check valuation risk sections
    valuation_headers = [line for line in lines if 'Valuation Risk' in line]
    assert len(valuation_headers) > 0, "Should have valuation risk sections"
    
    # Check margin of safety is displayed
    mos_lines = [line for line in lines if 'Margin of Safety' in line and '25.5%' in line]
    assert len(mos_lines) > 0, "Should display margin of safety percentage"


def test_valuation_risk_with_negative_margin():
    """Test valuation risk assessment with negative margin of safety (overvalued)."""
    financial_data = create_test_financial_data()
    metrics = create_test_metrics()
    metrics['margin_of_safety'] = -10.5  # Negative margin (overvalued)
    
    section = RiskFactorsSection(financial_data, metrics)
    lines = section.generate()
    
    # Check for overvaluation warning
    overvaluation_lines = [line for line in lines if 'Overvaluation' in line or 'above intrinsic value' in line]
    assert len(overvaluation_lines) > 0, "Should warn about overvaluation"


def test_data_quality_risk_assessment():
    """Test data quality risk assessment."""
    financial_data = create_test_financial_data()
    metrics = create_test_metrics()
    
    section = RiskFactorsSection(financial_data, metrics)
    lines = section.generate()
    
    # Check data quality sections
    data_quality_headers = [line for line in lines if 'Data Quality Risk' in line]
    assert len(data_quality_headers) > 0, "Should have data quality risk sections"
    
    # Check institutional ownership verification note
    institutional_lines = [line for line in lines if 'Institutional Ownership' in line]
    assert len(institutional_lines) > 0, "Should mention institutional ownership"


def test_grahams_principle_included():
    """Test that Graham's principle on risk is included."""
    financial_data = create_test_financial_data()
    metrics = create_test_metrics()
    
    section = RiskFactorsSection(financial_data, metrics)
    lines = section.generate()
    
    # Check for Graham's principle quote
    graham_quotes = [line for line in lines if "Graham's Principle" in line]
    assert len(graham_quotes) >= 1, "Should include Graham's principle quote"


def test_section_ends_with_separator():
    """Test that section ends with horizontal rule separator."""
    financial_data = create_test_financial_data()
    metrics = create_test_metrics()
    
    section = RiskFactorsSection(financial_data, metrics)
    lines = section.generate()
    
    # Should end with separator
    assert lines[-1] == "---", "Section should end with horizontal rule"


def test_handles_missing_history_data():
    """Test that section handles missing historical data gracefully."""
    financial_data = create_test_financial_data()
    financial_data['history'] = {}  # No history
    metrics = create_test_metrics()
    
    section = RiskFactorsSection(financial_data, metrics)
    lines = section.generate()
    
    # Should still generate section with appropriate message
    assert "## RISK FACTORS" in lines
    insufficient_data_lines = [line for line in lines if 'Insufficient' in line]
    assert len(insufficient_data_lines) >= 1, "Should indicate insufficient data"


def test_handles_incomplete_year_data():
    """Test that section handles years with incomplete financial data."""
    financial_data = create_test_financial_data()
    # Add a year with only dividend data (no revenue/income)
    financial_data['history']['2024-12-31'] = {
        'dividend': 2.60,
        'shares_outstanding': 2000000
    }
    metrics = create_test_metrics()
    
    section = RiskFactorsSection(financial_data, metrics)
    lines = section.generate()
    
    # Should still generate sections and skip incomplete year for most calculations
    assert "## RISK FACTORS" in lines
    assert len(lines) > 10, "Should generate substantial content despite incomplete data"


def test_high_debt_warning():
    """Test that high debt levels trigger appropriate warnings."""
    financial_data = create_test_financial_data()
    # Set high debt level
    financial_data['history']['2023-12-31']['long_term_debt'] = 50000000  # 62.5% of assets
    metrics = create_test_metrics()
    
    section = RiskFactorsSection(financial_data, metrics)
    lines = section.generate()
    
    # Should warn about high debt
    high_debt_lines = [line for line in lines if 'High' in line and ('Debt' in line or 'leverage' in line)]
    assert len(high_debt_lines) > 0, "Should warn about high debt levels"


def test_low_current_ratio_warning():
    """Test that low current ratio triggers appropriate warnings."""
    financial_data = create_test_financial_data()
    # Set low current ratio (below 1.5x)
    financial_data['history']['2023-12-31']['current_assets'] = 12000000  # 1.2x ratio
    metrics = create_test_metrics()
    
    section = RiskFactorsSection(financial_data, metrics)
    lines = section.generate()
    
    # Should warn about low current ratio
    warning_lines = [line for line in lines if '⚠️' in line and 'current ratio' in line.lower()]
    assert len(warning_lines) > 0, "Should warn about low current ratio"


def test_loss_years_detection():
    """Test that loss years are properly detected and reported."""
    financial_data = create_test_financial_data()
    # Add a loss year
    financial_data['history']['2020-12-31'] = {
        'revenue': 85000000,
        'net_income': -5000000,  # Loss
        'eps': -2.50,
        'total_equity': 44000000,
        'shares_outstanding': 2000000
    }
    metrics = create_test_metrics()
    
    section = RiskFactorsSection(financial_data, metrics)
    lines = section.generate()
    
    # Should report loss years
    loss_lines = [line for line in lines if 'Loss' in line or 'loss' in line]
    assert len(loss_lines) > 0, "Should report loss years"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
