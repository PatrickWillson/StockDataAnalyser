"""
Property-based tests for formatting helper functions.

Tests verify that formatting functions behave correctly across a wide range
of inputs using Hypothesis property-based testing.
"""

import pytest
from hypothesis import given, strategies as st

from output.sections.financial_history import FinancialHistorySection


class TestFormatDebt:
    """Property-based tests for format_debt()."""
    
    @given(value=st.floats(min_value=0, max_value=1e15, allow_nan=False, allow_infinity=False))
    def test_format_debt_non_negative(self, value):
        """Test that format_debt handles non-negative values correctly."""
        result = FinancialHistorySection.format_debt(value, "USD")
        
        # Should always return a string
        assert isinstance(result, str)
        
        # Should contain B or M suffix (unless N/A)
        if value > 0:
            assert "B" in result or "M" in result
    
    def test_format_debt_zero(self):
        """Test that zero debt returns N/A."""
        result = FinancialHistorySection.format_debt(0, "USD")
        assert result == "N/A"
    
    @given(value=st.floats(min_value=1_000_000_000, max_value=1e15, allow_nan=False, allow_infinity=False))
    def test_format_debt_billions(self, value):
        """Test that values >= 1B are formatted with 'B' suffix."""
        result = FinancialHistorySection.format_debt(value, "USD")
        assert "B" in result
        assert "M" not in result
    
    @given(value=st.floats(min_value=1_000_000, max_value=999_999_999, allow_nan=False, allow_infinity=False))
    def test_format_debt_millions(self, value):
        """Test that values < 1B are formatted with 'M' suffix."""
        result = FinancialHistorySection.format_debt(value, "USD")
        assert "M" in result
        assert "B" not in result
    
    def test_format_debt_specific_values(self):
        """Test specific known values."""
        assert FinancialHistorySection.format_debt(42_688_000_000, "USD") == "42.69B"
        assert FinancialHistorySection.format_debt(500_000_000, "USD") == "500.00M"
        assert FinancialHistorySection.format_debt(1_500_000_000, "GBP") == "1.50B"


class TestFormatShares:
    """Property-based tests for format_shares()."""
    
    @given(value=st.floats(min_value=0, max_value=1e15, allow_nan=False, allow_infinity=False))
    def test_format_shares_non_negative(self, value):
        """Test that format_shares handles non-negative values correctly."""
        result = FinancialHistorySection.format_shares(value)
        
        # Should always return a string
        assert isinstance(result, str)
    
    def test_format_shares_zero(self):
        """Test that zero shares returns N/A."""
        result = FinancialHistorySection.format_shares(0)
        assert result == "N/A"
    
    @given(value=st.floats(min_value=1_000_000_000, max_value=1e15, allow_nan=False, allow_infinity=False))
    def test_format_shares_billions(self, value):
        """Test that values >= 1B are formatted with 'B' suffix."""
        result = FinancialHistorySection.format_shares(value)
        assert "B" in result
        assert "M" not in result
    
    @given(value=st.floats(min_value=1_000_000, max_value=999_999_999, allow_nan=False, allow_infinity=False))
    def test_format_shares_millions(self, value):
        """Test that values < 1B are formatted with 'M' suffix."""
        result = FinancialHistorySection.format_shares(value)
        assert "M" in result
        assert "B" not in result
    
    def test_format_shares_specific_values(self):
        """Test specific known values."""
        assert FinancialHistorySection.format_shares(7_469_000_000) == "7.469B"
        assert FinancialHistorySection.format_shares(500_000_000) == "500.00M"
        assert FinancialHistorySection.format_shares(8_254_000_000) == "8.254B"
    
    def test_format_shares_precision(self):
        """Test that billions show 3 decimal places, millions show 2."""
        # Billions: 3 decimal places
        result_b = FinancialHistorySection.format_shares(7_469_123_456)
        assert ".469B" in result_b
        
        # Millions: 2 decimal places
        result_m = FinancialHistorySection.format_shares(500_123_456)
        assert ".12M" in result_m


