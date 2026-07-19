# Git Workflow Guide

This guide explains the Git workflow for the **Resilient Data Importer** project, including branch naming conventions, feature development, and pull request strategy.

---

## Branch Structure

| Branch Name        | Purpose                                          |
|-------------------|--------------------------------------------------|
| `developer`        | Main development branch, always stable          |
| `feature/cli`      | CLI functionality                               |
| `feature/docs`     | Documentation updates                            |
| `feature/model`    | User model and data structures                   |
| `feature/parser`   | CSV parsing logic                               |
| `feature/storage`  | JSON storage / repository logic                  |
| `feature/tests`    | Unit and integration test additions              |
| `feature/validator`| User validation logic                             |

> **Note**: Feature branches are created from `developer`. All work must go through pull requests (PRs) for review.

---

## Branch Naming Convention

- **Feature branches:** `feature/<feature-name>`
  Example: `feature/parser`, `feature/storage`
- **Bugfix branches:** `bugfix/<bug-name>`
  Example: `bugfix/csv-header-error`
- **Hotfix branches:** `hotfix/<issue>`
  Example: `hotfix/corrupted-json-fix`
- **Documentation branches:** `feature/docs`

---

## Workflow Steps

### 1. Start Feature Development
```bash
# Switch to developer branch
git checkout developer

# Pull latest changes
git pull origin developer

# Create new feature branch
git checkout -b feature/parser
