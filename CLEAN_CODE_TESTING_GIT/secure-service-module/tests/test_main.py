"""Tests for the CLI entry point (main.py) -- register/login helpers and menu loop."""

import main
from src.auth.implementation.bcrypt_hasher import BcryptPasswordHasher
from src.auth.implementation.memory_repo import InMemoryUserRepository
from src.auth.service import UserService


def _service():
    return UserService(InMemoryUserRepository(), BcryptPasswordHasher())


def test_register_prints_success_message(monkeypatch, capsys):
    """A well-formed registration prints the created username and email."""
    service = _service()
    inputs = iter(["Patrick", "patrick@gmail.com"])
    monkeypatch.setattr(main, "input", lambda _prompt: next(inputs), raising=False)
    monkeypatch.setattr(main, "getpass", lambda _prompt: "SecurePass1")

    main._register(service)

    out = capsys.readouterr().out
    assert "Registered 'Patrick' (patrick@gmail.com)" in out


def test_register_prints_failure_message_on_invalid_input(monkeypatch, capsys):
    """A validation failure during registration prints a clear error, not a crash."""
    service = _service()
    inputs = iter(["Patrick", "not-an-email"])
    monkeypatch.setattr(main, "input", lambda _prompt: next(inputs), raising=False)
    monkeypatch.setattr(main, "getpass", lambda _prompt: "SecurePass1")

    main._register(service)

    out = capsys.readouterr().out
    assert "Registration failed" in out


def test_login_prints_success_message(monkeypatch, capsys):
    """Verifying correct credentials for a registered user prints success."""
    service = _service()
    service.register_user("Patrick", "patrick@gmail.com", "SecurePass1")
    monkeypatch.setattr(
        main, "input", lambda _prompt: "patrick@gmail.com", raising=False
    )
    monkeypatch.setattr(main, "getpass", lambda _prompt: "SecurePass1")

    main._login(service)

    out = capsys.readouterr().out
    assert "Login successful" in out


def test_login_prints_failure_message_for_unknown_user(monkeypatch, capsys):
    """Logging in with an unregistered email prints a clear error, not a crash."""
    service = _service()
    monkeypatch.setattr(
        main, "input", lambda _prompt: "unknown@gmail.com", raising=False
    )
    monkeypatch.setattr(main, "getpass", lambda _prompt: "SecurePass1")

    main._login(service)

    out = capsys.readouterr().out
    assert "Login failed" in out


def test_main_menu_registers_then_logs_in_then_exits(monkeypatch, capsys):
    """The menu loop can register a user, log them in, and then exit cleanly."""
    # Order: menu->register, username, email, menu->login, email, menu->exit
    inputs = iter(["1", "Patrick", "patrick@gmail.com", "2", "patrick@gmail.com", "3"])
    monkeypatch.setattr(main, "input", lambda _prompt: next(inputs), raising=False)
    monkeypatch.setattr(main, "getpass", lambda _prompt: "SecurePass1")

    main.main()

    out = capsys.readouterr().out
    assert "Registered 'Patrick'" in out
    assert "Login successful" in out


def test_main_menu_rejects_invalid_choice_then_exits(monkeypatch, capsys):
    """An unrecognized menu choice prints a hint and re-prompts instead of crashing."""
    inputs = iter(["9", "3"])
    monkeypatch.setattr(main, "input", lambda _prompt: next(inputs), raising=False)

    main.main()

    out = capsys.readouterr().out
    assert "Please enter 1, 2, or 3." in out
