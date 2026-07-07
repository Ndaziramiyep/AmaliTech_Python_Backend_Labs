"""models/ContractEmployee.py — Hourly-paid employee."""

from models.Employee import Employee


class ContractEmployee(Employee):
    """Hourly-paid employee; gross = hourly_rate × hours_worked."""

    def __init__(self, emp_id: str, name: str, hourly_rate: float, hours_worked: float) -> None:
        """Initialise with an hourly rate and total hours worked this month."""
        super().__init__(emp_id, name, hourly_rate)  # hourly_rate stored as base_salary
        self.hours_worked = hours_worked  # routed through setter

    @property
    def hourly_rate(self) -> float:
        """Pay rate per hour (alias for base_salary)."""
        return self._base_salary

    @property
    def hours_worked(self) -> float:
        """Total hours worked in the current pay period."""
        return self._hours_worked

    @hours_worked.setter
    def hours_worked(self, value: float) -> None:
        """Raise ValueError if hours_worked is negative or not a number."""
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"hours_worked must be a number, got {type(value).__name__}.")
        if value < 0:
            raise ValueError(f"hours_worked must be >= 0, got {value}.")
        self._hours_worked = float(value)

    def calculate_salary(self) -> float:
        """Return gross pay as hourly rate multiplied by hours worked."""
        return self._base_salary * self._hours_worked

    def role(self) -> str:
        return "Contract Employee"

    @property
    def is_tax_exempt(self) -> bool:
        return False
