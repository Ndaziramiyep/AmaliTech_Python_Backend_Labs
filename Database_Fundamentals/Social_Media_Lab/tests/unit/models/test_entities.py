"""Superseded: dedicated entity tests were removed as part of the project restructure.

The old `User`/`ActivityEvent` equality and default-field tests only verified Python's
own `@dataclass` semantics (field-by-field equality, default values), not application
behavior -- so they added little value and were dropped rather than ported. Entities now
live per-feature under `src/social_platform/features/*/model.py`; delete this file (and
the rest of this `tests/unit/models/` folder, which has no replacement) whenever
convenient -- it collects zero tests and is kept only because bulk deletion was blocked
during the restructure.
"""

from __future__ import annotations
