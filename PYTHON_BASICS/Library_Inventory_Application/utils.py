"""
utils.py
Shared formatting helpers for consistent CLI output across all modules.

Centralising these functions means any styling change (width, separator
character, alignment) is a single-line edit in one place.
"""


def divider(width: int = 50, char: str = "-") -> str:
    """Return a horizontal line of repeated characters.

    Args:
        width: Total number of characters. Defaults to 50.
        char:  Character to repeat. Defaults to '-'.

    Returns:
        A string of `width` repeated `char` characters.
    """
    return char * width


def format_header(title: str, width: int = 50) -> str:
    """Return a three-line centred section header.

    Args:
        title: Text to display in the centre line.
        width: Total width of the border lines. Defaults to 50.

    Returns:
        Three-line string: '=' border, centred title, '=' border.
    """
    border = divider(width, "=")
    return f"{border}\n{title.center(width)}\n{border}"


def format_row(label: str, value: str, label_width: int = 14) -> str:
    """Return a single aligned label-value row for detail blocks.

    Args:
        label:       Field name (e.g. 'Title').
        value:       Field value (e.g. 'Clean Code').
        label_width: Column width reserved for the label. Defaults to 14.

    Returns:
        Formatted string, e.g. '  Title         : Clean Code'.
    """
    return f"  {label:<{label_width}}: {value}"
