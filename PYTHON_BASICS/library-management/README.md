# Library Management System

A **console-based Python application** to manage a library's books, authors, and borrowing records.
This project demonstrates **Python OOP principles**, **file I/O**, **data persistence**, and **basic library operations**.

---

## Features

### Book Management
- **Add Books** - Add new books with details (title, author, ISBN, category, year, copies)
- **List All Books** - View complete library inventory
- **Delete Books** - Remove books from the system

### Borrowing System
- **Borrow Books** - Check out books with automatic availability checking
- **Return Books** - Return borrowed books and update records
- **Track Copies** - Dynamically track available and borrowed copies
- **Borrow History** - View all borrowing records with dates

### Search & Filter
- **Search by**:
  - Title
  - Author
  - ISBN
  - Category
  - Publication year
- **Filter by**:
  - Available books only
  - Borrowed books only
  - Category
- **Overdue Detection** - Identify overdue borrowings (optional)

---

## Folder Structure

```
library-management/
│
├── main.py                 # Main program entry point
├── requirements.txt        # Python dependencies
├── data/                   # JSON files storing library data
│   ├── books.json          # Book inventory
│   ├── authors.json        # Author information
│   └── borrow.json         # Borrowing records
├── library/
│   ├── __init__.py
│   ├── resources.py        # LibraryResource & Book class
│   ├── author.py           # Author class
│   ├── borrow.py           # Borrow class
│   ├── file_io.py          # File read/write logic
│   └── utils.py            # Helper functions (search, filter, copies)
└── README.md               # Project documentation
```

---

## Installation

### 1. Clone the Project
```bash
git clone https://github.com/yourusername/library-management.git
cd library-management
```

### 2. Create a Virtual Environment
```bash
python -m venv env
```

### 3. Activate the Environment

**Windows (PowerShell):**
```powershell
.\env\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.\env\Scripts\activate
```

**Mac/Linux:**
```bash
source env/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Usage

### Running the Program

```bash
python main.py
```

### Main Menu

```
========================================
    LIBRARY MANAGEMENT SYSTEM
========================================

1. Add a book
2. List all books
3. Borrow a book
4. Return a book
5. List borrow records
6. Search a book
7. Filter records
8. Delete a book
9. Exit

Enter your choice (1-9):
```

### Operations Guide

#### Adding a Book
```
Enter your choice: 1

Enter book title: The Great Gatsby
Enter author name: F. Scott Fitzgerald
Enter ISBN: 978-0743273565
Enter category: Fiction
Enter publication year: 1925
Enter number of copies: 5

✔ Book "The Great Gatsby" added successfully!
```

#### Borrowing a Book
```
Enter your choice: 3

Enter ISBN of the book to borrow: 978-0743273565
Enter borrower name: John Doe

✔ Book borrowed successfully!
Available copies: 4
```

#### Searching Books
```
Enter your choice: 6

Search by:
1. Title
2. Author
3. ISBN
4. Category
5. Year

Enter choice: 1
Enter title: Gatsby

Found 1 book(s):
----------------------------------------
Title: The Great Gatsby
Author: F. Scott Fitzgerald
ISBN: 978-0743273565
Category: Fiction
Year: 1925
Available: 4 / 5 copies
----------------------------------------
```

#### Filtering Books
```
Enter your choice: 7

Filter by:
1. Available books only
2. Borrowed books only
3. By category

Enter choice: 1

