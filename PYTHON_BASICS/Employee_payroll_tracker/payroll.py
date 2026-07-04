"""
payroll.py
Core payroll functions: tax calculation, salary processing, payslip generation.
"""

from employee import Employee, Intern
from utils import format_currency, divider


# Tax brackets (annual-equivalent thresholds applied to monthly gross × 12)
# Rates are illustrative; adjust to your locale.
_TAX_BRACKETS = [
    (0,      5_000,  0.00),
    (5_000,  20_000, 0.10),
    (20_000, 40_000, 0.20),
    (40_000, float("inf"), 0.30),
]


def apply_tax(annual_gross: float) -> float:
    """
    Compute annual income tax using progressive brackets.

    Args:
        annual_gross: Annualised gross salary.

    Returns:
        Total annual tax owed.
    """
    tax = 0.0
    for lower, upper, rate in _TAX_BRACKETS:
        if annual_gross <= lower:
            break
        taxable = min(annual_gross, upper) - lower
        tax += taxable * rate
    return tax


def calculate_salary(employee: Employee) -> dict:
    """
    Compute full payroll details for one employee.

    Args:
        employee: Any Employee subclass instance.

    Returns:
        Dictionary with gross, tax, and net figures (monthly).
    """
    gross_monthly = employee.calculate_salary()

    # Interns are tax-exempt
    if isinstance(employee, Intern):
        tax_monthly = 0.0
    else:
        annual_tax = apply_tax(gross_monthly * 12)
        tax_monthly = annual_tax / 12

    net_monthly = gross_monthly - tax_monthly

    return {
        "emp_id": employee.emp_id,
        "name": employee.name,
        "role": employee.role(),
        "gross": gross_monthly,
        "tax": tax_monthly,
        "net": net_monthly,
    }


def generate_payslip(employee: Employee) -> str:
    """
    Build a formatted payslip string for the given employee.

    Args:
        employee: Any Employee subclass instance.

    Returns:
        Multi-line payslip string ready for printing.
    """
    data = calculate_salary(employee)
    lines = [
        divider(),
        f"  PAYSLIP",
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

    Args:
        employees: List of Employee instances.

    Returns:
        List of payroll detail dictionaries.
    """
    return [calculate_salary(emp) for emp in employees]
