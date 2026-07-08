from library import file_io
from library.author import Author
from library.enum import Categories, TypeOfBook
from library.resources import Book
from library.utils import (filter_books, get_available_copies,
                           get_borrowed_count, search_books)


def add_book(books, authors):
    """Prompt user for book details, validate input, and add the book."""
    title = input("Title: ").strip()
    if not title:
        print("Title cannot be empty.")
        return

    author_name = input("Author name: ").strip()
    if not author_name:
        print("Author name cannot be empty.")
        return

    nationality = input("Nationality (optional): ").strip() or None
    birth_year_input = input("Birth year (optional): ").strip() or None
    if birth_year_input is not None:
        try:
            birth_year_input = int(birth_year_input)
        except ValueError:
            print("Birth year must be a number.")
            return

    author = next((a for a in authors if a.name == author_name), None)
    if not author:
        try:
            author = Author(author_name, nationality, birth_year_input)
        except ValueError as e:
            print(f"Invalid author data: {e}")
            return
        authors.append(author)
        file_io.save_authors(authors)

    isbn = input("ISBN: ").strip()
    if not isbn:
        print("ISBN cannot be empty.")
        return
    if any(b.isbn == isbn for b in books):
        print("ISBN already exists! Book not added.")
        return

    year_input = input("Publication year: ").strip()
    if not year_input:
        print("Publication year cannot be empty.")
        return
    try:
        year = int(year_input)
    except ValueError:
        print("Publication year must be a number.")
        return

    copies_input = input("Number of copies: ").strip()
    if not copies_input:
        print("Number of copies cannot be empty.")
        return
    try:
        copies = int(copies_input)
        if copies < 1:
            raise ValueError
    except ValueError:
        print("Number of copies must be a positive integer.")
        return

    print("\nAvailable categories:")
    for cat in Categories:
        print(cat.value)
    category_input = input("Enter Category: ").strip().title()
    try:
        category = Categories(category_input) if category_input else Categories.GENERAL
    except ValueError:
        print(f"Invalid category '{category_input}'. Using General.")
        category = Categories.GENERAL

    print("\nAvailable book types:")
    for t in TypeOfBook:
        print(t.value)
    book_type_input = input("Book type: ").strip().title()
    try:
        book_type = TypeOfBook(book_type_input) if book_type_input else TypeOfBook.HARDCOVER
    except ValueError:
        print(f"Invalid book type '{book_type_input}'. Using Hardcover.")
        book_type = TypeOfBook.HARDCOVER

    try:
        book = Book(title, author, isbn, year, category, book_type, copies)
    except ValueError as e:
        print(f"Invalid book data: {e}")
        return

    books.append(book)
    file_io.save_books(books)
    print("Book added successfully.")


def list_books(books, borrows):
    """Display all books with their available and borrowed copy counts."""
    if not books:
        print("No books in the library.")
        return
    print("\nBooks in library:")
    for b in books:
        available = get_available_copies(b, borrows)
        borrowed = get_borrowed_count(b, borrows)
        print(f"{b} | Available: {available} | Borrowed: {borrowed}")


def search_book_cli(books):
    """Prompt user for a search field and query, then display matching books."""
    field = input("Search by (title/author/isbn/category/year): ").strip().lower()
    if field not in ("title", "author", "isbn", "category", "year"):
        print("Invalid search field.")
        return
    query = input("Enter search query: ").strip()
    if not query:
        print("Search query cannot be empty.")
        return
    results = search_books(books, query, field)
    if results:
        for b in results:
            print(b)
    else:
        print("No books found.")


def filter_books_cli(books, borrows):
    """Prompt user for filter criteria and display matching books."""
    print("Filter by: category / type / available / borrowed")
    criteria = input("Enter filter criteria: ").strip().lower()
    value = None

    if criteria == "category":
        print("\nAvailable Categories:")
        for cat in Categories:
            print(cat.value)
        value_input = input("Enter category: ").strip().title()
        if not value_input:
            print("Category cannot be empty.")
            return
        try:
            value = Categories(value_input)
        except ValueError:
            print(f"Invalid category '{value_input}'.")
            return

    elif criteria == "type":
        print("\nAvailable Book Types:")
        for t in TypeOfBook:
            print(t.value)
        value_input = input("Enter type: ").strip().title()
        if not value_input:
            print("Book type cannot be empty.")
            return
        try:
            value = TypeOfBook(value_input)
        except ValueError:
            print(f"Invalid book type '{value_input}'.")
            return

    elif criteria in ["available", "borrowed"]:
        value = criteria

    else:
        print("Invalid filter criteria.")
        return

    results = filter_books(books, borrows, criteria, value)
    if results:
        for b in results:
            available = get_available_copies(b, borrows)
            borrowed = get_borrowed_count(b, borrows)
            print(f"{b} | Available: {available} | Borrowed: {borrowed}")
    else:
        print("No books match the filter criteria.")

def delete_book(books, borrows):
    """Delete a book by ISBN if it has no active borrows."""
    isbn = input("Enter ISBN of the book to delete: ").strip()
    if not isbn:
        print("ISBN cannot be empty.")
        return
    book = next((b for b in books if b.isbn == isbn), None)

    if not book:
        print("Book not found.")
        return

    active_borrows = [b for b in borrows if b.book_title == book.title and not b.return_date]

    if active_borrows:
        print("Cannot delete. Some copies are currently borrowed.")
        return

    books.remove(book)
    file_io.save_books(books)
    print(f"Book {book.title} deleted successfully.")
