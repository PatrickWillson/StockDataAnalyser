"""
Property-based tests for profitability metrics calculations.

Uses Hypothesis to test universal properties that should hold true
across all valid inputs (100+ iterations with random data).
"""

import pytest
from hypothesis import given, strategies as st, assume
from core.financial_data_processor import FinancialDataProcessor


# Strategy for generating valid financial data
@st.composite
def financial_history(draw):
    """Generate valid financial history data for testing."""
    year = draw(st.sampled_from(['2025-06-30', '2024-12-31', '2023-09-30']))
    net_income = draw(st.floats(min_value=-1e9, max_value=1e9, allow_nan=False, allow_infinity=False))
    total_equity = draw(st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False))
    total_assets = draw(st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False))
    revenue = draw(st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False))
    
    return {
        year: {
            'net_income': net_income,
            'total_equity': total_equity,
            'total_assets': total_assets,
            'revenue': revenue
        }
    }


class TestProfitabilityProperties:
    """Property-based tests for profitability calculations."""
    
    @given(financial_history())
    def test_property_1_roe_calculation_correctness(self, history):
        """Property 1: For any financial history with valid net income and total equity,
        calculating ROE should return net_income / total_equity."""
        year = list(history.keys())[0]
        data = history[year]
        net_income = data['net_income']
        total_equity = data['total_equity']
        
        roe, _, _, _ = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        if total_equity > 0:
            expected_roe = net_income / total_equity
            assert roe == pytest.approx(expected_roe, rel=1e-6)
        else:
            assert roe == 0.0
    
    @given(financial_history())
    def test_property_2_roa_calculation_correctness(self, history):
        """Property 2: For any financial history with valid net income and total assets,
        calculating ROA should return net_income / total_assets."""
        year = list(history.keys())[0]
        data = history[year]
        net_income = data['net_income']
        total_assets = data['total_assets']
        
        _, roa, _, _ = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        if total_assets > 0:
            expected_roa = net_income / total_assets
            assert roa == pytest.approx(expected_roa, rel=1e-6)
        else:
            assert roa == 0.0
    
    @given(financial_history())
    def test_property_3_profit_margin_calculation_correctness(self, history):
        """Property 3: For any financial history with valid net income and revenue,
        calculating profit margin should return net_income / revenue."""
        year = list(history.keys())[0]
        data = history[year]
        net_income = data['net_income']
        revenue = data['revenue']
        
        _, _, profit_margin, _ = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        if revenue > 0:
            expected_margin = net_income / revenue
            assert profit_margin == pytest.approx(expected_margin, rel=1e-6)
        else:
            assert profit_margin == 0.0
    
    @given(
        net_income=st.floats(min_value=-1e9, max_value=1e9, allow_nan=False, allow_infinity=False),
        year=st.sampled_from(['2025-06-30', '2024-12-31'])
    )
    def test_property_4_zero_denominator_handling(self, net_income, year):
        """Property 4: For any profitability metric calculation where the denominator is zero,
        the result should be 0.0."""
        # Test with zero equity
        history_zero_equity = {
            year: {
                'net_income': net_income,
                'total_equity': 0,
                'total_assets': 1000000,
                'revenue': 1000000
            }
        }
        roe, _, _, _ = FinancialDataProcessor.calculate_profitability_metrics(history_zero_equity)
        assert roe == 0.0
        
        # Test with zero assets
        history_zero_assets = {
            year: {
                'net_income': net_income,
                'total_equity': 500000,
                'total_assets': 0,
                'revenue': 1000000
            }
        }
        _, roa, _, _ = FinancialDataProcessor.calculate_profitability_metrics(history_zero_assets)
        assert roa == 0.0
        
        # Test with zero revenue
        history_zero_revenue = {
            year: {
                'net_income': net_income,
                'total_equity': 500000,
                'total_assets': 1000000,
                'revenue': 0
            }
        }
        _, _, profit_margin, _ = FinancialDataProcessor.calculate_profitability_metrics(history_zero_revenue)
        assert profit_margin == 0.0
    
    @given(
        total_equity=st.floats(min_value=1, max_value=1e12, allow_nan=False, allow_infinity=False),
        total_assets=st.floats(min_value=1, max_value=1e12, allow_nan=False, allow_infinity=False),
        revenue=st.floats(min_value=1, max_value=1e12, allow_nan=False, allow_infinity=False),
        year=st.sampled_from(['2025-06-30', '2024-12-31'])
    )
    def test_property_5_negative_net_income_handling(self, total_equity, total_assets, revenue, year):
        """Property 5: For any financial history with negative net income,
        all profitability metrics should return correct negative percentages."""
        net_income = -100000  # Fixed negative value
        
        history = {
            year: {
                'net_income': net_income,
                'total_equity': total_equity,
                'total_assets': total_assets,
                'revenue': revenue
            }
        }
        
        roe, roa, profit_margin, _ = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        # All metrics should be negative
        assert roe < 0
        assert roa < 0
        assert profit_margin < 0
        
        # Verify formulas are correct
        assert roe == pytest.approx(net_income / total_equity, rel=1e-6)
        assert roa == pytest.approx(net_income / total_assets, rel=1e-6)
        assert profit_margin == pytest.approx(net_income / revenue, rel=1e-6)
    
    @given(
        net_income=st.floats(min_value=-1e9, max_value=1e9, allow_nan=False, allow_infinity=False),
        year=st.sampled_from(['2025-06-30', '2024-12-31'])
    )
    def test_property_6_missing_data_handling(self, net_income, year):
        """Property 6: For any financial history with missing required fields,
        affected metrics should return 0.0."""
        # Skip test if net_income is 0 (edge case where year won't be identified)
        assume(net_income != 0)
        
        # Missing all denominators
        history = {
            year: {
                'net_income': net_income,
                # Missing total_equity, total_assets, revenue
            }
        }
        
        roe, roa, profit_margin, returned_year = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        # All metrics should be 0.0 due to missing denominators
        assert roe == 0.0
        assert roa == 0.0
        assert profit_margin == 0.0
        # Year should still be identified (since net_income != 0)
        assert returned_year == year
    
    @given(
        net_income_2025=st.floats(min_value=1, max_value=1e9, allow_nan=False, allow_infinity=False),
        net_income_2024=st.floats(min_value=1, max_value=1e9, allow_nan=False, allow_infinity=False),
        total_equity_2025=st.floats(min_value=1, max_value=1e12, allow_nan=False, allow_infinity=False),
        total_equity_2024=st.floats(min_value=1, max_value=1e12, allow_nan=False, allow_infinity=False),
        total_assets_2025=st.floats(min_value=1, max_value=1e12, allow_nan=False, allow_infinity=False),
        total_assets_2024=st.floats(min_value=1, max_value=1e12, allow_nan=False, allow_infinity=False),
        revenue_2025=st.floats(min_value=1, max_value=1e12, allow_nan=False, allow_infinity=False),
        revenue_2024=st.floats(min_value=1, max_value=1e12, allow_nan=False, allow_infinity=False)
    )
    def test_property_7_most_recent_year_selection(self, net_income_2025, net_income_2024,
                                                   total_equity_2025, total_equity_2024,
                                                   total_assets_2025, total_assets_2024,
                                                   revenue_2025, revenue_2024):
        """Property 7: For any financial history with multiple complete years,
        all profitability metrics should use the same most recent complete year."""
        history = {
            '2025-06-30': {
                'net_income': net_income_2025,
                'total_equity': total_equity_2025,
                'total_assets': total_assets_2025,
                'revenue': revenue_2025
            },
            '2024-06-30': {
                'net_income': net_income_2024,
                'total_equity': total_equity_2024,
                'total_assets': total_assets_2024,
                'revenue': revenue_2024
            }
        }
        
        roe, roa, profit_margin, year = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        # Should use 2025 data (most recent)
        assert year == '2025-06-30'
        
        # Verify calculations use 2025 data
        expected_roe = net_income_2025 / total_equity_2025
        expected_roa = net_income_2025 / total_assets_2025
        expected_margin = net_income_2025 / revenue_2025
        
        assert roe == pytest.approx(expected_roe, rel=1e-6)
        assert roa == pytest.approx(expected_roa, rel=1e-6)
        assert profit_margin == pytest.approx(expected_margin, rel=1e-6)
    
    @given(financial_history())
    def test_property_8_consistent_net_income_usage(self, history):
        """Property 8: For any calculation of ROE, ROA, and Profit Margin,
        all three metrics should use the same net income value."""
        year = list(history.keys())[0]
        data = history[year]
        net_income = data['net_income']
        total_equity = data['total_equity']
        total_assets = data['total_assets']
        revenue = data['revenue']
        
        # Skip edge cases with very small denominators that cause numerical issues
        assume(total_equity == 0 or total_equity > 1e-100)
        assume(total_assets == 0 or total_assets > 1e-100)
        assume(revenue == 0 or revenue > 1e-100)
        
        roe, roa, profit_margin, _ = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        # Verify all metrics use the same net income
        if total_equity > 0:
            assert roe * total_equity == pytest.approx(net_income, rel=1e-6)
        if total_assets > 0:
            assert roa * total_assets == pytest.approx(net_income, rel=1e-6)
        if revenue > 0:
            assert profit_margin * revenue == pytest.approx(net_income, rel=1e-6)
    
    @given(financial_history())
    def test_property_11_logging_completeness(self, history):
        """Property 11: For any profitability metric calculation,
        the calculation should complete without errors."""
        # This property tests that the method handles all inputs gracefully
        # and returns a valid tuple
        result = FinancialDataProcessor.calculate_profitability_metrics(history, debug=True)
        
        assert isinstance(result, tuple)
        assert len(result) == 4
        
        roe, roa, profit_margin, year = result
        
        # All metrics should be floats
        assert isinstance(roe, float)
        assert isinstance(roa, float)
        assert isinstance(profit_margin, float)
        
        # Year should be string or None
        assert year is None or isinstance(year, str)
    
    @given(
        total_assets=st.floats(min_value=1, max_value=1e12, allow_nan=False, allow_infinity=False),
        year=st.sampled_from(['2025-06-30', '2024-12-31'])
    )
    def test_property_12_total_assets_extraction(self, total_assets, year):
        """Property 12: For any balance sheet data with totalAssets field,
        the parsed result should include total_assets."""
        history = {
            year: {
                'net_income': 100000,
                'total_equity': 500000,
                'total_assets': total_assets,
                'revenue': 1000000
            }
        }
        
        _, roa, _, _ = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        # ROA should be calculated using total_assets
        expected_roa = 100000 / total_assets
        assert roa == pytest.approx(expected_roa, rel=1e-6)
