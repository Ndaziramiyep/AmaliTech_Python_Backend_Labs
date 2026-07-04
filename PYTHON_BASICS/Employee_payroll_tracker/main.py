"""
main.py
CLI entry point for the Employee Payroll Tracker.

Flow:
    1. collect_employees() — interactive loop; builds the employee list.
    2. print_all_payslips() — prints one formatted payslip per employee.
    3. process_payroll()    — computes payroll dicts for all employees.
    4. print_summary()      — prints the tabular summary with totals.
"""

from employee import Employee, FullTimeEmployee, ContractEmployee, Intern
from payroll import generate_payslip, process_payroll
from utils import format_currency, divider, format_header


# Maps menu keys to (display label, factory function) pairs.
# Adding a new employee type only requires one new entry here.
_ROLE_MAP: dict[str, tuple[str, callable]] = {
    "1": ("Full-Time Employee", None),  # factories assigned below
    "2": ("Contract Employee",  None),
    "3": ("Intern",             None),
}


# ------------------------------------------------------------------
# Input helpers
# ------------------------------------------------------------------

def prompt_float(label: str, min_val: float = 0.0) -> float:
    """
    Prompt the user for a float value, repeating until valid input is given.

    Args:
        label:   Text shown in the prompt.
        min_val: Minimum acceptable value (inclusive).

    Returns:
        A validated float >= min_val.
    """
    while True:
        try:
            value = float(input(f"  {label}: ").strip())
            if value < min_val:
                print(f"  ! Value must be >= {min_val:.2f}. Try again.")
            else:
                return value
        except ValueError:
            print("  ! Invalid number. Try again.")


# ------------------------------------------------------------------
# Employee factory functions
# ------------------------------------------------------------------

def _add_full_time() -> FullTimeEmployee:
    """Collect input and return a new FullTimeEmployee instance."""
    print("\n  -- Full-Time Employee --")
    emp_id = input("  Employee ID  : ").strip()
    name   = input("  Name         : ").strip()
    salary = prompt_float("Base Salary   ", min_val=0.01)
    bonus  = prompt_float("Bonus (0 if none)", min_val=0.0)
    return FullTimeEmployee(emp_id, name, salary, bonus)


def _add_contract() -> ContractEmployee:
    """Collect input and return a new ContractEmployee instance."""
    print("\n  -- Contract Employee --")
    emp_id = input("  Employee ID  : ").strip()
    name   = input("  Name         : ").strip()
    rate   = prompt_float("Hourly Rate   ", min_val=0.01)
    hours  = prompt_float("Hours Worked  ", min_val=0.0)
    return ContractEmployee(emp_id, name, rate, hours)


def _add_intern() -> Intern:
    """Collect input and return a new Intern instance."""
    print("\n  -- Intern --")
    emp_id  = input("  Employee ID  : ").strip()
    name    = input("  Name         : ").strip()
    stipend = prompt_float("Stipend       ", min_val=0.01)
    return Intern(emp_id, name, stipend)


# Assign factory functions now that they are defined
_ROLE_MAP["1"] = ("Full-Time Employee", _add_full_time)
_ROLE_MAP["2"] = ("Contract Employee",  _add_contract)
_ROLE_MAP["3"] = ("Intern",             _add_intern)


# ------------------------------------------------------------------
# Collection loop
# ------------------------------------------------------------------

def collect_employees() -> list[Employee]:
    """
    Run the interactive menu loop to collect employee data from the user.

    Continues until the user selects '0' (done) with at least one
    employee already added.

    Returns:
        List of Employee subclass instances entered by the user.
    """
    employees: list[Employee] = []
    print(format_header("EMPLOYEE PAYROLL TRACKER"))

    while True:
        print("\n  Select employee type:")
        for key, (label, _) in _ROLE_MAP.items():
            print(f"    [{key}] {label}")
        # Only show the exit option once at least one employee has been added
        if employees:
            print("    [0] Done — generate payroll")

        choice = input("\n  Your choice: ").strip()

        if choice == "0":
            if not employees:
                print("  ! Invalid choice. Enter 1, 2, or 3.")
            else:
                break
        elif choice in _ROLE_MAP:
            try:
                emp = _ROLE_MAP[choice][1]()
                employees.append(emp)
                print(f"\n  + {emp.name} added successfully.")
            except ValueError as exc:
                print(f"  ! Error: {exc}")
        else:
            print("  ! Invalid choice. Enter 1, 2, 3, or 0.")

    return employees


# ------------------------------------------------------------------
# Output functions
# ------------------------------------------------------------------

def print_all_payslips(employees: list[Employee]) -> None:
    """
    Print a formatted payslip for every employee in the list.

    Args:
        employees: List of Employee instances to print payslips for.
    """
    print("\n" + format_header("PAYSLIPS"))
    for emp in employees:
        print(generate_payslip(emp))


def print_summary(payroll_data: list[dict]) -> None:
    """
    Print a tabular payroll summary followed by company-wide totals.

    Args:
        payroll_data: List of payroll detail dicts from process_payroll().
    """
    col_width = 62

    print("\n" + divider(col_width, "="))
    print(f"  {'ID':<8} {'Name':<18} {'Role':<22} {'Net Pay':>10}")
    print(divider(col_width, "="))

    # Accumulate totals while printing each row
    total_gross, total_tax, total_net = 0.0, 0.0, 0.0

    for record in payroll_data:
        print(
            f"  {record['emp_id']:<8} {record['name']:<18} "
            f"{record['role']:<22} {format_currency(record['net']):>10}"
        )
        total_gross += record["gross"]
        total_tax   += record["tax"]
        total_net   += record["net"]

    print(divider(col_width, "-"))
    print(f"  {'TOTALS':<49} {format_currency(total_net):>10}")
    print(f"  Total Gross : {format_currency(total_gross)}")
    print(f"  Total Tax   : {format_currency(total_tax)}")
    print(f"  Total Net   : {format_currency(total_net)}")
    print(divider(col_width, "="))


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def main() -> None:
    """
    Orchestrate the full payroll tracker workflow:
        collect → payslips → process → summary.
    """
    employees    = collect_employees()
    print_all_payslips(employees)
    payroll_data = process_payroll(employees)
    print_summary(payroll_data)


if __name__ == "__main__":
    main()
