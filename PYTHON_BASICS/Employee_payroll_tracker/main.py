"""main.py — CLI entry point for the Employee Payroll Tracker."""

from employee import Employee, FullTimeEmployee, ContractEmployee, Intern
from payroll import generate_payslip, process_payroll
from utils import format_currency, divider, format_header


# Maps menu keys to (display label, factory function) pairs.
# To add a new employee type, insert one entry here — nothing else changes.
_ROLE_MAP: dict[str, tuple[str, callable]] = {
    "1": ("Full-Time Employee", None),
    "2": ("Contract Employee", None),
    "3": ("Intern", None),
}


# ----------------------------------------------------------------------
# Input helpers
# ----------------------------------------------------------------------


def prompt_emp_id(existing_ids: set[str]) -> str:
    """Prompt until a valid, unique alphanumeric employee ID is entered."""
    while True:
        raw = input("  Employee ID     (e.g. FT001)    : ").strip()
        if not raw:
            print("  ! ID cannot be empty.")
        elif len(raw) > 10:
            print("  ! ID must be 10 characters or fewer.")
        elif not raw.isalnum():
            print("  ! ID must contain only letters and digits (e.g. FT001).")
        elif raw.upper() in existing_ids:
            print(f"  ! ID '{raw.upper()}' is already taken. Use a different ID.")
        else:
            return raw.upper()


def prompt_name() -> str:
    """Prompt until a valid full name with only letters, spaces, hyphens, or apostrophes is entered."""
    while True:
        raw = input("  Full Name (e.g. Nziza Paul) : ").strip()
        if not raw:
            print("  ! Name cannot be empty.")
        elif len(raw) < 2:
            print("  ! Name must be at least 2 characters.")
        elif len(raw) > 50:
            print("  ! Name must be 50 characters or fewer.")
        elif not all(ch.isalpha() or ch in " -'" for ch in raw):
            print(
                "  ! Name must contain only letters, spaces, hyphens, or apostrophes."
            )
        else:
            return raw.title()


def prompt_float(label: str, min_val: float = 0.0) -> float:
    """Prompt until a valid float greater than or equal to min_val is entered."""
    while True:
        try:
            value = float(input(f"  {label}: ").strip())
            if value < min_val:
                print(f"  ! Value must be >= {min_val:,.2f}.")
            else:
                return value
        except ValueError:
            print("  ! Invalid number — enter digits only (e.g. 350000).")


# ----------------------------------------------------------------------
# Employee factory functions
# ----------------------------------------------------------------------


def _add_full_time(existing_ids: set[str]) -> FullTimeEmployee:
    """Collect validated input and return a new FullTimeEmployee."""
    print("\n  -- Full-Time Employee --")
    emp_id = prompt_emp_id(existing_ids)
    name = prompt_name()
    salary = prompt_float("Base Salary (e.g. 350000)          ", min_val=0.01)
    bonus = prompt_float("Monthly Bonus (e.g. 50000, 0 if none)", min_val=0.0)
    return FullTimeEmployee(emp_id, name, salary, bonus)


def _add_contract(existing_ids: set[str]) -> ContractEmployee:
    """Collect validated input and return a new ContractEmployee."""
    print("\n  -- Contract Employee --")
    emp_id = prompt_emp_id(existing_ids)
    name = prompt_name()
    rate = prompt_float("Hourly Rate (e.g. 3000)            ", min_val=0.01)
    hours = prompt_float("Hours Worked (e.g. 160)             ", min_val=0.0)
    return ContractEmployee(emp_id, name, rate, hours)


def _add_intern(existing_ids: set[str]) -> Intern:
    """Collect validated input and return a new Intern."""
    print("\n  -- Intern --")
    emp_id = prompt_emp_id(existing_ids)
    name = prompt_name()
    stipend = prompt_float("Monthly Stipend (e.g. 80000)           ", min_val=0.01)
    return Intern(emp_id, name, stipend)


# Assign factories after definition to avoid forward-reference issues
_ROLE_MAP["1"] = ("Full-Time Employee", _add_full_time)
_ROLE_MAP["2"] = ("Contract Employee", _add_contract)
_ROLE_MAP["3"] = ("Intern", _add_intern)


# ----------------------------------------------------------------------
# Collection loop
# ----------------------------------------------------------------------


def collect_employees() -> list[Employee]:
    """Run the interactive menu loop and return the collected list of employees."""
    employees: list[Employee] = []
    existing_ids: set[str] = set()
    print(format_header("EMPLOYEE PAYROLL TRACKER"))

    while True:
        print("\n  Select employee type:")
        for key, (label, _) in _ROLE_MAP.items():
            print(f"    [{key}] {label}")
        if employees:  # show exit option only after at least one employee is added
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
                existing_ids.add(emp.emp_id)
                print(f"\n  + {emp.name} ({emp.emp_id}) added successfully.")
            except ValueError as exc:
                print(f"  ! Error: {exc}")
        else:
            print("  ! Invalid choice. Enter 1, 2, or 3.")

    return employees


# ----------------------------------------------------------------------
# Output functions
# ----------------------------------------------------------------------


def print_all_payslips(employees: list[Employee]) -> None:
    """Print a formatted payslip for every employee in the list."""
    print("\n" + format_header("PAYSLIPS"))
    for emp in employees:
        print(generate_payslip(emp))


def print_summary(payroll_data: list[dict]) -> None:
    """Print a tabular payroll summary with gross, tax, and net totals."""
    col_width = 62

    print("\n" + divider(col_width, "="))
    print(f"  {'ID':<8} {'Name':<18} {'Role':<22} {'Net Pay':>10}")
    print(divider(col_width, "="))

    total_gross, total_tax, total_net = 0.0, 0.0, 0.0

    for record in payroll_data:
        print(
            f"  {record['emp_id']:<8} {record['name']:<18} "
            f"{record['role']:<22} {format_currency(record['net']):>10}"
        )
        total_gross += record["gross"]
        total_tax += record["tax"]
        total_net += record["net"]

    print(divider(col_width, "-"))
    print(f"  {'TOTALS':<49} {format_currency(total_net):>10}")
    print(f"  Total Gross : {format_currency(total_gross)}")
    print(f"  Total Tax   : {format_currency(total_tax)}")
    print(f"  Total Net   : {format_currency(total_net)}")
    print(divider(col_width, "="))


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------


def main() -> None:
    """Orchestrate the full payroll workflow: collect → payslips → process → summary."""
    employees = collect_employees()
    print_all_payslips(employees)
    payroll_data = process_payroll(employees)
    print_summary(payroll_data)


if __name__ == "__main__":
    main()
