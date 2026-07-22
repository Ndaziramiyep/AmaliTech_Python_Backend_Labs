# Lab 3: Secure Service Module with TDD

> **Assessment:** Clean Code, Testing & Git | **Complexity:** Medium | **Estimated Time:** 6–10 hours

## Overview

Lab 3 is a reusable Python authentication library that provides:

- User registration and credential verification
- Password hashing with bcrypt
- Duplicate user prevention
- Full test coverage using pytest and mocks
- Strict TDD workflow
- SOLID architecture and dependency injection

> ⚠️ **Note**: This is **not** a web application or CLI. It's a backend library.

---

## Project Objectives

By completing this lab, learners should be able to:

- Build a secure, reusable module following a strict TDD process
- Apply SOLID principles to create a decoupled and testable service layer
- Achieve 100% test coverage on the core business logic
- Use modern Python features like type hints and context managers effectively
- Follow a standard Git workflow with code reviews and automated quality checks

---

## Project Structure

```
secure-service-module/
├── src/auth/
│   ├── implementation/
│   │   ├── __init__.py
│   │   ├── bcrypt_hasher.py     # BcryptPasswordHasher
│   │   └── memory_repo.py       # InMemoryUserRepository
│   ├── __init__.py
│   ├── exceptions.py            # Custom exceptions
│   ├── interfaces.py            # Abstract base classes
│   ├── models.py                # User dataclass
│   └── service.py               # UserService (core logic)
├── tests/
│   ├── __init__.py
│   ├── test_implementation.py   # End-to-end test
│   ├── test_interface.py        # Interface coverage
│   ├── test_login.py            # Login tests
│   ├── test_registration.py     # Registration tests
│   └── test_security.py        # Password security tests
├── docs/
│   ├── architecture.md
│   ├── modules.md
│   ├── testing.md
│   └── usage.md
├── pyproject.toml
├── requirements.txt
├── .gitignore
├── .pre-commit-config.yaml
└── README.md
```

---

## Architecture & SOLID Design

`UserService` is the core entry point. It depends on two abstractions defined in `interfaces.py`:

- `UserRepository` — abstract interface for user storage (`get_by_email`, `add`)
- `PasswordHasher` — abstract interface for hashing and verification (`hash_password`, `verify_password`)

Concrete implementations are injected at runtime:

| Interface        | Concrete Implementation      | Location                              |
|------------------|------------------------------|---------------------------------------|
| `UserRepository` | `InMemoryUserRepository`     | `src/auth/implementation/memory_repo.py` |
| `PasswordHasher` | `BcryptPasswordHasher`       | `src/auth/implementation/bcrypt_hasher.py` |

This dependency injection pattern means `UserService` can be tested in complete isolation using mocks — no real database or hashing needed in unit tests.

```
UserService
    ├── depends on → UserRepository (ABC)
    │                   └── implemented by → InMemoryUserRepository
    └── depends on → PasswordHasher (ABC)
                        └── implemented by → BcryptPasswordHasher
```

---

## Documentation

Detailed documentation is available in the `docs/` folder:

- **[ARCHITECTURE](docs/architecture.md)** – Class diagrams, dependency graph, architecture principles
- **[MODULES](docs/modules.md)** – Description of modules, classes, and methods
- **[TESTING](docs/testing.md)** – Testing strategy, TDD workflow, example tests
- **[USAGE](docs/usage.md)** – Usage examples, exception handling, optional logging

---

## Requirements

- Python 3.11+
- Dependencies listed in `requirements.txt`:

```
bcrypt==4.0.1
coverage==7.0.0
pluggy==1.6.0
pytest==9.0.1
pytest-mock==3.15.1
```

- `pytest-cov` is required for coverage reports (not in `requirements.txt`):

```bash
pip install pytest-cov
```

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd secure-service-module
```

### 2. Create and activate a virtual environment

```bash
# Create
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

**Expected output (Windows):**
```
(venv) C:\...\secure-service-module>
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install pytest-cov
```

**Expected output:**
```
Successfully installed bcrypt-4.0.1 colorama-0.4.6 coverage-7.0.0 iniconfig-2.3.0 packaging-26.2 pluggy-1.6.0 pygments-2.20.0 pytest-9.0.1 pytest-mock-3.15.1
Successfully installed pytest-cov-7.1.0
```

---

## Running the Tests

### Run all tests

```bash
pytest tests/
```

**Expected output:**
```
========================= test session starts ==========================
platform win32 -- Python 3.14.5, pytest-9.0.1, pluggy-1.6.0
rootdir: C:\...\secure-service-module
configfile: pyproject.toml
plugins: mock-3.15.1
collected 16 items

tests/test_implementation.py .                                   [  6%]
tests/test_interface.py .                                        [ 12%]
tests/test_login.py .....                                        [ 43%]
tests/test_registration.py .....                                 [ 75%]
tests/test_security.py ....                                      [100%]

========================== 16 passed in X.XXs ==========================
```

### Run tests with coverage report
# Readme.md
```bash
pytest --cov=src/auth tests/
```

