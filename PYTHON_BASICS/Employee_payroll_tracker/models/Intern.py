"""models/Intern.py — Intern on a fixed monthly stipend."""

from models.Employee import Employee


class Intern(Employee):
    """Intern on a fixed monthly stipend; subject to Rwanda PAYE."""

    def __init__(self, emp_id: str, name: str, stipend: float) -> None:
        """Initialise with a fixed monthly stipend."""
        super().__init__(emp_id, name, stipend)  # stipend stored as base_salary

    @property
    def stipend(self) -> float:
        """Fixed monthly stipend (alias for base_salary)."""
        return self._base_salary

    def calculate_salary(self) -> float:
        """Return gross pay as the fixed stipend."""
        return self._base_salary

    def role(self) -> str:
        return "Intern"

    @property
    def is_tax_exempt(self) -> bool:
        return False
