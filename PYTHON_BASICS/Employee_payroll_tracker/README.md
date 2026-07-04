# Employee Payroll Tracker

A Python CLI application that collects employee data interactively, computes
monthly gross pay, applies Rwanda PAYE tax, and prints individual payslips
plus a full payroll summary. Built with OOP, abstract base classes, property
decorators, centralised logging, and modular design.

## Project Structure

```
Employee_payroll_tracker/
├── main.py               # CLI entry point — input, validation, output
├── employee.py           # Abstract Employee base class + subclasses
├── payroll.py            # Rwanda PAYE tax logic, payslip generation
├── utils.py              # Shared formatting helpers
├── logger.py             # Centralised logging configuration
├── tests/
│   └── test_payroll.py   # 39 unit tests (pytest)
├── logs/
│   └── payroll.log       # Rotating log file (auto-generated, git-ignored)
├── pyproject.toml        # Poetry project config and dependencies
├── poetry.lock           # Locked dependency versions (auto-generated)
└── .gitignore            # Excludes __pycache__, .pytest_cache, logs/
```

## Setup

```bash
# Install dependencies
poetry install

# Run the app
poetry run python main.py
```

## Usage

When the app starts, select an employee type and fill in the prompted fields.
Sample hints are shown next to every field. After adding at least one employee,
option `[0] Done` appears to generate the payroll report.

```
========================================
     EMPLOYEE PAYROLL TRACKER
========================================

  Select employee type:
    [1] Full-Time Employee
    [2] Contract Employee
    [3] Intern

  -- Full-Time Employee --
  Employee ID   (e.g. FT001)      : FT001
  Full Name     (e.g. Nziza Paul) : Nziza Paul
  Base Salary   (e.g. 350000)     : 350000
  Monthly Bonus (e.g. 50000, 0 if none) : 50000

  + Nziza Paul (FT001) added successfully.
```

## Input Validation

| Field | Rules |
|---|---|
| Employee ID | Letters and digits only (e.g. `FT001`); no duplicates allowed |
| Full Name | Letters, spaces, hyphens, and apostrophes only (e.g. `Nziza Paul`) |
| Salary / Rate / Stipend | Must be a number greater than 0 |
| Bonus / Hours Worked | Must be a number greater than or equal to 0 |

## Sample Output

```
----------------------------------------
  PAYSLIP
----------------------------------------
  ID     : FT001
  Name   : Nziza Paul
  Role   : Full-Time Employee
----------------------------------------
  Gross  : $400,000.00
  Tax    : $104,000.00
  Net    : $296,000.00
----------------------------------------

==============================================================
  ID       Name               Role                   Net Pay
==============================================================
  FT001    Nziza Paul         Full-Time Employee   $296,000.00
  CT001    Uwase Marie        Contract Employee    $352,000.00
  IN001    Amour Jean         Intern                $70,000.00
--------------------------------------------------------------
  TOTALS                                           $718,000.00
  Total Gross : $930,000.00
  Total Tax   : $242,000.00
  Total Net   : $718,000.00
==============================================================
```

## Rwanda PAYE Tax Rules (Monthly)

Tax is computed directly on monthly gross using Rwanda Revenue Authority (RRA)
progressive brackets. All employee types — including interns — are subject to PAYE.

| Monthly Gross (RWF) | Rate |
|---------------------|------|
| 0 – 30,000          | 0%   |
| 30,001 – 100,000    | 20%  |
| 100,001+            | 30%  |

Each bracket taxes only the income that falls within its band (no cliff effect).

Example — monthly gross of RWF 400,000:
- RWF 0 on first 30,000 (0%)
- RWF 14,000 on 30,001–100,000 (20%)
- RWF 90,000 on 100,001–400,000 (30%)
- **Total tax = RWF 104,000**

## Logging

All activity is written to `logs/payroll.log` automatically.
The console only shows WARNING-level messages and above to keep CLI output clean.

| Level | Where logged | Example |
|---|---|---|
| DEBUG | File only | Employee created, tax calculation result |
| INFO | File only | Employee added, payroll computed, session start/end |
| WARNING | File + console | Failed employee addition (bad input) |
| ERROR | File + console | Invalid property value (salary, bonus, hours) |

Log format:
```
2026-07-04 11:50:45 | INFO     | payroll | Payroll | Nziza Paul (FT001) | gross=400000.00 tax=104000.00 net=296000.00
```

The log file rotates at 1 MB and keeps 3 backups. The `logs/` folder is git-ignored.

## Running Tests

```bash
poetry run pytest tests/ -v
```

39 tests covering employee models, Rwanda PAYE tax brackets, payroll
computation, and formatting helpers.
