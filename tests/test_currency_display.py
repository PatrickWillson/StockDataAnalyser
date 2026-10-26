"""
Unit tests for currency display logic in dossier generation.

Tests Requirements 4.1, 4.2, 4.4:
- Trading currency displayed first
- Conversion shown when currencies differ
- Format consistency across all price displays
"""

from stock_data_analyser import format_price_display


def test_single_currency_format():
    """Test that single currency displays without conversion."""
    # Requirements 4.1
    result = format_price_display(1650.0, 'GBX', 'GBX')
    assert result == "1,650.00 GBX"
    
    result = format_price_display(150.50, 'USD', 'USD')
    assert result == "150.50 USD"


def test_dual_currency_format():
    """Test that dual currency shows trading currency first with conversion."""
    # Requirements 4.1, 4.2
    result = format_price_display(1650.0, 'GBX', 'GBP', converted_value=16.50)
    assert result == "1,650.00 GBX (16.50 GBP)"
    
    result = format_price_display(100.0, 'USD', 'GBP', converted_value=78.50)
    assert result == "100.00 USD (78.50 GBP)"


def test_trading_currency_always_first():
    """Test that trading currency is always displayed first."""
    # Requirements 4.1
    result = format_price_display(1650.0, 'GBX', 'GBP', converted_value=16.50)
    assert result.startswith("1,650.00 GBX")
    
    result = format_price_display(100.0, 'USD', 'EUR', converted_value=92.0)
    assert result.startswith("100.00 USD")


def test_format_consistency_across_displays():
    """Test that format is consistent for different price types."""
    # Requirements 4.4
    # Current price
    current = format_price_display(1650.0, 'GBX', 'GBP', converted_value=16.50)
    
    # 52-week high
    high = format_price_display(1800.0, 'GBX', 'GBP', converted_value=18.00)
    
    # 52-week low
    low = format_price_display(1400.0, 'GBX', 'GBP', converted_value=14.00)
    
    # All should follow same format pattern: "X.XX GBX (Y.YY GBP)"
    assert " GBX (" in current and " GBP)" in current
    assert " GBX (" in high and " GBP)" in high
    assert " GBX (" in low and " GBP)" in low


def test_per_share_metrics_format():
    """Test that per-share metrics use consistent currency notation."""
    # Requirements 4.4
    eps = format_price_display(2.50, 'GBX', 'GBP', converted_value=0.025)
    bvps = format_price_display(15.0, 'GBX', 'GBP', converted_value=0.15)
    
    # Both should use same format
    assert " GBX (" in eps
    assert " GBX (" in bvps


def test_large_numbers_with_commas():
    """Test that large numbers are formatted with commas."""
    result = format_price_display(123456.78, 'USD', 'USD')
    assert "123,456.78" in result


def test_small_numbers_precision():
    """Test that small numbers maintain precision."""
    result = format_price_display(0.025, 'GBP', 'GBP')
    assert "0.03" in result or "0.02" in result  # Rounded to 2 decimals


def test_zero_price_handling():
    """Test that zero prices are handled gracefully."""
    result = format_price_display(0.0, 'USD', 'USD')
    assert "0.00 USD" in result


def test_negative_price_handling():
    """Test that negative prices are handled (edge case)."""
    # Should not happen in practice, but test defensive coding
    result = format_price_display(-10.0, 'USD', 'USD')
    assert "-10.00 USD" in result
