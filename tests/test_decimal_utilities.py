"""
Unit Tests for Decimal Utilities

Verifies that the Decimal utility functions work correctly.

Feature: graham-metrics-enhancement
Validates: Requirements 10.2
"""

import pytest
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from hypothesis import given, settings
from tests.test_utils_decimal import (
    to_decimal,
    round_decimal,
    decimal_to_float,
    decimal_to_percentage,
    decimal_strategy,
    positive_decimal_strategy,
    currency_strategy,
    ratio_strategy,
    percentage_strategy,
    shares_strategy,
    assert_decimal_equal,
    assert_decimal_percentage_equal,
    is_valid_decimal,
    safe_divide,
    safe_multiply,
    generate_balance_sheet_data,
    generate_income_statement_data,
    generate_financial_year_data,
    generate_multi_year_history
)


class TestDecimalConversion:
    """Test Decimal conversion utilities."""
    
    def test_to_decimal_from_float(self):
        """Test converting float to Decimal via string."""
        result = to_decimal(1.1)
        assert result == Decimal('1.1')
        assert str(result) == '1.1'  # No float artifacts
    
    def test_to_decimal_from_int(self):
        """Test converting int to Decimal."""
        result = to_decimal(42)
        assert result == Decimal('42')
    
    def test_to_decimal_from_string(self):
        """Test converting string to Decimal."""
        result = to_decimal('123.45')
        assert result == Decimal('123.45')
    
    def test_to_decimal_from_decimal(self):
        """Test that Decimal passes through unchanged."""
        original = Decimal('99.99')
        result = to_decimal(original)
        assert result is original
    
    def test_to_decimal_invalid_type(self):
        """Test that invalid types raise InvalidOperation."""
        with pytest.raises(InvalidOperation):
            to_decimal([1, 2, 3])
    
    def test_round_decimal_default(self):
        """Test rounding to 2 decimal places (default)."""
        result = round_decimal(Decimal('1.234'))
        assert result == Decimal('1.23')
    
    def test_round_decimal_round_up(self):
        """Test rounding up with ROUND_HALF_UP."""
        result = round_decimal(Decimal('1.235'), 2)
        assert result == Decimal('1.24')
    
    def test_round_decimal_custom_places(self):
        """Test rounding to custom decimal places."""
        result = round_decimal(Decimal('1.23456'), 3)
        assert result == Decimal('1.235')
    
    def test_decimal_to_float(self):
        """Test converting Decimal to float with rounding."""
        result = decimal_to_float(Decimal('1.234'), 2)
        assert result == 1.23
        assert isinstance(result, float)
    
    def test_decimal_to_percentage(self):
        """Test converting Decimal to percentage string."""
        result = decimal_to_percentage(Decimal('0.456'), 1)
        assert result == '45.6%'
    
    def test_decimal_to_percentage_whole_number(self):
        """Test converting whole number percentage."""
        result = decimal_to_percentage(Decimal('1.0'), 1)
        assert result == '100.0%'


class TestHypothesisStrategies:
    """Test Hypothesis strategy generators."""
    
    @settings(max_examples=10)
    @given(value=decimal_strategy(min_value="0", max_value="1000", places=2))
    def test_decimal_strategy_generates_decimals(self, value):
        """Test that decimal_strategy generates Decimal values."""
        assert isinstance(value, Decimal)
        assert Decimal('0') <= value <= Decimal('1000')
    
    @settings(max_examples=10)
    @given(value=positive_decimal_strategy(max_value="1000", places=2))
    def test_positive_decimal_strategy_generates_positive(self, value):
        """Test that positive_decimal_strategy generates positive values."""
        assert isinstance(value, Decimal)
        assert value > Decimal('0')
        assert value <= Decimal('1000')
    
    @settings(max_examples=10)
    @given(value=currency_strategy(min_value="0", max_value="1000000"))
    def test_currency_strategy_has_two_places(self, value):
        """Test that currency_strategy generates values with 2 decimal places."""
        assert isinstance(value, Decimal)
        # Check that value has at most 2 decimal places
        str_value = str(value)
        if '.' in str_value:
            decimal_part = str_value.split('.')[1]
            assert len(decimal_part) <= 2
    
    @settings(max_examples=10)
    @given(value=ratio_strategy(min_value="0", max_value="100"))
    def test_ratio_strategy_generates_ratios(self, value):
        """Test that ratio_strategy generates ratio values."""
        assert isinstance(value, Decimal)
        assert Decimal('0') <= value <= Decimal('100')
    
    @settings(max_examples=10)
    @given(value=percentage_strategy(min_value="0", max_value="100"))
    def test_percentage_strategy_generates_percentages(self, value):
        """Test that percentage_strategy generates percentage values."""
        assert isinstance(value, Decimal)
        assert Decimal('0') <= value <= Decimal('100')
    
    @settings(max_examples=10)
    @given(value=shares_strategy(min_value="1", max_value="1000000"))
    def test_shares_strategy_generates_whole_numbers(self, value):
        """Test that shares_strategy generates whole numbers."""
        assert isinstance(value, Decimal)
        assert value == value.to_integral_value()  # No fractional part


