"""
inventory.py
Manages the library's collection of items.

Provides add, remove, search, borrow, return, and statistics operations.
All items are stored in a dict keyed by ISBN for O(1) access. Borrow and
return logic is fully delegated to each item's own do_borrow() / do_return()
methods, keeping this module decoupled from item-type internals.
"""

from book import LibraryItem, PhysicalBook, EBook, AudioBook


class Inventory:
    """Manages the full library collection keyed by ISBN."""

    def __init__(self) -> None:
        self._items: dict[str, LibraryItem] = {}

    def add_item(self, item: LibraryItem) -> None:
        """Add a new item to the inventory.

        Args:
            item: Any concrete LibraryItem subclass instance.

        Raises:
            ValueError: If an item with the same ISBN already exists.
        """
        if item.isbn in self._items:
            raise ValueError(f"ISBN '{item.isbn}' already exists.")
        self._items[item.isbn] = item

    def remove_item(self, isbn: str) -> LibraryItem:
        """Remove and return the item with the given ISBN.

        Args:
            isbn: ISBN of the item to remove.

        Returns:
            The removed LibraryItem instance.

        Raises:
            ValueError: If the item is not found or is currently on loan.
        """
        item = self.get_item(isbn)
        if not item.is_available:
            raise ValueError(f"Cannot remove '{item.title}': it is currently on loan.")
        del self._items[isbn]
        return item

    def get_item(self, isbn: str) -> LibraryItem:
        """Return the item with the given ISBN.

        Args:
            isbn: Exact ISBN string to look up.

        Raises:
            ValueError: If no item with that ISBN exists.
        """
        item = self._items.get(isbn)
        if item is None:
            raise ValueError(f"No item found with ISBN '{isbn}'.")
        return item

    def all_items(self) -> list[LibraryItem]:
        """Return all items in insertion order."""
        return list(self._items.values())

    def search(self, query: str) -> list[LibraryItem]:
        """Return items whose title, author, or ISBN contains query.

        The search is case-insensitive and matches any substring.

        Args:
            query: Search string.

        Returns:
            List of matching LibraryItem instances; empty list if none found.
        """
        q = query.lower()
        return [
            item for item in self._items.values()
            if q in item.title.lower()
            or q in item.author.lower()
            or q in item.isbn.lower()
        ]

    def borrow_item(self, isbn: str, member_name: str) -> None:
        """Borrow an item on behalf of a library member.

        Delegates all borrow rules and state changes to the item itself.

        Args:
            isbn:        ISBN of the item to borrow.
            member_name: Name of the borrowing member.

        Raises:
            ValueError: Propagated from the item's do_borrow() method.
        """
        self.get_item(isbn).do_borrow(member_name)

    def return_item(self, isbn: str) -> str:
        """Return a borrowed item.

        Delegates all return rules and state changes to the item itself.

        Args:
            isbn: ISBN of the item being returned.

        Returns:
            Name of the member who had borrowed the item.

        Raises:
            ValueError: Propagated from the item's do_return() method.
        """
        return self.get_item(isbn).do_return()

    def stats(self) -> dict[str, int]:
        """Return a summary of the inventory by item type and availability.

        Uses a single pass over all items to build per-type lists, then
        derives counts and availability figures from those lists.

        Returns:
            Dict with keys: total, physical_books, ebooks, audio_books,
            copies_on_shelf, audio_on_loan.
        """
        # Single-pass categorisation using list comprehensions
        physical   = [i for i in self._items.values() if isinstance(i, PhysicalBook)]
        ebooks     = [i for i in self._items.values() if isinstance(i, EBook)]
        audiobooks = [i for i in self._items.values() if isinstance(i, AudioBook)]

        return {
            "total":          len(self._items),
            "physical_books": len(physical),
            "ebooks":         len(ebooks),
            "audio_books":    len(audiobooks),
            "copies_on_shelf": sum(b.copies_available for b in physical),
            "audio_on_loan":  sum(1 for a in audiobooks if not a.is_available),
        }
