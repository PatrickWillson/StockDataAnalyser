"""
Unit tests for configuration module.

Tests verify:
- Configuration immutability (frozen dataclasses)
- Configuration value access
- Constants cannot be modified
"""

import pytest
from dataclasses import FrozenInstanceError

from config.graham_constants import GRAHAM_MULTIPLIER, COST_OF_CAPITAL
from config.investor_thresholds import (
    DefensiveThresholds,
    EnterprisingThresholds,
    DEFENSIVE,
    ENTERPRISING
)
from config.api_config import APIConfig, EODHD_CONFIG, FX_CONFIG
from config.output_config import OutputConfig


class TestGrahamConstants:
    """Test Graham methodology constants."""
    
    def test_graham_multiplier_value(self):
        """Test GRAHAM_MULTIPLIER has correct value."""
        assert GRAHAM_MULTIPLIER == 22.5
    
    def test_cost_of_capital_value(self):
        """Test COST_OF_CAPITAL has correct value."""
        assert COST_OF_CAPITAL == 0.10
    
    def test_constants_are_immutable(self):
        """Test that constants cannot be reassigned (Python Final hint)."""
        # Note: Python's Final is a type hint only, not enforced at runtime
        # This test documents the intent that these should not be modified
        assert isinstance(GRAHAM_MULTIPLIER, float)
        assert isinstance(COST_OF_CAPITAL, float)


class TestDefensiveThresholds:
    """Test Defensive Investor thresholds."""
    
    def test_default_values(self):
        """Test DefensiveThresholds has correct default values."""
        thresholds = DefensiveThresholds()
        assert thresholds.MIN_CURRENT_RATIO == 2.0
        assert thresholds.MIN_EARNINGS_YEARS == 10  # Strict Graham: ALL 10 years
        assert thresholds.MAX_PE_RATIO == 15.0
        assert thresholds.MAX_PB_RATIO == 1.5
        assert thresholds.MIN_EARNINGS_GROWTH == 1.33
    
    def test_immutability(self):
        """Test DefensiveThresholds is frozen and cannot be modified."""
        thresholds = DefensiveThresholds()
        with pytest.raises(FrozenInstanceError):
            thresholds.MIN_CURRENT_RATIO = 3.0
    
    def test_singleton_instance(self):
        """Test DEFENSIVE singleton has correct values."""
        assert DEFENSIVE.MIN_CURRENT_RATIO == 2.0
        assert DEFENSIVE.MIN_EARNINGS_YEARS == 10  # Strict Graham: ALL 10 years
        assert DEFENSIVE.MAX_PE_RATIO == 15.0
        assert DEFENSIVE.MAX_PB_RATIO == 1.5
        assert DEFENSIVE.MIN_EARNINGS_GROWTH == 1.33
    
    def test_singleton_immutability(self):
        """Test DEFENSIVE singleton cannot be modified."""
        with pytest.raises(FrozenInstanceError):
            DEFENSIVE.MIN_CURRENT_RATIO = 3.0


class TestEnterprisingThresholds:
    """Test Enterprising Investor thresholds."""
    
    def test_default_values(self):
        """Test EnterprisingThresholds has correct default values."""
        thresholds = EnterprisingThresholds()
        assert thresholds.MIN_CURRENT_RATIO == 1.5
        assert thresholds.MAX_DEBT_ASSETS == 1.10
        assert thresholds.MIN_EARNINGS_YEARS == 5
        assert thresholds.MAX_PE_RATIO == 10.0
        assert thresholds.MAX_PB_RATIO == 1.2
    
    def test_immutability(self):
        """Test EnterprisingThresholds is frozen and cannot be modified."""
        thresholds = EnterprisingThresholds()
        with pytest.raises(FrozenInstanceError):
            thresholds.MIN_CURRENT_RATIO = 2.0
    
    def test_singleton_instance(self):
        """Test ENTERPRISING singleton has correct values."""
        assert ENTERPRISING.MIN_CURRENT_RATIO == 1.5
        assert ENTERPRISING.MAX_DEBT_ASSETS == 1.10
        assert ENTERPRISING.MIN_EARNINGS_YEARS == 5
        assert ENTERPRISING.MAX_PE_RATIO == 10.0
        assert ENTERPRISING.MAX_PB_RATIO == 1.2
    
    def test_singleton_immutability(self):
        """Test ENTERPRISING singleton cannot be modified."""
        with pytest.raises(FrozenInstanceError):
            ENTERPRISING.MIN_CURRENT_RATIO = 2.0


