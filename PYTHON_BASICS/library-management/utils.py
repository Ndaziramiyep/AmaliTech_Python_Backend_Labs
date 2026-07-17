from author import Author
from book import Book, Categories, TypeOfBook
from borrower import Borrow, load_data, save_data


# ── copy helpers ──────────────────────────────────────────────────────────────

def get_available_copies(book: Book, borrows: list[Borrow]) -> int:
    """Return total copies minus the number of active (unreturned) borrows."""
    return book.copies - get_borrowed_count(book, borrows)


def get_borrowed_count(book: Book, borrows: list[Borrow]) -> int:
    """Return the number of copies currently borrowed."""
    return sum(1 for b in borrows if b.book_title == book.title and not b.return_date)


# ── search & filter ───────────────────────────────────────────────────────────

def search_books(books: list[Book], query: str, field: str) -> list[Book]:
    """Search books by a given field (title, author, isbn, category, year)."""
    query = query.lower()
    results = []
    for book in books:
        if field == "title" and query in book.title.lower():
            results.append(book)
        elif field == "author" and query in book.author.name.lower():
            results.append(book)
        elif field == "isbn" and query in book.isbn.lower():
            results.append(book)
        elif field == "category" and book.category and query in book.category.value.lower():
            results.append(book)
        elif field == "year" and book.year and query in str(book.year):
            results.append(book)
    return results


def filter_books(books: list[Book], borrows: list[Borrow], criteria: str, value=None) -> list[Book]:
    """
    Filter books by criteria:
    - available: books with copies available
    - borrowed: books currently borrowed
    - category: books matching a Categories enum value
    - type: books matching a TypeOfBook enum value
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


# ── menu actions ──────────────────────────────────────────────────────────────

def add_book(books, authors, borrows):
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
    save_data(books, authors, borrows)
    print("Book added successfully.")


def _fmt_row(widths, values):
    return "  ".join(str(v).ljust(w) for w, v in zip(widths, values))


def list_books(books, borrows):
    """Display all books in a column-aligned table without border lines."""
    if not books:
        print("No books in the library.")
        return
    headers = ["#", "Title", "Author", "ISBN", "Category", "Type", "Year", "Copies", "Avail", "Status"]
    rows = []
    for i, b in enumerate(books, 1):
        available = get_available_copies(b, borrows)
        rows.append([
            i, b.title, b.author.name, b.isbn,
            b.category.value if b.category else "",
            b.book_type.value if b.book_type else "",
            b.year or "", b.copies, available,
            "Available" if available > 0 else "Not Available",
        ])
    widths = [max(len(str(r[i])) for r in [headers] + rows) for i in range(len(headers))]
    print(f"\nBooks in library ({len(books)} total):")
    print(_fmt_row(widths, headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(_fmt_row(widths, row))


def list_authors(authors):
    """Display all authors in a column-aligned table without border lines."""
    if not authors:
        print("No authors found.")
        return
    headers = ["#", "Name", "Nationality", "Birth Year"]
    rows = [[i, a.name, a.nationality or "", a.birth_year or ""] for i, a in enumerate(authors, 1)]
    widths = [max(len(str(r[i])) for r in [headers] + rows) for i in range(len(headers))]
    print(f"\nAuthors ({len(authors)} total):")
    print(_fmt_row(widths, headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(_fmt_row(widths, row))


def borrow_book(books, borrows, authors):
    """Borrow a book by ISBN if copies are available."""
    isbn = input("ISBN of book to borrow: ").strip()
    if not isbn:
        print("ISBN cannot be empty.")
        return
    book_to_borrow = next((b for b in books if b.isbn == isbn), None)
    if not book_to_borrow:
        print("Book not found.")
        return

    available = get_available_copies(book_to_borrow, borrows)
    if available <= 0:
        print("No available copies to borrow.")
        return

    borrower = input("Your name: ").strip()
    if not borrower:
        print("Borrower name cannot be empty.")
        return

    borrow_record = Borrow(borrower, book_to_borrow.title)
    borrows.append(borrow_record)
    save_data(books, authors, borrows)
    print(f"Book borrowed successfully! Due date: {borrow_record.due_date}")


def return_book(books, borrows, authors):
    """Mark a borrowed book as returned."""
    borrower = input("Your name: ").strip()
    if not borrower:
        print("Borrower name cannot be empty.")
        return
    isbn = input("ISBN of book to return: ").strip()
    if not isbn:
        print("ISBN cannot be empty.")
        return

    book_to_return = next((b for b in books if b.isbn == isbn), None)
    if not book_to_return:
        print("Book not found.")
        return

    borrow_record = next(
        (b for b in borrows if b.borrower_name == borrower
         and b.book_title == book_to_return.title and b.return_date is None),
        None,
    )

    if borrow_record:
        borrow_record.mark_returned()
        save_data(books, authors, borrows)
        print("Book returned successfully.")
    else:
        print("No active borrow record found for this book and borrower.")



def list_borrows(borrows):
    """Display only active (unreturned) borrow records in a column-aligned table."""
    active = [b for b in borrows if not b.return_date]
    if not active:
        print("No active borrow records found.")
        return
    headers = ["#", "Borrower", "Book Title", "Borrowed On", "Due Date", "Status"]
    rows = [
        [i, b.borrower_name, b.book_title, b.borrow_date, b.due_date,
         "Overdue" if b.is_overdue() else "Borrowed"]
        for i, b in enumerate(active, 1)
    ]
    widths = [max(len(str(r[i])) for r in [headers] + rows) for i in range(len(headers))]
    print(f"\nActive Borrow records ({len(active)} total):")
    print(_fmt_row(widths, headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(_fmt_row(widths, row))


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


def delete_book(books, borrows, authors):
    """Delete a book by ISBN if it has no active borrows."""
    isbn = input("Enter ISBN of the book to delete: ").strip()
    if not isbn:
        print("ISBN cannot be empty.")
        return
    book = next((b for b in books if b.isbn == isbn), None)
    if not book:
        print("Book not found.")
        return

    if any(b.book_title == book.title and not b.return_date for b in borrows):
        print("Cannot delete. Some copies are currently borrowed.")
        return

    books.remove(book)
    save_data(books, authors, borrows)
    print(f"Book '{book.title}' deleted successfully.")


# ── CLI loop ──────────────────────────────────────────────────────────────────

def cli():
    """Main CLI loop: load data, display menu, and dispatch user actions."""
    books, authors, borrows = load_data()

    actions = {
        "1": lambda: add_book(books, authors, borrows),
        "2": lambda: list_books(books, borrows),
        "3": lambda: list_authors(authors),
        "4": lambda: borrow_book(books, borrows, authors),
        "5": lambda: return_book(books, borrows, authors),
        "6": lambda: list_borrows(borrows),
        "7": lambda: search_book_cli(books),
        "8": lambda: filter_books_cli(books, borrows),
        "9": lambda: delete_book(books, borrows, authors),
        "0": lambda: (save_data(books, authors, borrows), print("Exiting...")),
    }

    while True:
        print("\nMenu:")
        print("1. Add a book")
        print("2. List all books")
        print("3. List authors")
        print("4. Borrow a book")
        print("5. Return a book")
        print("6. List borrow records")
        print("7. Search a book")
        print("8. Filter records")
        print("9. Delete a book")
        print("0. Exit")

        choice = input("Enter your choice: ")
        actions.get(choice, lambda: print("Invalid choice. Try again."))()

        if choice == "0":
            break
