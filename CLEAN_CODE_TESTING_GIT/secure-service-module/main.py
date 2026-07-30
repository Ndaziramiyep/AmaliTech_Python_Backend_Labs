"""CLI entry point: register/verify users via an in-memory UserService."""

from getpass import getpass

from src.auth.exceptions import (
    InvalidPasswordError,
    UserAlreadyExistsError,
    UserNotFoundError,
    WeakPasswordError,
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
    except (ValueError, UserAlreadyExistsError, WeakPasswordError) as exc:
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
        try:
            actions[choice](service)
        except KeyError:
            print("Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