class TestFormatPrice:
    """Property-based tests for format_price()."""
    
    @given(value=st.floats(min_value=0.01, max_value=1e6, allow_nan=False, allow_infinity=False))
    def test_format_price_positive(self, value):
        """Test that format_price handles positive values correctly."""
        result = FinancialHistorySection.format_price(value, "USD")
        
        # Should always return a string
        assert isinstance(result, str)
        
        # Should have 2 decimal places
        assert "." in result
    
    def test_format_price_none(self):
        """Test that None price returns N/A."""
        result = FinancialHistorySection.format_price(None, "USD")
        assert result == "N/A"
    
    def test_format_price_specific_values(self):
        """Test specific known values."""
        assert FinancialHistorySection.format_price(450.12, "USD") == "450.12"
        assert FinancialHistorySection.format_price(16.50, "GBP") == "16.50"
        assert FinancialHistorySection.format_price(100.00, "EUR") == "100.00"
    
    def test_format_price_rounding(self):
        """Test that prices are rounded to 2 decimal places."""
        result = FinancialHistorySection.format_price(450.126, "USD")
        assert result == "450.13"  # Rounded up
        
        result = FinancialHistorySection.format_price(450.124, "USD")
        assert result == "450.12"  # Rounded down


class TestCalculateHistoricalPE:
    """Property-based tests for calculate_historical_pe()."""
    
    @given(
        price=st.floats(min_value=0.01, max_value=10000, allow_nan=False, allow_infinity=False),
        eps=st.floats(min_value=0.01, max_value=1000, allow_nan=False, allow_infinity=False)
    )
    def test_calculate_pe_positive_values(self, price, eps):
        """Test P/E calculation with positive price and EPS."""
        result = FinancialHistorySection.calculate_historical_pe(price, eps)
        
        # Should return a string
        assert isinstance(result, str)
        
        # Should not be N/A or Negative for positive values
        assert result != "N/A"
        assert result != "Negative"
        
        # Should be a valid number
        pe_value = float(result)
        
        # Should match manual calculation (within rounding tolerance)
        expected = price / eps
        assert abs(pe_value - expected) < 0.1  # Allow 0.1 difference for rounding
    
    @given(
        price=st.floats(min_value=0.01, max_value=10000, allow_nan=False, allow_infinity=False),
        eps=st.floats(min_value=-1000, max_value=-0.01, allow_nan=False, allow_infinity=False)
    )
    def test_calculate_pe_negative_eps(self, price, eps):
        """Test that negative EPS returns 'Negative' (Graham's method)."""
        result = FinancialHistorySection.calculate_historical_pe(price, eps)
        assert result == "Negative"
    
    def test_calculate_pe_zero_eps(self):
        """Test that zero EPS returns N/A."""
        result = FinancialHistorySection.calculate_historical_pe(100.0, 0.0)
        assert result == "N/A"
    
    def test_calculate_pe_none_price(self):
        """Test that None price returns N/A."""
        result = FinancialHistorySection.calculate_historical_pe(None, 10.0)
        assert result == "N/A"
    
    def test_calculate_pe_none_eps(self):
        """Test that None EPS returns N/A."""
        result = FinancialHistorySection.calculate_historical_pe(100.0, None)
        assert result == "N/A"
    
    def test_calculate_pe_specific_values(self):
        """Test specific known values."""
        # MSFT 2025: Price 495.67, EPS 13.64 → P/E 36.3
        result = FinancialHistorySection.calculate_historical_pe(495.67, 13.639432092151084)
        assert result == "36.3"
        
        # Loss year
        result = FinancialHistorySection.calculate_historical_pe(100.0, -5.0)
        assert result == "Negative"
    
    def test_calculate_pe_formatting(self):
        """Test that P/E is formatted to 1 decimal place."""
        result = FinancialHistorySection.calculate_historical_pe(100.0, 3.0)
        assert result == "33.3"
        
        result = FinancialHistorySection.calculate_historical_pe(100.0, 2.5)
        assert result == "40.0"


