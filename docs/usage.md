# Usage Guide

## Setup

```bash
pip install -r requirements.txt
```

---

## Basic Example

```python
from auth.service import UserService
from auth.implementations.memory_repo import InMemoryUserRepository
from auth.implementations.bcrypt_hasher import BcryptPasswordHasher
from auth.exceptions import UserAlreadyExistsError, UserNotFoundError, InvalidPasswordError

# Initialize dependencies
repo = InMemoryUserRepository()
hasher = BcryptPasswordHasher()
service = UserService(user_repository=repo, password_hasher=hasher)

# Register user
try:
    user = service.register_user("diane", "SecurePass123")
    print(f"User registered: {user.username}")
except UserAlreadyExistsError:
    print("Username already exists")

# Verify credentials
try:
    success = service.verify_user("diane", "SecurePass123")
    print(f"Login success: {success}")
except (UserNotFoundError, InvalidPasswordError) as e:
    print(f"Login failed: {e}")
```

---

## Exception Handling

| Exception | When Raised |
|-----------|-------------|
| `UserAlreadyExistsError` | Username already registered |
| `UserNotFoundError` | User doesn't exist during login |
| `InvalidPasswordError` | Incorrect password provided |

---

## Optional Logging

```python
import logging

logger = logging.getLogger(__name__)
logger.info("User registered", extra={"username": user.username})
```
