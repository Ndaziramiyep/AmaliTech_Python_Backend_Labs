# tests/test_main.py

import pytest

import main as main_module
from main import main


def test_main_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = iter(["exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    main()


def test_main_valid_city(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    inputs = iter(["Kigali", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    main()
    assert "Forecast for Kigali" in capsys.readouterr().out


def test_main_unknown_city(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    inputs = iter(["Atlantis", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    main()
    assert "not found" in capsys.readouterr().out


def test_main_invalid_api_key(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(main_module, "API_KEY", "wrong_key")
    inputs = iter(["Kigali", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    main()
    assert "Invalid API key" in capsys.readouterr().out
