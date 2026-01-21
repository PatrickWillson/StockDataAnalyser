"""Unit tests for DossierGenerator orchestrator.

This module tests the DossierGenerator class that orchestrates the generation
of complete stock analysis dossiers by coordinating all section generators.

Requirements: 9.1
"""

import pytest
from output.dossier_generator import DossierGenerator


@pytest.fixture
def sample_financial_data():
    """Create sample financial data for testing."""
    return {
        'ticker': 'TEST.US',
        'exchange': 'US',
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'ceo_name': 'John Doe',
        'sector': 'Technology',
        'industry': 'Software',
        'employees': 10000,
        'price': 150.00,
        'price_source': 'yfinance',
        'pe_ratio': 20.0,
        'price_to_book': 3.5,
        'dividend_per_share': 2.50,
        'dividend_yield': 1.67,
        'book_value_per_share': 42.86,
        'roe': 0.15,
        'roa': 0.08,
        'profit_margin': 0.20,
        'insider_ownership': 5.0,
        'institutional_ownership': 75.0,
        'beta': 1.2,
        'week_52_high': 180.00,
        'week_52_low': 120.00,
        'forward_dividend_rate': 2.50,
        'dividend_source': 'cash_flow',
        'dividend_sources': {'2023': 'cash_flow'},
        'is_dividend_amounts': True,
        'history': {
            '2023-12-31': {
                'revenue': 100000000,
                'net_income': 20000000,
                'eps': 10.00,
                'dividend': 2.50,
                'shares_outstanding': 2000000,
                'total_equity': 85720000,
                'intangible_assets': 5000000,
                'goodwill': 3000000,
                'current_assets': 50000000,
                'current_liabilities': 20000000,
                'long_term_debt': 10000000,
                'total_assets': 120000000,
                'total_liabilities': 34280000,
                'operating_cash_flow': 25000000
            },
            '2022-12-31': {
                'revenue': 90000000,
                'net_income': 18000000,
                'eps': 9.00,
                'dividend': 2.25,
                'shares_outstanding': 2000000,
                'total_equity': 75720000,
                'intangible_assets': 4500000,
                'goodwill': 2800000,
                'current_assets': 45000000,
                'current_liabilities': 18000000,
                'long_term_debt': 12000000,
                'total_assets': 110000000,
                'total_liabilities': 34280000,
                'operating_cash_flow': 22000000
            }
        },
        'warnings': ['Test warning 1', 'Test warning 2']
    }


@pytest.fixture
def sample_metrics():
    """Create sample Graham metrics for testing."""
    return {
        'graham_number': 150.00,
        'epv': 200000000,
        'epv_details': {
            'epv': 200000000,
            'epv_per_share': 100.00,
            'normalized_earnings': 20000000,
            'years_used': 10,
            'years_included': ['2023-12-31', '2022-12-31'],
            'net_incomes': [20000000, 18000000],
            'cost_of_capital': 0.10
        },
        'net_net_value': 80.00,
        'margin_of_safety': 25.0,
        'verdict': 'UNDERVALUED',
        'defensive_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_test': 'PASS',
            'dividend_record': 'PASS',
            'earnings_growth': 'PASS',
            'pe_ratio': 'PASS',
            'price_to_book': 'PASS'
        },
        'enterprising_tests': {
            'earnings_stability': 'PASS',
            'current_ratio': 'PASS',
            'debt_test': 'PASS',
            'dividend_record': 'PASS',
            'price_test': 'PASS'
        },
        'warnings': ['Metric warning 1']
    }


@pytest.fixture
def sample_anomalies():
    """Create sample anomalies for testing."""
    return [
        'Revenue Z-Score: 2.5 (outlier)',
        'Net Income Z-Score: -1.8 (normal)'
    ]


def test_dossier_generator_initialization(sample_financial_data, sample_metrics, sample_anomalies):
    """Test DossierGenerator initialization.
    
    Requirements: 9.1
    """
    generator = DossierGenerator('TEST.US', sample_financial_data, sample_metrics, sample_anomalies)
    
    assert generator.ticker == 'TEST.US'
    assert generator.financial_data == sample_financial_data
    assert generator.metrics == sample_metrics
    assert generator.anomalies == sample_anomalies
    
    # Verify section generators are initialized
    assert generator.executive_summary is not None
    assert generator.key_metrics is not None
    assert generator.risk_factors is not None
    assert generator.methodology is not None
    assert generator.calculation_details is not None
    assert generator.graham_tests is not None
    assert generator.financial_history is not None


