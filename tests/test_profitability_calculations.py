"""
Unit tests for profitability metrics calculations.

Tests the calculate_profitability_metrics method in FinancialDataProcessor
to ensure correct calculation of ROE, ROA, and Profit Margin from annual data.
"""

import pytest
from core.financial_data_processor import FinancialDataProcessor


class TestProfitabilityCalculations:
    """Test suite for profitability metrics calculations."""
    
    def test_calculate_roe_with_valid_data(self):
        """Test ROE calculation with valid data."""
        history = {
            '2025-06-30': {
                'net_income': 100000,
                'total_equity': 500000,
                'total_assets': 1000000,
                'revenue': 1000000
            }
        }
        
        roe, roa, profit_margin, year = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        assert roe == 0.20  # 100000 / 500000
        assert year == '2025-06-30'
    
    def test_calculate_roa_with_valid_data(self):
        """Test ROA calculation with valid data."""
        history = {
            '2025-06-30': {
                'net_income': 100000,
                'total_equity': 500000,
                'total_assets': 1000000,
                'revenue': 1000000
            }
        }
        
        roe, roa, profit_margin, year = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        assert roa == 0.10  # 100000 / 1000000
        assert year == '2025-06-30'
    
    def test_calculate_profit_margin_with_valid_data(self):
        """Test Profit Margin calculation with valid data."""
        history = {
            '2025-06-30': {
                'net_income': 100000,
                'total_equity': 500000,
                'total_assets': 1000000,
                'revenue': 1000000
            }
        }
        
        roe, roa, profit_margin, year = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        assert profit_margin == 0.10  # 100000 / 1000000
        assert year == '2025-06-30'
    
    def test_zero_equity_returns_zero_roe(self):
        """Test that zero equity returns 0.0 for ROE."""
        history = {
            '2025-06-30': {
                'net_income': 100000,
                'total_equity': 0,
                'total_assets': 1000000,
                'revenue': 1000000
            }
        }
        
        roe, roa, profit_margin, year = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        assert roe == 0.0
        assert roa == 0.10  # Other metrics still calculated
        assert profit_margin == 0.10
    
    def test_zero_assets_returns_zero_roa(self):
        """Test that zero assets returns 0.0 for ROA."""
        history = {
            '2025-06-30': {
                'net_income': 100000,
                'total_equity': 500000,
                'total_assets': 0,
                'revenue': 1000000
            }
        }
        
        roe, roa, profit_margin, year = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        assert roe == 0.20  # Other metrics still calculated
        assert roa == 0.0
        assert profit_margin == 0.10
    
    def test_zero_revenue_returns_zero_margin(self):
        """Test that zero revenue returns 0.0 for Profit Margin."""
        history = {
            '2025-06-30': {
                'net_income': 100000,
                'total_equity': 500000,
                'total_assets': 1000000,
                'revenue': 0
            }
        }
        
        roe, roa, profit_margin, year = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        assert roe == 0.20  # Other metrics still calculated
        assert roa == 0.10
        assert profit_margin == 0.0
    
    def test_negative_net_income_returns_negative_percentages(self):
        """Test that negative net income returns correct negative percentages."""
        history = {
            '2025-06-30': {
                'net_income': -50000,
                'total_equity': 500000,
                'total_assets': 1000000,
                'revenue': 1000000
            }
        }
        
        roe, roa, profit_margin, year = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        assert roe == -0.10  # -50000 / 500000
        assert roa == -0.05  # -50000 / 1000000
        assert profit_margin == -0.05  # -50000 / 1000000
    
    def test_missing_data_returns_zeros(self):
        """Test that missing data returns 0.0 for affected metrics."""
        history = {
            '2025-06-30': {
                'net_income': 100000,
                # Missing total_equity, total_assets, revenue
            }
        }
        
        roe, roa, profit_margin, year = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        # All metrics should be 0.0 due to missing denominators
        assert roe == 0.0
        assert roa == 0.0
        assert profit_margin == 0.0
        assert year == '2025-06-30'  # Year is still identified
    
    def test_multiple_years_uses_most_recent(self):
        """Test that multiple years of data uses the most recent complete year."""
        history = {
            '2025-06-30': {
                'net_income': 200000,
                'total_equity': 600000,
                'total_assets': 1200000,
                'revenue': 2000000
            },
            '2024-06-30': {
                'net_income': 100000,
                'total_equity': 500000,
                'total_assets': 1000000,
                'revenue': 1000000
            },
            '2023-06-30': {
                'net_income': 80000,
                'total_equity': 400000,
                'total_assets': 800000,
                'revenue': 800000
            }
        }
        
        roe, roa, profit_margin, year = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        # Should use 2025 data (most recent)
        assert year == '2025-06-30'
        assert roe == pytest.approx(0.3333, rel=0.01)  # 200000 / 600000
        assert roa == pytest.approx(0.1667, rel=0.01)  # 200000 / 1200000
        assert profit_margin == 0.10  # 200000 / 2000000
    
    def test_consistent_net_income_across_metrics(self):
        """Test that all three metrics use the same net income value."""
        history = {
            '2025-06-30': {
                'net_income': 123456,
                'total_equity': 500000,
                'total_assets': 1000000,
                'revenue': 1000000
            }
        }
        
        roe, roa, profit_margin, year = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        # Verify all metrics use the same net income (123456)
        assert roe * 500000 == pytest.approx(123456, rel=0.01)
        assert roa * 1000000 == pytest.approx(123456, rel=0.01)
        assert profit_margin * 1000000 == pytest.approx(123456, rel=0.01)
    
    def test_no_history_returns_zeros_and_none(self):
        """Test that empty history returns (0.0, 0.0, 0.0, None)."""
        history = {}
        
        roe, roa, profit_margin, year = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        assert roe == 0.0
        assert roa == 0.0
        assert profit_margin == 0.0
        assert year is None
    
    def test_incomplete_year_skipped(self):
        """Test that incomplete years are skipped to find most recent complete year."""
        history = {
            '2026-06-30': {
                # Incomplete - no financial data
                'dividend': 0.91
            },
            '2025-06-30': {
                'net_income': 100000,
                'total_equity': 500000,
                'total_assets': 1000000,
                'revenue': 1000000
            }
        }
        
        roe, roa, profit_margin, year = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        # Should skip 2026 and use 2025
        assert year == '2025-06-30'
        assert roe == 0.20
    
    def test_total_assets_extraction(self):
        """Test that total_assets is properly extracted and used in ROA calculation."""
        # This tests that the balance sheet parsing includes total_assets
        history = {
            '2025-06-30': {
                'net_income': 100000,
                'total_equity': 500000,
                'total_assets': 1500000,  # Different from equity
                'revenue': 1000000
            }
        }
        
        roe, roa, profit_margin, year = FinancialDataProcessor.calculate_profitability_metrics(history)
        
        # ROA should use total_assets, not total_equity
        assert roa == pytest.approx(0.0667, rel=0.01)  # 100000 / 1500000
        assert roe == 0.20  # 100000 / 500000 (different from ROA)
