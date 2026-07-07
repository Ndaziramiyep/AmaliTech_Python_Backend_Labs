"""book.py — LibraryItem ABC and its three concrete subclasses."""

from abc import ABC, abstractmethod
from utils import divider, format_row


class LibraryItem(ABC):
    """Abstract base for all library items.

    Subclasses must implement item_type(), summary(), format_details(),
    is_available, is_borrowable, do_borrow(), and do_return().
    """

    def __init__(self, isbn: str, title: str, author: str, year: int) -> None:
        """Store shared fields; all string fields and year are validated."""
        if not isbn.strip():
            raise ValueError("ISBN cannot be empty.")
        if not title.strip():
            raise ValueError("Title cannot be empty.")
        if not author.strip():
            raise ValueError("Author cannot be empty.")
        self.isbn   = isbn.strip()
        self.title  = title.strip()
        self.author = author.strip()
        self.year   = year

    @property
    def year(self) -> int:
        """Publication year as a positive integer."""
        return self._year

    @year.setter
    def year(self, value: int) -> None:
        """Reject non-positive or non-integer values."""
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"Year must be a positive whole number, got {value!r}.")
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
        """Return a readable string: 'Type | ISBN — Title'."""
        return f"{self.item_type()} | {self.isbn} — {self.title}"

    def __repr__(self) -> str:
        """Return an unambiguous representation for debugging."""
        return f"{self.__class__.__name__}(isbn={self.isbn!r}, title={self.title!r})"


class PhysicalBook(LibraryItem):
    """Printed book with copy-count tracking; multiple copies can be borrowed at once."""

    def __init__(self, isbn: str, title: str, author: str, year: int,
                 genre: str, total_copies: int) -> None:
        """Initialise a physical book; total_copies must be >= 1."""
        super().__init__(isbn, title, author, year)
        self.genre        = genre
        self.total_copies = total_copies  # validated via setter
        self._copies_out  = 0

    @property
    def total_copies(self) -> int:
        """Total copies held in the library."""
        return self._total_copies

    @total_copies.setter
    def total_copies(self, value: int) -> None:
        """Reject values less than 1."""
        if not isinstance(value, int) or value < 1:
            raise ValueError(f"Total copies must be at least 1, got {value!r}.")
        self._total_copies = value

    @property
    def copies_available(self) -> int:
        """Copies currently on the shelf (total minus borrowed)."""
        return self._total_copies - self._copies_out

    @property
    def is_available(self) -> bool:
        """True when at least one copy is on the shelf."""
        return self.copies_available > 0

    @property
    def is_borrowable(self) -> bool:
        """Physical books are always borrowable."""
        return True

    def do_borrow(self, member_name: str) -> None:
        """Increment borrowed count; raise ValueError if no copies are available."""
        if not member_name.strip():
            raise ValueError("Member name cannot be empty.")
        if self.copies_available == 0:
            raise ValueError(f"Sorry, all copies of '{self.title}' are currently on loan. Please check back later.")
        self._copies_out += 1

    def do_return(self) -> str:
        """Decrement borrowed count; raise ValueError if all copies are already in."""
        if self._copies_out == 0:
            raise ValueError(f"No copies of '{self.title}' are currently on loan — nothing to return.")
        self._copies_out -= 1
        return "a member"

    def item_type(self) -> str:
        """Return the item type label."""
        return "Physical Book"

    def summary(self) -> str:
        """Return a one-line summary including copy availability."""
        return (
            f"{self.title} — {self.author} ({self.year})"
            f"  [{self.copies_available}/{self._total_copies} available]"
        )

    def format_details(self) -> str:
        """Return a formatted detail block for this physical book."""
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
        """Initialise an e-book; file_size_mb must be > 0."""
        super().__init__(isbn, title, author, year)
        self.file_format  = file_format
        self.file_size_mb = file_size_mb  # validated via setter

    @property
    def file_size_mb(self) -> float:
        """File size in megabytes."""
        return self._file_size_mb

    @file_size_mb.setter
    def file_size_mb(self, value: float) -> None:
        """Reject non-positive values."""
        if value <= 0:
            raise ValueError(f"File size must be greater than 0 MB, got {value}.")
        self._file_size_mb = float(value)

    @property
    def is_available(self) -> bool:
        """Always True — digital items are never checked out."""
        return True

    @property
    def is_borrowable(self) -> bool:
        """E-Books cannot be physically borrowed."""
        return False

    def do_borrow(self, member_name: str) -> None:
        """Always raises ValueError — e-books cannot be borrowed."""
        raise ValueError(f"'{self.title}' is an E-Book — it is always available digitally and cannot be checked out.")

    def do_return(self) -> str:
        """Always raises ValueError — e-books cannot be returned."""
        raise ValueError(f"'{self.title}' is an E-Book — it was never borrowed, so it cannot be returned.")

    def item_type(self) -> str:
        """Return the item type label."""
        return "E-Book"

    def summary(self) -> str:
        """Return a one-line summary including format and file size."""
        return (
            f"{self.title} — {self.author} ({self.year})"
            f"  [{self.file_format}, {self._file_size_mb:.1f} MB]"
        )

    def format_details(self) -> str:
        """Return a formatted detail block for this e-book."""
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
        """Initialise an audio book; duration_minutes must be a positive integer."""
        super().__init__(isbn, title, author, year)
        self.narrator         = narrator
        self.duration_minutes = duration_minutes  # validated via setter
        self._borrowed_by: str | None = None

    @property
    def duration_minutes(self) -> int:
        """Total runtime in minutes."""
        return self._duration_minutes

    @duration_minutes.setter
    def duration_minutes(self, value: int) -> None:
        """Reject non-positive or non-integer values."""
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"Duration must be a positive whole number of minutes, got {value!r}.")
        self._duration_minutes = value

    @property
    def is_available(self) -> bool:
        """True when no member currently holds this item."""
        return self._borrowed_by is None

    @property
    def is_borrowable(self) -> bool:
        """Audio books can be borrowed."""
        return True

    def do_borrow(self, member_name: str) -> None:
        """Record member as borrower; raise ValueError if already borrowed."""
        if not member_name.strip():
            raise ValueError("Member name cannot be empty.")
        if not self.is_available:
            raise ValueError(f"'{self.title}' is currently borrowed by {self._borrowed_by} and is not available.")
        self._borrowed_by = member_name

    def do_return(self) -> str:
        """Clear borrower and return their name; raise ValueError if not borrowed."""
        if self.is_available:
            raise ValueError(f"'{self.title}' is not currently on loan — there is nothing to return.")
        borrower, self._borrowed_by = self._borrowed_by, None
        return borrower

    def item_type(self) -> str:
        """Return the item type label."""
        return "Audio Book"

    def summary(self) -> str:
        """Return a one-line summary including duration and borrow status."""
        h, m   = divmod(self._duration_minutes, 60)
        status = "Available" if self.is_available else f"Borrowed by {self._borrowed_by}"
        return (
            f"{self.title} — {self.author} ({self.year})"
            f"  [{h}h {m:02d}m]  [{status}]"
        )

    def format_details(self) -> str:
        """Return a formatted detail block for this audio book."""
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
