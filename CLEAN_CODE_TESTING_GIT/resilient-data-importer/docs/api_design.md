# API Design Documentation

## Module: logging_config.py

### Function: `setup_logging`
- Configures Python logging for the entire application.
- Default level: `INFO`.
- Log format: timestamp, level, message.
- All modules use `logger = logging.getLogger(__name__)`.
- Logs: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

**Test Coverage**: Covered by `tests/test_logging.py`.

---

## Module: models.py

### Class: `User`
- Represents a system user.

**Attributes**:
- `user_id: int`
- `name: str`
- `email: str`

**Methods**:
- `to_dict()` – Convert to dictionary.
- `from_dict(data: dict)` – Create from dictionary.
- `__eq__()` – Compare two users.

---

## Module: user_manager.py

### Class: `UserManager`
- Manages users stored in CSV files.

**Methods**:
- `load_users()` – Load users from CSV.
- `save_users()` – Save users to CSV.
- `add_user(user: User)` – Add user to memory.
- `find_user(email: str)` – Retrieve user by email.

---

## Module: parser.py

### Class: `CSVParser`
- Parses CSV files into `User` objects.

**Methods**:
- `parse()` – Returns `List[User]`.
- Raises:
  - `FileNotFoundError`
  - `FileFormatError`

---

## Module: validator.py

### Class: `UserValidator`
- Validates user data.

**Methods**:
- `validate(user: User)` – Validates all fields.
- `validate_email(email: str)` – Checks email format.
- Raises `ValidationError` on invalid data.

---

## Module: storage.py

### Class: `UserRepository`
- Manages user storage in JSON.

**Methods**:
- `add_user(user: User)` – Raises `DuplicateUserError` or `DatabaseError`.
- `user_exists(user_id: int)` – Checks existence.

---

## Module: main.py

### Function: `main()`
- CLI entry point.
- Accepts `--file` and `--help`.
- Coordinates parsing, validation, storage.
- Logs all major steps.
- Handles errors gracefully.
