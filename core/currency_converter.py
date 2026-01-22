"""
Currency Converter

Handles all currency conversion operations with FX rate fetching and conversion history tracking.
Centralizes currency logic for maintainability and testability.
"""

import logging
from typing import List, Tuple, Optional, Dict
from clients.fx_client import FXClient

logger = logging.getLogger(__name__)


class CurrencyConverter:
    """Handles all currency conversion operations."""
    
    def __init__(self, fx_client: Optional[FXClient] = None):
        """
        Initialize currency converter with optional FX client.
        
        Args:
            fx_client: Optional FX client for fetching rates (creates one if not provided)
        """
        self.fx_client = fx_client or FXClient()
        self.conversion_history: List[str] = []
    
    def convert(self, amount: float, from_currency: str, 
                to_currency: str) -> Tuple[float, bool]:
        """
        Convert amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., 'EUR', 'GBP', 'USD')
            to_currency: Target currency code (e.g., 'USD', 'EUR', 'GBP')
            
        Returns:
            Tuple of (converted_amount, success)
            - converted_amount: Converted amount (or original if conversion fails)
            - success: True if conversion succeeded, False otherwise
            
        Example:
            >>> converter = CurrencyConverter()
            >>> amount, success = converter.convert(100.0, 'GBP', 'USD')
            >>> if success:
            ...     print(f"100 GBP = {amount:.2f} USD")
        """
        # Same currency - no conversion needed
        if from_currency == to_currency:
            return amount, True
        
        # Special handling for GBX ↔ GBP conversion
        # GBX (pence) is not a real currency, it's just GBP × 100
        if from_currency == "GBX" and to_currency == "GBP":
            converted_amount = amount / 100
            self.conversion_history.append("GBX → GBP (÷100)")
            logger.debug(f"Converted {amount:.2f} GBX to {converted_amount:.2f} GBP")
            return converted_amount, True
        elif from_currency == "GBP" and to_currency == "GBX":
            converted_amount = amount * 100
            self.conversion_history.append("GBP → GBX (×100)")
            logger.debug(f"Converted {amount:.2f} GBP to {converted_amount:.2f} GBX")
            return converted_amount, True
        
        # Get FX rate
        fx_rate = self.fx_client.get_rate(from_currency, to_currency)
        
        if fx_rate:
            converted_amount = amount * fx_rate
            # Track conversion in history
            self.conversion_history.append(
                f"{from_currency} → {to_currency} at rate {fx_rate:.4f}"
            )
            logger.debug(f"Converted {amount:.2f} {from_currency} to {converted_amount:.2f} {to_currency} at rate {fx_rate:.4f}")
            return converted_amount, True
        else:
            # Conversion failed - return original amount
            self.conversion_history.append(
                f"Failed to convert {from_currency} → {to_currency} (rate unavailable)"
            )
            logger.warning(f"Could not get FX rate for {from_currency}/{to_currency}")
            return amount, False
    
    def apply_london_fix(self, price: float, eps: float, 
                        exchange: str) -> Tuple[float, bool]:
        """
        Apply London Fix for LSE stocks (GBp → GBP).
        
        The London Stock Exchange quotes prices in pence (GBp) but financial
        statements are in pounds (GBP). When P/E ratio exceeds 500, it indicates
        a currency mismatch that needs correction.
        
        Args:
            price: Current stock price
            eps: Earnings per share
            exchange: Stock exchange code
            
        Returns:
            Tuple of (adjusted_price, fix_applied)
            - adjusted_price: Price after London Fix (or original if not needed)
            - fix_applied: True if London Fix was applied, False otherwise
            
        Example:
            >>> converter = CurrencyConverter()
            >>> price, applied = converter.apply_london_fix(1500.0, 2.5, 'LSE')
            >>> if applied:
            ...     print(f"London Fix applied: {price:.2f} GBP")
        """
        if exchange == "LSE" and eps > 0 and price > 0:
            pe_ratio = price / eps
            if pe_ratio > 500:
                # Price is in pence, convert to pounds
                adjusted_price = price / 100
                self.conversion_history.append("London Fix applied (GBp → GBP)")
                logger.info(f"London Fix applied: {price:.2f} GBp → {adjusted_price:.2f} GBP")
                return adjusted_price, True
        
        return price, False
    
    def convert_batch(self, amounts: Dict[str, float], 
                     from_currency: str, to_currency: str) -> Dict[str, float]:
        """
        Convert multiple amounts (e.g., historical dividends).
        
        Args:
            amounts: Dictionary with keys (e.g., years) and amounts to convert
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Dictionary with same keys and converted amounts
            
        Example:
            >>> converter = CurrencyConverter()
            >>> dividends = {'2020': 1.5, '2021': 1.6, '2022': 1.7}
            >>> converted = converter.convert_batch(dividends, 'GBP', 'USD')
        """
        # Same currency - no conversion needed
        if from_currency == to_currency:
            return amounts.copy()
        
        # Get FX rate once for all conversions
        fx_rate = self.fx_client.get_rate(from_currency, to_currency)
        
        if fx_rate:
            converted = {key: value * fx_rate for key, value in amounts.items()}
            self.conversion_history.append(
                f"Batch conversion: {len(amounts)} values from {from_currency} → {to_currency} at rate {fx_rate:.4f}"
            )
            logger.info(f"Batch converted {len(amounts)} values from {from_currency} to {to_currency} at rate {fx_rate:.4f}")
            return converted
        else:
            # Conversion failed - return original amounts
            self.conversion_history.append(
                f"Failed batch conversion: {from_currency} → {to_currency} (rate unavailable)"
            )
            logger.warning(f"Could not get FX rate for batch conversion {from_currency}/{to_currency}")
            return amounts.copy()
    
    def get_consolidated_warning(self) -> str:
        """
        Get consolidated warning message for all conversions.
        
        Returns:
            Consolidated warning string, or empty string if no conversions
            
        Example:
            >>> converter = CurrencyConverter()
            >>> converter.convert(100.0, 'GBP', 'USD')
            >>> warning = converter.get_consolidated_warning()
            >>> print(warning)
            Currency Conversions: GBP → USD at rate 1.3399
        """
        if not self.conversion_history:
            return ""
        
        return "Currency Conversions: " + "; ".join(self.conversion_history)
    
    def clear_history(self):
        """Clear conversion history. Useful for starting fresh analysis."""
        self.conversion_history.clear()
