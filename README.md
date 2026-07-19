# Resilient Data Importer CLI

A command-line tool that reliably imports user records (`user_id`, `name`,
`email`) from a CSV file into a JSON-file-backed "database", handling
missing files, malformed rows, and duplicate users gracefully instead of
crashing.

## Features

- **Custom exception hierarchy** (`ImporterError`, `FileFormatError`,
  `RowValidationError`, `DuplicateUserError`, `RepositoryError`) so callers
  can handle each failure mode precisely.
- **Context managers** for safe file reading (`CsvUserReader`) and atomic,
  safe writes (`JsonUserRepository`, written via a temp file + rename).
- **Structured logging** reporting successes, warnings (skipped rows), and
  errors during the import.
- **Repository pattern**: parsing (`importer.parser`), validation
  (`importer.validator`), and storage (`importer.repository`) are separate,
  independently testable components, wired together by
  `importer.service.ImportService`.
- Fully **type-hinted** (`mypy --strict` clean) and **PEP 8** formatted
  (`black`, `ruff`).

## Project layout

```
resilient-data-importer/
├── src/importer/
│   ├── models.py          # User dataclass
│   ├── exceptions.py      # Custom exception hierarchy
│   ├── parser.py          # CsvUserReader (context manager)
│   ├── validator.py        # UserRowValidator
│   ├── repository.py      # JsonUserRepository (repository pattern)
│   ├── service.py          # ImportService orchestration + ImportSummary
│   ├── logging_config.py   # Structured logging setup
│   └── cli.py               # argparse entry point
├── tests/                  # pytest suite (unit + integration)
├── data/                    # sample CSV files for manual testing
├── .pre-commit-config.yaml
├── pyproject.toml           # black/ruff/mypy/pytest/coverage config
├── requirements.txt          # runtime deps (none — stdlib only)
└── requirements-dev.txt      # pytest, black, ruff, mypy, pre-commit
```

## Setup

This project targets **Python 3.11+**. Always work inside a virtual
environment — never install dependencies globally.

```bash
# Create and activate a virtual environment (already present as venv/ in
# this repo — reuse it, or create your own with the commands below).
python -m venv venv

# Windows (PowerShell)
venv\Scripts\Activate.ps1
# Windows (Git Bash)
source venv/Scripts/activate
# macOS / Linux
source venv/bin/activate

# Install runtime + development dependencies into the venv
pip install -r requirements-dev.txt

# Install the package itself in editable mode so `resilient-importer` and
# `import importer` work
pip install -e .

# Set up git hooks (black, ruff, mypy) to run automatically before each commit
pre-commit install
```

## Usage

```bash
# Basic import: reads users.csv, writes/updates db.json in the current directory
resilient-importer data/users_valid.csv

# Specify a custom database file
resilient-importer data/users_valid.csv --db my_database.json

# Verbose (debug-level) logging
resilient-importer data/users_with_errors.csv --db db.json -v
```

You can also run it without installing, via the module path:

```bash
python -m importer.cli data/users_valid.csv --db db.json
```

### Exit codes

- `0` — every row imported successfully.
- `1` — the CSV file itself was unreadable/malformed (missing file, empty
  file, missing required column), **or** one or more individual rows were
  skipped (validation failure or duplicate `user_id`). The tool still
  imports every valid row in this case; check the log output / summary for
  details.

### CSV format

The CSV file must have a header row containing at least these columns:

```csv
user_id,name,email
1,Alice Uwimana,alice@example.com
2,Bob Habimana,bob@example.com
```

Sample files are provided under [`data/`](data/):
- `users_valid.csv` — three clean rows, demonstrates a fully successful import.
- `users_with_errors.csv` — a blank name, an invalid email, and a duplicate
  `user_id`, demonstrating the tool's error handling.

## Running the tests

```bash
pytest
```

This runs the full suite (unit tests for each component plus end-to-end
integration tests) and prints a coverage report (also written as HTML to
`htmlcov/index.html`); coverage is configured to fail if it drops below
90% (`pyproject.toml`, `[tool.coverage.report]`).

```bash
# Open the HTML coverage report
start htmlcov/index.html   # Windows
open htmlcov/index.html    # macOS
```

## Code quality checks

```bash
black --check src tests
ruff check src tests
mypy src tests
```

These are the same checks wired into `.pre-commit-config.yaml` and will
run automatically on `git commit` once `pre-commit install` has been run.

## Git workflow

This repository follows Git Flow:

- `main` — always deployable/tagged release state.
- `develop` — integration branch for finished features.
- `feature/*` — one branch per feature (e.g. `feature/csv-parser`,
  `feature/json-repository`), merged into `develop` via pull request.

## License

MIT
