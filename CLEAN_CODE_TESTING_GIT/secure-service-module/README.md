# Secure Service Module

A backend Python authentication library built with **Test-Driven Development (TDD)**, **SOLID principles**, and **dependency injection**. It handles user registration, login, and password security — with no web framework or database required.

---

## How It Works

The library is built around three core ideas:

### 1. Interfaces (Abstractions)
Two abstract base classes define the contracts the system depends on:

- `UserRepository` — defines how users are stored and retrieved (`add`, `get_by_email`)
- `PasswordHasher` — defines how passwords are hashed and verified (`hash_password`, `verify_password`)

These are defined in `src/auth/interfaces.py`. The service never depends on a specific database or hashing library — only on these interfaces.

### 2. UserService (Core Logic)
`src/auth/service.py` contains the `UserService` class. It receives a `UserRepository` and a `PasswordHasher` via its constructor (dependency injection) and exposes two methods:

**`register_user(username, email, password) → User`**
1. Checks if the email already exists in the repository — raises `UserAlreadyExistsError` if it does
2. Validates the password is at least 8 characters — raises `InvalidPasswordError` if not
3. Hashes the password using the injected hasher
4. Creates a `User` object with a auto-generated UUID
5. Saves the user to the repository
6. Logs the event and returns the user

**`verify_user(email, password) → bool`**
1. Looks up the user by email — raises `UserNotFoundError` if not found
2. Verifies the plain password against the stored hash — raises `InvalidPasswordError` if wrong
3. Logs the outcome and returns `True` on success

### 3. Implementations (Concrete Classes)
Two ready-to-use implementations are provided in `src/auth/implementation/`:

- `InMemoryUserRepository` — stores users in a Python dictionary (for testing and demos)
- `BcryptPasswordHasher` — hashes and verifies passwords using the `bcrypt` library

### 4. Data Model
`src/auth/models.py` defines the `User` dataclass:

```
User
├── id            → auto-generated UUID string
├── username      → display name
├── email         → unique identifier
└── password_hash → bcrypt hash (plain password is never stored)
```

### 5. Exceptions
`src/auth/exceptions.py` defines three custom exceptions:

| Exception | When it's raised |
|---|---|
| `UserAlreadyExistsError` | Email already registered |
| `UserNotFoundError` | Email not found during login |
| `InvalidPasswordError` | Password too short or wrong on login |

---

## Project Structure

```
secure-service-module/
├── src/
│   └── auth/
│       ├── implementation/
│       │   ├── bcrypt_hasher.py   # bcrypt password hashing
│       │   └── memory_repo.py     # in-memory user storage
│       ├── exceptions.py          # custom exceptions
│       ├── interfaces.py          # abstract base classes
│       ├── models.py              # User dataclass
│       └── service.py             # core business logic
├── tests/
│   ├── test_implementation.py     # end-to-end test with real implementations
│   ├── test_interface.py          # interface contract coverage
│   ├── test_login.py              # login flow tests
│   ├── test_registration.py       # registration flow tests
│   ├── test_security.py           # password security tests
│   └── user_registration.py       # additional registration scenarios
├── docs/
│   ├── architecture.md
│   ├── modules.md
│   ├── testing.md
│   └── usage.md
├── pyproject.toml
├── requirements.txt
└── .pre-commit-config.yaml
```

---

## Requirements

- Python 3.11+
- pip or poetry

---

## Setup and Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/Ndaziramiyep/AmaliTech_Python_Backend_Labs.git
cd AmaliTech_Python_Backend_Labs/CLEAN_CODE_TESTING_GIT/secure-service-module
```

### Step 2 — Create and activate a virtual environment

```bash
# Create
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

---

## How to Run the Tests

All tests live in the `tests/` folder and use `pytest`.

### Run all tests

```bash
pytest tests/
```

### Run with coverage report

```bash
pytest --cov=src/auth tests/
```

### Run a specific test file

```bash
pytest tests/test_registration.py
pytest tests/test_login.py
pytest tests/test_security.py
```

### Run a specific test by name

```bash
pytest tests/test_registration.py::test_register_user_success
```

> Tests use `pytest-mock` to mock the repository and hasher, so no real database or bcrypt calls are made in unit tests. The only test that uses real implementations is `test_implementation.py::test_end_to_end_registration_and_login`.

---

## Using the Library in Your Code

```python
from src.auth.service import UserService
from src.auth.implementation.memory_repo import InMemoryUserRepository
from src.auth.implementation.bcrypt_hasher import BcryptPasswordHasher

# Wire up dependencies
repo = InMemoryUserRepository()
hasher = BcryptPasswordHasher()
service = UserService(user_repository=repo, password_hasher=hasher)

# Register a new user
user = service.register_user("Diane", "diane@example.com", "SecurePass123")
print(user.id)        # auto-generated UUID
print(user.username)  # Diane
print(user.email)     # diane@example.com

# Login / verify credentials
result = service.verify_user("diane@example.com", "SecurePass123")
print(result)  # True
```

### Handling exceptions

```python
from src.auth.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    InvalidPasswordError,
)

try:
    service.register_user("Diane", "diane@example.com", "SecurePass123")
except UserAlreadyExistsError:
    print("Email already registered.")
except InvalidPasswordError:
    print("Password must be at least 8 characters.")

try:
    service.verify_user("diane@example.com", "WrongPassword")
except UserNotFoundError:
    print("No account found with that email.")
except InvalidPasswordError:
    print("Incorrect password.")
```

---

## Extending the Library

Because the service depends on interfaces, not concrete classes, you can swap implementations without touching any business logic.

**Example: plug in a real database repository**

```python
from src.auth.interfaces import UserRepository
from src.auth.models import User

class PostgresUserRepository(UserRepository):
    def get_by_email(self, email: str):
        # query your database here
        ...

    def add(self, user: User) -> None:
        # insert into your database here
        ...
```

Then pass it to `UserService` the same way:

```python
service = UserService(user_repository=PostgresUserRepository(), password_hasher=BcryptPasswordHasher())
```

---

## Git Workflow

Branches follow a feature-branch workflow:

```
main          ← stable, production-ready
developer     ← integration branch
feature/*     ← individual feature branches
```

Commit message convention follows the TDD cycle:

```
test: add failing test for duplicate email
feat: raise UserAlreadyExistsError on duplicate registration
refactor: extract password validation into helper
```

Pre-commit hooks enforce `black` (formatting), `ruff` (linting), and `mypy` (type checking) before every commit.

---

## Features

- Secure password hashing with bcrypt (plain passwords are never stored)
- Duplicate email prevention on registration
- Custom exceptions for all failure cases
- Full unit test coverage with mocks
- End-to-end integration test with real implementations
- Structured logging on registration and login events
- Type-annotated codebase with mypy support
- Easily extensible via interface-based design