class TestCalculateHistoricalPB:
    """Property-based tests for calculate_historical_pb()."""
    
    @given(
        price=st.floats(min_value=0.01, max_value=10000, allow_nan=False, allow_infinity=False),
        bvps=st.floats(min_value=0.01, max_value=1000, allow_nan=False, allow_infinity=False)
    )
    def test_calculate_pb_positive_values(self, price, bvps):
        """Test P/B calculation with positive price and BVPS."""
        result = FinancialHistorySection.calculate_historical_pb(price, bvps)
        
        # Should return a string
        assert isinstance(result, str)
        
        # Should not be N/A for positive values
        assert result != "N/A"
        
        # Should be a valid number
        pb_value = float(result)
        
        # Should match manual calculation (within rounding tolerance)
        expected = price / bvps
        assert abs(pb_value - expected) < 0.1  # Allow 0.1 difference for rounding
    
    @given(
        price=st.floats(min_value=0.01, max_value=10000, allow_nan=False, allow_infinity=False),
        bvps=st.floats(min_value=-1000, max_value=0, allow_nan=False, allow_infinity=False)
    )
    def test_calculate_pb_negative_or_zero_bvps(self, price, bvps):
        """Test that negative or zero BVPS returns N/A."""
        result = FinancialHistorySection.calculate_historical_pb(price, bvps)
        assert result == "N/A"
    
    def test_calculate_pb_none_price(self):
        """Test that None price returns N/A."""
        result = FinancialHistorySection.calculate_historical_pb(None, 10.0)
        assert result == "N/A"
    
    def test_calculate_pb_none_bvps(self):
        """Test that None BVPS returns N/A."""
        result = FinancialHistorySection.calculate_historical_pb(100.0, None)
        assert result == "N/A"
    
    def test_calculate_pb_specific_values(self):
        """Test specific known values."""
        # MSFT 2025: Price 495.67, BVPS 46.01 → P/B 10.8
        result = FinancialHistorySection.calculate_historical_pb(495.67, 46.01)
        assert result == "10.8"
        
        # Negative book value
        result = FinancialHistorySection.calculate_historical_pb(100.0, -5.0)
        assert result == "N/A"
    
    def test_calculate_pb_formatting(self):
        """Test that P/B is formatted to 1 decimal place."""
        result = FinancialHistorySection.calculate_historical_pb(100.0, 10.0)
        assert result == "10.0"
        
        result = FinancialHistorySection.calculate_historical_pb(100.0, 7.5)
        assert result == "13.3"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_very_small_values(self):
        """Test formatting with very small values."""
        # Small debt (< 1M)
        result = FinancialHistorySection.format_debt(500_000, "USD")
        assert result == "0.50M"
        
        # Small shares (< 1M)
        result = FinancialHistorySection.format_shares(500_000)
        assert result == "0.50M"
    
    def test_very_large_values(self):
        """Test formatting with very large values."""
        # Large debt (trillions)
        result = FinancialHistorySection.format_debt(5_000_000_000_000, "USD")
        assert result == "5000.00B"
        
        # Large shares (hundreds of billions)
        result = FinancialHistorySection.format_shares(500_000_000_000)
        assert result == "500.000B"
    
    def test_extreme_pe_ratios(self):
        """Test P/E calculation with extreme ratios."""
        # Very high P/E (growth stock)
        result = FinancialHistorySection.calculate_historical_pe(1000.0, 0.1)
        assert result == "10000.0"
        
        # Very low P/E (value stock)
        result = FinancialHistorySection.calculate_historical_pe(10.0, 5.0)
        assert result == "2.0"
    
    def test_extreme_pb_ratios(self):
        """Test P/B calculation with extreme ratios."""
        # Very high P/B
        result = FinancialHistorySection.calculate_historical_pb(1000.0, 1.0)
        assert result == "1000.0"
        
        # Very low P/B (deep value)
        result = FinancialHistorySection.calculate_historical_pb(10.0, 50.0)
        assert result == "0.2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
