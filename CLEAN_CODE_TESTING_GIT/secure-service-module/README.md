# Secure Service Module with TDD

> **Assessment:** Clean Code, Testing & Git | **Complexity:** Medium | **Estimated Time:** 6-10 hours

## Overview

A secure, standalone **User Authentication Service Module** — a reusable
library responsible for user registration and credential verification. It
handles password hashing, enforces a password policy, and prevents
duplicate registrations.

The core logic (`src/auth/`) is a plain, dependency-free Python library
built strictly via TDD with 100% test coverage. `main.py` is a thin
command-line entry point on top of it — run `python main.py` to register
and verify users interactively. This is **not** a web application; the CLI
is purely a convenient way to exercise the library from the keyboard.

---

## Project Objectives

- Build a secure, reusable module following a strict TDD process
- Apply SOLID principles to create a decoupled and testable service layer
- Achieve 100% test coverage on the core business logic
- Use modern Python features like type hints and context managers effectively
- Follow a standard Git workflow with code reviews and automated quality checks

---

## Project Structure

```
secure-service-module/
├── src/
│   └── auth/                       # Core library -- dependency-free, 100% covered
│       ├── implementation/
│       │   ├── __init__.py
│       │   ├── bcrypt_hasher.py     # BcryptPasswordHasher
│       │   └── memory_repo.py       # InMemoryUserRepository
│       ├── __init__.py
│       ├── exceptions.py            # Custom exceptions
│       ├── interfaces.py            # Abstract base classes
│       ├── models.py                # User dataclass
│       └── service.py               # UserService (core logic)
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_interfaces.py
│   ├── test_registration.py
│   ├── test_login.py
│   ├── test_validation.py
│   ├── test_timing.py
│   ├── test_implementations.py
│   ├── test_end_to_end.py
│   └── test_main.py
├── main.py                         # CLI entry point: `python main.py`
├── pyproject.toml
├── requirements.txt
├── .gitignore
├── .pre-commit-config.yaml
└── README.md
```

---

## Architecture & SOLID Design

`UserService` is the core entry point. It depends on two abstractions
defined in `interfaces.py`:

- `UserRepository` — abstract interface for user storage (`get_by_email`, `add`)
- `PasswordHasher` — abstract interface for hashing and verification
  (`hash_password`, `verify_password`)

Concrete implementations are injected at construction time:

| Interface        | Concrete Implementation  | Location                                   |
|-------------------|---------------------------|---------------------------------------------|
| `UserRepository`  | `InMemoryUserRepository`  | `src/auth/implementation/memory_repo.py`    |
| `PasswordHasher`  | `BcryptPasswordHasher`    | `src/auth/implementation/bcrypt_hasher.py`  |

This dependency injection pattern means `UserService` can be tested in
complete isolation using mocks — no real database or hashing needed in unit
tests (see `tests/test_registration.py` and `tests/test_login.py`, which
mock both dependencies with `pytest-mock`).

```
UserService
    ├── depends on → UserRepository (ABC)
    │                   └── implemented by → InMemoryUserRepository
    └── depends on → PasswordHasher (ABC)
                        └── implemented by → BcryptPasswordHasher

main.py
    └── depends on → UserService (constructed with the concrete
                      implementations above)
```

**Why this matters:** swapping `InMemoryUserRepository` for a real
database-backed repository — or bcrypt for another hashing algorithm —
requires touching only the concrete implementation and the one line that
constructs `UserService`. `UserService` itself, and every test that mocks
its dependencies, is completely unaffected.

### Modern Python features

- **Type hints** throughout the public API.
- **Dataclasses** for the `User` model.
- **Context manager**: `_timed_operation` (in `service.py`) is a
  `@contextlib.contextmanager`-based timer wrapping `register_user` and
  `verify_user`. It logs a structured `DEBUG` start/finish event with the
  operation's duration in milliseconds, whether the operation succeeds or
  raises — a `try/finally` inside the context manager guarantees the
  "finished" log always fires.

---

## Error Handling & Security

- **Custom exceptions** (`src/auth/exceptions.py`): `UserAlreadyExistsError`,
  `UserNotFoundError`, `InvalidPasswordError`.
- **Input validation**: blank usernames and malformed emails raise a plain
  `ValueError` before any repository lookup happens (fail fast).
- **Password hashing**: `BcryptPasswordHasher` uses bcrypt with a fresh
  salt per call — plain-text passwords are never stored.
- **Password policy**: registration requires a password of at least 8
  characters (`InvalidPasswordError` otherwise).
- **Structured logging**: registration and login attempts (success and
  failure) are logged at `INFO` with `extra={"email": ...}`.

---

## Requirements

- Python 3.11+
- Dependencies listed in `requirements.txt`:

```
bcrypt==5.0.0
pluggy==1.6.0
pytest==9.1.1
pytest-mock==3.15.1
pytest-cov==7.1.0
coverage==7.15.2
black==25.12.0
ruff==0.14.14
mypy==1.20.2
```

---

## Setup & Installation

```bash
git clone <repository-url>
cd secure-service-module

python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux

pip install -r requirements.txt
```

