from library.borrow import Borrow
from library.resources import Book


def get_available_copies(book: Book, borrows: list[Borrow]) -> int:
    """
    Calculate available copies of a book.
    Total copies minus number of active borrows.
    """
    borrowed_count = sum(1 for b in borrows if b.book_title == book.title and not b.return_date)
    return book.copies - borrowed_count

def get_borrowed_count(book: Book, borrows: list[Borrow]) -> int:
    """
    Number of copies currently borrowed.
    """
    return sum(1 for b in borrows if b.book_title == book.title and not b.return_date)

def search_books(books: list[Book], query: str, field: str) -> list[Book]:
    query = query.lower()
    results = []
    for book in books:
        if field == "title" and query in book.title.lower():
            results.append(book)
        elif field == "author" and query in book.author.name.lower():
            results.append(book)
        elif field == "isbn" and query in book.isbn.lower():
            results.append(book)
        elif field == "category" and book.category and query in book.category.lower():
            results.append(book)
        elif field == "year" and book.year and query in str(book.year):
            results.append(book)
    return results

def filter_books(books: list[Book], borrows: list[Borrow], criteria: str, value=None) -> list[Book]:
    """
    Filter books based on criteria:
    - available: books with copies available
    - borrowed: books currently borrowed
    - category: books matching a specific category (value should be a Categories enum)
    - type: books matching a specific type (value should be a TypeOfBook enum)
    """
    filtered = []
    for book in books:
        available_count = get_available_copies(book, borrows)
        borrowed_count = get_borrowed_count(book, borrows)

        if criteria == "available" and available_count > 0:
            filtered.append(book)
        elif criteria == "borrowed" and borrowed_count > 0:
            filtered.append(book)
        elif criteria == "category" and isinstance(value, Categories) and book.category == value:
            filtered.append(book)
        elif criteria == "type" and isinstance(value, TypeOfBook) and book.book_type == value:
            filtered.append(book)

    return filtered
