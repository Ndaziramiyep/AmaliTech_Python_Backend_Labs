"""Command-line entry point for the secure-service-module library.

Run with `python main.py` to register users and verify their credentials
from the keyboard, backed by the real UserService (bcrypt hashing,
in-memory storage). This script is a thin CLI wrapper -- all business
logic lives in src/auth, framework-free and unit-tested in isolation.
"""

from getpass import getpass

from src.auth.exceptions import (
    InvalidPasswordError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.auth.implementation.bcrypt_hasher import BcryptPasswordHasher
from src.auth.implementation.memory_repo import InMemoryUserRepository
from src.auth.service import UserService


def _register(service: UserService) -> None:
    """Prompt for username/email/password and register a new user."""
    print("\n--- Register a new user ---")
    username = input("Username: ")
    email = input("Email: ")
    password = getpass("Password: ")

    try:
        user = service.register_user(username, email, password)
    except (ValueError, UserAlreadyExistsError, InvalidPasswordError) as exc:
        print(f"Registration failed: {exc}")
        return

    print(f"Registered '{user.username}' ({user.email}), id={user.id}")


def _login(service: UserService) -> None:
    """Prompt for email/password and verify them against a registered user."""
    print("\n--- Verify login ---")
    email = input("Email: ")
    password = getpass("Password: ")

    try:
        service.verify_user(email, password)
    except (ValueError, UserNotFoundError, InvalidPasswordError) as exc:
        print(f"Login failed: {exc}")
        return

    print("Login successful.")


def main() -> None:
    """Run an interactive register/login menu against an in-memory repository."""
    service = UserService(InMemoryUserRepository(), BcryptPasswordHasher())
    print("Secure Service Module -- CLI")
    print("(Data is stored in memory only and is lost when this script exits.)")

    actions = {"1": _register, "2": _login}
    while True:
        choice = input("\n1) Register  2) Login  3) Exit\n> ").strip()
        if choice == "3":
            break
        action = actions.get(choice)
        if action is None:
            print("Please enter 1, 2, or 3.")
            continue
        action(service)


if __name__ == "__main__":
    main()