---

## Running It

```bash
python main.py
```

You'll get an interactive menu:

```
Secure Service Module -- CLI
(Data is stored in memory only and is lost when this script exits.)

1) Register  2) Login  3) Exit
>
```

Choosing **1** prompts for a username, email, and password (hidden as you
type) and registers you; choosing **2** prompts for email and password and
verifies them against a previously registered user. Validation and auth
errors are caught and printed clearly rather than crashing, e.g.:

```
--- Register a new user ---
Username: Patrick
Email: patrick@gmail.com
Password:
Registered 'Patrick' (patrick@gmail.com), id=<uuid>

1) Register  2) Login  3) Exit
> 2

--- Verify login ---
Email: patrick@gmail.com
Password:
Login successful.
```

Data lives only in memory for the lifetime of the process — restarting
`main.py` starts with an empty user store.

---

## Running the Tests

Coverage runs automatically (configured in `pyproject.toml`):

```bash
pytest
```

**Expected output:**

```
================================ test session starts =================================
collected 44 items

tests/test_end_to_end.py .                                                     [  2%]
tests/test_implementations.py .....                                           [ 13%]
tests/test_interfaces.py ....                                                 [ 22%]
tests/test_login.py ......                                                    [ 36%]
tests/test_main.py ......                                                     [ 50%]
tests/test_models.py ..                                                       [ 54%]
tests/test_registration.py .....                                              [ 65%]
tests/test_timing.py ..                                                       [ 70%]
tests/test_validation.py .............                                       [100%]

=================================== tests coverage ====================================
Name                                       Stmts   Miss  Cover   Missing
------------------------------------------------------------------------
src\auth\__init__.py                           0      0   100%
src\auth\exceptions.py                         3      0   100%
src\auth\implementation\__init__.py            0      0   100%
src\auth\implementation\bcrypt_hasher.py       8      0   100%
src\auth\implementation\memory_repo.py        10      0   100%
src\auth\interfaces.py                        13      0   100%
src\auth\models.py                             8      0   100%
src\auth\service.py                           59      0   100%
------------------------------------------------------------------------
TOTAL                                        101      0   100%
=========================== 44 passed in X.XXs ============================
```

Run a specific file: `pytest tests/test_registration.py -v`

---

## Using the Library Directly (no CLI)

```python
from src.auth.service import UserService
from src.auth.implementation.memory_repo import InMemoryUserRepository
from src.auth.implementation.bcrypt_hasher import BcryptPasswordHasher

service = UserService(InMemoryUserRepository(), BcryptPasswordHasher())

user = service.register_user("Patrick", "patrick@gmail.com", "SecurePass1")
print(f"Registered: {user.username}, ID: {user.id}")

success = service.verify_user("patrick@gmail.com", "SecurePass1")
print("Login success:", success)
```

### Exception handling

```python
from src.auth.exceptions import UserAlreadyExistsError, UserNotFoundError, InvalidPasswordError

try:
    service.register_user("Patrick", "patrick@gmail.com", "SecurePass1")
except UserAlreadyExistsError as e:
    print(e)  # User with email 'patrick@gmail.com' already exists.

try:
    service.verify_user("patrick@gmail.com", "WrongPassword")
except InvalidPasswordError as e:
    print(e)  # Invalid password.

try:
    service.verify_user("unknown@gmail.com", "AnyPassword")
except UserNotFoundError as e:
    print(e)  # No user found with email 'unknown@gmail.com'.

try:
    service.register_user("Patrick", "not-an-email", "SecurePass1")
except ValueError as e:
    print(e)  # 'not-an-email' is not a valid email address.
```

---

## Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Runs Black, ruff, and mypy (on `src/`, `tests/`, and `main.py`) on every
commit; the full pytest suite runs on `pre-push`.

---

## Git Workflow

- **Feature branches**: `feature/registration`, `feature/login`
- **Commit messages** reflect the TDD cycle: `test: ...`, `feat: ...`, `refactor: ...`
- All new code is introduced via Pull Requests with a simulated code review

---

## Grading Criteria

| Criteria | Points | Description |
|----------|--------|-------------|
| Feature Implementation | 20 | Authentication module correctly handles registration and login securely |
| Code Quality & Structure | 15 | Flawless execution of SOLID principles, especially dependency injection |
| Best Practices & Patterns | 15 | Strict TDD process followed; strong password hashing and logging |
| Testing & Validation | 20 | 100% test coverage on core logic; excellent use of mocking and pytest |
| Documentation & Comments | 10 | Professional-level docstrings and a clear architectural overview in README |
| Final Integration & Output Quality | 20 | The module is a high-quality, reusable, and thoroughly tested library |
| **Total** | **100** | |

---

## Features

- Secure password hashing with bcrypt
- In-memory user repository (swappable for a real database)
- Custom exception handling + input validation
- 100% test coverage on core logic (`src/auth`)
- Structured logging, including operation timing via a context manager
- Simple CLI (`python main.py`) for interactively trying registration/login
- Type hints validated with mypy; formatting/linting via Black and ruff
