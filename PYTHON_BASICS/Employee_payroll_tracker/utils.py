"""utils.py — Shared formatting helpers for consistent CLI output across all modules."""


def format_currency(amount: float, symbol: str = "$") -> str:
    """Return a currency string with thousands separator, e.g. '$1,234.56'."""
    return f"{symbol}{amount:,.2f}"


def divider(width: int = 40, char: str = "-") -> str:
    """Return a horizontal line of `width` repeated `char` characters."""
    if width < 1:
        raise ValueError(f"width must be >= 1, got {width}.")
    return char * width


def format_header(title: str, width: int = 40) -> str:
    """Return a three-line centred header wrapped in '=' divider lines."""
    border = divider(width, "=")
    return f"{border}\n{title.center(width)}\n{border}"
