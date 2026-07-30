# tests/test_main.py

import pytest
from pytest_mock import MockerFixture

import main as main_module
from main import main


def test_main_exit(mocker: MockerFixture) -> None:
    # User types "exit" right away, so the CLI should quit without a forecast.
    mocker.patch("builtins.input", side_effect=["exit"])
    main()


def test_main_valid_city(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    # Look up a known city, then quit.
    mocker.patch("builtins.input", side_effect=["Kigali", "exit"])
    main()
    assert "Forecast for Kigali" in capsys.readouterr().out


def test_main_unknown_city(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    # City isn't in the mock data set, so the CLI should report it as not found.
    mocker.patch("builtins.input", side_effect=["Atlantis", "exit"])
    main()
    assert "not found" in capsys.readouterr().out


def test_main_invalid_api_key(
    mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    # Swap in a wrong key to check the CLI surfaces the invalid-key error.
    mocker.patch.object(main_module, "API_KEY", "wrong_key")
    mocker.patch("builtins.input", side_effect=["Kigali", "exit"])
    main()
    assert "Invalid API key" in capsys.readouterr().out
