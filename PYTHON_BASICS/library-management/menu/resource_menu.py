from library import file_io
from library.author import Author
from library.enum import Categories, TypeOfBook
from library.resources import Book
from library.utils import (filter_books, get_available_copies,
                           get_borrowed_count, search_books)


def add_book(books, authors):
    title = input("Title: ")
    author_name = input("Author name: ")
    nationality = input("Nationality (optional): ") or None
    birth_year = input("Birth year (optional): ") or None

    author = next((a for a in authors if a.name == author_name), None)
    if not author:
        author = Author(author_name, nationality, birth_year)
        authors.append(author)
        file_io.save_authors(authors)

    isbn = input("ISBN: ")
    if any(b.isbn == isbn for b in books):
       print("ISBN already exists! Book not added.")
       return

    year = input("Publication year: ")

    copies = int(input("Number of copies: "))
    print("\nAvailable categories:")
    for cat in Categories:
        print(cat.value)

    category = input("Enter Category: ").strip().title()
    if not category:
        category = Categories.GENERAL

    print("\navailable book types:")
    for cat in TypeOfBook:
        print(cat.value)

    book_type = input("Book type: ").strip().title()
    if not book_type:
        book_type = TypeOfBook.HARDCOVER

    book = Book(title, author, isbn, year, category,book_type,copies)
    books.append(book)
    file_io.save_books(books)
    print("Book added successfully.")


def list_books(books, borrows):
    print("\nBooks in library:")
    for b in books:
        available = get_available_copies(b, borrows)
        borrowed = get_borrowed_count(b, borrows)
        print(f"{b} | Available: {available} | Borrowed: {borrowed}")


def search_book_cli(books):
    field = input("Search by (title/author/isbn/category/year): ").lower()
    query = input("Enter search query: ")

    results = search_books(books, query, field)

    if results:
        for b in results:
            print(b)
    else:
        print("No books found.")


def filter_books_cli(books, borrows):
    print("Filter by: category / type / available / borrowed")
    criteria = input("Enter filter criteria: ").strip().lower()
    value = None

    if criteria == "category":
        print("\nAvailable Categories:")
        for cat in Categories:
            print(cat.value)
        value_input = input("Enter category: ").strip().title()
        value = Categories(value_input)

    elif criteria == "type":
        print("\nAvailable Book Types:")
        for t in TypeOfBook:
            print(t.value)
        value_input = input("Enter type: ").strip().title()
        value = TypeOfBook(value_input)

    elif criteria in ["available", "borrowed"]:
        # no extra input needed
        value = criteria

    else:
        print("Invalid filter criteria.")
        return

    # Use your existing filter_books utility
    results = filter_books(books, borrows, criteria, value)

    if results:
        for b in results:
            available = get_available_copies(b, borrows)
            borrowed = get_borrowed_count(b, borrows)
            print(f"{b} | Available: {available} | Borrowed: {borrowed}")
    else:
        print("No books match the filter criteria.")

def delete_book(books, borrows):
    isbn = input("Enter ISBN of the book to delete: ")
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
