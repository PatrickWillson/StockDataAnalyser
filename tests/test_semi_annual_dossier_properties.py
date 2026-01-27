"""
Property-based tests for dossier generation with semi-annual data.

Feature: ttm-semi-annual-gap-fix
Property 8: Correct Dossier Generation for Semi-Annual Reporters

For any semi-annual reporter with valid data, the generated dossier should include
the TTM Analysis section, display "semi-annual" as the frequency, format period
coverage as "H1 YYYY through H2 YYYY", and not include false gap warnings in
Critical Alerts.

Validates: Requirements 6.1, 6.2, 6.3, 6.4
"""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from core.ttm_calculator import TTMCalculator
from output.sections.ttm_analysis import TTMAnalysisSection


class TestSemiAnnualDossierGeneration:
    """Property-based tests for dossier generation with semi-annual data."""
    
    # Feature: ttm-semi-annual-gap-fix, Property 8: Correct Dossier Generation for Semi-Annual Reporters
    @settings(suppress_health_check=[HealthCheck.too_slow], max_examples=100)
    @given(
        interval_days=st.integers(min_value=150, max_value=210),
        h1_revenue=st.floats(min_value=1000.0, max_value=100000000000.0),
        h2_revenue=st.floats(min_value=1000.0, max_value=100000000000.0),
        h1_net_income=st.floats(min_value=-10000000000.0, max_value=50000000000.0),
        h2_net_income=st.floats(min_value=-10000000000.0, max_value=50000000000.0),
        total_equity=st.floats(min_value=1000000.0, max_value=1000000000000.0),
        shares=st.floats(min_value=1000000.0, max_value=10000000000.0),
    )
    def test_semi_annual_dossier_includes_ttm_section(
        self, interval_days, h1_revenue, h2_revenue, h1_net_income, h2_net_income,
        total_equity, shares
    ):
        """
        Property: For any semi-annual data with valid intervals (150-210 days),
        the dossier should include the TTM Analysis section with correct formatting.
        
        **Validates: Requirements 6.1, 6.2, 6.3**
        """
        # Arrange: Create semi-annual data
        most_recent_date = datetime(2025, 6, 30)
        older_date = most_recent_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': {
                most_recent_date.strftime('%Y-%m-%d'): {
                    'revenue': h1_revenue,
                    'net_income': h1_net_income
                },
                older_date.strftime('%Y-%m-%d'): {
                    'revenue': h2_revenue,
                    'net_income': h2_net_income
                },
            },
            'balance_sheet': {
                most_recent_date.strftime('%Y-%m-%d'): {
                    'total_equity': total_equity,
                    'shares_outstanding': shares,
                    'intangible_assets': 100.0,
                    'goodwill': 200.0,
                    'current_assets': 5000.0,
                    'total_liabilities': 3000.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        ttm_metrics = calculator.compute_all()
        
        # Create annual metrics for comparison
        annual_metrics = {
            'graham_number': 250.00,
            'tbvps': 28.00,
            'net_net_value': 14.00,
            'margin_of_safety': 10.0,
            'pe_ratio': 23.4,
            'pb_ratio': 12.0
        }
        
        # Act: Generate TTM section
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, {"currency": "USD", "price": 100.0, "ttm_dividend": 0.0, "ttm_dividend_payments": [], "history": {}})
        lines = section.generate()
        dossier_content = '\n'.join(lines)
        
        # Assert: Verify TTM section is present
        assert "## SECTION 1.5: TTM (TRAILING TWELVE MONTHS) ANALYSIS" in dossier_content, \
            "Dossier should include TTM Analysis section header"
        
        # Verify frequency is displayed as "Semi-Annual"
        assert "Reporting Frequency: Semi-Annual" in dossier_content, \
            f"Dossier should display 'Semi-Annual' frequency, got: {dossier_content}"
        
        # Verify period coverage is formatted (should contain "through")
        assert "Period Covered:" in dossier_content, \
            "Dossier should include period coverage"
        assert "through" in dossier_content, \
            "Period coverage should be formatted with 'through'"
        
        # Verify TTM metrics are displayed
        assert "TTM Graham Number" in dossier_content
        assert "TTM Tangible Book Value Per Share" in dossier_content
        assert "TTM P/E Ratio" in dossier_content
    
    # Feature: ttm-semi-annual-gap-fix, Property 8: Correct Dossier Generation for Semi-Annual Reporters
    @settings(max_examples=50)
    @given(
        interval_days=st.integers(min_value=150, max_value=210),
    )
    def test_semi_annual_dossier_no_false_gap_warnings(self, interval_days):
        """
        Property: For any semi-annual data with valid intervals (150-210 days),
        the dossier should not include false gap warnings in Critical Alerts.
        
        **Validates: Requirements 6.4**
        """
        # Arrange: Create semi-annual data with valid interval
        most_recent_date = datetime(2025, 6, 30)
        older_date = most_recent_date - timedelta(days=interval_days)
        
        quarterly_data = {
            'income_statement': {
                most_recent_date.strftime('%Y-%m-%d'): {
                    'revenue': 50000000.0,
                    'net_income': 5000000.0
                },
                older_date.strftime('%Y-%m-%d'): {
                    'revenue': 55000000.0,
                    'net_income': 5500000.0
                },
            },
            'balance_sheet': {
                most_recent_date.strftime('%Y-%m-%d'): {
                    'total_equity': 100000000.0,
                    'shares_outstanding': 10000000.0,
                    'intangible_assets': 5000000.0,
                    'goodwill': 3000000.0,
                    'current_assets': 60000000.0,
                    'total_liabilities': 40000000.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        ttm_metrics = calculator.compute_all()
        
        # Assert: Verify no gap warnings
        warnings = ttm_metrics.get('warnings', [])
        gap_warnings = [w for w in warnings if 'gap' in w.lower() or 'missing' in w.lower()]
        
        assert len(gap_warnings) == 0, \
            f"Should not have gap warnings for valid semi-annual data (interval: {interval_days} days), but got: {gap_warnings}"
    
    def test_aep_lse_dossier_generation(self):
        """
        Unit test: Verify AEP.LSE pattern generates correct dossier section.
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4**
        """
        # Arrange: AEP.LSE pattern
        quarterly_data = {
            'income_statement': {
                '2025-06-30': {'revenue': 50000000.0, 'net_income': 5000000.0},  # H1 2025
                '2024-12-31': {'revenue': 55000000.0, 'net_income': 5500000.0},  # FY 2024
                '2024-06-30': {'revenue': 48000000.0, 'net_income': 4800000.0},  # H1 2024
                '2023-12-31': {'revenue': 52000000.0, 'net_income': 5200000.0},  # FY 2023
            },
            'balance_sheet': {
                '2025-06-30': {
                    'total_equity': 100000000.0,
                    'intangible_assets': 5000000.0,
                    'goodwill': 3000000.0,
                    'current_assets': 60000000.0,
                    'total_liabilities': 40000000.0,
                    'shares_outstanding': 10000000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        ttm_metrics = calculator.compute_all()
        
        annual_metrics = {
            'graham_number': 250.00,
            'tbvps': 28.00,
            'net_net_value': 14.00,
            'margin_of_safety': 10.0,
            'pe_ratio': 23.4,
            'pb_ratio': 12.0
        }
        
        # Act: Generate dossier section
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, {"currency": "USD", "price": 100.0, "ttm_dividend": 0.0, "ttm_dividend_payments": [], "history": {}})
        lines = section.generate()
        dossier_content = '\n'.join(lines)
        
        # Assert: Verify all requirements
        assert "## SECTION 1.5: TTM (TRAILING TWELVE MONTHS) ANALYSIS" in dossier_content
        assert "Reporting Frequency: Semi-Annual" in dossier_content
        assert "Period Covered:" in dossier_content
        assert "through" in dossier_content
        
        # Verify no gap warnings
        warnings = ttm_metrics.get('warnings', [])
        gap_warnings = [w for w in warnings if 'gap' in w.lower() or 'missing' in w.lower()]
        assert len(gap_warnings) == 0, f"Should not have gap warnings, but got: {gap_warnings}"
    
    def test_mpe_lse_dossier_generation(self):
        """
        Unit test: Verify MPE.LSE pattern generates correct dossier section.
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4**
        """
        # Arrange: MPE.LSE pattern
        quarterly_data = {
            'income_statement': {
                '2025-06-30': {'revenue': 30000000.0, 'net_income': 3000000.0},  # H1 2025
                '2024-12-31': {'revenue': 35000000.0, 'net_income': 3500000.0},  # FY 2024
                '2024-06-30': {'revenue': 28000000.0, 'net_income': 2800000.0},  # H1 2024
            },
            'balance_sheet': {
                '2025-06-30': {
                    'total_equity': 80000000.0,
                    'intangible_assets': 4000000.0,
                    'goodwill': 2000000.0,
                    'current_assets': 50000000.0,
                    'total_liabilities': 30000000.0,
                    'shares_outstanding': 8000000.0
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        ttm_metrics = calculator.compute_all()
        
        annual_metrics = {
            'graham_number': 250.00,
            'tbvps': 28.00,
            'net_net_value': 14.00,
            'margin_of_safety': 10.0,
            'pe_ratio': 23.4,
            'pb_ratio': 12.0
        }
        
        # Act: Generate dossier section
        section = TTMAnalysisSection(ttm_metrics, annual_metrics, {"currency": "USD", "price": 100.0, "ttm_dividend": 0.0, "ttm_dividend_payments": [], "history": {}})
        lines = section.generate()
        dossier_content = '\n'.join(lines)
        
        # Assert: Verify all requirements
        assert "## SECTION 1.5: TTM (TRAILING TWELVE MONTHS) ANALYSIS" in dossier_content
        assert "Reporting Frequency: Semi-Annual" in dossier_content
        assert "Period Covered:" in dossier_content
        assert "through" in dossier_content
        
        # Verify no gap warnings
        warnings = ttm_metrics.get('warnings', [])
        gap_warnings = [w for w in warnings if 'gap' in w.lower() or 'missing' in w.lower()]
        assert len(gap_warnings) == 0, f"Should not have gap warnings, but got: {gap_warnings}"
    
    def test_semi_annual_period_coverage_format(self):
        """
        Unit test: Verify period coverage is formatted as "H1 YYYY through H2 YYYY".
        
        **Validates: Requirements 6.3**
        """
        # Arrange: Semi-annual data
        quarterly_data = {
            'income_statement': {
                '2025-06-30': {'revenue': 50000000.0, 'net_income': 5000000.0},
                '2024-12-31': {'revenue': 55000000.0, 'net_income': 5500000.0},
            },
            'balance_sheet': {
                '2025-06-30': {
                    'total_equity': 100000000.0,
                    'shares_outstanding': 10000000.0,
                    'intangible_assets': 5000000.0,
                    'goodwill': 3000000.0,
                    'current_assets': 60000000.0,
                    'total_liabilities': 40000000.0,
                }
            }
        }
        
        calculator = TTMCalculator(quarterly_data, price=100.0, currency='USD')
        ttm_metrics = calculator.compute_all()
        
        # Assert: Verify date range format
        date_range = ttm_metrics.get('date_range', '')
        
        # Should contain H1 or H2 (half-year indicators)
        assert 'H1' in date_range or 'H2' in date_range, \
            f"Period coverage should use H1/H2 format for semi-annual, got: {date_range}"
        
        # Should contain "through"
        assert 'through' in date_range, \
            f"Period coverage should contain 'through', got: {date_range}"
        
        # Should contain year
        assert '2024' in date_range or '2025' in date_range, \
            f"Period coverage should contain year, got: {date_range}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