class TestAPIConfig:
    """Test API configuration."""
    
    def test_default_values(self):
        """Test APIConfig has correct default values."""
        config = APIConfig()
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.backoff_factor == 1.0
    
    def test_custom_values(self):
        """Test APIConfig accepts custom values."""
        config = APIConfig(timeout=60, max_retries=5, backoff_factor=2.0)
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.backoff_factor == 2.0
    
    def test_immutability(self):
        """Test APIConfig is frozen and cannot be modified."""
        config = APIConfig()
        with pytest.raises(FrozenInstanceError):
            config.timeout = 60
    
    def test_eodhd_config(self):
        """Test EODHD_CONFIG has correct values."""
        assert EODHD_CONFIG.timeout == 30
        assert EODHD_CONFIG.max_retries == 3
        assert EODHD_CONFIG.backoff_factor == 1.0
    
    def test_fx_config(self):
        """Test FX_CONFIG has correct values."""
        assert FX_CONFIG.timeout == 10
        assert FX_CONFIG.max_retries == 3
        assert FX_CONFIG.backoff_factor == 1.0
    
    def test_config_immutability(self):
        """Test predefined configs cannot be modified."""
        with pytest.raises(FrozenInstanceError):
            EODHD_CONFIG.timeout = 60
        with pytest.raises(FrozenInstanceError):
            FX_CONFIG.timeout = 20


class TestOutputConfig:
    """Test output formatting configuration."""
    
    def test_default_values(self):
        """Test OutputConfig has correct default values."""
        config = OutputConfig()
        assert config.decimal_places == 2
        assert config.currency_format == "{value:,.2f}"
        assert config.percentage_format == "{value:.2f}%"
        assert config.date_format == "%Y-%m-%d"
    
    def test_custom_values(self):
        """Test OutputConfig accepts custom values."""
        config = OutputConfig(
            decimal_places=3,
            currency_format="{value:,.3f}",
            percentage_format="{value:.1f}%",
            date_format="%d/%m/%Y"
        )
        assert config.decimal_places == 3
        assert config.currency_format == "{value:,.3f}"
        assert config.percentage_format == "{value:.1f}%"
        assert config.date_format == "%d/%m/%Y"
    
    def test_immutability(self):
        """Test OutputConfig is frozen and cannot be modified."""
        config = OutputConfig()
        with pytest.raises(FrozenInstanceError):
            config.decimal_places = 3


class TestConfigurationValueAccess:
    """Test that all configuration values are accessible."""
    
    def test_graham_constants_accessible(self):
        """Test Graham constants can be accessed."""
        assert GRAHAM_MULTIPLIER is not None
        assert COST_OF_CAPITAL is not None
    
    def test_threshold_values_accessible(self):
        """Test threshold values can be accessed."""
        assert DEFENSIVE.MIN_CURRENT_RATIO is not None
        assert ENTERPRISING.MIN_CURRENT_RATIO is not None
    
    def test_api_config_values_accessible(self):
        """Test API config values can be accessed."""
        assert EODHD_CONFIG.timeout is not None
        assert FX_CONFIG.timeout is not None
    
    def test_output_config_values_accessible(self):
        """Test output config values can be accessed."""
        config = OutputConfig()
        assert config.decimal_places is not None
        assert config.currency_format is not None
