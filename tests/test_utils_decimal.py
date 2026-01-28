"""
Test Utilities for Decimal-Based Property Testing

This module provides reusable utilities for property-based testing with Python's Decimal type.
All financial calculations should use Decimal to prevent floating-point precision errors.

Feature: graham-metrics-enhancement
Validates: Requirements 10.2
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Union, Any
from hypothesis import strategies as st


# Decimal Conversion Utilities

def to_decimal(value: Union[float, int, str, Decimal]) -> Decimal:
    """
    Convert a value to Decimal safely.
    
    CRITICAL: Always convert floats to strings first to avoid float artifacts.
    - Decimal(1.1) → 1.1000000000000000888... (BAD)
    - Decimal(str(1.1)) → 1.1 (GOOD)
    
    Args:
        value: Value to convert (float, int, str, or Decimal)
    
    Returns:
        Decimal representation of the value
    
    Raises:
        InvalidOperation: If value cannot be converted to Decimal
    """
    if isinstance(value, Decimal):
        return value
    elif isinstance(value, (int, str)):
        return Decimal(value)
    elif isinstance(value, float):
        # Convert float to string first to avoid binary float artifacts
        return Decimal(str(value))
    else:
        raise InvalidOperation(f"Cannot convert {type(value)} to Decimal")


def round_decimal(value: Decimal, decimal_places: int = 2, 
                  rounding: str = ROUND_HALF_UP) -> Decimal:
    """
    Round a Decimal value to specified decimal places.
    
    Args:
        value: Decimal value to round
        decimal_places: Number of decimal places (default: 2)
        rounding: Rounding mode (default: ROUND_HALF_UP)
    
    Returns:
        Rounded Decimal value
    
    Example:
        >>> round_decimal(Decimal('1.234'), 2)
        Decimal('1.23')
        >>> round_decimal(Decimal('1.235'), 2)
        Decimal('1.24')
    """
    quantizer = Decimal('0.1') ** decimal_places
    return value.quantize(quantizer, rounding=rounding)


def decimal_to_float(value: Decimal, decimal_places: int = 2) -> float:
    """
    Convert Decimal to float with rounding.
    
    Use this for final output values that need to be floats.
    
    Args:
        value: Decimal value to convert
        decimal_places: Number of decimal places to round to
    
    Returns:
        Float representation rounded to specified decimal places
    """
    rounded = round_decimal(value, decimal_places)
    return float(rounded)


def decimal_to_percentage(value: Decimal, decimal_places: int = 1) -> str:
    """
    Convert Decimal to percentage string.
    
    Args:
        value: Decimal value (e.g., 0.45 for 45%)
        decimal_places: Number of decimal places in percentage
    
    Returns:
        Formatted percentage string (e.g., "45.0%")
    
    Example:
        >>> decimal_to_percentage(Decimal('0.456'), 1)
        '45.6%'
    """
    percentage = value * 100
    rounded = round_decimal(percentage, decimal_places)
    return f"{rounded}%"


# Hypothesis Strategies for Financial Data

def decimal_strategy(min_value: Union[str, int, float] = "0",
                    max_value: Union[str, int, float] = "1000000000000",
                    places: int = 2) -> st.SearchStrategy:
    """
    Create a Hypothesis strategy for generating Decimal values.
    
    This strategy generates Decimal values directly without going through floats,
    avoiding floating-point precision issues.
    
    Args:
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive)
        places: Number of decimal places
    
    Returns:
        Hypothesis strategy that generates Decimal values
    
    Example:
        >>> @given(amount=decimal_strategy(min_value="0", max_value="1000000", places=2))
        ... def test_calculation(amount):
        ...     assert isinstance(amount, Decimal)
    """
    # Convert bounds to Decimal
    min_dec = to_decimal(min_value)
    max_dec = to_decimal(max_value)
    
    # Generate integers and convert to Decimal with specified places
    # This avoids float artifacts entirely
    multiplier = 10 ** places
    min_int = int(min_dec * multiplier)
    max_int = int(max_dec * multiplier)
    
    return st.integers(min_value=min_int, max_value=max_int).map(
        lambda x: Decimal(x) / Decimal(multiplier)
    )


def positive_decimal_strategy(max_value: Union[str, int, float] = "1000000000000",
                              places: int = 2) -> st.SearchStrategy:
    """
    Create a Hypothesis strategy for generating positive Decimal values.
    
    Convenience wrapper around decimal_strategy with min_value > 0.
    
    Args:
        max_value: Maximum value (inclusive)
        places: Number of decimal places
    
    Returns:
        Hypothesis strategy that generates positive Decimal values
    """
    min_value = Decimal('0.01') if places >= 2 else Decimal('0.1')
    return decimal_strategy(min_value=str(min_value), max_value=max_value, places=places)


def currency_strategy(min_value: Union[str, int, float] = "0",
                     max_value: Union[str, int, float] = "1000000000000") -> st.SearchStrategy:
    """
    Create a Hypothesis strategy for generating currency amounts.
    
    Currency amounts are always rounded to 2 decimal places.
    
    Args:
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive)
    
    Returns:
        Hypothesis strategy that generates Decimal currency values
    """
    return decimal_strategy(min_value=min_value, max_value=max_value, places=2)


def ratio_strategy(min_value: Union[str, int, float] = "0",
                  max_value: Union[str, int, float] = "1000") -> st.SearchStrategy:
    """
    Create a Hypothesis strategy for generating financial ratios.
    
    Ratios are typically rounded to 2 decimal places.
    
    Args:
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive)
    
    Returns:
        Hypothesis strategy that generates Decimal ratio values
    """
    return decimal_strategy(min_value=min_value, max_value=max_value, places=2)


def percentage_strategy(min_value: Union[str, int, float] = "0",
                       max_value: Union[str, int, float] = "100") -> st.SearchStrategy:
    """
    Create a Hypothesis strategy for generating percentage values.
    
    Percentages are typically rounded to 1 decimal place.
    
    Args:
        min_value: Minimum percentage (inclusive)
        max_value: Maximum percentage (inclusive)
    
    Returns:
        Hypothesis strategy that generates Decimal percentage values
    """
    return decimal_strategy(min_value=min_value, max_value=max_value, places=1)


def shares_strategy(min_value: Union[str, int, float] = "1",
                   max_value: Union[str, int, float] = "100000000000") -> st.SearchStrategy:
    """
    Create a Hypothesis strategy for generating share counts.
    
    Share counts are whole numbers (no decimal places).
    
    Args:
        min_value: Minimum shares (inclusive)
        max_value: Maximum shares (inclusive)
    
    Returns:
        Hypothesis strategy that generates Decimal share counts
    """
    return decimal_strategy(min_value=min_value, max_value=max_value, places=0)


# Validation Utilities

def assert_decimal_equal(actual: Decimal, expected: Decimal, 
                        tolerance: Decimal = Decimal('0.01'),
                        message: str = None) -> None:
    """
    Assert that two Decimal values are equal within tolerance.
    
    Args:
        actual: Actual value
        expected: Expected value
        tolerance: Maximum allowed difference (default: 0.01)
        message: Optional custom error message
    
    Raises:
        AssertionError: If values differ by more than tolerance
    """
    diff = abs(actual - expected)
    if diff > tolerance:
        if message:
            raise AssertionError(message)
        else:
            raise AssertionError(
                f"Decimal values not equal within tolerance {tolerance}: "
                f"actual={actual}, expected={expected}, diff={diff}"
            )


def assert_decimal_percentage_equal(actual: str, expected: Decimal,
                                   tolerance: Decimal = Decimal('0.1'),
                                   message: str = None) -> None:
    """
    Assert that a percentage string matches expected Decimal value.
    
    Args:
        actual: Actual percentage string (e.g., "45.6%")
        expected: Expected Decimal value (e.g., Decimal('45.6'))
        tolerance: Maximum allowed difference (default: 0.1)
        message: Optional custom error message
    
    Raises:
        AssertionError: If values differ by more than tolerance
    """
    # Parse percentage string
    if not actual.endswith('%'):
        raise AssertionError(f"Expected percentage string ending with '%', got: {actual}")
    
    actual_value = Decimal(actual[:-1])
    assert_decimal_equal(actual_value, expected, tolerance, message)


def is_valid_decimal(value: Any) -> bool:
    """
    Check if a value can be converted to Decimal.
    
    Args:
        value: Value to check
    
    Returns:
        True if value can be converted to Decimal, False otherwise
    """
    try:
        to_decimal(value)
        return True
    except (InvalidOperation, ValueError, TypeError):
        return False


# Calculation Helpers

def safe_divide(numerator: Decimal, denominator: Decimal,
               default: Union[str, Decimal] = "N/A") -> Union[Decimal, str]:
    """
    Safely divide two Decimal values, returning default on zero denominator.
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Value to return if denominator is zero (default: "N/A")
    
    Returns:
        Division result or default value
    
    Example:
        >>> safe_divide(Decimal('10'), Decimal('2'))
        Decimal('5')
        >>> safe_divide(Decimal('10'), Decimal('0'))
        'N/A'
    """
    if denominator == 0:
        return default
    return numerator / denominator


def safe_multiply(*values: Decimal) -> Decimal:
    """
    Safely multiply multiple Decimal values.
    
    Args:
        *values: Decimal values to multiply
    
    Returns:
        Product of all values
    
    Example:
        >>> safe_multiply(Decimal('2'), Decimal('3'), Decimal('4'))
        Decimal('24')
    """
    result = Decimal('1')
    for value in values:
        result *= value
    return result


# Test Data Generators

def generate_balance_sheet_data(
    current_assets: Decimal = None,
    current_liabilities: Decimal = None,
    total_assets: Decimal = None,
    total_liabilities: Decimal = None,
    total_equity: Decimal = None,
    long_term_debt: Decimal = None,
    inventory: Decimal = None,
    intangible_assets: Decimal = None,
    goodwill: Decimal = None,
    shares_outstanding: Decimal = None
) -> dict:
    """
    Generate a balance sheet data dictionary for testing.
    
    Provides default values if not specified, ensuring consistency.
    
    Args:
        current_assets: Current assets (default: 1000000)
        current_liabilities: Current liabilities (default: 400000)
        total_assets: Total assets (default: 2000000)
        total_liabilities: Total liabilities (default: 800000)
        total_equity: Total equity (default: 1200000)
        long_term_debt: Long-term debt (default: 400000)
        inventory: Inventory (default: 100000)
        intangible_assets: Intangible assets (default: 50000)
        goodwill: Goodwill (default: 30000)
        shares_outstanding: Shares outstanding (default: 1000000)
    
    Returns:
        Dictionary with balance sheet data
    """
    return {
        'current_assets': float(current_assets if current_assets is not None else Decimal('1000000')),
        'current_liabilities': float(current_liabilities if current_liabilities is not None else Decimal('400000')),
        'total_assets': float(total_assets if total_assets is not None else Decimal('2000000')),
        'total_liabilities': float(total_liabilities if total_liabilities is not None else Decimal('800000')),
        'total_equity': float(total_equity if total_equity is not None else Decimal('1200000')),
        'long_term_debt': float(long_term_debt if long_term_debt is not None else Decimal('400000')),
        'inventory': float(inventory if inventory is not None else Decimal('100000')),
        'intangible_assets': float(intangible_assets if intangible_assets is not None else Decimal('50000')),
        'goodwill': float(goodwill if goodwill is not None else Decimal('30000')),
        'shares_outstanding': float(shares_outstanding if shares_outstanding is not None else Decimal('1000000'))
    }


def generate_income_statement_data(
    revenue: Decimal = None,
    net_income: Decimal = None,
    eps: Decimal = None,
    operating_income: Decimal = None,
    gross_profit: Decimal = None
) -> dict:
    """
    Generate an income statement data dictionary for testing.
    
    Args:
        revenue: Total revenue (default: 5000000)
        net_income: Net income (default: 500000)
        eps: Earnings per share (default: 5.00)
        operating_income: Operating income (default: 750000)
        gross_profit: Gross profit (default: 2000000)
    
    Returns:
        Dictionary with income statement data
    """
    return {
        'revenue': float(revenue if revenue is not None else Decimal('5000000')),
        'net_income': float(net_income if net_income is not None else Decimal('500000')),
        'eps': float(eps if eps is not None else Decimal('5.00')),
        'operating_income': float(operating_income if operating_income is not None else Decimal('750000')),
        'gross_profit': float(gross_profit if gross_profit is not None else Decimal('2000000'))
    }


def generate_financial_year_data(
    year: str = '2023-12-31',
    balance_sheet: dict = None,
    income_statement: dict = None,
    dividend: Decimal = None
) -> dict:
    """
    Generate a complete financial year data dictionary for testing.
    
    Combines balance sheet and income statement data for a single year.
    
    Args:
        year: Year string (default: '2023-12-31')
        balance_sheet: Balance sheet data (uses defaults if None)
        income_statement: Income statement data (uses defaults if None)
        dividend: Dividend per share (default: 1.00)
    
    Returns:
        Dictionary with complete financial data for one year
    """
    bs_data = balance_sheet if balance_sheet is not None else generate_balance_sheet_data()
    is_data = income_statement if income_statement is not None else generate_income_statement_data()
    
    return {
        **bs_data,
        **is_data,
        'dividend': float(dividend if dividend is not None else Decimal('1.00'))
    }


def generate_multi_year_history(
    years: int = 10,
    base_year: int = 2023,
    growth_rate: Decimal = Decimal('0.05')
) -> dict:
    """
    Generate multi-year financial history for testing.
    
    Creates realistic growing financials with specified growth rate.
    
    Args:
        years: Number of years to generate (default: 10)
        base_year: Most recent year (default: 2023)
        growth_rate: Annual growth rate as decimal (default: 0.05 = 5%)
    
    Returns:
        Dictionary with year keys and financial data values
    """
    history = {}
    
    for i in range(years):
        year = base_year - i
        year_str = f'{year}-12-31'
        
        # Apply growth backwards (older years have smaller values)
        factor = (Decimal('1') + growth_rate) ** i
        
        # Generate data with growth applied
        bs_data = generate_balance_sheet_data(
            current_assets=Decimal('1000000') * factor,
            current_liabilities=Decimal('400000') * factor,
            total_equity=Decimal('1200000') * factor,
            shares_outstanding=Decimal('1000000')  # Shares stay constant
        )
        
        is_data = generate_income_statement_data(
            revenue=Decimal('5000000') * factor,
            net_income=Decimal('500000') * factor,
            eps=Decimal('5.00') * factor
        )
        
        history[year_str] = generate_financial_year_data(
            year=year_str,
            balance_sheet=bs_data,
            income_statement=is_data,
            dividend=Decimal('1.00') * factor
        )
    
    return history
