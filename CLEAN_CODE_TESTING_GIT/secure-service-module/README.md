# Secure Service Module

A secure, standalone **User Authentication Service** — a reusable,
framework-free Python library for user registration and credential
verification. It hashes passwords with bcrypt, enforces a password policy,
prevents duplicate registrations, and validates input up front.

The core logic (`src/auth/`) has zero dependencies beyond bcrypt and 100%
test coverage. `main.py` is a thin CLI on top of it — run `python main.py`
to register and verify users interactively. Data lives in memory only, for
the lifetime of the process. The CLI is a convenience wrapper for
exercising the library; it is not a web application.

## Contents

- [Highlights](#highlights)
- [Project Structure](#project-structure)
- [Architecture & SOLID Design](#architecture--solid-design)
- [Error Handling & Security](#error-handling--security)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Testing](#testing)
- [Development](#development)

---

## Highlights

- **Secure by default** — bcrypt password hashing with a fresh salt per
  call; plain-text passwords are never stored or logged.
- **SOLID, dependency-injected design** — `UserService` depends only on the
  `UserRepository` and `PasswordHasher` abstractions, never on a concrete
  implementation.
- **100% test coverage** on `src/auth`, built TDD-first, with `pytest-mock`
  isolating unit tests and a real end-to-end test proving the pieces work
  together.
- **Swappable storage** — `UserService` depends only on the `UserRepository`
  abstraction, so a new backend (SQL, a real database, etc.) can be added
  with no changes to `UserService` or its tests.
- **Enforced password strength** — registration rejects any password that
  isn't at least 8 characters with an uppercase letter, a lowercase letter,
  a digit, and a special character.
- **Fully typed and lint-clean** — `mypy --strict`-friendly type hints
  throughout, enforced by `ruff`, `black`, and `mypy` as pre-commit hooks.

---

## Project Structure

```text
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

- `UserRepository` — abstract interface for user storage (`get_user_by_email`, `add_user`)
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

```text
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

Modern Python features used throughout: type hints on the full public API,
`dataclasses` for the `User` model, and `abc.ABC` to define the swappable
interfaces above.

---

## Error Handling & Security

- **Custom exceptions** (`src/auth/exceptions.py`): `UserAlreadyExistsError`,
  `UserNotFoundError`, `WeakPasswordError`, `InvalidPasswordError`.
- **Input validation**: blank usernames and malformed emails raise a plain
  `ValueError` before any repository lookup happens (fail fast).
- **Password hashing**: `BcryptPasswordHasher` uses bcrypt with a fresh
  salt per call — plain-text passwords are never stored.
- **Strong password policy**: registration requires at least 8 characters,
  including an uppercase letter, a lowercase letter, a digit, and a special
  character (`WeakPasswordError` otherwise). A separate `InvalidPasswordError`
  is raised at login when a password doesn't match the stored hash — the
  two failure modes are never confused.
- **Structured logging**: registration and login attempts (success and
  failure) are logged at `INFO` with `extra={"email": ...}` — passwords are
  never logged.

---

## Getting Started

**Requirements:** Python 3.11+. All dependencies are pinned in
`requirements.txt` (bcrypt for hashing; pytest/pytest-mock/pytest-cov for
testing; black/ruff/mypy for quality gates).

```bash
git clone <repository-url>
cd secure-service-module

python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux

pip install -r requirements.txt
```

---

## Usage

### Running the CLI

```bash
python main.py
```

You'll get an interactive menu:

```text
Secure Service Module -- CLI
(Data is stored in memory only and is lost when this script exits.)

1) Register  2) Login  3) Exit
>
```

Choosing **1** prompts for a username, email, and password (hidden as you
type) and registers you; choosing **2** prompts for email and password and
verifies them against a previously registered user. Validation and auth
errors are caught and printed clearly rather than crashing, e.g.:

```text
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

### Using the library directly (no CLI)

```python
from src.auth.service import UserService
from src.auth.implementation.memory_repo import InMemoryUserRepository
from src.auth.implementation.bcrypt_hasher import BcryptPasswordHasher

service = UserService(InMemoryUserRepository(), BcryptPasswordHasher())

user = service.register_user("Patrick", "patrick@gmail.com", "SecurePass1!")
print(f"Registered: {user.username}, ID: {user.id}")

success = service.verify_user("patrick@gmail.com", "SecurePass1!")
print("Login success:", success)
```

#### Exception handling

```python
from src.auth.exceptions import (
    InvalidPasswordError,
    UserAlreadyExistsError,
    UserNotFoundError,
    WeakPasswordError,
)

try:
    service.register_user("Patrick", "patrick@gmail.com", "SecurePass1!")
except UserAlreadyExistsError as e:
    print(e)  # User with email 'patrick@gmail.com' already exists.

try:
    service.register_user("Patrick", "new@gmail.com", "weak")
except WeakPasswordError as e:
    print(e)  # Password must be at least 8 characters and include ...

try:
    service.verify_user("patrick@gmail.com", "WrongPassword1!")
except InvalidPasswordError as e:
    print(e)  # Invalid password.

try:
    service.verify_user("unknown@gmail.com", "AnyPassword1!")
except UserNotFoundError as e:
    print(e)  # No user found with email 'unknown@gmail.com'.

try:
    service.register_user("Patrick", "not-an-email", "SecurePass1!")
except ValueError as e:
    print(e)  # 'not-an-email' is not a valid email address.
```

---

## Testing

Coverage runs automatically (configured in `pyproject.toml`):

```bash
pytest
```

**Expected output:**

```text
================================ test session starts =================================
collected 46 items

tests/test_end_to_end.py .                                                     [  2%]
tests/test_implementations.py .....                                           [ 13%]
tests/test_interfaces.py ....                                                 [ 21%]
tests/test_login.py ......                                                    [ 34%]
tests/test_main.py ......                                                     [ 47%]
tests/test_models.py ..                                                       [ 52%]
tests/test_registration.py .........                                         [ 71%]
tests/test_validation.py .............                                       [100%]

=================================== tests coverage ====================================
Name                                       Stmts   Miss  Cover   Missing
------------------------------------------------------------------------
src\auth\__init__.py                           0      0   100%
src\auth\exceptions.py                         4      0   100%
src\auth\implementation\__init__.py            0      0   100%
src\auth\implementation\bcrypt_hasher.py      10      0   100%
src\auth\implementation\memory_repo.py        10      0   100%
src\auth\interfaces.py                        13      0   100%
src\auth\models.py                             8      0   100%
src\auth\service.py                           46      0   100%
------------------------------------------------------------------------
TOTAL                                         91      0   100%
=========================== 46 passed in X.XXs ============================
```

Run a specific file: `pytest tests/test_registration.py -v`

---

## Development

Quality gates are enforced via [pre-commit](https://pre-commit.com/):

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

This runs Black, ruff, and mypy (on `src/`, `tests/`, and `main.py`) on
every commit; the full pytest suite runs on `pre-push`.
