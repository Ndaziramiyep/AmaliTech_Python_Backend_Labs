"""main.py — CLI entry point for the Library Inventory Application."""

from book import PhysicalBook, EBook, AudioBook
from inventory import Inventory
from utils import divider, format_header


def _prompt_isbn(existing: set[str] | None = None, label: str = "ISBN") -> str:
    """Prompt for a non-empty ISBN; reject duplicates when existing is given."""
    while True:
        raw = input(f"  {label} (e.g. 978-0-13-468599-1): ").strip().upper()
        if not raw:
            print("  ! ISBN cannot be empty.")
        elif existing is not None and raw in existing:
            print(f"  ! ISBN '{raw}' already exists.")
        else:
            return raw


def _prompt_str(label: str, allow_digits: bool = True) -> str:
    """Prompt for a non-empty string; optionally reject digit characters."""
    while True:
        raw   = input(f"  {label}: ").strip()
        field = label.split("(")[0].strip()
        if not raw:
            print(f"  ! {field} cannot be empty.")
        elif not allow_digits and any(ch.isdigit() for ch in raw):
            print(f"  ! {field} must not contain digits.")
        else:
            return raw


def _prompt_int(label: str, min_val: int = 1) -> int:
    """Prompt for an integer >= min_val."""
    while True:
        try:
            value = int(input(f"  {label}: ").strip())
            if value < min_val:
                print(f"  ! Value must be >= {min_val}.")
            else:
                return value
        except ValueError:
            print("  ! Enter a whole number (e.g. 2024).")


def _prompt_float(label: str, min_val: float = 0.01) -> float:
    """Prompt for a float >= min_val."""
    while True:
        try:
            value = float(input(f"  {label}: ").strip())
            if value < min_val:
                print(f"  ! Value must be >= {min_val:.2f}.")
            else:
                return value
        except ValueError:
            print("  ! Enter a number (e.g. 4.5).")


def _add_physical(inv: Inventory) -> None:
    """Collect input and add a PhysicalBook."""
    print("\n  -- Add Physical Book --")
    existing = {i.isbn for i in inv.all_items()}
    isbn   = _prompt_isbn(existing)
    title  = _prompt_str("Title        (e.g. Clean Code)")
    author = _prompt_str("Author       (e.g. Robert C. Martin)", allow_digits=False)
    year   = _prompt_int("Year         (e.g. 2008)")
    genre  = _prompt_str("Genre        (e.g. Technology)")
    copies = _prompt_int("Total Copies (e.g. 3)")
    try:
        inv.add_item(PhysicalBook(isbn, title, author, year, genre, copies))
        print(f"\n  + '{title}' added.")
    except ValueError as exc:
        print(f"  ! {exc}")


def _add_ebook(inv: Inventory) -> None:
    """Collect input and add an EBook."""
    print("\n  -- Add E-Book --")
    existing = {i.isbn for i in inv.all_items()}
    isbn    = _prompt_isbn(existing)
    title   = _prompt_str("Title      (e.g. The Pragmatic Programmer)")
    author  = _prompt_str("Author     (e.g. David Thomas)", allow_digits=False)
    year    = _prompt_int("Year       (e.g. 2019)")
    fmt     = _prompt_str("Format     (e.g. PDF, EPUB)")
    size_mb = _prompt_float("Size (MB)  (e.g. 4.5)")
    try:
        inv.add_item(EBook(isbn, title, author, year, fmt, size_mb))
        print(f"\n  + '{title}' added.")
    except ValueError as exc:
        print(f"  ! {exc}")


def _add_audiobook(inv: Inventory) -> None:
    """Collect input and add an AudioBook."""
    print("\n  -- Add Audio Book --")
    existing = {i.isbn for i in inv.all_items()}
    isbn     = _prompt_isbn(existing)
    title    = _prompt_str("Title    (e.g. Atomic Habits)")
    author   = _prompt_str("Author   (e.g. James Clear)", allow_digits=False)
    year     = _prompt_int("Year     (e.g. 2018)")
    narrator = _prompt_str("Narrator (e.g. James Clear)", allow_digits=False)
    duration = _prompt_int("Duration in minutes (e.g. 330)")
    try:
        inv.add_item(AudioBook(isbn, title, author, year, narrator, duration))
        print(f"\n  + '{title}' added.")
    except ValueError as exc:
        print(f"  ! {exc}")


