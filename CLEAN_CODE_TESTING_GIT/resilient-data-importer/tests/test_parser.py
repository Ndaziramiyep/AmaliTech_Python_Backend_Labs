import pytest
from src.exceptions import FileFormatError
from src.models.user import User
from src.parser import CSVParser


# ----------------------------
# Fixtures
# ----------------------------
@pytest.fixture
def valid_csv(tmp_path):
    """Temporary valid CSV file with 2 users."""
    csv_file = tmp_path / "users.csv"
    csv_file.write_text(
        "user_id,name,email\n"
        "1,John Doe,john@example.com\n"
        "2,Jane Smith,jane@example.com\n"
    )
    return str(csv_file)


@pytest.fixture
def empty_csv(tmp_path):
    """CSV file with header only (no user data)."""
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("user_id,name,email\n")
    return str(csv_file)


@pytest.fixture
def truly_empty_csv(tmp_path):
    """Completely empty CSV file (0 bytes)."""
    csv_file = tmp_path / "truly_empty.csv"
    csv_file.write_text("")
    return str(csv_file)


@pytest.fixture
def malformed_csv(tmp_path):
    """CSV file with missing email column."""
    csv_file = tmp_path / "malformed.csv"
    csv_file.write_text("user_id,name\n" "1,John Doe\n")  # missing email header
    return str(csv_file)


@pytest.fixture
def malformed_rows_csv(tmp_path):
    """CSV file with some malformed rows (extra/missing data)."""
    csv_file = tmp_path / "malformed_rows.csv"
    csv_file.write_text(
        "user_id,name,email\n"
        "1,John Doe,john@example.com\n"
        "abc,Missing,email\n"  # malformed user_id
        "3,NoEmail\n"  # missing email
    )
    return str(csv_file)


# ----------------------------
# Tests
# ----------------------------
def test_parse_valid_csv(valid_csv):
    parser = CSVParser(valid_csv)
    users = parser.parse()
    assert len(users) == 2
    assert users[0] == User(1, "John Doe", "john@example.com")
    assert users[1] == User(2, "Jane Smith", "jane@example.com")


def test_parse_missing_file():
    parser = CSVParser("non_existent_file.csv")
    with pytest.raises(FileNotFoundError):
        parser.parse()


def test_parse_empty_file(empty_csv):
    parser = CSVParser(empty_csv)
    users = parser.parse()
    assert len(users) == 0


def test_parse_truly_empty_file(truly_empty_csv):
    """Hits StopIteration branch for completely empty file"""
    parser = CSVParser(truly_empty_csv)
    users = parser.parse()
    assert users == []


def test_parse_malformed_csv_headers(malformed_csv):
    """Raises FileFormatError for invalid headers"""
    parser = CSVParser(malformed_csv)
    with pytest.raises(FileFormatError):
        parser.parse()


def test_parse_malformed_rows_logs(malformed_rows_csv, caplog):
    """Malformed rows are skipped, valid rows parsed"""
    parser = CSVParser(malformed_rows_csv)
    with caplog.at_level("WARNING"):
        users = parser.parse()
    # Only valid row is parsed
    assert len(users) == 1
    assert users[0] == User(1, "John Doe", "john@example.com")
    # Warnings are logged for malformed rows
    assert "Skipping malformed row" in caplog.text
