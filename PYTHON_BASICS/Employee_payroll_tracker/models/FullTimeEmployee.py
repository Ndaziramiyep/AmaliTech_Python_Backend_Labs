"""models/FullTimeEmployee.py — Salaried employee with an optional monthly bonus."""

from models.Employee import Employee


class FullTimeEmployee(Employee):
    """Salaried employee; gross = base_salary + bonus."""

    def __init__(self, emp_id: str, name: str, base_salary: float, bonus: float = 0.0) -> None:
        """Initialise with a fixed monthly salary and an optional bonus."""
        super().__init__(emp_id, name, base_salary)
        self.bonus = bonus  # routed through setter

    @property
    def bonus(self) -> float:
        """Optional monthly bonus on top of base salary."""
        return self._bonus

    @bonus.setter
    def bonus(self, value: float) -> None:
        """Raise ValueError if bonus is negative or not a number."""
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"bonus must be a number, got {type(value).__name__}.")
        if value < 0:
            raise ValueError(f"bonus must be >= 0, got {value}.")
        self._bonus = float(value)

    def calculate_salary(self) -> float:
        """Return gross pay as base salary plus bonus."""
        return self._base_salary + self._bonus

    def role(self) -> str:
        return "Full-Time Employee"

    @property
    def is_tax_exempt(self) -> bool:
        return False
