
---

## 2️⃣ `docs/MODULES.md`

```markdown
# Module & Component Documentation

## 1. auth/models.py
- `User` dataclass with:
  - `username: str`
  - `password_hash: str`

## 2. auth/exceptions.py
- `UserAlreadyExistsError` – raised on duplicate registration
- `UserNotFoundError` – raised if user not found during login
- `InvalidPasswordError` – raised if password verification fails

## 3. auth/interfaces.py
- **UserRepository (ABC)**
  - `get_by_username(username: str) -> Optional[User]`
  - `add(user: User) -> None`
- **PasswordHasher (ABC)**
  - `hash_password(password: str) -> str`
  - `verify_password(password: str, hashed: str) -> bool`

## 4. auth/service.py
- `UserService`
  - `register_user(username, password) -> User`
  - `verify_user(username, password) -> bool`

## 5. auth/implementations/memory_repo.py
- `InMemoryUserRepository` – stores users in memory (for testing/demo purposes)

## 6. auth/implementations/bcrypt_hasher.py
- `BcryptPasswordHasher` – hashes and verifies passwords using bcrypt
