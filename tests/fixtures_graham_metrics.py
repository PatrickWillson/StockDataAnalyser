"""
Test Fixtures for Graham Metrics Enhancement

This module provides reusable fixtures for testing the new Graham methodology metrics.
All fixtures use Decimal-based calculations to ensure precision.

Feature: graham-metrics-enhancement
"""

from decimal import Decimal
from typing import Dict, Any, List
from tests.test_utils_decimal import (
    generate_balance_sheet_data,
    generate_income_statement_data,
    generate_financial_year_data,
    to_decimal
)


class GrahamMetricsFixtures:
    """Fixtures for testing Graham metrics calculations."""
    
    @staticmethod
    def get_basic_financial_data(
        ticker: str = 'TEST.US',
        price: float = 100.0,
        currency: str = 'USD',
        sector: str = 'Technology'
    ) -> Dict[str, Any]:
        """
        Get basic financial data structure for testing.
        
        Args:
            ticker: Stock ticker
            price: Current stock price
            currency: Currency code
            sector: Company sector
        
        Returns:
            Basic financial_data dictionary
        """
        return {
            'ticker': ticker,
            'price': price,
            'currency': currency,
            'sector': sector,
            'history': {}
        }
    
    @staticmethod
    def get_nca_test_data(
        current_assets: Decimal = Decimal('1000000'),
        total_liabilities: Decimal = Decimal('600000'),
        long_term_debt: Decimal = Decimal('300000'),
        sector: str = 'Technology'
    ) -> Dict[str, Any]:
        """
        Get financial data for testing NCA calculations.
        
        Args:
            current_assets: Current assets value
            total_liabilities: Total liabilities value
            long_term_debt: Long-term debt value
            sector: Company sector
        
        Returns:
            Financial data with balance sheet for NCA testing
        """
        balance_sheet = generate_balance_sheet_data(
            current_assets=current_assets,
            total_liabilities=total_liabilities,
            long_term_debt=long_term_debt
        )
        
        year_data = generate_financial_year_data(
            year='2023-12-31',
            balance_sheet=balance_sheet
        )
        
        return {
            'ticker': 'TEST.US',
            'price': 100.0,
            'currency': 'USD',
            'sector': sector,
            'history': {
                '2023-12-31': year_data
            }
        }
    
    @staticmethod
    def get_quick_ratio_test_data(
        current_assets: Decimal = Decimal('1000000'),
        inventory: Decimal = Decimal('200000'),
        current_liabilities: Decimal = Decimal('400000'),
        sector: str = 'Manufacturing'
    ) -> Dict[str, Any]:
        """
        Get financial data for testing Quick Ratio calculations.
        
        Args:
            current_assets: Current assets value
            inventory: Inventory value
            current_liabilities: Current liabilities value
            sector: Company sector
        
        Returns:
            Financial data with balance sheet for Quick Ratio testing
        """
        balance_sheet = generate_balance_sheet_data(
            current_assets=current_assets,
            inventory=inventory,
            current_liabilities=current_liabilities
        )
        
        year_data = generate_financial_year_data(
            year='2023-12-31',
            balance_sheet=balance_sheet
        )
        
        return {
            'ticker': 'TEST.US',
            'price': 100.0,
            'currency': 'USD',
            'sector': sector,
            'history': {
                '2023-12-31': year_data
            }
        }
    
    @staticmethod
    def get_wcps_test_data(
        years: int = 5,
        base_year: int = 2023,
        working_capital_values: List[Decimal] = None,
        shares_outstanding: Decimal = Decimal('1000000')
    ) -> Dict[str, Any]:
        """
        Get financial data for testing WCPS calculations.
        
        Args:
            years: Number of years to generate
            base_year: Most recent year
            working_capital_values: List of working capital values (current_assets - current_liabilities)
            shares_outstanding: Shares outstanding (constant across years)
        
        Returns:
            Financial data with multi-year history for WCPS testing
        """
        if working_capital_values is None:
            # Generate default values with growth
            working_capital_values = [
                Decimal('600000') * (Decimal('1.05') ** i)
                for i in range(years)
            ]
        
        history = {}
        for i in range(years):
            year = base_year - i
            year_str = f'{year}-12-31'
            
            wc = working_capital_values[i]
            current_assets = wc + Decimal('400000')  # Add fixed liabilities
            current_liabilities = Decimal('400000')
            
            balance_sheet = generate_balance_sheet_data(
                current_assets=current_assets,
                current_liabilities=current_liabilities,
                shares_outstanding=shares_outstanding
            )
            
            year_data = generate_financial_year_data(
                year=year_str,
                balance_sheet=balance_sheet
            )
            
            history[year_str] = year_data
        
        return {
            'ticker': 'TEST.US',
            'price': 100.0,
            'currency': 'USD',
            'sector': 'Technology',
            'history': history
        }
    
    @staticmethod
    def get_three_year_avg_pe_test_data(
        eps_values: List[Decimal],
        price: Decimal = Decimal('100.0'),
        base_year: int = 2023
    ) -> Dict[str, Any]:
        """
        Get financial data for testing three-year average P/E calculations.
        
        Args:
            eps_values: List of EPS values (most recent first)
            price: Current stock price
            base_year: Most recent year
        
        Returns:
            Financial data with EPS history for three-year P/E testing
        """
        history = {}
        for i, eps in enumerate(eps_values):
            year = base_year - i
            year_str = f'{year}-12-31'
            
            income_statement = generate_income_statement_data(
                eps=eps,
                net_income=eps * Decimal('1000000')  # Assume 1M shares
            )
            
            year_data = generate_financial_year_data(
                year=year_str,
                income_statement=income_statement
            )
            
            history[year_str] = year_data
        
        return {
            'ticker': 'TEST.US',
            'price': float(price),
            'currency': 'USD',
            'sector': 'Technology',
            'history': history
        }
    
    @staticmethod
    def get_combined_pe_pb_test_data(
        eps: Decimal,
        total_equity: Decimal,
        shares_outstanding: Decimal,
        price: Decimal
    ) -> Dict[str, Any]:
        """
        Get financial data for testing combined P/E × P/B test.
        
        Args:
            eps: Earnings per share
            total_equity: Total shareholder equity
            shares_outstanding: Number of shares outstanding
            price: Current stock price
        
        Returns:
            Financial data configured to produce specified P/E and P/B ratios
        """
        balance_sheet = generate_balance_sheet_data(
            total_equity=total_equity,
            intangible_assets=Decimal('0'),
            goodwill=Decimal('0'),
            shares_outstanding=shares_outstanding
        )
        
        income_statement = generate_income_statement_data(
            eps=eps,
            net_income=eps * shares_outstanding
        )
        
        year_data = generate_financial_year_data(
            year='2023-12-31',
            balance_sheet=balance_sheet,
            income_statement=income_statement
        )
        
        return {
            'ticker': 'TEST.US',
            'price': float(price),
            'currency': 'USD',
            'sector': 'Technology',
            'history': {
                '2023-12-31': year_data
            }
        }
    
    @staticmethod
    def get_payout_ratio_test_data(
        eps_dividend_pairs: List[tuple],
        base_year: int = 2023
    ) -> Dict[str, Any]:
        """
        Get financial data for testing payout ratio calculations.
        
        Args:
            eps_dividend_pairs: List of (eps, dividend) tuples for each year
            base_year: Most recent year
        
        Returns:
            Financial data with EPS and dividend history for payout ratio testing
        """
        history = {}
        for i, (eps, dividend) in enumerate(eps_dividend_pairs):
            year = base_year - i
            year_str = f'{year}-12-31'
            
            income_statement = generate_income_statement_data(
                eps=to_decimal(eps),
                net_income=to_decimal(eps) * Decimal('1000000')
            )
            
            year_data = generate_financial_year_data(
                year=year_str,
                income_statement=income_statement,
                dividend=to_decimal(dividend)
            )
            
            history[year_str] = year_data
        
        return {
            'ticker': 'TEST.US',
            'price': 100.0,
            'currency': 'USD',
            'sector': 'Technology',
            'history': history
        }
    
    @staticmethod
    def get_earnings_stability_test_data(
        eps_values: List[Decimal],
        base_year: int = 2023
    ) -> Dict[str, Any]:
        """
        Get financial data for testing earnings stability.
        
        Args:
            eps_values: List of EPS values (most recent first)
            base_year: Most recent year
        
        Returns:
            Financial data with EPS history for earnings stability testing
        """
        history = {}
        for i, eps in enumerate(eps_values):
            year = base_year - i
            year_str = f'{year}-12-31'
            
            income_statement = generate_income_statement_data(
                eps=eps,
                net_income=eps * Decimal('1000000')
            )
            
            # Add required balance sheet fields for defensive tests
            balance_sheet = generate_balance_sheet_data()
            
            year_data = generate_financial_year_data(
                year=year_str,
                balance_sheet=balance_sheet,
                income_statement=income_statement
            )
            
            history[year_str] = year_data
        
        return {
            'ticker': 'TEST.US',
            'price': 100.0,
            'currency': 'USD',
            'sector': 'Technology',
            'history': history
        }


