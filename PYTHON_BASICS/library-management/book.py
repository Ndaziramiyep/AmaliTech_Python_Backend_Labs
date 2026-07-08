from abc import ABC, abstractmethod
from datetime import date
from enum import Enum


class Categories(Enum):
    FICTION = "Fiction"
    NON_FICTION = "Non-Fiction"
    SCIENCE_FICTION = "Science Fiction"
    FANTASY = "Fantasy"
    MYSTERY = "Mystery"
    THRILLER = "Thriller"
    ROMANCE = "Romance"
    BIOGRAPHY = "Biography"
    HISTORY = "History"
    CHILDREN = "Children"
    POETRY = "Poetry"
    COOKBOOKS = "Cookbooks"
    SELF_HELP = "Self-Help"
    TECHNOLOGY = "Technology"
    SCIENCE = "Science"
    GENERAL = "General"


class TypeOfBook(Enum):
    HARDCOVER = "Hardcover"
    PAPERBACK = "Paperback"
    EBOOK = "Ebook"
    AUDIOBOOK = "Audiobook"


class LibraryResource(ABC):
    """Abstract base class for all library resources."""

    def __init__(self, title):
        self.title = title

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def __eq__(self, other):
        pass


class Book(LibraryResource):
    """Represents a book in the library."""

    def __init__(
        self,
        title,
        author,
        isbn,
        year,
        category: Categories = Categories.GENERAL,
        book_type: TypeOfBook = TypeOfBook.HARDCOVER,
        copies=1,
    ):
        self._title = None
        self._isbn = None
        self._category = None
        self._book_type = None
        self._author = None
        self._year = None
        self._copies = None

        self.title = title
        self.author = author
        self.isbn = isbn
        self.year = year
        self.category = category
        self.book_type = book_type
        self.copies = copies

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        if not value or not value.strip():
            raise ValueError("Title cannot be empty")
        if not value.replace(" ", "").replace("-", "").replace("'", "").replace(":", "").replace(",", "").replace(".", "").isalnum():
            raise ValueError("Title must contain only letters, numbers, spaces, or common punctuation")
        self._title = value.strip()

    @property
    def isbn(self):
        return self._isbn

    @isbn.setter
    def isbn(self, value):
        if not value or not str(value).strip():
            raise ValueError("ISBN cannot be empty")
        self._isbn = str(value).strip()

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        if isinstance(value, Categories):
            self._category = value
        elif isinstance(value, str):
            self._category = Categories(value)
        else:
            raise ValueError("Invalid category")

    @property
    def book_type(self):
        return self._book_type

    @book_type.setter
    def book_type(self, value):
        if isinstance(value, TypeOfBook):
            self._book_type = value
        elif isinstance(value, str):
            self._book_type = TypeOfBook(value)
        else:
            raise ValueError("Invalid book type")

    @property
    def author(self):
        return self._author

    @author.setter
    def author(self, value):
        from author import Author
        if not isinstance(value, Author):
            raise ValueError("author must be an Author object")
        self._author = value

    @property
    def year(self):
        """Publication year — positive integer not in the future."""
        return self._year

    @year.setter
    def year(self, value):
        if value is None:
            self._year = None
            return
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValueError("Publication year must be a number")
        if value < 1 or value > date.today().year:
            raise ValueError(f"Publication year must be between 1 and {date.today().year}")
        self._year = value

    @property
    def copies(self):
        """Total number of copies — must be a positive integer."""
        return self._copies

    @copies.setter
    def copies(self, value):
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValueError("Copies must be a number")
        if value < 1:
            raise ValueError("Copies must be at least 1")
        self._copies = value

    def __repr__(self):
        return (
            f"Book(title={self.title}, author={self.author}, isbn={self.isbn}, "
            f"year={self._year}, category={self.category.value}, book_type={self.book_type.value})"
        )

    def __eq__(self, other):
        if not isinstance(other, Book):
            return False
        return self.isbn == other.isbn
