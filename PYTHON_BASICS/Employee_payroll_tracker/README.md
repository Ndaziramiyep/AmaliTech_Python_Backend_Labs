# Employee Payroll Tracker

A Python CLI application that computes payslips for Full-Time Employees,
Contract Employees, and Interns using OOP, property decorators, and modular design.

## Project Structure

```
PYTHON_BASICS/
├── main.py        # CLI entry point
├── employee.py    # Employee base class + subclasses
├── payroll.py     # Salary, tax, and payslip logic
├── utils.py       # Formatting helpers
└── requirements.txt
```

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 2. Install dev dependencies
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Sample Output

```
========================================
       EMPLOYEE PAYROLL TRACKER
========================================
----------------------------------------
  PAYSLIP
----------------------------------------
  ID     : FT001
  Name   : Alice Johnson
  Role   : Full-Time Employee
----------------------------------------
  Gross  : $5,500.00
  Tax    : $591.67
  Net    : $4,908.33
----------------------------------------
...

============================================================
  ID       Name               Role                   Net Pay
============================================================
  FT001    Alice Johnson      Full-Time Employee   $4,908.33
  FT002    Bob Smith          Full-Time Employee   $4,340.00
  CT001    Carol White        Contract Employee    $6,300.00
  CT002    David Brown        Contract Employee    $6,600.00
  IN001    Eve Davis          Intern                 $800.00
  IN002    Frank Miller       Intern               $1,000.00
------------------------------------------------------------
  TOTALS                                          $23,948.33
  Total Gross : $24,700.00
  Total Tax   : $751.67
  Total Net   : $23,948.33
============================================================
```

## Tax Rules

Progressive monthly tax (annualised):

| Annual Income     | Rate |
|-------------------|------|
| $0 – $5,000       | 0%   |
| $5,001 – $20,000  | 10%  |
| $20,001 – $40,000 | 20%  |
| $40,001+          | 30%  |

Interns are **tax-exempt**.

## Running Tests

```bash
pytest
```
