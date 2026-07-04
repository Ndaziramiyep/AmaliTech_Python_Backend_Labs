"""
main.py
Entry point for the Employee Payroll Tracker CLI.
"""

from employee import FullTimeEmployee, ContractEmployee, Intern
from payroll import generate_payslip, process_payroll
from utils import format_currency, divider


def prompt_float(label: str, min_val: float = 0.0) -> float:
    """Prompt until a valid float above min_val is entered."""
    while True:
        try:
            value = float(input(f"  {label}: ").strip())
            if value < min_val:
                print(f"  X Value must be >= {min_val}. Try again.")
            else:
                return value
        except ValueError:
            print("  X Invalid number. Try again.")


def add_full_time() -> FullTimeEmployee:
    """Collect data and return a FullTimeEmployee instance."""
    print("\n  -- Full-Time Employee --")
    emp_id = input("  Employee ID : ").strip()
    name   = input("  Name        : ").strip()
    salary = prompt_float("Base Salary  ", min_val=0.01)
    bonus  = prompt_float("Bonus (0 if none)", min_val=0.0)
    return FullTimeEmployee(emp_id, name, salary, bonus)


def add_contract() -> ContractEmployee:
    """Collect data and return a ContractEmployee instance."""
    print("\n  -- Contract Employee --")
    emp_id = input("  Employee ID : ").strip()
    name   = input("  Name        : ").strip()
    rate   = prompt_float("Hourly Rate  ", min_val=0.01)
    hours  = prompt_float("Hours Worked ", min_val=0.0)
    return ContractEmployee(emp_id, name, rate, hours)


def add_intern() -> Intern:
    """Collect data and return an Intern instance."""
    print("\n  -- Intern --")
    emp_id  = input("  Employee ID : ").strip()
    name    = input("  Name        : ").strip()
    stipend = prompt_float("Stipend      ", min_val=0.01)
    return Intern(emp_id, name, stipend)


ROLE_MAP = {
    "1": ("Full-Time Employee", add_full_time),
    "2": ("Contract Employee",  add_contract),
    "3": ("Intern",             add_intern),
}


def collect_employees() -> list:
    """Interactive loop to collect one or more employees from the user."""
    employees = []
    print("\n" + "=" * 40)
    print("    EMPLOYEE PAYROLL TRACKER")
    print("=" * 40)

    while True:
        print("\n  Select employee type:")
        for key, (label, _) in ROLE_MAP.items():
            print(f"    [{key}] {label}")
        print("    [0] Done — generate payroll")

        choice = input("\n  Your choice: ").strip()

        if choice == "0":
            if not employees:
                print("  X Add at least one employee first.")
            else:
                break
        elif choice in ROLE_MAP:
            try:
                emp = ROLE_MAP[choice][1]()
                employees.append(emp)
                print(f"\n  + {emp.name} added successfully.")
            except ValueError as e:
                print(f"  X Error: {e}")
        else:
            print("  X Invalid choice. Enter 1, 2, 3, or 0.")

    return employees


def print_all_payslips(employees: list):
    """Print individual payslips for every employee."""
    print("\n" + "=" * 40)
    print("           PAYSLIPS")
    print("=" * 40)
    for emp in employees:
        print(generate_payslip(emp))


def print_summary(payroll_data: list[dict]):
    """Print a tabular payroll summary and company totals."""
    print("\n" + divider(60, "="))
    print(f"  {'ID':<8} {'Name':<18} {'Role':<20} {'Net Pay':>10}")
    print(divider(60, "="))

    total_gross = total_tax = total_net = 0.0

    for d in payroll_data:
        print(f"  {d['emp_id']:<8} {d['name']:<18} {d['role']:<20} "
              f"{format_currency(d['net']):>10}")
        total_gross += d["gross"]
        total_tax   += d["tax"]
        total_net   += d["net"]

    print(divider(60, "-"))
    print(f"  {'TOTALS':<47} {format_currency(total_net):>10}")
    print(f"  Total Gross : {format_currency(total_gross)}")
    print(f"  Total Tax   : {format_currency(total_tax)}")
    print(f"  Total Net   : {format_currency(total_net)}")
    print(divider(60, "="))


def main():
    employees = collect_employees()
    print_all_payslips(employees)
    payroll_data = process_payroll(employees)
    print_summary(payroll_data)


if __name__ == "__main__":
    main()
