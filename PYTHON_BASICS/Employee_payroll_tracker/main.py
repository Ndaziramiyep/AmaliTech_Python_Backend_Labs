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
from logger import get_logger

_log = get_logger(__name__)


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

def prompt_emp_id(existing_ids: set[str]) -> str:
    """
    Prompt for a unique, alphanumeric employee ID.

    Rules:
        - Must not be empty.
        - Must contain only letters and digits (no spaces or symbols).
        - Must not duplicate an ID already in existing_ids.

    Args:
        existing_ids: Set of IDs already registered in this session.

    Returns:
        A validated, uppercased employee ID string.
    """
    while True:
        raw = input("  Employee ID   (e.g. FT001)  : ").strip()
        if not raw:
            print("  ! ID cannot be empty. Try again.")
        elif not raw.isalnum():
            print("  ! ID must contain only letters and digits (e.g. FT001). Try again.")
        elif raw.upper() in existing_ids:
            print(f"  ! ID '{raw.upper()}' is already taken. Use a different ID.")
        else:
            return raw.upper()


def prompt_name() -> str:
    """
    Prompt for a non-empty full name containing only letters, spaces, and hyphens.

    Returns:
        A validated, title-cased name string.
    """
    while True:
        raw = input("  Full Name     (e.g. Nziza Paul) : ").strip()
        if not raw:
            print("  ! Name cannot be empty. Try again.")
        elif not all(ch.isalpha() or ch in " -'" for ch in raw):
            print("  ! Name must contain only letters, spaces, hyphens, or apostrophes. Try again.")
        else:
            return raw.title()


def prompt_float(label: str, min_val: float = 0.0) -> float:
    """
    Prompt the user for a float value, repeating until valid input is given.

    Args:
        label:   Full prompt text including sample hint.
        min_val: Minimum acceptable value (inclusive).

    Returns:
        A validated float >= min_val.
    """
    while True:
        try:
            value = float(input(f"  {label}: ").strip())
            if value < min_val:
                print(f"  ! Value must be >= {min_val:,.2f}. Try again.")
            else:
                return value
        except ValueError:
            print("  ! Invalid number — enter digits only (e.g. 350000). Try again.")


# ------------------------------------------------------------------
# Employee factory functions
# ------------------------------------------------------------------

def _add_full_time(existing_ids: set[str]) -> FullTimeEmployee:
    """Collect validated input and return a new FullTimeEmployee instance."""
    print("\n  -- Full-Time Employee --")
    emp_id = prompt_emp_id(existing_ids)
    name   = prompt_name()
    salary = prompt_float("Base Salary    (e.g. 350000) ", min_val=0.01)
    bonus  = prompt_float("Monthly Bonus  (e.g. 50000, 0 if none) ", min_val=0.0)
    return FullTimeEmployee(emp_id, name, salary, bonus)


def _add_contract(existing_ids: set[str]) -> ContractEmployee:
    """Collect validated input and return a new ContractEmployee instance."""
    print("\n  -- Contract Employee --")
    emp_id = prompt_emp_id(existing_ids)
    name   = prompt_name()
    rate   = prompt_float("Hourly Rate    (e.g. 3000)   ", min_val=0.01)
    hours  = prompt_float("Hours Worked   (e.g. 160)    ", min_val=0.0)
    return ContractEmployee(emp_id, name, rate, hours)


def _add_intern(existing_ids: set[str]) -> Intern:
    """Collect validated input and return a new Intern instance."""
    print("\n  -- Intern --")
    emp_id  = prompt_emp_id(existing_ids)
    name    = prompt_name()
    stipend = prompt_float("Monthly Stipend (e.g. 80000) ", min_val=0.01)
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

    Tracks registered IDs in a set to prevent duplicates. The '[0] Done'
    option is hidden until at least one employee has been added.

    Returns:
        List of Employee subclass instances entered by the user.
    """
    employees: list[Employee] = []
    existing_ids: set[str] = set()  # tracks all registered IDs this session
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
                emp = _ROLE_MAP[choice][1](existing_ids)
                employees.append(emp)
                existing_ids.add(emp.emp_id)  # register ID immediately
                _log.info("Employee added: %s (%s) as %s", emp.name, emp.emp_id, emp.role())
                print(f"\n  + {emp.name} ({emp.emp_id}) added successfully.")
            except ValueError as exc:
                _log.warning("Failed to add employee: %s", exc)
                print(f"  ! Error: {exc}")
        else:
            _log.debug("Invalid menu choice entered: %r", choice)
            print("  ! Invalid choice. Enter 1, 2, or 3.")

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
    _log.info("=== Payroll session started ===")
    employees    = collect_employees()
    _log.info("Total employees collected: %d", len(employees))
    print_all_payslips(employees)
    payroll_data = process_payroll(employees)
    print_summary(payroll_data)
    _log.info("=== Payroll session completed ===")


if __name__ == "__main__":
    main()
