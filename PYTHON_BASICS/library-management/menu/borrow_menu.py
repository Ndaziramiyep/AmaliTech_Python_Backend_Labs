from library import file_io
from library.borrow import Borrow
from library.utils import (get_available_copies)


def borrow_book(books, borrows):
    isbn = input("ISBN of book to borrow: ")
    book_to_borrow = next((b for b in books if b.isbn == isbn), None)

    if not book_to_borrow:
        print("Book not found.")
        return

    available = get_available_copies(book_to_borrow, borrows)
    if available <= 0:
        print("No available copies to borrow.")
        return

    borrower = input("Your name: ")
    borrow_record = Borrow(borrower, book_to_borrow.title)

    borrows.append(borrow_record)
    file_io.save_borrows(borrows)
    print(f"Book borrowed successfully! Due date: {borrow_record.due_date}")


def return_book(books, borrows):
    borrower = input("Your name: ")
    isbn = input("ISBN of book to return: ")

    book_to_return = next((b for b in books if b.isbn == isbn), None)

    if not book_to_return:
        print("Book not found.")
        return

    borrow_record = next(
        (b for b in borrows if b.borrower_name == borrower and
         b.book_title == book_to_return.title and b.return_date is None),
        None
    )

    if borrow_record:
        borrow_record.mark_returned()
        file_io.save_borrows(borrows)
        print("Book returned successfully.")
    else:
        print("No active borrow record found for this book and borrower.")


def list_borrows(borrows):
    print("\nBorrow records:")
    for b in borrows:
        status = "Returned" if b.return_date else ("Overdue" if b.is_overdue() else "Borrowed")
        print(f"{b} | Status: {status}")
