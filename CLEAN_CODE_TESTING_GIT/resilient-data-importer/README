# Resilient Data Importer CLI

A robust, production-ready Python command-line tool for importing, validating, and storing user data from CSV files into a JSON database with comprehensive error handling and logging.

---

## 🚀 Features

- **CSV Parsing**: Efficiently reads and processes CSV files with user data
- **Data Validation**: Validates email formats, required fields, and data types
- **Duplicate Detection**: Identifies and handles duplicate records intelligently
- **JSON Storage**: Persistent storage with atomic write operations
- **Comprehensive Logging**: Detailed logs for debugging and auditing
- **Error Resilience**: Graceful handling of malformed data and edge cases
- **Modular Architecture**: Clean separation of concerns for maintainability

---

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## 🛠️ Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/resilient-data-importer.git
   cd resilient-data-importer
   ```

2. **Create and activate virtual environment**

   **Windows:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

   **macOS/Linux:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚡ Quick Start

1. **Prepare your CSV file** (`users.csv`):
   ```csv
   user_id,name,email
   1,John Doe,john@example.com
   2,Jane Smith,jane@example.com
   3,Bob Johnson,bob@example.com
   ```

2. **Run the importer**:
   ```bash
   python main.py --file users.csv
   ```

3. **Check the output**:
   - Valid records saved to `database.json`
   - Logs available in `logs/importer.log`

---

## 📖 Usage

### Basic Command

```bash
python main.py --file <path-to-csv>
```

### Options

```bash
python main.py --help
```

**Available arguments:**
- `--file`: Path to the CSV file to import (required)
- `--database`: Path to JSON database (default: `database.json`)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Example Commands

```bash
# Import with custom database location
python main.py --file data/users.csv --database data/db.json

# Enable debug logging
python main.py --file users.csv --log-level DEBUG

# Process large dataset
python main.py --file bulk_users.csv
```

---

## 📁 Project Structure

```
resilient-data-importer/
│
├── src/
│   ├── __init__.py
│   ├── models.py          # Data models and entities
│   ├── exceptions.py      # Custom exception classes
│   ├── parser.py          # CSV parsing logic
│   ├── validator.py       # Data validation rules
│   └── storage.py         # JSON database operations
│
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_validator.py
│   ├── test_storage.py
│   ├── test_models.py
│   └── test_integration.py
│
├── docs/
│   ├── 01_requirements.md
│   ├── 02_api_design.md
│   ├── 03_architecture.md
│   ├── 04_testing.md
│   ├── 05_code_review_checklist.md
│   └── 06_git_workflow.md
│
├── main.py                # CLI entry point
├── requirements.txt       # Project dependencies
├── .gitignore
└── README.md
```

---

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

| Document | Description |
|----------|-------------|
| **[Requirements](docs/01_requirements.md)** | Functional and non-functional requirements |
| **[API Design](docs/02_api_design.md)** | Module interfaces, classes, and methods |
| **[Architecture](docs/03_architecture.md)** | System design, diagrams, and patterns |
| **[Testing Strategy](docs/04_testing.md)** | Test plans, fixtures, and coverage goals |
| **[Code Review](docs/05_code_review_checklist.md)** | Quality assurance checklist |
| **[Git Workflow](docs/06_git_workflow.md)** | Branching strategy and contribution guide |

---

## 💻 Development

### Architecture Overview

The project follows a **layered architecture** pattern:

```
┌─────────────────────┐
│   CLI Layer         │  main.py
├─────────────────────┤
│   Business Logic    │  parser.py, validator.py
├─────────────────────┤
│   Data Layer        │  models.py, storage.py
├─────────────────────┤
│   Infrastructure    │  exceptions.py, logging
└─────────────────────┘
```

### Code Quality Tools

The project uses industry-standard tools:

- **black**: Code formatting
- **mypy**: Static type checking
- **ruff**: Fast Python linter
- **pytest**: Testing framework

### Running Quality Checks

```bash
# Format code
black src/ tests/

# Type checking
mypy src/

# Linting
ruff check src/

# Run all checks
black src/ tests/ && mypy src/ && ruff check src/
```

---

## 🧪 Testing

### Run All Tests

```bash
pytest -v
```

### Run Specific Test Suite

```bash
# Unit tests only
pytest tests/test_validator.py -v

# Integration tests
pytest tests/test_integration.py -v
```

### Code Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View report
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

**Coverage Goal**: >90% for all modules

### Test Categories

- **Unit Tests**: Individual module functionality
- **Integration Tests**: End-to-end workflow validation
- **Edge Cases**: Malformed data, duplicates, empty files

---

## 🤝 Contributing

### Git Workflow

1. **Create feature branch from `developer`**
   ```bash
   git checkout developer
   git pull origin developer
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and commit**
   ```bash
   git add .
   git commit -m "feat: add new validation rule"
   ```

3. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Code review and merge**
   - Request review from maintainers
   - Address feedback
   - Merge to `developer` after approval

### Branch Naming Convention

- `feature/` - New features
- `bugfix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring

See [Git Workflow Guide](docs/06_git_workflow.md) for details.

---

## 📦 Requirements

```txt
pytest>=7.4.0
pytest-cov>=4.1.0
black>=23.0.0
mypy>=1.5.0
ruff>=0.0.290
```

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👥 Authors

- **Your Name** - Initial work - [GitHub Profile](https://github.com/yourusername)

---

## 🙏 Acknowledgments

- CSV parsing best practices from Python's `csv` module documentation
- Validation patterns inspired by modern data engineering practices
- Architecture based on clean code principles

---

## 📞 Support

For issues, questions, or contributions:
- **Issues**: [GitHub Issues](https://github.com/Ishimwediane/resilient-data-importer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Ishimwediane/resilient-data-importer/discussions)
- **Email**: ishimwediane400@gmail.com

---

**Happy Coding! 🚀**
