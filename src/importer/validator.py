"""Row validation for the resilient data importer.

Converts raw CSV rows (``dict[str, str]``) into validated :class:`~importer.models.User`
instances, raising :class:`~importer.exceptions.RowValidationError` for any
row that does not meet the requirements below. Kept separate from parsing
and storage so each concern can be tested and changed independently.
"""

from __future__ import annotations

import re

from importer.exceptions import RowValidationError
from importer.models import User

#: A pragmatic (not fully RFC 5322 compliant) email pattern, sufficient to
#: reject obviously malformed addresses.
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserRowValidator:
    """Validates raw CSV rows and converts them into :class:`User` objects."""

    def validate(self, row_number: int, raw_row: dict[str, str]) -> User:
        """Validate a single raw CSV row and build a :class:`User`.

        Args:
            row_number: The 1-based data row number, used for error messages.
            raw_row: Mapping of column name to raw string value, as produced
                by :meth:`importer.parser.CsvUserReader.rows`.

        Returns:
            A validated :class:`User` instance.

        Raises:
            RowValidationError: If any required field is missing/blank or
                the email address is not well-formed.
        """
        user_id = (raw_row.get("user_id") or "").strip()
        name = (raw_row.get("name") or "").strip()
        email = (raw_row.get("email") or "").strip()

        if not user_id:
            raise RowValidationError(row_number, "user_id is required")
        if not name:
            raise RowValidationError(row_number, "name is required")
        if not email:
            raise RowValidationError(row_number, "email is required")
        if not _EMAIL_PATTERN.match(email):
            raise RowValidationError(row_number, f"invalid email format: {email!r}")

        return User(user_id=user_id, name=name, email=email)
