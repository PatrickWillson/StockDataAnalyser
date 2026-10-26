"""
Unit tests for CurrencyConverter class.

Tests single conversions, London Fix, batch conversions, and warning generation.
"""

import pytest
from core.currency_converter import CurrencyConverter


class MockFXClient:
    """Mock FX client for testing without live API calls."""
    
    def __init__(self, rates=None):
        """
        Initialize mock FX client with predefined rates.
        
        Args:
            rates: Dictionary of (from_currency, to_currency) -> rate
        """
        self.rates = rates or {}
        self._cache = {}
    
    def get_rate(self, from_currency: str, to_currency: str):
        """Get mock FX rate."""
        if from_currency == to_currency:
            return 1.0
        
        key = (from_currency, to_currency)
        return self.rates.get(key)
    
    def clear_cache(self):
        """Clear cache (for compatibility)."""
        self._cache.clear()


def test_convert_same_currency():
    """Test that converting to same currency returns original amount."""
    converter = CurrencyConverter()
    amount, success = converter.convert(100.0, 'USD', 'USD')
    
    assert amount == 100.0
    assert success is True


def test_convert_different_currency_success():
    """Test successful currency conversion."""
    mock_fx = MockFXClient(rates={('GBP', 'USD'): 1.3})
    converter = CurrencyConverter(fx_client=mock_fx)
    
    amount, success = converter.convert(100.0, 'GBP', 'USD')
    
    assert amount == 130.0
    assert success is True


def test_convert_different_currency_failure():
    """Test currency conversion when FX rate unavailable."""
    mock_fx = MockFXClient(rates={})  # No rates available
    converter = CurrencyConverter(fx_client=mock_fx)
    
    amount, success = converter.convert(100.0, 'GBP', 'USD')
    
    assert amount == 100.0  # Returns original amount
    assert success is False


def test_conversion_history_tracking():
    """Test that conversion history is tracked correctly."""
    mock_fx = MockFXClient(rates={('GBP', 'USD'): 1.3})
    converter = CurrencyConverter(fx_client=mock_fx)
    
    converter.convert(100.0, 'GBP', 'USD')
    
    assert len(converter.conversion_history) == 1
    assert 'GBP → USD at rate 1.3000' in converter.conversion_history[0]


def test_conversion_history_tracking_failure():
    """Test that failed conversions are tracked in history."""
    mock_fx = MockFXClient(rates={})
    converter = CurrencyConverter(fx_client=mock_fx)
    
    converter.convert(100.0, 'GBP', 'USD')
    
    assert len(converter.conversion_history) == 1
    assert 'Failed to convert' in converter.conversion_history[0]


def test_apply_london_fix_needed():
    """Test London Fix application when P/E > 500."""
    converter = CurrencyConverter()
    
    # Price in pence, EPS in pounds -> P/E = 1500 / 2.5 = 600
    price, applied = converter.apply_london_fix(1500.0, 2.5, 'LSE')
    
    assert price == 15.0  # 1500 / 100
    assert applied is True
    assert len(converter.conversion_history) == 1
    assert 'London Fix applied' in converter.conversion_history[0]


def test_apply_london_fix_not_needed():
    """Test London Fix not applied when P/E < 500."""
    converter = CurrencyConverter()
    
    # Price in pounds, EPS in pounds -> P/E = 15.0 / 2.5 = 6
    price, applied = converter.apply_london_fix(15.0, 2.5, 'LSE')
    
    assert price == 15.0  # Unchanged
    assert applied is False
    assert len(converter.conversion_history) == 0


def test_apply_london_fix_non_lse_exchange():
    """Test London Fix not applied for non-LSE exchanges."""
    converter = CurrencyConverter()
    
    # High P/E but not LSE
    price, applied = converter.apply_london_fix(1500.0, 2.5, 'NYSE')
    
    assert price == 1500.0  # Unchanged
    assert applied is False


def test_apply_london_fix_zero_eps():
    """Test London Fix not applied when EPS is zero."""
    converter = CurrencyConverter()
    
    price, applied = converter.apply_london_fix(1500.0, 0.0, 'LSE')
    
    assert price == 1500.0  # Unchanged
    assert applied is False


def test_convert_batch_same_currency():
    """Test batch conversion with same currency."""
    converter = CurrencyConverter()
    amounts = {'2020': 1.5, '2021': 1.6, '2022': 1.7}
    
    converted = converter.convert_batch(amounts, 'USD', 'USD')
    
    assert converted == amounts
    assert len(converter.conversion_history) == 0


def test_convert_batch_different_currency_success():
    """Test successful batch conversion."""
    mock_fx = MockFXClient(rates={('GBP', 'USD'): 1.3})
    converter = CurrencyConverter(fx_client=mock_fx)
    amounts = {'2020': 1.5, '2021': 1.6, '2022': 1.7}
    
    converted = converter.convert_batch(amounts, 'GBP', 'USD')
    
    assert converted['2020'] == pytest.approx(1.95)
    assert converted['2021'] == pytest.approx(2.08)
    assert converted['2022'] == pytest.approx(2.21)
    assert len(converter.conversion_history) == 1
    assert 'Batch conversion' in converter.conversion_history[0]


