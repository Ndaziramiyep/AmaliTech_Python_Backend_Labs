import sys
from unittest.mock import MagicMock, patch

from main import main
from src.exceptions import (DatabaseError, DuplicateUserError, FileFormatError,
                            ValidationError)


# Helper to simulate command line arguments
def run_cli_with_args(args):
    with patch.object(sys, "argv", args):
        main()


# ----------------------------
# Test valid CSV processing
# ----------------------------
@patch("src.parser.CSVParser.parse")
@patch("src.storage.UserRepository.add_user")
@patch("src.validator.UserValidator.validate")
def test_main_valid_users(mock_validate, mock_add_user, mock_parse):
    mock_parse.return_value = [
        MagicMock(user_id=1, name="John Doe", email="john@example.com"),
        MagicMock(user_id=2, name="Jane Smith", email="jane@example.com"),
    ]
    mock_validate.return_value = True

    run_cli_with_args(["main.py", "dummy.csv"])

    assert mock_parse.called
    assert mock_validate.call_count == 2
    assert mock_add_user.call_count == 2


# ----------------------------
# Test empty CSV file
# ----------------------------
@patch("src.parser.CSVParser.parse")
def test_main_empty_csv(mock_parse):
    mock_parse.return_value = []
    run_cli_with_args(["main.py", "empty.csv"])
    mock_parse.assert_called_once()


# ----------------------------
# Test validation error for a user
# ----------------------------
@patch("src.parser.CSVParser.parse")
@patch("src.storage.UserRepository.add_user")
@patch("src.validator.UserValidator.validate")
def test_main_validation_error(mock_validate, mock_add_user, mock_parse):
    user = MagicMock(user_id=1, name="John Doe", email="john@example.com")
    mock_parse.return_value = [user]
    mock_validate.side_effect = ValidationError("Validation failed")

    run_cli_with_args(["main.py", "dummy.csv"])

    mock_validate.assert_called_once()
    mock_add_user.assert_not_called()


# ----------------------------
# Test duplicate user error
# ----------------------------
@patch("src.parser.CSVParser.parse")
@patch("src.storage.UserRepository.add_user")
@patch("src.validator.UserValidator.validate")
def test_main_duplicate_user(mock_validate, mock_add_user, mock_parse):
    user = MagicMock(user_id=1, name="John Doe", email="john@example.com")
    mock_parse.return_value = [user]
    mock_validate.return_value = True
    mock_add_user.side_effect = DuplicateUserError("Duplicate user")

    run_cli_with_args(["main.py", "dummy.csv"])

    mock_validate.assert_called_once()
    mock_add_user.assert_called_once()


# ----------------------------
# Test file not found
# ----------------------------
@patch("src.parser.CSVParser.parse")
def test_main_file_not_found(mock_parse):
    mock_parse.side_effect = FileNotFoundError("File not found")
    run_cli_with_args(["main.py", "missing.csv"])
    mock_parse.assert_called_once()


# ----------------------------
# Test CSV format error
# ----------------------------
@patch("src.parser.CSVParser.parse")
def test_main_file_format_error(mock_parse):
    mock_parse.side_effect = FileFormatError("Invalid CSV format")
    run_cli_with_args(["main.py", "malformed.csv"])
    mock_parse.assert_called_once()


# ----------------------------
# Test Database error
# ----------------------------
@patch("src.parser.CSVParser.parse")
@patch("src.validator.UserValidator.validate")
@patch("src.storage.UserRepository.add_user")
def test_main_database_error(mock_add, mock_validate, mock_parse):
    user = MagicMock(user_id=1, name="John Doe", email="john@example.com")
    mock_parse.return_value = [user]
    mock_validate.return_value = True
    mock_add.side_effect = DatabaseError("DB write error")

    run_cli_with_args(["main.py", "dummy.csv"])


# ----------------------------
# Test unexpected exception
# ----------------------------
@patch("src.parser.CSVParser.parse")
@patch("src.validator.UserValidator.validate")
def test_main_unexpected_exception(mock_validate, mock_parse):
    user = MagicMock(user_id=1, name="John Doe", email="john@example.com")
    mock_parse.return_value = [user]
    mock_validate.side_effect = Exception("Unexpected fail")

    run_cli_with_args(["main.py", "dummy.csv"])
