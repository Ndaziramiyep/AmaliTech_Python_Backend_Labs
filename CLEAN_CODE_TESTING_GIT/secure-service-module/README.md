# Lab 3: Secure Service Module with TDD

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

## Project Structure

```
lab3-auth-service/
├── src/auth/              # Core module
├── tests/                 # Test cases
├── docs/                  # Documentation
│   ├── architecture.md
│   ├── modules.md
│   ├── testing.md
│   └── usage.md
├── requirements.txt
├── .gitignore
├── .pre-commit-config.yaml
└── README.md
```

---

## Documentation

Detailed documentation is available in the `docs/` folder:

- **[ARCHITECTURE](docs/architecture.md)** – Class diagrams, dependency graph, architecture principles
- **[MODULES](docs/modules.md)** – Description of modules, classes, and methods
- **[TESTING](docs/testing.md)** – Testing strategy, TDD workflow, example tests
- **[USAGE](docs/usage.md)** – Usage examples, exception handling, optional logging

---

## Installation

Requires **Python 3.11+**. Install dependencies:

```bash
pip install -r requirements.txt
```

Requirements include:

```
bcrypt
pytest
pytest-mock
coverage
mypy
black
ruff
```

---

## Quick Usage Example

```python
from auth.service import UserService
from auth.implementations.memory_repo import InMemoryUserRepository
from auth.implementations.bcrypt_hasher import BcryptPasswordHasher

repo = InMemoryUserRepository()
hasher = BcryptPasswordHasher()
service = UserService(user_repository=repo, password_hasher=hasher)

# Register user
user = service.register_user("diane", "SecurePass123")

# Verify credentials
success = service.verify_user("diane", "SecurePass123")
print("Login success:", success)
```

For detailed examples and exception handling, see **[USAGE.md](docs/usage.md)**.

---

## Testing

Run all tests and check coverage:

```bash
pytest --cov=src/auth tests/
```

See **[TESTING.md](docs/testing.md)** for full strategy and sample tests.

---

## Git Workflow

- **Feature branches**: `feature/registration`, `feature/login`
- **Commit messages** reflect TDD cycle:
  ```
  test: add failing test
  feat: implement feature
  refactor: clean code
  ```
- **Pre-commit hooks** enforce Black, ruff, and mypy checks

---

## Features

✅ Secure password hashing with bcrypt
✅ In-memory user repository (extensible to database)
✅ Custom exception handling
✅ 100% test coverage on core logic
✅ Type hints with mypy validation
✅ Code formatting with Black and ruff

---
