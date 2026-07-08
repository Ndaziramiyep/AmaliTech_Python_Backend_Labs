"""payroll.py — Rwanda PAYE tax logic, payslip generation, and batch payroll processing."""

from employee import Employee
from utils import format_currency, divider


# Rwanda RRA monthly PAYE brackets: (lower_bound, upper_bound, rate)
# Tax is applied directly to monthly gross — no annualisation required.
_TAX_BRACKETS: list[tuple[float, float, float]] = [
    (0,       30_000,       0.00),
    (30_000,  100_000,      0.20),
    (100_000, float("inf"), 0.30),
]


def apply_tax(monthly_gross: float) -> float:
    """Compute monthly Rwanda PAYE tax using progressive brackets on the given gross."""
    if monthly_gross < 0:
        raise ValueError(f"monthly_gross cannot be negative, got {monthly_gross}.")
    tax = 0.0
    for lower, upper, rate in _TAX_BRACKETS:
        if monthly_gross <= lower:
            break  # income does not reach this bracket — stop early
        taxable_in_band = min(monthly_gross, upper) - lower
        tax += taxable_in_band * rate
    return tax


def compute_payroll_details(employee: Employee) -> dict:
    """Return a dict of gross, tax, and net monthly figures for the given employee."""
    gross = employee.calculate_salary()
    tax   = apply_tax(gross)
    net   = gross - tax
    return {
        "emp_id": employee.emp_id,
        "name":   employee.name,
        "role":   employee.role(),
        "gross":  gross,
        "tax":    tax,
        "net":    net,
    }


def generate_payslip(employee: Employee) -> str:
    """Build and return a formatted multi-line payslip string for the given employee."""
    data  = compute_payroll_details(employee)
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
    """Return a list of payroll detail dicts for every employee in the given list."""
    return [compute_payroll_details(emp) for emp in employees]
