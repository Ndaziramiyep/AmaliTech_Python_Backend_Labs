# Requirements Analysis

## Project Information
- **Project Name**: Resilient Data Importer CLI
- **Date**: 12-12-2025
- **Author**: ISHIMWE Diane
- **Module 2**: Lab 1

## Functional Requirements
1. **CSV Import**: Read CSV with `user_id`, `name`, `email`. Return list of `User`.
2. **Data Validation**: Validate email, positive `user_id`, non-empty name.
3. **Duplicate Prevention**: Prevent duplicate `user_id`. Log warnings.
4. **Error Handling**: Handle missing/malformed CSV, corrupted JSON. Log all errors.
5. **CLI Interface**: Accept `--file` and `--help`. Exit with proper codes.

## Non-Functional Requirements
- Code quality: PEP 8, type hints, no lint errors.
- Testing: >90% coverage.
- Documentation: Full docstrings and README.
- Version Control: Git Flow, clean commits.
- Performance: 1,000 records < 2 sec, memory < 100MB for 10,000 records.

## Out of Scope
- Web interface
- Databases (MySQL, PostgreSQL)
- Authentication
- Real-time updates

## Dependencies
- Python 3.11+
- pytest, black, mypy, ruff, coverage

## Success Metrics
- Functional requirements met.
- Coverage >90%.
- Quality checks pass.
