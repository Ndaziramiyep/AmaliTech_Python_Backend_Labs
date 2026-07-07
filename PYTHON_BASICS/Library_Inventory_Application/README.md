# Library Inventory Application

A Python CLI application for managing a library's book inventory. Supports
adding, removing, searching, borrowing, and returning three item types —
Physical Books, E-Books, and Audio Books. Built with OOP, abstract base
classes, and property decorators for input validation.

---

## File & Folder Structure

```
Library_Inventory_Application/
├── main.py        # CLI entry point — menu, input helpers, output handlers
├── book.py        # Abstract LibraryItem base class + subclasses
├── inventory.py   # Inventory management logic
└── utils.py       # Shared formatting helpers
```

---

## Running the Application

```bash
python main.py
```

---

## Key Design Decisions

- `LibraryItem` is an ABC — `item_type()`, `summary()`, `format_details()`,
  and `is_borrowable` are all abstract, enforcing the contract at instantiation.
- `is_borrowable` is a property on each subclass rather than an `isinstance`
  check in `inventory.py`, keeping the inventory module decoupled from
  specific subclass types (open/closed principle).
- `Inventory` stores items in a `dict[isbn -> LibraryItem]` for O(1) lookups.
- Borrow/return rules differ per type: `PhysicalBook` tracks copy counts,
  `AudioBook` tracks a single borrower, `EBook` rejects borrow entirely.
- `_MENU` eliminates if/elif chains; adding a new action is a single-line change.
