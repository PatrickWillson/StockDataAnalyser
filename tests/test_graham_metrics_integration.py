"""End-to-end integration tests for Graham Metrics Enhancement.

Tests verify that all new metrics are calculated correctly and appear in the
dossier output with proper formatting and structure preservation.
"""

from core.graham_math import GrahamCalculator
from output.sections.executive_summary import ExecutiveSummarySection
from output.sections.key_metrics import KeyMetricsSection
from output.sections.graham_tests import GrahamTestsSection
from output.sections.financial_history import FinancialHistorySection
from output.sections.methodology import MethodologySection


def create_test_financial_data():
    """Create comprehensive test financial data with all required fields."""
    return {
        'ticker': 'TEST',
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'price': 100.0,
        'exchange': 'US',
        'sector': 'Technology',
        'pe_ratio': 12.5,
        'price_to_book': 1.2,
        'current_ratio': 2.15,
        'history': {
            '2023-12-31': {
                'revenue': 1000000.0,
                'net_income': 100000.0,
                'eps': 5.0,
                'dividend': 2.0,
                'total_equity': 500000.0,
                'current_assets': 600000.0,
                'current_liabilities': 280000.0,
                'total_liabilities': 400000.0,
                'long_term_debt': 150000.0,
                'inventory': 50000.0,
                'shares_outstanding': 20000.0,
                'wcps': 16.0,
                'payout_ratio': '40.0%',
                'total_debt': 200000.0,
                'year_end_price': 100.0
            },
            '2022-12-31': {
                'revenue': 950000.0,
                'net_income': 95000.0,
                'eps': 4.75,
                'dividend': 1.80,
                'total_equity': 480000.0,
                'current_assets': 580000.0,
                'current_liabilities': 270000.0,
                'total_liabilities': 390000.0,
                'long_term_debt': 145000.0,
                'inventory': 48000.0,
                'shares_outstanding': 20000.0,
                'wcps': 15.5,
                'payout_ratio': '37.9%',
                'total_debt': 195000.0,
                'year_end_price': 95.0
            },
            '2021-12-31': {
                'revenue': 900000.0,
                'net_income': 90000.0,
                'eps': 4.5,
                'dividend': 1.60,
                'total_equity': 460000.0,
                'current_assets': 560000.0,
                'current_liabilities': 260000.0,
                'total_liabilities': 380000.0,
                'long_term_debt': 140000.0,
                'inventory': 46000.0,
                'shares_outstanding': 20000.0,
                'wcps': 15.0,
                'payout_ratio': '35.6%',
                'total_debt': 190000.0,
                'year_end_price': 90.0
            }
        },
        'is_dividend_amounts': True,
        'historical_fx_rates': {}
    }


def test_end_to_end_all_new_metrics_calculated():
    """Test that all new metrics are calculated in the complete workflow."""
    # Arrange
    financial_data = create_test_financial_data()
    calculator = GrahamCalculator(financial_data)
    
    # Act - Calculate all metrics
    metrics = calculator.compute_all()
    
    # Assert - All new metrics present
    assert 'nca_details' in metrics
    assert 'quick_ratio' in metrics
    assert 'three_year_avg_pe' in metrics
    assert 'combined_pe_pb_test' in metrics
    
    # Assert - NCA details structure
    nca_details = metrics['nca_details']
    assert 'current_assets' in nca_details
    assert 'total_liabilities' in nca_details
    assert 'nca' in nca_details
    assert 'debt_coverage_ratio' in nca_details
    
    # Assert - Three-year P/E structure
    three_year_pe = metrics['three_year_avg_pe']
    assert 'three_year_avg_eps' in three_year_pe
    assert 'pe_on_avg' in three_year_pe
    assert 'years_used' in three_year_pe
    
    # Assert - Combined test structure
    combined_test = metrics['combined_pe_pb_test']
    assert 'pe_ratio' in combined_test
    assert 'pb_ratio' in combined_test
    assert 'product' in combined_test
    assert 'result' in combined_test


