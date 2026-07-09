# Employee Payroll Tracker

A Python CLI application that collects employee data interactively, computes monthly gross pay, applies Rwanda RRA PAYE income tax using progressive brackets, and prints individual payslips plus a full payroll summary.

---

## Project Structure

```
Employee_payroll_tracker/
├── employee.py        # Employee data models (ABC + 3 concrete classes)
├── payroll.py         # Tax logic, payslip generation, batch processing
├── utils.py           # Shared CLI formatting helpers
├── main.py            # CLI entry point — menus, input prompts, output
├── test_payroll.py    # 55 unit tests (pytest)
└── pyproject.toml     # Poetry config + pytest settings
```

---

## Requirements

- Python 3.14+
- [Poetry](https://python-poetry.org/) for dependency management

### Install and run

```bash
poetry install
poetry run python main.py
```

### Run tests

```bash
poetry run pytest -v
```

---

## File Reference

### `employee.py`

Defines the employee type hierarchy using Python's `abc` module.

#### `Employee` (Abstract Base Class)

The root class that all employee types inherit from. It cannot be instantiated directly.

**Constructor** — `__init__(emp_id, name, base_salary)`
- `emp_id` — stripped and uppercased automatically; raises `ValueError` if empty or whitespace.
- `name` — stripped automatically; raises `ValueError` if empty or whitespace.
- `base_salary` — stored via the property setter described below.

**Properties**

| Property | Type | Rules |
|---|---|---|
| `base_salary` | `float` | Must be a number (not `bool`), must be `> 0`. |
| `is_tax_exempt` | `bool` | Abstract — each subclass must declare it. |

**Abstract methods** — subclasses must implement both:
- `calculate_salary() -> float` — returns the monthly gross pay.
- `role() -> str` — returns a human-readable role label.

**Dunder methods**
- `__str__` — `"Full-Time Employee | FT001 — Nziza Paul"`
- `__repr__` — `"FullTimeEmployee(emp_id='FT001', name='Nziza Paul')"`

---

#### `FullTimeEmployee(Employee)`

Represents a salaried employee who may also receive a monthly bonus.

**Constructor** — `__init__(emp_id, name, base_salary, bonus=0.0)`

**Extra property**

| Property | Type | Rules |
|---|---|---|
| `bonus` | `float` | Must be a number (not `bool`), must be `>= 0`. |

**`calculate_salary()`** — returns `base_salary + bonus`.

**`role()`** — returns `"Full-Time Employee"`.

**`is_tax_exempt`** — `False`.

---

#### `ContractEmployee(Employee)`

Represents an hourly-paid contractor. The `base_salary` field stores the hourly rate.

**Constructor** — `__init__(emp_id, name, hourly_rate, hours_worked)`

**Extra property**

| Property | Type | Rules |
|---|---|---|
| `hours_worked` | `float` | Must be a number (not `bool`), must be `>= 0`. |

**Alias property** — `hourly_rate` reads from `_base_salary` for semantic clarity.

**`calculate_salary()`** — returns `hourly_rate × hours_worked`. Zero hours produces zero gross (no tax).

**`role()`** — returns `"Contract Employee"`.

**`is_tax_exempt`** — `False`.

---

#### `Intern(Employee)`

Represents an intern on a fixed monthly stipend. The `base_salary` field stores the stipend.

**Constructor** — `__init__(emp_id, name, stipend)`

**Alias property** — `stipend` reads from `_base_salary` for semantic clarity.

**`calculate_salary()`** — returns the stipend directly.

**`role()`** — returns `"Intern"`.

**`is_tax_exempt`** — `False`. Interns are subject to Rwanda PAYE like all other employee types.

---

### `payroll.py`

Handles all tax computation, payslip formatting, and batch payroll processing.

#### Rwanda PAYE Tax Brackets — `_TAX_BRACKETS`

A module-level constant — a list of `(lower_bound, upper_bound, rate)` tuples representing Rwanda RRA monthly PAYE brackets. Tax is applied directly to the monthly gross; no annualisation is performed.

| Band | Monthly Gross | Rate |
|---|---|---|
| 1 | RWF 0 – 30,000 | 0% |
| 2 | RWF 30,001 – 100,000 | 20% |
| 3 | RWF 100,001+ | 30% |

#### `apply_tax(monthly_gross) -> float`

Computes the total monthly PAYE tax using the progressive brackets above.

- Raises `ValueError` if `monthly_gross` is negative.
- Iterates through each bracket, accumulates tax on the portion of income that falls within that band, and stops early once the income does not reach the next bracket.

**Examples**

| Gross | Calculation | Tax |
|---|---|---|
| 20,000 | 0% on 20k | 0 |
| 65,000 | 0% on 30k + 20% on 35k | 7,000 |
| 100,000 | 0% on 30k + 20% on 70k | 14,000 |
| 150,000 | 0 + 14,000 + 30% on 50k | 29,000 |
| 400,000 | 0 + 14,000 + 30% on 300k | 104,000 |

#### `compute_payroll_details(employee) -> dict`

Calls `employee.calculate_salary()` to get the gross, passes it to `apply_tax()`, and returns a dict with six keys:

```python
{
    "emp_id": str,
    "name":   str,
    "role":   str,
    "gross":  float,
    "tax":    float,
    "net":    float,   # gross - tax
}
```

#### `generate_payslip(employee) -> str`

Builds a formatted multi-line payslip string by calling `compute_payroll_details()` and assembling the result with `divider()` and `format_currency()` from `utils.py`. Returns the full string — it does not print.

**Sample output**

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
```

#### `process_payroll(employees) -> list[dict]`

Accepts a list of `Employee` objects and returns a list of payroll detail dicts by calling `compute_payroll_details()` on each one. Used by `main.py` to build the summary table.

---

### `utils.py`

Shared formatting helpers used by both `payroll.py` and `main.py`.

#### `format_currency(amount, symbol="$") -> str`

Returns a currency string with a thousands separator and two decimal places.

```python
format_currency(296_000)          # "$296,000.00"
format_currency(1_000, "RWF ")    # "RWF 1,000.00"
```

#### `divider(width=40, char="-") -> str`

Returns a horizontal line of `width` repeated `char` characters. Raises `ValueError` if `width < 1`.

```python
divider()        # "----------------------------------------"
divider(10, "=") # "=========="
```

#### `format_header(title, width=40) -> str`

Returns a three-line centred header: a `=` border line, the title centred within `width`, and another `=` border line.

```python
format_header("PAYSLIPS")
# ========================================
#                 PAYSLIPS
# ========================================
```

---

### `main.py`

The CLI entry point. Handles all user interaction — menus, input validation, and output printing.

#### `_ROLE_MAP`

A module-level dict that maps menu keys to `(display label, factory function)` pairs. Adding a new employee type only requires inserting one entry here.

```python
_ROLE_MAP = {
    "1": ("Full-Time Employee", _add_full_time),
    "2": ("Contract Employee",  _add_contract),
    "3": ("Intern",             _add_intern),
}
```

#### Input helpers

**`prompt_emp_id(existing_ids: set[str]) -> str`**

Loops until the user enters a valid employee ID:
- Not empty.
- 10 characters or fewer.
- Alphanumeric only (`isalnum()`).
- Not already in `existing_ids` (case-insensitive — IDs are uppercased before the check).

Returns the ID uppercased.

**`prompt_name() -> str`**

Loops until the user enters a valid full name:
- Not empty.
- Between 2 and 50 characters.
- Contains only letters, spaces, hyphens, or apostrophes.

Returns the name in title case.

**`prompt_float(label, min_val=0.0) -> float`**

Loops until the user enters a valid float that is `>= min_val`. Catches `ValueError` from `float()` and re-prompts with a clear error message.

#### Employee factory functions

Each factory prints a section header, calls the three input helpers in order, and returns a fully constructed employee object.

| Function | Returns |
|---|---|
| `_add_full_time(existing_ids)` | `FullTimeEmployee` — prompts for base salary and bonus. |
| `_add_contract(existing_ids)` | `ContractEmployee` — prompts for hourly rate and hours worked. |
| `_add_intern(existing_ids)` | `Intern` — prompts for monthly stipend. |

#### `collect_employees() -> list[Employee]`

Owns the `existing_ids` set and the `employees` list. Runs the main menu loop:
- Shows role options `[1]`, `[2]`, `[3]` on every iteration.
- Shows `[0] Done — generate payroll` only after at least one employee has been added (prevents exiting with an empty list).
- On a valid role choice, calls the corresponding factory, appends the employee, and registers the ID.
- On `[0]` with employees present, breaks and returns the list.

#### Output functions

**`print_all_payslips(employees)`** — prints a `PAYSLIPS` header then calls `generate_payslip()` for each employee.

**`print_summary(payroll_data)`** — prints a tabular summary with columns for ID, Name, Role, and Net Pay, followed by total gross, total tax, and total net across all employees.

#### `main()`

Orchestrates the full workflow in four steps:
1. `collect_employees()` — interactive data collection.
2. `print_all_payslips()` — individual payslips.
3. `process_payroll()` — compute all payroll dicts.
4. `print_summary()` — tabular totals.

---

### `test_payroll.py`

55 unit tests written with `pytest`. All tests live at the project root alongside the source files.

| Class | Tests | What is covered |
|---|---|---|
| `TestFullTimeEmployee` | 15 | Gross calculation, role, `is_tax_exempt`, ID uppercasing, name stripping, `ValueError` on zero/negative/non-numeric salary, negative/non-numeric bonus, empty/whitespace ID and name. |
| `TestContractEmployee` | 8 | Gross calculation, zero-hours edge case, role, `is_tax_exempt`, `hourly_rate` alias, `ValueError` on negative hours, zero rate, non-numeric hours. |
| `TestIntern` | 6 | Gross equals stipend, role, `is_tax_exempt`, `stipend` alias, `ValueError` on zero and negative stipend. |
| `TestApplyTax` | 8 | Zero income, within first bracket, at first bracket ceiling, mid second bracket, at second bracket ceiling, into third bracket, large gross, negative gross raises. |
| `TestComputePayrollDetails` | 8 | All six keys present, correct figures for full-time/contract/intern, intern below threshold pays no tax, net = gross − tax, zero-hours contract, `process_payroll` returns all records in order. |
| `TestUtils` | 10 | `format_currency` default/custom symbol/zero, `divider` default/custom/zero-width/negative-width raises, `format_header` contains title and has three lines, `generate_payslip` contains all expected fields. |

---

### `pyproject.toml`

Minimal Poetry configuration file.

```toml
[tool.poetry]
package-mode = false          # flat layout — no src/ package to install

[tool.pytest.ini_options]
pythonpath = ["."]            # lets pytest import root-level modules without a src/ layout

[project]
name = "employee-payroll-tracker"
version = "0.1.0"
description = "A Python CLI application for computing employee payroll with Rwanda PAYE tax."
requires-python = ">=3.14"
```

`package-mode = false` tells Poetry this is a script project, not a library. `pythonpath = ["."]` is required so that `import employee`, `import payroll`, and `import utils` resolve correctly when running `pytest` from the project root.

---

## Rwanda PAYE Tax — How It Works

Tax is computed on the **monthly gross** using three progressive bands. Each band is taxed only on the portion of income that falls within it.

```
Gross = 150,000

Band 1:  0 – 30,000   →  30,000 × 0%  =      0
Band 2: 30,000 – 100,000 → 70,000 × 20% = 14,000
Band 3: 100,000+       →  50,000 × 30% = 15,000
                                  Total = 29,000

Net = 150,000 − 29,000 = 121,000
```

All three employee types — Full-Time, Contract, and Intern — are subject to this tax. There are no tax-exempt employee types.

---

## Design Decisions

- **Flat file structure** — all source files live at the project root. No `src/` or `models/` subfolders.
- **Single `employee.py`** — all four classes in one file to keep imports simple.
- **`existing_ids` set** — owned by `collect_employees()` and passed into each factory for O(1) duplicate ID detection.
- **`[0] Done` hidden on first iteration** — prevents the user from exiting before adding any employees.
- **No logging** — the project has no logging infrastructure by design.
- **One-line docstrings** — all docstrings are single-line for brevity.
