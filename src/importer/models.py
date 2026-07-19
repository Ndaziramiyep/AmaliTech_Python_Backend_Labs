"""Data models for the resilient data importer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class User:
    """A single, already-validated user record.

    Attributes:
        user_id: Unique identifier for the user.
        name: Full name of the user.
        email: Email address of the user.
    """

    user_id: str
    name: str
    email: str

    def to_dict(self) -> dict[str, str]:
        """Convert this user to a plain ``dict`` suitable for JSON storage.

        Returns:
            A dictionary with ``user_id``, ``name``, and ``email`` keys.
        """
        return {"user_id": self.user_id, "name": self.name, "email": self.email}