def test_generate_complete_dossier(sample_financial_data, sample_metrics, sample_anomalies):
    """Test complete dossier generation.
    
    Requirements: 9.1
    """
    generator = DossierGenerator('TEST.US', sample_financial_data, sample_metrics, sample_anomalies)
    dossier = generator.generate()
    
    # Verify dossier is a string
    assert isinstance(dossier, str)
    
    # Verify dossier is not empty
    assert len(dossier) > 0
    
    # Verify dossier contains key sections
    assert '# STOCK ANALYSIS DOSSIER: TEST.US' in dossier
    assert '## SECTION 1: EXECUTIVE SUMMARY' in dossier
    assert '## SECTION 2: KEY METRICS' in dossier
    assert '## RISK FACTORS' in dossier
    assert '## METHODOLOGY NOTES' in dossier
    assert '## CALCULATION DETAILS' in dossier
    assert '## SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS' in dossier
    assert '## SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS' in dossier
    assert '## SECTION 6: 20-YEAR FINANCIALS' in dossier
    assert '## SECTION 3: CRITICAL ALERTS' in dossier


def test_section_ordering(sample_financial_data, sample_metrics, sample_anomalies):
    """Test that sections appear in the correct order.
    
    Requirements: 9.1
    """
    generator = DossierGenerator('TEST.US', sample_financial_data, sample_metrics, sample_anomalies)
    dossier = generator.generate()
    
    # Find positions of each section
    header_pos = dossier.find('# STOCK ANALYSIS DOSSIER')
    exec_summary_pos = dossier.find('## SECTION 1: EXECUTIVE SUMMARY')
    key_metrics_pos = dossier.find('## SECTION 2: KEY METRICS')
    risk_factors_pos = dossier.find('## RISK FACTORS')
    methodology_pos = dossier.find('## METHODOLOGY NOTES')
    calc_details_pos = dossier.find('## CALCULATION DETAILS')
    defensive_tests_pos = dossier.find('## SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS')
    enterprising_tests_pos = dossier.find('## SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS')
    financials_pos = dossier.find('## SECTION 6: 20-YEAR FINANCIALS')
    alerts_pos = dossier.find('## SECTION 3: CRITICAL ALERTS')
    
    # Verify all sections are present
    assert header_pos >= 0
    assert exec_summary_pos >= 0
    assert key_metrics_pos >= 0
    assert risk_factors_pos >= 0
    assert methodology_pos >= 0
    assert calc_details_pos >= 0
    assert defensive_tests_pos >= 0
    assert enterprising_tests_pos >= 0
    assert financials_pos >= 0
    assert alerts_pos >= 0
    
    # Verify sections are in correct order
    assert header_pos < exec_summary_pos
    assert exec_summary_pos < key_metrics_pos
    assert key_metrics_pos < risk_factors_pos
    assert risk_factors_pos < methodology_pos
    assert methodology_pos < calc_details_pos
    assert calc_details_pos < defensive_tests_pos
    assert defensive_tests_pos < enterprising_tests_pos
    assert enterprising_tests_pos < financials_pos
    assert financials_pos < alerts_pos


def test_header_generation(sample_financial_data, sample_metrics, sample_anomalies):
    """Test header generation with metadata.
    
    Requirements: 9.1
    """
    generator = DossierGenerator('TEST.US', sample_financial_data, sample_metrics, sample_anomalies)
    dossier = generator.generate()
    
    # Verify header contains required metadata
    assert '# STOCK ANALYSIS DOSSIER: TEST.US' in dossier
    assert '# DATE:' in dossier
    assert '# SOURCE: EODHD (Tier 1 Data)' in dossier
    assert '# CEO: John Doe' in dossier
    assert '# SECTOR: Technology | INDUSTRY: Software' in dossier
    assert '# EMPLOYEES: 10,000' in dossier
    assert '# MOST RECENT ANNUAL DATA: 2023' in dossier
    assert '# CURRENCY: USD' in dossier