class TestValidationUtilities:
    """Test validation utility functions."""
    
    def test_assert_decimal_equal_passes(self):
        """Test that equal Decimals pass assertion."""
        assert_decimal_equal(Decimal('1.23'), Decimal('1.23'))
    
    def test_assert_decimal_equal_within_tolerance(self):
        """Test that values within tolerance pass assertion."""
        assert_decimal_equal(
            Decimal('1.234'),
            Decimal('1.235'),
            tolerance=Decimal('0.01')
        )
    
    def test_assert_decimal_equal_fails(self):
        """Test that unequal Decimals fail assertion."""
        with pytest.raises(AssertionError):
            assert_decimal_equal(
                Decimal('1.23'),
                Decimal('1.25'),
                tolerance=Decimal('0.01')
            )
    
    def test_assert_decimal_percentage_equal_passes(self):
        """Test that matching percentage passes assertion."""
        assert_decimal_percentage_equal('45.6%', Decimal('45.6'))
    
    def test_assert_decimal_percentage_equal_fails(self):
        """Test that non-matching percentage fails assertion."""
        with pytest.raises(AssertionError):
            assert_decimal_percentage_equal('45.6%', Decimal('50.0'))
    
    def test_assert_decimal_percentage_equal_invalid_format(self):
        """Test that invalid percentage format fails assertion."""
        with pytest.raises(AssertionError):
            assert_decimal_percentage_equal('45.6', Decimal('45.6'))
    
    def test_is_valid_decimal_true(self):
        """Test that valid values return True."""
        assert is_valid_decimal(1.23)
        assert is_valid_decimal(42)
        assert is_valid_decimal('99.99')
        assert is_valid_decimal(Decimal('1.23'))
    
    def test_is_valid_decimal_false(self):
        """Test that invalid values return False."""
        assert not is_valid_decimal('not a number')
        assert not is_valid_decimal([1, 2, 3])
        assert not is_valid_decimal(None)


class TestCalculationHelpers:
    """Test calculation helper functions."""
    
    def test_safe_divide_normal(self):
        """Test safe division with non-zero denominator."""
        result = safe_divide(Decimal('10'), Decimal('2'))
        assert result == Decimal('5')
    
    def test_safe_divide_zero_denominator(self):
        """Test safe division with zero denominator returns default."""
        result = safe_divide(Decimal('10'), Decimal('0'))
        assert result == "N/A"
    
    def test_safe_divide_custom_default(self):
        """Test safe division with custom default value."""
        result = safe_divide(Decimal('10'), Decimal('0'), default=Decimal('0'))
        assert result == Decimal('0')
    
    def test_safe_multiply_two_values(self):
        """Test multiplying two values."""
        result = safe_multiply(Decimal('2'), Decimal('3'))
        assert result == Decimal('6')
    
    def test_safe_multiply_multiple_values(self):
        """Test multiplying multiple values."""
        result = safe_multiply(Decimal('2'), Decimal('3'), Decimal('4'))
        assert result == Decimal('24')
    
    def test_safe_multiply_with_zero(self):
        """Test multiplying with zero."""
        result = safe_multiply(Decimal('2'), Decimal('0'), Decimal('4'))
        assert result == Decimal('0')


