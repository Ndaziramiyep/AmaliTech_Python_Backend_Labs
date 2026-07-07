from library import file_io
from menu.author_menu import list_authors
from menu.borrow_menu import borrow_book, list_borrows, return_book
from menu.resource_menu import (add_book, delete_book, filter_books_cli,
                                list_books, search_book_cli)


def cli():
    books = file_io.load_books()
    borrows = file_io.load_borrows()
    authors = file_io.load_authors()


    actions = {
        "1": lambda: add_book(books, authors),
        "2": lambda: list_books(books, borrows),
        "3": lambda: list_authors(authors),
        "4": lambda: borrow_book(books, borrows),
        "5": lambda: return_book(books, borrows),
        "6": lambda: list_borrows(borrows),
        "7": lambda: search_book_cli(books),
        "8": lambda: filter_books_cli(books, borrows),
        "9": lambda: delete_book(books, borrows),
        "0": lambda: (
            file_io.save_books(books),
            file_io.save_borrows(borrows),
            print("Exiting...")
        )
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

        action = actions.get(choice, lambda: print("Invalid choice. Try again."))
        action()

        if choice == "0":
            break
