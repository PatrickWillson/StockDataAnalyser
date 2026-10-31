"""
Shared formatting helpers for dossier output.

Formatting lives here, once; sections import from this module rather than
defining their own copies.
"""

from typing import Optional


def format_price_display(price: float, trading_currency: str, financials_currency: str,
                         converted_value: Optional[float] = None) -> str:
    """
    Format a money amount with its currency, trading currency first.

    - Same currency: "29.11 USD"
    - Currencies differ and a converted value is given: "1,650.00 GBX (16.50 GBP)"
    - Currencies differ, no converted value: "1,650.00 GBX"

    Args:
        price: Amount in the trading currency
        trading_currency: Currency the amount is expressed in
        financials_currency: Currency of the financial statements
        converted_value: Optional amount converted to the financials currency

    Returns:
        Formatted string (comma thousands separator, 2 decimal places)
    """
    formatted_price = f"{price:,.2f}"

    if trading_currency == financials_currency:
        return f"{formatted_price} {trading_currency}"

    if converted_value is not None:
        return f"{formatted_price} {trading_currency} ({converted_value:,.2f} {financials_currency})"

    return f"{formatted_price} {trading_currency}"