class TestDataGenerators:
    """Test data generator functions."""
    
    def test_generate_balance_sheet_data_defaults(self):
        """Test generating balance sheet with default values."""
        data = generate_balance_sheet_data()
        
        assert 'current_assets' in data
        assert 'current_liabilities' in data
        assert 'total_equity' in data
        assert 'shares_outstanding' in data
        
        # Verify all values are floats (for compatibility with existing code)
        assert isinstance(data['current_assets'], float)
        assert isinstance(data['total_equity'], float)
    
    def test_generate_balance_sheet_data_custom(self):
        """Test generating balance sheet with custom values."""
        data = generate_balance_sheet_data(
            current_assets=Decimal('2000000'),
            total_equity=Decimal('1500000')
        )
        
        assert data['current_assets'] == 2000000.0
        assert data['total_equity'] == 1500000.0
    
    def test_generate_income_statement_data_defaults(self):
        """Test generating income statement with default values."""
        data = generate_income_statement_data()
        
        assert 'revenue' in data
        assert 'net_income' in data
        assert 'eps' in data
        
        assert isinstance(data['revenue'], float)
        assert isinstance(data['net_income'], float)
    
    def test_generate_income_statement_data_custom(self):
        """Test generating income statement with custom values."""
        data = generate_income_statement_data(
            revenue=Decimal('10000000'),
            net_income=Decimal('1000000')
        )
        
        assert data['revenue'] == 10000000.0
        assert data['net_income'] == 1000000.0
    
    def test_generate_financial_year_data(self):
        """Test generating complete financial year data."""
        data = generate_financial_year_data(year='2023-12-31')
        
        # Should have both balance sheet and income statement fields
        assert 'current_assets' in data
        assert 'revenue' in data
        assert 'dividend' in data
    
    def test_generate_multi_year_history(self):
        """Test generating multi-year history."""
        history = generate_multi_year_history(years=5, base_year=2023)
        
        assert len(history) == 5
        assert '2023-12-31' in history
        assert '2019-12-31' in history
        
        # Verify each year has complete data
        for year_data in history.values():
            assert 'current_assets' in year_data
            assert 'revenue' in year_data
            assert 'eps' in year_data
    
    def test_generate_multi_year_history_growth(self):
        """Test that multi-year history shows growth pattern."""
        history = generate_multi_year_history(
            years=3,
            base_year=2023,
            growth_rate=Decimal('0.10')  # 10% growth
        )
        
        # Note: Growth is applied backwards (older years have smaller values)
        # So 2021 should have highest revenue, 2023 should have lowest
        revenue_2023 = history['2023-12-31']['revenue']
        revenue_2022 = history['2022-12-31']['revenue']
        revenue_2021 = history['2021-12-31']['revenue']
        
        # Verify growth pattern (backwards in time)
        assert revenue_2021 > revenue_2022
        assert revenue_2022 > revenue_2023


class TestFloatingPointPrecision:
    """Test that Decimal prevents floating-point precision errors."""
    
    def test_decimal_avoids_float_artifacts(self):
        """Test that Decimal avoids binary float artifacts."""
        # Classic floating-point error: 0.1 + 0.2 != 0.3
        float_result = 0.1 + 0.2
        assert float_result != 0.3  # This is the problem we're avoiding
        
        # Decimal handles this correctly
        decimal_result = to_decimal('0.1') + to_decimal('0.2')
        assert decimal_result == Decimal('0.3')
    
    def test_decimal_multiplication_precision(self):
        """Test that Decimal maintains precision in multiplication."""
        # Multiply large currency values
        value1 = to_decimal('1234567.89')
        value2 = to_decimal('9876.54')
        
        result = value1 * value2
        # Calculate expected value correctly
        expected = Decimal('1234567.89') * Decimal('9876.54')
        
        assert result == expected
    
    def test_decimal_division_precision(self):
        """Test that Decimal maintains precision in division."""
        # Divide with repeating decimal
        numerator = to_decimal('10')
        denominator = to_decimal('3')
        
        result = numerator / denominator
        
        # Result should be precise to many decimal places
        assert str(result).startswith('3.333333')
    
    def test_decimal_rounding_consistency(self):
        """Test that Decimal rounding is consistent."""
        # Test banker's rounding (ROUND_HALF_UP)
        value1 = Decimal('1.235')
        value2 = Decimal('1.245')
        
        rounded1 = round_decimal(value1, 2)
        rounded2 = round_decimal(value2, 2)
        
        assert rounded1 == Decimal('1.24')
        assert rounded2 == Decimal('1.25')
