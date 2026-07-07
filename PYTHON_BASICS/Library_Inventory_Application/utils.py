"""utils.py — Shared formatting helpers for consistent CLI output."""


def divider(width: int = 50, char: str = "-") -> str:
    """Return a horizontal line of `width` repeated `char` characters."""
    return char * width


def format_header(title: str, width: int = 50) -> str:
    """Return a three-line centred header: '=' border, title, '=' border."""
    border = divider(width, "=")
    return f"{border}\n{title.center(width)}\n{border}"


def format_row(label: str, value: str, label_width: int = 14) -> str:
    """Return an aligned '  Label : Value' row for detail blocks."""
    return f"  {label:<{label_width}}: {value}"
