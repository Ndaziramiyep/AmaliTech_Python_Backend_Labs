"""Unit tests for the unified `main.py` command dispatcher."""

from __future__ import annotations

import main as main_module
import pytest
from pytest_mock import MockerFixture


def test_main_dispatches_to_the_matching_command(mocker: MockerFixture) -> None:
    """The first argument selects a command; the rest are passed through as its arguments."""
    fake_follow_user_main = mocker.Mock(return_value=0)
    mocker.patch.dict(main_module._COMMANDS, {"follow-user": fake_follow_user_main})

    exit_code = main_module.main(["follow-user", "1", "2"])

    assert exit_code == 0
    fake_follow_user_main.assert_called_once_with(["1", "2"])


def test_main_prints_usage_and_fails_for_an_unknown_command(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unrecognized command prints the list of available commands and exits nonzero."""
    exit_code = main_module.main(["not-a-real-command"])

    assert exit_code == 1
    assert "follow-user" in capsys.readouterr().out


def test_main_launches_the_interactive_session_with_no_arguments(mocker: MockerFixture) -> None:
    """Running with no arguments at all launches the interactive menu-driven session."""
    fake_run_interactive_session = mocker.patch(
        "main.run_interactive_session", return_value=0
    )

    exit_code = main_module.main([])

    assert exit_code == 0
    fake_run_interactive_session.assert_called_once_with()


def test_main_prints_usage_and_succeeds_with_an_explicit_help_flag(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--help` with no command prints usage and exits 0, since it was explicitly requested."""
    exit_code = main_module.main(["--help"])

    assert exit_code == 0
    assert "Usage:" in capsys.readouterr().out
