"""Resilient Data Importer.

A small, well-tested CLI tool that imports user records from a CSV file
into a JSON-file-backed "database", handling missing files, malformed
rows, and duplicate users gracefully.
"""

from importer.models import User

__all__ = ["User"]
__version__ = "0.1.0"
