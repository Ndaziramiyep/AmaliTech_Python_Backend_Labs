"""inventory.py — Inventory class managing the full library collection."""

from book import LibraryItem, PhysicalBook, EBook, AudioBook


class Inventory:
    """Library collection keyed by ISBN for O(1) access."""

    def __init__(self) -> None:
        """Initialise an empty inventory."""
        self._items: dict[str, LibraryItem] = {}

    def add_item(self, item: LibraryItem) -> None:
        """Add item; raise ValueError on duplicate ISBN."""
        if item.isbn in self._items:
            raise ValueError(f"An item with ISBN '{item.isbn}' is already in the inventory.")
        self._items[item.isbn] = item

    def remove_item(self, isbn: str) -> LibraryItem:
        """Remove and return item; raise ValueError if on loan or not found."""
        item = self.get_item(isbn)
        if not item.is_available:
            raise ValueError(f"Cannot remove '{item.title}': it is currently on loan and must be returned first.")
        del self._items[isbn]
        return item

    def get_item(self, isbn: str) -> LibraryItem:
        """Return item by ISBN; raise ValueError if not found."""
        item = self._items.get(isbn)
        if item is None:
            raise ValueError(f"No item with ISBN '{isbn}' was found in the inventory.")
        return item

    def all_items(self) -> list[LibraryItem]:
        """Return all items in insertion order."""
        return list(self._items.values())

    def search(self, query: str) -> list[LibraryItem]:
        """Return items matching query in title, author, or ISBN (case-insensitive)."""
        if not query.strip():
            raise ValueError("Search query cannot be empty.")
        q = query.lower()
        return [
            item for item in self._items.values()
            if q in item.title.lower()
            or q in item.author.lower()
            or q in item.isbn.lower()
        ]

    def borrow_item(self, isbn: str, member_name: str) -> None:
        """Delegate borrow to the item; raise ValueError if not possible."""
        self.get_item(isbn).do_borrow(member_name)

    def return_item(self, isbn: str) -> str:
        """Delegate return to the item; return borrower name."""
        return self.get_item(isbn).do_return()

    def stats(self) -> dict[str, int]:
        """Return inventory counts and availability by item type."""
        physical   = [i for i in self._items.values() if isinstance(i, PhysicalBook)]
        ebooks     = [i for i in self._items.values() if isinstance(i, EBook)]
        audiobooks = [i for i in self._items.values() if isinstance(i, AudioBook)]
        return {
            "total":           len(self._items),
            "physical_books":  len(physical),
            "ebooks":          len(ebooks),
            "audio_books":     len(audiobooks),
            "copies_on_shelf": sum(b.copies_available for b in physical),
            "audio_on_loan":   sum(1 for a in audiobooks if not a.is_available),
        }