class EdgeCaseFixtures:
    """Fixtures for testing edge cases."""
    
    @staticmethod
    def get_negative_nca_data() -> Dict[str, Any]:
        """
        Get financial data with negative NCA.
        
        Returns:
            Financial data where total liabilities exceed current assets
        """
        return GrahamMetricsFixtures.get_nca_test_data(
            current_assets=Decimal('500000'),
            total_liabilities=Decimal('800000'),
            long_term_debt=Decimal('400000')
        )
    
    @staticmethod
    def get_zero_current_liabilities_data() -> Dict[str, Any]:
        """
        Get financial data with zero current liabilities.
        
        Returns:
            Financial data with zero current liabilities (for Quick Ratio edge case)
        """
        return GrahamMetricsFixtures.get_quick_ratio_test_data(
            current_assets=Decimal('1000000'),
            inventory=Decimal('200000'),
            current_liabilities=Decimal('0')
        )
    
    @staticmethod
    def get_missing_inventory_data(sector: str = 'Services') -> Dict[str, Any]:
        """
        Get financial data with missing inventory.
        
        Args:
            sector: Company sector (Services/Technology vs others)
        
        Returns:
            Financial data with None inventory value
        """
        balance_sheet = generate_balance_sheet_data(
            current_assets=Decimal('1000000'),
            current_liabilities=Decimal('400000')
        )
        # Remove inventory
        balance_sheet['inventory'] = None
        
        year_data = generate_financial_year_data(
            year='2023-12-31',
            balance_sheet=balance_sheet
        )
        
        return {
            'ticker': 'TEST.US',
            'price': 100.0,
            'currency': 'USD',
            'sector': sector,
            'history': {
                '2023-12-31': year_data
            }
        }
    
    @staticmethod
    def get_negative_working_capital_data() -> Dict[str, Any]:
        """
        Get financial data with negative working capital.
        
        Returns:
            Financial data where current liabilities exceed current assets
        """
        return GrahamMetricsFixtures.get_wcps_test_data(
            years=3,
            working_capital_values=[
                Decimal('-100000'),  # 2023: negative
                Decimal('50000'),    # 2022: positive
                Decimal('-50000')    # 2021: negative
            ]
        )
    
    @staticmethod
    def get_insufficient_years_data(years: int = 2) -> Dict[str, Any]:
        """
        Get financial data with insufficient years for three-year average.
        
        Args:
            years: Number of years to include (< 3)
        
        Returns:
            Financial data with fewer than 3 years of history
        """
        eps_values = [Decimal('5.0'), Decimal('4.5')][:years]
        return GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
            eps_values=eps_values
        )
    
    @staticmethod
    def get_loss_years_data() -> Dict[str, Any]:
        """
        Get financial data with loss years (negative EPS).
        
        Returns:
            Financial data including years with negative earnings
        """
        return GrahamMetricsFixtures.get_three_year_avg_pe_test_data(
            eps_values=[
                Decimal('5.0'),   # 2023: profit
                Decimal('-2.0'),  # 2022: loss
                Decimal('3.0')    # 2021: profit
            ]
        )
    
    @staticmethod
    def get_zero_eps_data() -> Dict[str, Any]:
        """
        Get financial data with zero EPS.
        
        Returns:
            Financial data with zero earnings
        """
        return GrahamMetricsFixtures.get_payout_ratio_test_data(
            eps_dividend_pairs=[
                (Decimal('0'), Decimal('1.0')),  # Zero EPS, dividend paid
                (Decimal('5.0'), Decimal('2.0'))
            ]
        )
    
    @staticmethod
    def get_negative_eps_data() -> Dict[str, Any]:
        """
        Get financial data with negative EPS.
        
        Returns:
            Financial data with losses
        """
        return GrahamMetricsFixtures.get_payout_ratio_test_data(
            eps_dividend_pairs=[
                (Decimal('-2.0'), Decimal('1.0')),  # Loss, dividend paid
                (Decimal('5.0'), Decimal('2.0'))
            ]
        )
    
    @staticmethod
    def get_payout_over_100_data() -> Dict[str, Any]:
        """
        Get financial data with payout ratio > 100%.
        
        Returns:
            Financial data where dividend exceeds earnings
        """
        return GrahamMetricsFixtures.get_payout_ratio_test_data(
            eps_dividend_pairs=[
                (Decimal('2.0'), Decimal('3.0')),  # Dividend > EPS
                (Decimal('5.0'), Decimal('2.0'))
            ]
        )


class SectorSpecificFixtures:
    """Fixtures for testing sector-specific behavior."""
    
    @staticmethod
    def get_financial_sector_data() -> Dict[str, Any]:
        """
        Get financial data for a Financial sector company.
        
        Returns:
            Financial data with sector='Financials'
        """
        return GrahamMetricsFixtures.get_nca_test_data(
            sector='Financials'
        )
    
    @staticmethod
    def get_utility_sector_data() -> Dict[str, Any]:
        """
        Get financial data for a Utility sector company.
        
        Returns:
            Financial data with sector='Utilities'
        """
        return GrahamMetricsFixtures.get_nca_test_data(
            sector='Utilities'
        )
    
    @staticmethod
    def get_services_sector_data() -> Dict[str, Any]:
        """
        Get financial data for a Services sector company.
        
        Returns:
            Financial data with sector='Services'
        """
        return GrahamMetricsFixtures.get_quick_ratio_test_data(
            sector='Services'
        )
    
    @staticmethod
    def get_technology_sector_data() -> Dict[str, Any]:
        """
        Get financial data for a Technology sector company.
        
        Returns:
            Financial data with sector='Technology'
        """
        return GrahamMetricsFixtures.get_quick_ratio_test_data(
            sector='Technology'
        )
