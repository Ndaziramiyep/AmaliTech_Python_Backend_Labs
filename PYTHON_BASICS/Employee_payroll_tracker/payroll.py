"""
payroll.py
Core payroll logic: progressive tax calculation, per-employee salary
processing, payslip generation, and batch payroll processing.

Tax model (Rwanda PAYE — monthly):
    Tax is computed directly on the monthly gross using Rwanda Revenue
    Authority (RRA) progressive brackets. No annualisation is needed.
    All employee types, including interns, are subject to PAYE.
"""

from employee import Employee
from utils import format_currency, divider


# Rwanda PAYE monthly brackets (RRA): (lower, upper, rate)
# Applied directly to monthly gross — no annualisation required.
_TAX_BRACKETS: list[tuple[float, float, float]] = [
    (0,        30_000,       0.00),
    (30_000,   100_000,      0.20),
    (100_000,  float("inf"), 0.30),
]


def apply_tax(monthly_gross: float) -> float:
    """
    Compute monthly PAYE tax using Rwanda's progressive brackets.

    Each bracket taxes only the slice of income within its band, so a
    higher bracket never reduces tax on lower income (no cliff effect).

    Args:
        monthly_gross: Monthly gross salary in RWF.

    Returns:
        Monthly tax owed as a float.

    Example:
        apply_tax(150_000)
        → RWF 0 on first 30k (0%)
          + RWF 14,000 on 30k–100k (20%)
          + RWF 15,000 on 100k–150k (30%)
          = RWF 29,000
    """
    tax = 0.0
    for lower, upper, rate in _TAX_BRACKETS:
        if monthly_gross <= lower:
            break  # income doesn't reach this bracket — stop early
        taxable_in_band = min(monthly_gross, upper) - lower
        tax += taxable_in_band * rate
    return tax


def compute_payroll_details(employee: Employee) -> dict:
    """
    Compute the full monthly payroll breakdown for a single employee.

    Steps:
        1. Get monthly gross via the employee's calculate_salary().
        2. Skip tax entirely if employee.is_tax_exempt is True.
        3. Otherwise annualise gross, apply progressive tax, convert back
           to a monthly figure.
        4. Derive net pay as gross − tax.

    Args:
        employee: Any concrete Employee subclass instance.

    Returns:
        Dictionary with keys:
            emp_id, name, role, gross (float), tax (float), net (float)
    """
    gross_monthly = employee.calculate_salary()

    # All employees (including interns) are subject to Rwanda PAYE
    tax_monthly = apply_tax(gross_monthly)

    net_monthly = gross_monthly - tax_monthly

    return {
        "emp_id": employee.emp_id,
        "name":   employee.name,
        "role":   employee.role(),
        "gross":  gross_monthly,
        "tax":    tax_monthly,
        "net":    net_monthly,
    }


def generate_payslip(employee: Employee) -> str:
    """
    Build a formatted payslip string for the given employee.

    Calls compute_payroll_details() internally; returns a multi-line
    string so the caller controls when and where it is printed.

    Args:
        employee: Any concrete Employee subclass instance.

    Returns:
        Ready-to-print multi-line payslip string.
    """
    data = compute_payroll_details(employee)
    lines = [
        divider(),
        "  PAYSLIP",
        divider(),
        f"  ID     : {data['emp_id']}",
        f"  Name   : {data['name']}",
        f"  Role   : {data['role']}",
        divider(),
        f"  Gross  : {format_currency(data['gross'])}",
        f"  Tax    : {format_currency(data['tax'])}",
        f"  Net    : {format_currency(data['net'])}",
        divider(),
    ]
    return "\n".join(lines)


def process_payroll(employees: list[Employee]) -> list[dict]:
    """
    Process payroll for a list of employees.

    Uses a list comprehension to apply compute_payroll_details() to
    every employee in a single, readable expression.

    Args:
        employees: List of concrete Employee instances.

    Returns:
        List of payroll detail dictionaries (one per employee).
    """
    return [compute_payroll_details(emp) for emp in employees]
