import json
from datetime import timedelta
from pathlib import Path

from .author import Author
from .borrow import Borrow
from .enum import Categories, TypeOfBook
from .resources import Book

DATA_FOLDER = Path("data")
DATA_FOLDER.mkdir(exist_ok=True)

BOOKS_FILE = DATA_FOLDER / "books.json"
BORROWS_FILE = DATA_FOLDER / "borrowers.json"
AUTHORS_FILE = DATA_FOLDER / "authors.json"

def save_books(books):
    with open(BOOKS_FILE, "w",encoding="utf-8") as f:
        json.dump([serialize_book(b) for b in books], f, indent=4)

def load_books():
    if not BOOKS_FILE.exists() or BOOKS_FILE.stat().st_size == 0:
        return []
    with open(BOOKS_FILE, "r") as f:
        return [deserialize_book(b) for b in json.load(f)]

def serialize_book(book):
    return {
        "title": book.title,
        "isbn": book.isbn,
        "category": book.category.value,
        "book_type": book.book_type.value,
        "year": book.year,
        "copies": book.copies,
        "author": {
            "name": book.author.name,
            "nationality": getattr(book.author, "nationality", None),
            "birth_year": getattr(book.author, "birth_year", None)
        }
    }

def deserialize_book(data):
    """Convert dict from JSON back to Book object."""
    author_data = data["author"]
    author = Author(author_data["name"], author_data.get("nationality"), author_data.get("birth_year"))
    return Book(
        title=data["title"],
        author=author,
        isbn=data["isbn"],
        category=Categories(data.get("category","General")),
        book_type=TypeOfBook(data.get("book_type","Hardcover")),
        year=data.get("year"),
        copies=data.get("copies",1)
    )

def save_borrows(borrows):
    with open(BORROWS_FILE, "w",encoding="utf-8") as f:
        json.dump([serialize_borrow(b) for b in borrows], f, indent=4)

def load_borrows():
     if not BORROWS_FILE.exists() or BORROWS_FILE.stat().st_size == 0:
        return []
     with open(BORROWS_FILE,"r",encoding="utf-8") as f:
        data =json.load(f)
        return [deserialize_borrow(b) for b in data]

def serialize_borrow(borrow):
    return{
        "borrower_name": borrow.borrower_name,
        "book_title": borrow.book_title,
        "borrow_date": str(borrow.borrow_date),
        "return_date": str(borrow.return_date) if borrow.return_date else None,
        "due_date": str(borrow.due_date)

    }

def deserialize_borrow(data):
   from datetime import date
   borrow_date = date.fromisoformat(data["borrow_date"]) if data.get("borrow_date") and data["borrow_date"] != "None" else date.today()
   due_date = date.fromisoformat(data["due_date"]) if data.get("due_date") and data["due_date"] != "None" else (borrow_date + timedelta(days=14))
   return_date = date.fromisoformat(data["return_date"]) if data.get("return_date") and data["return_date"] != "None" else None

   return Borrow(
        borrower_name=data["borrower_name"],
        book_title=data["book_title"],
        borrow_date=borrow_date,
        due_date=due_date,
        return_date=return_date
    )

def save_authors(authors):
    """Save authors list to authors.json"""
    with open(AUTHORS_FILE, "w", encoding="utf-8") as f:
        json.dump([serialize_author(a) for a in authors], f, indent=4)

def load_authors():
    """Load authors list from authors.json"""
    if not AUTHORS_FILE.exists() or AUTHORS_FILE.stat().st_size == 0:
        return []
    with open(AUTHORS_FILE, "r", encoding="utf-8") as f:
        return [deserialize_author(a) for a in json.load(f)]

def serialize_author(author):
    return {
        "name": author.name,
        "nationality": getattr(author, "nationality", None),
        "birth_year": getattr(author, "birth_year", None)
    }

def deserialize_author(data):
    return Author(
        name=data["name"],
        nationality=data.get("nationality"),
        birth_year=data.get("birth_year")
    )
