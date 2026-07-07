"""book.py — LibraryItem ABC and its three concrete subclasses."""

from abc import ABC, abstractmethod
from utils import divider, format_row


class LibraryItem(ABC):
    """Abstract base for all library items.

    Subclasses must implement item_type(), summary(), format_details(),
    is_available, is_borrowable, do_borrow(), and do_return().
    """

    def __init__(self, isbn: str, title: str, author: str, year: int) -> None:
        self.isbn   = isbn
        self.title  = title
        self.author = author
        self.year   = year  # validated via setter

    @property
    def year(self) -> int:
        return self._year

    @year.setter
    def year(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"year must be a positive integer, got {value!r}")
        self._year = value

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """True when the item can be borrowed right now."""

    @property
    @abstractmethod
    def is_borrowable(self) -> bool:
        """True if this item type supports physical borrowing."""

    @abstractmethod
    def item_type(self) -> str:
        """Human-readable type label, e.g. 'Physical Book'."""

    @abstractmethod
    def summary(self) -> str:
        """One-line summary for list views."""

    @abstractmethod
    def format_details(self) -> str:
        """Multi-line detail block for full-record display."""

    @abstractmethod
    def do_borrow(self, member_name: str) -> None:
        """Apply borrow state; raise ValueError if not possible."""

    @abstractmethod
    def do_return(self) -> str:
        """Apply return state; return borrower name or raise ValueError."""

    def __str__(self) -> str:
        return f"{self.item_type()} | {self.isbn} — {self.title}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(isbn={self.isbn!r}, title={self.title!r})"


class PhysicalBook(LibraryItem):
    """Printed book with copy-count tracking; multiple copies can be borrowed at once."""

    def __init__(self, isbn: str, title: str, author: str, year: int,
                 genre: str, total_copies: int) -> None:
        super().__init__(isbn, title, author, year)
        self.genre        = genre
        self.total_copies = total_copies  # validated via setter
        self._copies_out  = 0

    @property
    def total_copies(self) -> int:
        return self._total_copies

    @total_copies.setter
    def total_copies(self, value: int) -> None:
        if not isinstance(value, int) or value < 1:
            raise ValueError(f"total_copies must be >= 1, got {value!r}")
        self._total_copies = value

    @property
    def copies_available(self) -> int:
        return self._total_copies - self._copies_out

    @property
    def is_available(self) -> bool:
        return self.copies_available > 0

    @property
    def is_borrowable(self) -> bool:
        return True

    def do_borrow(self, member_name: str) -> None:
        if self.copies_available == 0:
            raise ValueError(f"No copies of '{self.title}' are currently available.")
        self._copies_out += 1

    def do_return(self) -> str:
        if self._copies_out == 0:
            raise ValueError(f"All copies of '{self.title}' are already returned.")
        self._copies_out -= 1
        return "a member"

    def item_type(self) -> str:
        return "Physical Book"

    def summary(self) -> str:
        return (
            f"{self.title} — {self.author} ({self.year})"
            f"  [{self.copies_available}/{self._total_copies} available]"
        )

    def format_details(self) -> str:
        return "\n".join([
            divider(),
            f"  {self.item_type().upper()}",
            divider(),
            format_row("ISBN",   self.isbn),
            format_row("Title",  self.title),
            format_row("Author", self.author),
            format_row("Year",   str(self.year)),
            format_row("Genre",  self.genre),
            format_row("Stock",  f"{self.copies_available}/{self._total_copies} available"),
            divider(),
        ])


class EBook(LibraryItem):
    """Digital book — always accessible, never physically borrowed."""

    def __init__(self, isbn: str, title: str, author: str, year: int,
                 file_format: str, file_size_mb: float) -> None:
        super().__init__(isbn, title, author, year)
        self.file_format  = file_format
        self.file_size_mb = file_size_mb  # validated via setter

    @property
    def file_size_mb(self) -> float:
        return self._file_size_mb

    @file_size_mb.setter
    def file_size_mb(self, value: float) -> None:
        if value <= 0:
            raise ValueError(f"file_size_mb must be > 0, got {value}")
        self._file_size_mb = float(value)

    @property
    def is_available(self) -> bool:
        return True

    @property
    def is_borrowable(self) -> bool:
        return False

    def do_borrow(self, member_name: str) -> None:
        raise ValueError(f"'{self.title}' is an E-Book and cannot be borrowed.")

    def do_return(self) -> str:
        raise ValueError(f"'{self.title}' is an E-Book and cannot be returned.")

    def item_type(self) -> str:
        return "E-Book"

    def summary(self) -> str:
        return (
            f"{self.title} — {self.author} ({self.year})"
            f"  [{self.file_format}, {self._file_size_mb:.1f} MB]"
        )

    def format_details(self) -> str:
        return "\n".join([
            divider(),
            f"  {self.item_type().upper()}",
            divider(),
            format_row("ISBN",   self.isbn),
            format_row("Title",  self.title),
            format_row("Author", self.author),
            format_row("Year",   str(self.year)),
            format_row("Format", self.file_format),
            format_row("Size",   f"{self._file_size_mb:.1f} MB"),
            format_row("Access", "Always available (digital)"),
            divider(),
        ])


class AudioBook(LibraryItem):
    """Audio recording — one borrower at a time."""

    def __init__(self, isbn: str, title: str, author: str, year: int,
                 narrator: str, duration_minutes: int) -> None:
        super().__init__(isbn, title, author, year)
        self.narrator         = narrator
        self.duration_minutes = duration_minutes  # validated via setter
        self._borrowed_by: str | None = None

    @property
    def duration_minutes(self) -> int:
        return self._duration_minutes

    @duration_minutes.setter
    def duration_minutes(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"duration_minutes must be a positive integer, got {value!r}")
        self._duration_minutes = value

    @property
    def is_available(self) -> bool:
        return self._borrowed_by is None

    @property
    def is_borrowable(self) -> bool:
        return True

    def do_borrow(self, member_name: str) -> None:
        if not self.is_available:
            raise ValueError(f"'{self.title}' is already borrowed by {self._borrowed_by}.")
        self._borrowed_by = member_name

    def do_return(self) -> str:
        if self.is_available:
            raise ValueError(f"'{self.title}' is not currently borrowed.")
        borrower, self._borrowed_by = self._borrowed_by, None
        return borrower

    def item_type(self) -> str:
        return "Audio Book"

    def summary(self) -> str:
        h, m   = divmod(self._duration_minutes, 60)
        status = "Available" if self.is_available else f"Borrowed by {self._borrowed_by}"
        return (
            f"{self.title} — {self.author} ({self.year})"
            f"  [{h}h {m:02d}m]  [{status}]"
        )

    def format_details(self) -> str:
        h, m   = divmod(self._duration_minutes, 60)
        status = "Available" if self.is_available else f"Borrowed by {self._borrowed_by}"
        return "\n".join([
            divider(),
            f"  {self.item_type().upper()}",
            divider(),
            format_row("ISBN",     self.isbn),
            format_row("Title",    self.title),
            format_row("Author",   self.author),
            format_row("Year",     str(self.year)),
            format_row("Narrator", self.narrator),
            format_row("Duration", f"{h}h {m:02d}m"),
            format_row("Status",   status),
            divider(),
        ])
