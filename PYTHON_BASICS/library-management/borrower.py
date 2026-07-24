import json
from datetime import date, timedelta
from pathlib import Path

from author import Author
from book import Book, Categories, LibraryResource, TypeOfBook

DATA_FILE = Path("data/library.json")
DATA_FILE.parent.mkdir(exist_ok=True)


class Borrow(LibraryResource):
    """Represents a book borrowing record."""

    def __init__(
        self,
        borrower_name,
        book_title,
        borrow_date=None,
        return_date=None,
        due_date=None,
    ):
        if not borrower_name or not str(borrower_name).strip():
            raise ValueError("Borrower name cannot be empty")
        if not book_title or not str(book_title).strip():
            raise ValueError("Book title cannot be empty")
        super().__init__(borrower_name)
        self.borrower_name = borrower_name.strip()
        self.book_title = book_title.strip()
        self.borrow_date = borrow_date or date.today()
        self.due_date = due_date or self.borrow_date + timedelta(days=14)
        self.return_date = return_date

    def is_overdue(self):
        """Return True if the book is past its due date and not yet returned."""
        return self.return_date is None and date.today() > self.due_date

    def mark_returned(self):
        """Mark this borrow record as returned today."""
        self.return_date = date.today()

    def __str__(self):
        status = (
            "Returned"
            if self.return_date
            else ("Overdue" if self.is_overdue() else "Borrowed")
        )
        return (
            f"  [Borrow] Borrower: {self.borrower_name} | Book: {self.book_title} "
            f"| Borrowed: {self.borrow_date} | Due: {self.due_date} "
            f"| Returned: {self.return_date or 'N/A'} | Status: {status}"
        )

    def __repr__(self):
        return (
            f"Borrow(borrower_name={self.borrower_name}, book_title={self.book_title}, "
            f"borrow_date={self.borrow_date}, return_date={self.return_date}, due_date={self.due_date})"
        )

    def __eq__(self, other):
        if not isinstance(other, Borrow):
            return False
        return (
            self.borrower_name == other.borrower_name
            and self.book_title == other.book_title
            and self.borrow_date == other.borrow_date
            and self.return_date == other.return_date
        )


# ── helpers ──────────────────────────────────────────────────────────────────


def _safe_int(value):
    """Return int(value) or None if value is not a valid integer."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _parse_date(value):
    """Return a date from an ISO string, or None if missing/invalid."""
    if value and value != "None":
        return date.fromisoformat(value)
    return None


# ── serialization ─────────────────────────────────────────────────────────────


def _serialize_book(book):
    """Convert a Book object to a JSON-serializable dict."""
    return {
        "title": book.title,
        "isbn": book.isbn,
        "category": book.category.value,
        "book_type": book.book_type.value,
        "year": book.year,
        "copies": book.copies,
        "author": {
            "name": book.author.name,
            "nationality": book.author.nationality,
            "birth_year": book.author.birth_year,
        },
    }


def _deserialize_book(data):
    """Convert a dict from JSON back to a Book object."""
    a = data["author"]
    author = Author(a["name"], a.get("nationality"), _safe_int(a.get("birth_year")))
    return Book(
        title=data["title"],
        author=author,
        isbn=data["isbn"],
        category=Categories(data.get("category", "General")),
        book_type=TypeOfBook(data.get("book_type", "Hardcover")),
        year=_safe_int(data.get("year")),
        copies=data.get("copies", 1),
    )


def _serialize_author(author):
    """Convert an Author object to a JSON-serializable dict."""
    return {
        "name": author.name,
        "nationality": author.nationality,
        "birth_year": author.birth_year,
    }


def _deserialize_author(data):
    """Convert a dict from JSON back to an Author object."""
    return Author(
        name=data["name"],
        nationality=data.get("nationality"),
        birth_year=_safe_int(data.get("birth_year")),
    )


def _serialize_borrow(borrow):
    """Convert a Borrow object to a JSON-serializable dict."""
    return {
        "borrower_name": borrow.borrower_name,
        "book_title": borrow.book_title,
        "borrow_date": str(borrow.borrow_date),
        "return_date": str(borrow.return_date) if borrow.return_date else None,
        "due_date": str(borrow.due_date),
    }


def _deserialize_borrow(data):
    """Convert a dict from JSON back to a Borrow object."""
    borrow_date = _parse_date(data.get("borrow_date")) or date.today()
    due_date = _parse_date(data.get("due_date")) or borrow_date + timedelta(days=14)
    return Borrow(
        borrower_name=data["borrower_name"],
        book_title=data["book_title"],
        borrow_date=borrow_date,
        due_date=due_date,
        return_date=_parse_date(data.get("return_date")),
    )


# ── public I/O ────────────────────────────────────────────────────────────────


def load_data():
    """Load books, authors, and borrows from library.json."""
    if not DATA_FILE.exists() or DATA_FILE.stat().st_size == 0:
        return [], [], []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    books = [_deserialize_book(b) for b in data.get("books", [])]
    authors = [_deserialize_author(a) for a in data.get("authors", [])]
    borrows = [_deserialize_borrow(b) for b in data.get("borrows", [])]
    return books, authors, borrows


def save_data(books, authors, borrows):
    """Save books, authors, and borrows to library.json."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "books": [_serialize_book(b) for b in books],
                "authors": [_serialize_author(a) for a in authors],
                "borrows": [_serialize_borrow(b) for b in borrows],
            },
            f,
            indent=4,
        )