def test_convert_batch_different_currency_failure():
    """Test batch conversion when FX rate unavailable."""
    mock_fx = MockFXClient(rates={})
    converter = CurrencyConverter(fx_client=mock_fx)
    amounts = {'2020': 1.5, '2021': 1.6, '2022': 1.7}
    
    converted = converter.convert_batch(amounts, 'GBP', 'USD')
    
    assert converted == amounts  # Returns original amounts
    assert len(converter.conversion_history) == 1
    assert 'Failed batch conversion' in converter.conversion_history[0]


def test_get_consolidated_warning_empty():
    """Test consolidated warning when no conversions performed."""
    converter = CurrencyConverter()
    
    warning = converter.get_consolidated_warning()
    
    assert warning == ""


def test_get_consolidated_warning_single_conversion():
    """Test consolidated warning with single conversion."""
    mock_fx = MockFXClient(rates={('GBP', 'USD'): 1.3})
    converter = CurrencyConverter(fx_client=mock_fx)
    
    converter.convert(100.0, 'GBP', 'USD')
    warning = converter.get_consolidated_warning()
    
    assert warning.startswith("Currency Conversions:")
    assert 'GBP → USD' in warning


def test_get_consolidated_warning_multiple_conversions():
    """Test consolidated warning with multiple conversions."""
    mock_fx = MockFXClient(rates={
        ('GBP', 'USD'): 1.3,
        ('EUR', 'USD'): 1.1
    })
    converter = CurrencyConverter(fx_client=mock_fx)
    
    converter.convert(100.0, 'GBP', 'USD')
    converter.convert(50.0, 'EUR', 'USD')
    warning = converter.get_consolidated_warning()
    
    assert warning.startswith("Currency Conversions:")
    assert 'GBP → USD' in warning
    assert 'EUR → USD' in warning
    assert ';' in warning  # Multiple conversions separated by semicolon


def test_clear_history():
    """Test clearing conversion history."""
    mock_fx = MockFXClient(rates={('GBP', 'USD'): 1.3})
    converter = CurrencyConverter(fx_client=mock_fx)
    
    converter.convert(100.0, 'GBP', 'USD')
    assert len(converter.conversion_history) == 1
    
    converter.clear_history()
    assert len(converter.conversion_history) == 0
    assert converter.get_consolidated_warning() == ""


def test_multiple_conversions_accumulate():
    """Test that multiple conversions accumulate in history."""
    mock_fx = MockFXClient(rates={
        ('GBP', 'USD'): 1.3,
        ('EUR', 'USD'): 1.1,
        ('JPY', 'USD'): 0.0091
    })
    converter = CurrencyConverter(fx_client=mock_fx)
    
    converter.convert(100.0, 'GBP', 'USD')
    converter.convert(50.0, 'EUR', 'USD')
    converter.apply_london_fix(1500.0, 2.5, 'LSE')
    
    assert len(converter.conversion_history) == 3


def test_batch_conversion_preserves_keys():
    """Test that batch conversion preserves dictionary keys."""
    mock_fx = MockFXClient(rates={('GBP', 'USD'): 1.3})
    converter = CurrencyConverter(fx_client=mock_fx)
    amounts = {'2020-12-31': 1.5, '2021-12-31': 1.6, '2022-12-31': 1.7}
    
    converted = converter.convert_batch(amounts, 'GBP', 'USD')
    
    assert set(converted.keys()) == set(amounts.keys())


def test_convert_with_zero_amount():
    """Test conversion with zero amount."""
    mock_fx = MockFXClient(rates={('GBP', 'USD'): 1.3})
    converter = CurrencyConverter(fx_client=mock_fx)
    
    amount, success = converter.convert(0.0, 'GBP', 'USD')
    
    assert amount == 0.0
    assert success is True


def test_convert_with_negative_amount():
    """Test conversion with negative amount (e.g., dividends paid)."""
    mock_fx = MockFXClient(rates={('GBP', 'USD'): 1.3})
    converter = CurrencyConverter(fx_client=mock_fx)
    
    amount, success = converter.convert(-100.0, 'GBP', 'USD')
    
    assert amount == -130.0
    assert success is True


def test_convert_gbx_to_gbp():
    """Test GBX to GBP conversion (pence to pounds)."""
    converter = CurrencyConverter()
    
    amount, success = converter.convert(1650.0, 'GBX', 'GBP')
    
    assert amount == 16.50  # 1650 / 100
    assert success is True
    assert len(converter.conversion_history) == 1
    assert 'GBX → GBP (÷100)' in converter.conversion_history[0]


def test_convert_gbp_to_gbx():
    """Test GBP to GBX conversion (pounds to pence)."""
    converter = CurrencyConverter()
    
    amount, success = converter.convert(16.50, 'GBP', 'GBX')
    
    assert amount == 1650.0  # 16.50 * 100
    assert success is True
    assert len(converter.conversion_history) == 1
    assert 'GBP → GBX (×100)' in converter.conversion_history[0]


def test_convert_gbx_to_gbx():
    """Test GBX to GBX conversion (same currency)."""
    converter = CurrencyConverter()
    
    amount, success = converter.convert(1650.0, 'GBX', 'GBX')
    
    assert amount == 1650.0  # No conversion
    assert success is True
    assert len(converter.conversion_history) == 0  # No conversion needed

