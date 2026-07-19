"""JSON-file-backed storage layer (repository pattern).

Isolates every detail of *how* users are persisted behind a small
interface (:class:`UserRepository`), so the rest of the application
(:mod:`importer.service`) does not need to know that the "database" is
a JSON file on disk. This makes it easy to swap in another backend, or
a mock, for testing.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from types import TracebackType
from typing import Literal, Protocol

from importer.exceptions import DuplicateUserError, RepositoryError
from importer.models import User

logger = logging.getLogger(__name__)


class UserRepository(Protocol):
    """Interface for a storage backend capable of persisting users."""

    def __init__(self, path: Path | str) -> None:
        """Open (and load, if present) the repository backed by ``path``."""
        ...

    def exists(self, user_id: str) -> bool:
        """Return whether a user with ``user_id`` is already stored."""
        ...

    def add(self, user: User) -> None:
        """Add a new user to the repository.

        Raises:
            DuplicateUserError: If a user with the same id already exists.
        """
        ...

    def save(self) -> None:
        """Persist any pending changes to durable storage."""
        ...

    def __len__(self) -> int:
        """Return the number of users currently stored."""
        ...

    def __enter__(self) -> UserRepository:
        """Enter the context manager, returning this repository."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Save on a clean exit; leave storage untouched if an error propagated."""
        ...


class JsonUserRepository:
    """Persists :class:`User` records to a JSON file, acting as a simple database.

    Existing data is loaded eagerly on construction. Changes made via
    :meth:`add` are kept in memory until :meth:`save` is called (or the
    object is used as a context manager and exits without an exception),
    at which point they are written atomically (via a temp file plus
    rename) so a crash mid-write cannot corrupt the database file.
    """

    def __init__(self, path: Path | str) -> None:
        """Initialize the repository, loading existing data if present.

        Args:
            path: Path to the JSON file backing this repository.

        Raises:
            RepositoryError: If the file exists but cannot be read or
                does not contain valid JSON.
        """
        self._path = Path(path)
        self._users: dict[str, dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            logger.debug("Database file %s does not exist yet; starting empty", self._path)
            self._users = {}
            return

        try:
            content = self._path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise RepositoryError(f"Could not read database file {self._path}: {exc}") from exc

        if not content:
            self._users = {}
            return

        try:
            loaded = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RepositoryError(
                f"Database file {self._path} contains invalid JSON: {exc}"
            ) from exc

        if not isinstance(loaded, dict):
            raise RepositoryError(f"Database file {self._path} must contain a JSON object")

        self._users = loaded

    def exists(self, user_id: str) -> bool:
        """Return whether a user with ``user_id`` is already stored."""
        return user_id in self._users

    def add(self, user: User) -> None:
        """Add a new user to the in-memory store.

        Args:
            user: The validated user to add.

        Raises:
            DuplicateUserError: If ``user.user_id`` is already present.
        """
        if self.exists(user.user_id):
            raise DuplicateUserError(user.user_id)
        self._users[user.user_id] = user.to_dict()

    def save(self) -> None:
        """Atomically write the current in-memory state to disk.

        Raises:
            RepositoryError: If the file cannot be written.
        """
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
            tmp_path.write_text(
                json.dumps(self._users, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            tmp_path.replace(self._path)
        except OSError as exc:
            raise RepositoryError(f"Could not write database file {self._path}: {exc}") from exc
        logger.debug("Saved %d user(s) to %s", len(self._users), self._path)

    def __enter__(self) -> JsonUserRepository:
        """Enter the context manager, returning this repository."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Save on a clean exit; leave storage untouched if an error propagated."""
        if exc_type is None:
            self.save()
        return False

    def __len__(self) -> int:
        """Return the number of users currently stored (saved or pending)."""
        return len(self._users)
