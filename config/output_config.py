"""
Output Formatting Configuration.

This module defines configuration settings for formatting output in dossiers,
including decimal precision, currency display, percentage formatting, and
date formatting.

The configuration is immutable (frozen dataclass) to ensure consistent
formatting across all generated dossiers.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class OutputConfig:
    """
    Configuration for output formatting in dossiers.
    
    This dataclass encapsulates all formatting preferences used when
    generating markdown dossiers, ensuring consistent presentation of
    financial data across all analyses.
    
    Attributes:
        decimal_places: Number of decimal places for general numeric values (2)
        currency_format: Format string for currency values with thousands separator
                        Example: "{value:,.2f}" produces "1,234.56"
        percentage_format: Format string for percentage values
                          Example: "{value:.2f}%" produces "12.34%"
        date_format: strftime format string for date display
                    Example: "%Y-%m-%d" produces "2024-01-15"
    """
    decimal_places: int = 2
    currency_format: str = "{value:,.2f}"
    percentage_format: str = "{value:.2f}%"
    date_format: str = "%Y-%m-%d"
