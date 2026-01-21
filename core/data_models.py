"""
Data Transfer Objects (DTOs) for Stock Data Analyser.

This module defines strongly-typed data structures for financial data and metrics.
All DTOs use Python dataclasses with type hints for IDE support and validation.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List, Union


@dataclass
class CompanyInfo:
    """
    Company identification and metadata.
    
    Attributes:
        ticker: Stock ticker symbol (e.g., "AAPL.US", "YU.LSE")
        exchange: Exchange code (e.g., "US", "LSE", "TO")
        ceo_name: Name of the Chief Executive Officer
        sector: Business sector (e.g., "Technology", "Financials")
        industry: Specific industry within sector
        employees: Number of employees
    """
    ticker: str
    exchange: str
    ceo_name: str
    sector: str
    industry: str
    employees: int


@dataclass
class CurrencyInfo:
    """
    Currency information and conversion details.
    
    Attributes:
        unified_currency: Currency used for all calculations (e.g., "USD", "GBP")
        original_stock_currency: Currency the stock trades in (e.g., "GBX" for LSE)
        financials_currency: Currency of financial statements
        dividend_currency: Currency of dividend payments
        conversion_details: List of conversion messages for transparency
    """
    unified_currency: str
    original_stock_currency: str
    financials_currency: str
    dividend_currency: str
    conversion_details: List[str]


@dataclass
class FinancialData:
    """
    Complete financial data for a company.
    
    All monetary values are in the unified currency specified in CurrencyInfo.
    
    Attributes:
        company: Company identification and metadata
        currency: Currency information and conversion details
        price: Current stock price (in unified currency)
        price_source: Source of price data ('yfinance', 'EODHD', or 'Missing')
        history: Historical financial data by year
        warnings: List of data quality warnings and notes
        
        # Highlights (current metrics)
        dividend_per_share: Annual dividend per share
        dividend_yield: Dividend yield as decimal (e.g., 0.05 = 5%)
        pe_ratio: Price-to-Earnings ratio
        book_value_per_share: Book value per share
        roe: Return on Equity as decimal
        roa: Return on Assets as decimal
        profit_margin: Profit margin as decimal
        
        # Valuation
        price_to_book: Price-to-Book ratio
        enterprise_value: Enterprise value
        
        # Ownership
        insider_ownership: Insider ownership percentage
        institutional_ownership: Institutional ownership percentage
        
        # Technicals
        beta: Beta (volatility measure)
        week_52_high: 52-week high price
        week_52_low: 52-week low price
        
        # Dividend metadata
        forward_dividend_rate: Forward annual dividend rate (if available)
        dividend_source: Primary source of dividend data
        dividend_sources: Dictionary mapping year to dividend source
    """
    company: CompanyInfo
    currency: CurrencyInfo
    price: float
    price_source: str
    history: Dict[str, Dict[str, float]]
    warnings: List[str]
    
    # Highlights
    dividend_per_share: float
    dividend_yield: float
    pe_ratio: float
    book_value_per_share: float
    roe: float
    roa: float
    profit_margin: float
    
    # Valuation
    price_to_book: float
    enterprise_value: float
    
    # Ownership
    insider_ownership: float
    institutional_ownership: float
    
    # Technicals
    beta: float
    week_52_high: float
    week_52_low: float
    
    # Dividend metadata
    forward_dividend_rate: Optional[float]
    dividend_source: str
    dividend_sources: Dict[str, str]


@dataclass
class EPVDetails:
    """
    Earnings Power Value calculation details.
    
    EPV uses Graham's full-cycle methodology with 7-10 years of earnings data.
    
    Attributes:
        epv: Enterprise Earnings Power Value
        epv_per_share: EPV divided by shares outstanding
        normalized_earnings: Average net income over the period
        years_used: Number of years included in calculation
        years_included: List of years included (ISO date format)
        net_incomes: List of net income values for each year
        cost_of_capital: Cost of capital used (typically 0.10 = 10%)
    """
    epv: float
    epv_per_share: float
    normalized_earnings: float
    years_used: int
    years_included: List[str]
    net_incomes: List[float]
    cost_of_capital: float


@dataclass
class GrahamMetrics:
    """
    Graham methodology calculation results.
    
    Contains all calculated metrics from Benjamin Graham's value investing formulas.
    
    Attributes:
        graham_number: Intrinsic value estimate (sqrt(22.5 × EPS × TBVPS))
        epv: Earnings Power Value (enterprise value)
        epv_details: Detailed EPV calculation breakdown
        net_net_value: Net-Net Working Capital Value per share
        margin_of_safety: Margin of Safety as percentage
        verdict: Investment verdict (e.g., "STRONG BUY", "OVERVALUED")
        defensive_tests: Results of 7 Defensive Investor tests
        enterprising_tests: Results of 6 Enterprising Investor tests
        warnings: List of calculation warnings
    """
    graham_number: Union[float, str]
    epv: float
    epv_details: EPVDetails
    net_net_value: Union[float, str]
    margin_of_safety: Union[float, str]
    verdict: str
    defensive_tests: Dict[str, str]
    enterprising_tests: Dict[str, str]
    warnings: List[str]