def test_header_with_currency_conversion(sample_financial_data, sample_metrics, sample_anomalies):
    """Test header generation with currency conversion note.
    
    Requirements: 9.1
    """
    # Modify financial data to have different currencies
    financial_data = sample_financial_data.copy()
    financial_data['original_stock_currency'] = 'GBP'
    financial_data['currency'] = 'USD'
    
    generator = DossierGenerator('TEST.LSE', financial_data, sample_metrics, sample_anomalies)
    dossier = generator.generate()
    
    # Verify currency conversion note is present
    assert '# CURRENCY: All values in USD (stock trades in GBP)' in dossier


def test_critical_alerts_generation(sample_financial_data, sample_metrics, sample_anomalies):
    """Test critical alerts generation.
    
    Requirements: 9.1
    """
    generator = DossierGenerator('TEST.US', sample_financial_data, sample_metrics, sample_anomalies)
    dossier = generator.generate()
    
    # Verify critical alerts section is present
    assert '## SECTION 3: CRITICAL ALERTS' in dossier
    
    # Verify warnings are included
    assert 'Test warning 1' in dossier
    assert 'Test warning 2' in dossier
    assert 'Metric warning 1' in dossier
    
    # Verify anomalies are included
    assert 'Revenue Z-Score: 2.5 (outlier)' in dossier
    assert 'Net Income Z-Score: -1.8 (normal)' in dossier


def test_critical_alerts_with_no_warnings_or_anomalies(sample_financial_data, sample_metrics):
    """Test critical alerts generation when there are no warnings or anomalies.
    
    Requirements: 9.1
    """
    # Remove warnings from data
    financial_data = sample_financial_data.copy()
    financial_data['warnings'] = []
    
    metrics = sample_metrics.copy()
    metrics['warnings'] = []
    
    generator = DossierGenerator('TEST.US', financial_data, metrics, [])
    dossier = generator.generate()
    
    # Verify critical alerts section is present
    assert '## SECTION 3: CRITICAL ALERTS' in dossier
    
    # Verify "no alerts" message is present
    assert 'No critical alerts or anomalies detected' in dossier


def test_verdict_in_dossier(sample_financial_data, sample_metrics, sample_anomalies):
    """Test that verdict appears in the dossier.
    
    Requirements: 9.1
    """
    generator = DossierGenerator('TEST.US', sample_financial_data, sample_metrics, sample_anomalies)
    dossier = generator.generate()
    
    # Verify verdict is present
    assert 'Verdict: **UNDERVALUED**' in dossier


def test_intrinsic_values_in_dossier(sample_financial_data, sample_metrics, sample_anomalies):
    """Test that intrinsic values appear in the dossier.
    
    Requirements: 9.1
    """
    generator = DossierGenerator('TEST.US', sample_financial_data, sample_metrics, sample_anomalies)
    dossier = generator.generate()
    
    # Verify intrinsic values are present
    assert 'Intrinsic Value (Graham)' in dossier
    assert 'Intrinsic Value (EPV)' in dossier
    assert 'Net-Net Value' in dossier


def test_graham_tests_in_dossier(sample_financial_data, sample_metrics, sample_anomalies):
    """Test that Graham tests appear in the dossier.
    
    Requirements: 9.1
    """
    generator = DossierGenerator('TEST.US', sample_financial_data, sample_metrics, sample_anomalies)
    dossier = generator.generate()
    
    # Verify defensive tests are present
    assert 'Earnings Stability: PASS' in dossier
    assert 'Current Ratio: PASS' in dossier
    assert 'Debt Test: PASS' in dossier
    
    # Verify enterprising tests are present
    assert 'Price Test: PASS' in dossier


def test_financial_history_table_in_dossier(sample_financial_data, sample_metrics, sample_anomalies):
    """Test that financial history table appears in the dossier.
    
    Requirements: 9.1
    """
    generator = DossierGenerator('TEST.US', sample_financial_data, sample_metrics, sample_anomalies)
    dossier = generator.generate()
    
    # Verify financial history table is present
    assert '| Year | Revenue | Net Income | EPS | Div/Share | BVPS |' in dossier
    assert '| 2023-12-31 |' in dossier
    assert '| 2022-12-31 |' in dossier