def _remove(inv: Inventory) -> None:
    """Prompt for an ISBN and remove the item."""
    print("\n  -- Remove Item --")
    isbn = _prompt_isbn(label="ISBN to remove")
    try:
        item = inv.remove_item(isbn)
        print(f"\n  - '{item.title}' removed.")
    except ValueError as exc:
        print(f"  ! {exc}")


def _search(inv: Inventory) -> None:
    """Search by title, author, or ISBN and print matches."""
    print("\n  -- Search --")
    query   = input("  Query (title / author / ISBN): ").strip()
    results = inv.search(query)
    if not results:
        print("  No matches found.")
        return
    print(f"\n  {len(results)} result(s):\n")
    for item in results:
        print(f"  {item.item_type()}: {item.summary()}")


def _view_details(inv: Inventory) -> None:
    """Print the full detail block for one item."""
    print("\n  -- Item Details --")
    isbn = _prompt_isbn(label="ISBN to view")
    try:
        print("\n" + inv.get_item(isbn).format_details())
    except ValueError as exc:
        print(f"  ! {exc}")


def _borrow(inv: Inventory) -> None:
    """Borrow an item for a named member."""
    print("\n  -- Borrow Item --")
    isbn   = _prompt_isbn(label="ISBN to borrow")
    member = _prompt_str("Member name (e.g. Alice Mutoni)", allow_digits=False)
    try:
        item = inv.get_item(isbn)
        inv.borrow_item(isbn, member)
        print(f"\n  + '{item.title}' borrowed by {member}.")
    except ValueError as exc:
        print(f"  ! {exc}")


def _return(inv: Inventory) -> None:
    """Return a borrowed item."""
    print("\n  -- Return Item --")
    isbn = _prompt_isbn(label="ISBN to return")
    try:
        item     = inv.get_item(isbn)
        borrower = inv.return_item(isbn)
        print(f"\n  + '{item.title}' returned (was: {borrower}).")
    except ValueError as exc:
        print(f"  ! {exc}")


def _view_all(inv: Inventory) -> None:
    """List every item in the inventory."""
    items = inv.all_items()
    if not items:
        print("\n  Inventory is empty.")
        return
    print(f"\n  {len(items)} item(s):\n")
    for item in items:
        print(f"  {item.item_type()}: {item.summary()}")


def _show_stats(inv: Inventory) -> None:
    """Print inventory counts and availability."""
    s = inv.stats()
    print("\n  Inventory Statistics")
    print(f"  Total items    : {s['total']}")
    print(f"  Physical Books : {s['physical_books']}")
    print(f"  E-Books        : {s['ebooks']}")
    print(f"  Audio Books    : {s['audio_books']}")
    print(f"  Copies on shelf: {s['copies_on_shelf']}")
    print(f"  Audio on loan  : {s['audio_on_loan']}")


_MENU: dict[str, tuple[str, callable]] = {
    "1":  ("Add a Physical Book",  _add_physical),
    "2":  ("Add an E-Book",        _add_ebook),
    "3":  ("Add an Audio Book",    _add_audiobook),
    "4":  ("Remove an item",       _remove),
    "5":  ("Search items",         _search),
    "6":  ("View item details",    _view_details),
    "7":  ("Borrow an item",       _borrow),
    "8":  ("Return an item",       _return),
    "9":  ("View all items",       _view_all),
    "10": ("View inventory stats", _show_stats),
    "0":  ("Exit",                 None),
}


def run_library() -> None:
    """Run the interactive menu loop until the user exits."""
    inv = Inventory()
    print(format_header("LIBRARY INVENTORY SYSTEM"))

    while True:
        print("\n  " + divider(46, "-"))
        for key, (label, _) in _MENU.items():
            print(f"    [{key:>2}] {label}")
        print("  " + divider(46, "-"))

        choice = input("\n  Your choice: ").strip()

        if choice == "0":
            print("\n  Goodbye.")
            break
        elif choice in _MENU:
            _MENU[choice][1](inv)
        else:
            print("  ! Invalid choice.")


if __name__ == "__main__":
    run_library()
