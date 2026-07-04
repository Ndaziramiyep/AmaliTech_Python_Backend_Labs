"""
utils.py
Shared formatting helpers used across the payroll system.
"""


def format_currency(amount: float, symbol: str = "$") -> str:
    """Return a human-readable currency string, e.g. '$1,234.56'."""
    return f"{symbol}{amount:,.2f}"


def divider(width: int = 40, char: str = "-") -> str:
    """Return a horizontal divider line."""
    return char * width