def test_end_to_end_executive_summary_section():
    """Test that Executive Summary section includes three-year P/E."""
    # Arrange
    financial_data = create_test_financial_data()
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    
    section = ExecutiveSummarySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'SECTION 1: EXECUTIVE SUMMARY' in content
    assert 'P/E Ratio (Current Year)' in content
    assert 'P/E Ratio (3-Year Avg)' in content
    assert 'based on avg EPS' in content


def test_end_to_end_key_metrics_section():
    """Test that Key Metrics section includes NCA and Quick Ratio."""
    # Arrange
    financial_data = create_test_financial_data()
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    
    section = KeyMetricsSection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'SECTION 2: KEY METRICS' in content
    assert 'Liquidity Analysis' in content
    assert 'Quick Ratio' in content
    assert 'Net Current Assets (NCA) Analysis' in content
    assert 'Current Assets' in content
    assert 'Total Liabilities' in content
    assert 'Debt Coverage Ratio' in content


def test_end_to_end_graham_tests_section():
    """Test that Graham Tests section includes combined test and updated criteria."""
    # Arrange
    financial_data = create_test_financial_data()
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    
    section = GrahamTestsSection(metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS' in content
    assert '8. **Combined P/E × P/B Test**' in content
    assert 'Positive earnings in each of the past 10 years' in content
    assert 'SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS' in content
    assert 'Profitability in most recent year and 5 of past 7 years' in content


def test_end_to_end_financial_history_section():
    """Test that Financial History section includes WCPS and Payout Ratio columns."""
    # Arrange
    financial_data = create_test_financial_data()
    
    section = FinancialHistorySection(financial_data)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'SECTION 6: 20-YEAR FINANCIALS' in content
    assert 'WCPS' in content
    assert 'Payout Ratio' in content
    assert '16.0' in content or '16.00' in content  # WCPS value
    assert '40.0%' in content  # Payout ratio value
    assert 'WCPS (Working Capital Per Share)' in content
    assert 'Payout Ratio**: (Dividend / EPS) × 100' in content


def test_end_to_end_methodology_section():
    """Test that Methodology section includes all new metric explanations."""
    # Arrange
    financial_data = create_test_financial_data()
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    
    section = MethodologySection(financial_data, metrics)
    
    # Act
    lines = section.generate()
    content = '\n'.join(lines)
    
    # Assert
    assert 'METHODOLOGY NOTES' in content
    assert 'P/E Ratio (3-Year Average)' in content
    assert "Graham's Defensive Criterion #6" in content
    assert 'Quick Ratio (Acid Test)' in content
    assert 'Net Current Assets (NCA) and Debt Coverage' in content
    assert 'Combined P/E × P/B Test' in content
    assert 'Historical Trend Metrics' in content


def test_end_to_end_table_alignment():
    """Test that financial history table has correct column alignment."""
    # Arrange
    financial_data = create_test_financial_data()
    
    section = FinancialHistorySection(financial_data)
    
    # Act
    lines = section.generate()
    
    # Find header and alignment rows
    header_line = None
    alignment_line = None
    for i, line in enumerate(lines):
        if line.startswith('| Year |'):
            header_line = line
            if i + 1 < len(lines):
                alignment_line = lines[i + 1]
            break
    
    # Assert
    assert header_line is not None, "Header line not found"
    assert alignment_line is not None, "Alignment line not found"
    
    # Count columns
    header_cols = header_line.count('|') - 1
    alignment_cols = alignment_line.count('|') - 1
    
    assert header_cols == alignment_cols, \
        f"Column mismatch: header has {header_cols} columns, alignment has {alignment_cols}"
    assert header_cols == 13, f"Expected 13 columns, got {header_cols}"


def test_end_to_end_with_edge_cases():
    """Test complete workflow with edge cases (negative values, N/A, etc.)."""
    # Arrange - Financial data with edge cases
    financial_data = {
        'ticker': 'EDGE',
        'currency': 'USD',
        'original_stock_currency': 'USD',
        'price': 50.0,
        'exchange': 'US',
        'sector': 'Services',
        'pe_ratio': 25.0,
        'price_to_book': 2.5,
        'current_ratio': 1.5,
        'history': {
            '2023-12-31': {
                'revenue': 500000.0,
                'net_income': -10000.0,  # Loss year
                'eps': -0.5,
                'dividend': 0.0,  # No dividend
                'total_equity': 200000.0,
                'current_assets': 150000.0,
                'current_liabilities': 200000.0,  # Negative working capital
                'total_liabilities': 250000.0,
                'long_term_debt': 100000.0,
                'inventory': 0.0,  # No inventory (Services sector)
                'shares_outstanding': 20000.0,
                'wcps': -2.5,  # Negative WCPS
                'payout_ratio': 'N/A',  # Can't calculate with negative EPS
                'total_debt': 120000.0,
                'year_end_price': 50.0
            },
            '2022-12-31': {
                'revenue': 480000.0,
                'net_income': 20000.0,
                'eps': 1.0,
                'dividend': 0.5,
                'total_equity': 210000.0,
                'current_assets': 180000.0,
                'current_liabilities': 150000.0,
                'total_liabilities': 220000.0,
                'long_term_debt': 90000.0,
                'inventory': 0.0,
                'shares_outstanding': 20000.0,
                'wcps': 1.5,
                'payout_ratio': '50.0%',
                'total_debt': 110000.0,
                'year_end_price': 55.0
            }
        },
        'is_dividend_amounts': True,
        'historical_fx_rates': {}
    }
    
    calculator = GrahamCalculator(financial_data)
    
    # Act
    metrics = calculator.compute_all()
    
    # Assert - Calculations handle edge cases gracefully
    assert metrics is not None
    assert 'nca_details' in metrics
    assert 'quick_ratio' in metrics
    assert 'three_year_avg_pe' in metrics
    assert 'combined_pe_pb_test' in metrics
    
    # Assert - NCA should be negative
    nca_details = metrics['nca_details']
    assert nca_details['nca'] < 0, "NCA should be negative when liabilities exceed current assets"
    
    # Assert - Quick Ratio should work without inventory (Services sector)
    quick_ratio = metrics['quick_ratio']
    assert quick_ratio != 'N/A', "Quick Ratio should be calculated for Services sector without inventory"
    
    # Assert - Three-year P/E should be N/A (only 2 years of data)
    three_year_pe = metrics['three_year_avg_pe']
    assert three_year_pe['three_year_avg_eps'] == 'N/A', "Should need 3 years of data"


def test_end_to_end_dossier_structure_preserved():
    """Test that dossier structure is preserved with new metrics."""
    # Arrange
    financial_data = create_test_financial_data()
    calculator = GrahamCalculator(financial_data)
    metrics = calculator.compute_all()
    
    # Act - Generate all sections
    exec_summary = ExecutiveSummarySection(financial_data, metrics)
    key_metrics = KeyMetricsSection(financial_data, metrics)
    graham_tests = GrahamTestsSection(metrics)
    fin_history = FinancialHistorySection(financial_data)
    methodology = MethodologySection(financial_data, metrics)
    
    exec_lines = exec_summary.generate()
    key_lines = key_metrics.generate()
    graham_lines = graham_tests.generate()
    fin_lines = fin_history.generate()
    method_lines = methodology.generate()
    
    # Combine all sections
    all_lines = exec_lines + key_lines + graham_lines + fin_lines + method_lines
    content = '\n'.join(all_lines)
    
    # Assert - All expected sections present
    assert 'SECTION 1: EXECUTIVE SUMMARY' in content
    assert 'SECTION 2: KEY METRICS' in content
    assert 'SECTION 4: GRAHAM DEFENSIVE INVESTOR TESTS' in content
    assert 'SECTION 5: GRAHAM ENTERPRISING INVESTOR TESTS' in content
    assert 'SECTION 6: 20-YEAR FINANCIALS' in content
    assert 'METHODOLOGY NOTES' in content
    
    # Assert - Section separators present
    assert content.count('---') >= 5, "Should have section separators"