Available Books:
----------------------------------------
[List of available books displayed]
----------------------------------------
```

---

## Data Persistence

### File Storage
All data is stored in JSON format in the `data/` folder:

- **books.json** - Stores book inventory
  ```json
  {
    "isbn": {
      "title": "Book Title",
      "author": "Author Name",
      "isbn": "978-XXXXXXXXX",
      "category": "Fiction",
      "year": 2024,
      "total_copies": 5,
      "available_copies": 3
    }
  }
  ```

- **authors.json** - Stores author information
  ```json
  {
    "author_id": {
      "name": "Author Name",
      "books": ["isbn1", "isbn2"]
    }
  }
  ```

- **borrow.json** - Stores borrowing records
  ```json
  {
    "borrow_id": {
      "isbn": "978-XXXXXXXXX",
      "borrower": "John Doe",
      "borrow_date": "2024-11-24",
      "return_date": null,
      "due_date": "2024-12-08"
    }
  }
  ```

### Data Integrity
- Data persists between program runs
- Automatic backup on critical operations (optional)
- Validation checks prevent data corruption

---

## Features in Detail

### Dynamic Copy Tracking
- System automatically tracks total and available copies
- Prevents borrowing when no copies are available
- Updates counts in real-time during borrow/return operations

### Overdue Detection
- Calculates days overdue based on due date
- Highlights overdue borrowings in red (if terminal supports colors)
- Sends reminders for overdue books (optional feature)

### Search Capabilities
- Case-insensitive search
- Partial matching for titles and authors
- Multiple filter criteria can be combined

---

## Technical Details

### OOP Structure
```
LibraryResource (Base Class)
    ├── Book
    ├── Author
    └── Borrow

FileIO (Utility Class)
    ├── read_json()
    ├── write_json()
    └── backup_data()

Utils (Helper Functions)
    ├── search_books()
    ├── filter_books()
    ├── check_availability()
    └── calculate_overdue()
```

### Key Classes

**Book Class**
```python
class Book(LibraryResource):
    def __init__(self, title, author, isbn, category, year, copies):
        # Book initialization

    def borrow(self):
        # Decrease available copies

    def return_book(self):
        # Increase available copies
```

**Borrow Class**
```python
class Borrow:
    def __init__(self, isbn, borrower, borrow_date, due_date):
        # Borrow record initialization

    def is_overdue(self):
        # Check if book is overdue
```

---

## Requirements

- **Python**: 3.11 or higher
- **Dependencies**: Listed in `requirements.txt`
  - No external dependencies required (uses Python standard library)
  - Optional: `colorama` for colored terminal output

---

## Contributing

We welcome contributions! Please follow these guidelines:

### Code Standards
- Follow Python 3.11+ standards
- Maintain OOP structure (LibraryResource → Book/Borrow/Author)
- Use `file_io.py` for all JSON read/write operations
- Add docstrings to all classes and functions
- Follow PEP 8 style guide

### Contribution Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

---

## Future Enhancements

- [ ] User authentication system
- [ ] Fine calculation for overdue books
- [ ] Email notifications for due dates
- [ ] Book reservation system
- [ ] Multi-library support
- [ ] Web interface using Flask/Django
- [ ] Database integration (SQLite/PostgreSQL)
- [ ] Book rating and review system
- [ ] Export reports to PDF/Excel
- [ ] Barcode scanning support
- [ ] Member management system

---

## Troubleshooting

### Common Issues

**Issue**: Data files not found
```
Solution: Ensure data/ folder exists with books.json, authors.json, and borrow.json
```

**Issue**: Permission denied when writing files
```
Solution: Check folder permissions or run with appropriate privileges
```

**Issue**: Invalid JSON format
```
Solution: Delete corrupted JSON file and restart (backup files recommended)
```

---

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

Manual testing checklist:
- [ ] Add book successfully
- [ ] Borrow book with available copies
- [ ] Prevent borrowing when no copies available
- [ ] Return book and update records
- [ ] Search functionality works correctly
- [ ] Filter displays correct results
- [ ] Data persists after program restart



## Acknowledgments

- Built with Python standard library
- Inspired by real-world library management systems
- Thanks to all contributors and testers

---

## Contact


**Email**: ishimwediane400@gmail.com

---

## Version History

- **v1.0.0** (2024-11-24)
  - Initial release
  - Basic CRUD operations
  - Search and filter functionality
  - JSON-based data persistence

---

## Video demo(Screen recording)
- https://drive.google.com/file/d/1Qh4kF7wqmGNKIUooH4Uy8rEXCsVAY0Uq/view?usp=sharing

**Happy Library Management!*
