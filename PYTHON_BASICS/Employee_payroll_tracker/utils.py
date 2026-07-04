"""
utils.py
Shared formatting helpers used across the payroll system.

Keeping these in one place ensures consistent output styling and makes
width or symbol changes a single-line edit.
"""


def format_currency(amount: float, symbol: str = "$") -> str:
    """
    Format a float as a currency string with thousands separator.

    Args:
        amount: Numeric value to format.
        symbol: Currency symbol prefix (default '$').

    Returns:
        Formatted string, e.g. '$1,234.56'.
    """
    return f"{symbol}{amount:,.2f}"


def divider(width: int = 40, char: str = "-") -> str:
    """
    Return a horizontal divider line of repeated characters.

    Args:
        width: Total character width (default 40).
        char:  Character to repeat (default '-').

    Returns:
        A string of `width` repeated `char` characters.
    """
    return char * width


def format_header(title: str, width: int = 40) -> str:
    """
    Return a centred section header wrapped in '=' divider lines.

    Args:
        title: Text to display in the header.
        width: Total width of the divider lines (default 40).

    Returns:
        Three-line string: top divider, centred title, bottom divider.
    """
    border = divider(width, "=")
    return f"{border}\n{title.center(width)}\n{border}"