**Expected output:**
```
========================= test session starts ==========================
platform win32 -- Python 3.14.5, pytest-9.0.1, pluggy-1.6.0
rootdir: C:\...\secure-service-module
configfile: pyproject.toml
plugins: cov-7.1.0, mock-3.15.1
collected 16 items

tests/test_implementation.py .                                   [  6%]
tests/test_interface.py .                                        [ 12%]
tests/test_login.py .....                                        [ 43%]
tests/test_registration.py .....                                 [ 75%]
tests/test_security.py ....                                      [100%]

============================== tests coverage ==============================
___________ coverage: platform win32, python 3.14.5-final-0 _______________

Name                                       Stmts   Miss  Cover
--------------------------------------------------------------
src/auth/__init__.py                           0      0   100%
src/auth/exceptions.py                         3      0   100%
src/auth/implementation/__init__.py            0      0   100%
src/auth/implementation/bcrypt_hasher.py       8      0   100%
src/auth/implementation/memory_repo.py        10      0   100%
src/auth/interfaces.py                        13      0   100%
src/auth/models.py                             8      0   100%
src/auth/service.py                           31      0   100%
--------------------------------------------------------------
TOTAL                                         73      0   100%

========================== 16 passed in X.XXs ==========================
```

### Run a specific test file

```bash
pytest tests/test_registration.py -v
```

**Expected output:**
```
========================= test session starts ==========================
platform win32 -- Python 3.14.5, pytest-9.0.1, pluggy-1.6.0
rootdir: C:\...\secure-service-module
configfile: pyproject.toml
plugins: mock-3.15.1
collected 5 items

tests/test_registration.py::test_register_user_success PASSED          [ 20%]
tests/test_registration.py::test_register_user_duplicate PASSED        [ 40%]
tests/test_registration.py::test_register_user_password_too_short PASSED [ 60%]
tests/test_registration.py::test_register_calls_repository_add_once PASSED [ 80%]
tests/test_registration.py::test_register_logs_event PASSED            [100%]

========================== 5 passed in X.XXs ==========================
```

---

## Using the Library

### Basic usage example

```python
from src.auth.service import UserService
from src.auth.implementation.memory_repo import InMemoryUserRepository
from src.auth.implementation.bcrypt_hasher import BcryptPasswordHasher

repo = InMemoryUserRepository()
hasher = BcryptPasswordHasher()
service = UserService(user_repository=repo, password_hasher=hasher)

# Register a user
user = service.register_user("Diane", "diane@example.com", "SecurePass123")
print(f"Registered: {user.username}, ID: {user.id}")

# Verify credentials
success = service.verify_user("diane@example.com", "SecurePass123")
print("Login success:", success)
```

**Expected output:**
```
Registered: Diane, ID: <uuid>
Login success: True
```

### Exception handling

```python
from src.auth.exceptions import UserAlreadyExistsError, UserNotFoundError, InvalidPasswordError

# Duplicate registration
try:
    service.register_user("Diane", "diane@example.com", "SecurePass123")
except UserAlreadyExistsError as e:
    print(e)
# Output: User with email 'diane@example.com' already exists.

# Wrong password
try:
    service.verify_user("diane@example.com", "WrongPassword")
except InvalidPasswordError as e:
    print(e)
# Output: Invalid password.

# User not found
try:
    service.verify_user("unknown@example.com", "AnyPassword")
except UserNotFoundError as e:
    print(e)
# Output: No user found with email 'unknown@example.com'.

# Password too short (< 8 characters)
try:
    service.register_user("Diane", "diane2@example.com", "short")
except InvalidPasswordError as e:
    print(e)
# Output: Password must be at least 8 characters.
```

---

## Pre-commit Hooks

Install and run pre-commit hooks (Black, ruff, mypy):

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

**Expected output:**
```
black....................................................................Passed
ruff.....................................................................Passed
mypy.....................................................................Passed
```

---

## Git Workflow

- **Feature branches**: `feature/registration`, `feature/login`
- **Commit messages** reflect TDD cycle:
  ```
  test: add failing test
  feat: implement feature
  refactor: clean code
  ```
- All new code is introduced via Pull Requests with a simulated code review

---

## Development Milestones

| Day | Focus | Tasks |
|-----|-------|-------|
| Day 1 | TDD Setup & Registration Logic | Set up project, testing tools, and architectural interfaces (`UserRepository`, `PasswordHasher`); write first failing test for user registration; implement registration logic including password hashing; write tests for `UserAlreadyExistsError` |
| Day 2 | Login Logic & Exception Handling | Write failing tests for the login/credential verification process; implement password verification logic; write tests for all failure cases; integrate structured logging for all auth events |
| Day 3 | Refinement & Achieving Full Coverage | Identify untested branches or statements; write tests to bring core service logic to 100% coverage; refactor for clarity; conduct code review on a feature PR |
| Day 4 | Documentation & Finalization | Write comprehensive Google-style docstrings for the entire public API; create README.md explaining architecture and usage; perform final check with all quality tools (mypy, ruff, etc.) |

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

✅ Secure password hashing with bcrypt
✅ In-memory user repository (extensible to database)
✅ Custom exception handling
✅ 100% test coverage on core logic
✅ Type hints with mypy validation
✅ Code formatting with Black and ruff
