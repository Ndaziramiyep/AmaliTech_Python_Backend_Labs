"""
employee.py
Defines the Employee base class and role-based subclasses.
"""


class Employee:
    """Base class representing a generic employee."""

    def __init__(self, emp_id: str, name: str, base_salary: float):
        self.emp_id = emp_id
        self.name = name
        self.base_salary = base_salary  # uses @property setter

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def base_salary(self) -> float:
        return self._base_salary

    @base_salary.setter
    def base_salary(self, value: float):
        if value <= 0:
            raise ValueError(f"base_salary must be > 0, got {value}")
        self._base_salary = float(value)

    # ------------------------------------------------------------------
    # Overridable methods
    # ------------------------------------------------------------------

    def calculate_salary(self) -> float:
        """Return gross salary. Subclasses override this."""
        return self._base_salary

    def role(self) -> str:
        """Return a human-readable role label."""
        return "Employee"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.emp_id!r}, name={self.name!r})"


# ----------------------------------------------------------------------
# Subclasses
# ----------------------------------------------------------------------

class FullTimeEmployee(Employee):
    """Salaried employee who may receive a monthly bonus."""

    def __init__(self, emp_id: str, name: str, base_salary: float, bonus: float = 0.0):
        super().__init__(emp_id, name, base_salary)
        self.bonus = bonus  # uses @property setter

    @property
    def bonus(self) -> float:
        return self._bonus

    @bonus.setter
    def bonus(self, value: float):
        if value < 0:
            raise ValueError(f"bonus must be >= 0, got {value}")
        self._bonus = float(value)

    def calculate_salary(self) -> float:
        """Gross = base salary + bonus."""
        return self._base_salary + self._bonus

    def role(self) -> str:
        return "Full-Time Employee"


class ContractEmployee(Employee):
    """Paid per hour worked."""

    def __init__(self, emp_id: str, name: str, hourly_rate: float, hours_worked: float):
        super().__init__(emp_id, name, hourly_rate)
        self.hours_worked = hours_worked  # uses @property setter

    @property
    def hourly_rate(self) -> float:
        """Alias for base_salary to improve readability."""
        return self._base_salary

    @property
    def hours_worked(self) -> float:
        return self._hours_worked

    @hours_worked.setter
    def hours_worked(self, value: float):
        if value < 0:
            raise ValueError(f"hours_worked must be >= 0, got {value}")
        self._hours_worked = float(value)

    def calculate_salary(self) -> float:
        """Gross = hourly rate × hours worked."""
        return self._base_salary * self._hours_worked

    def role(self) -> str:
        return "Contract Employee"


class Intern(Employee):
    """Receives a fixed stipend; no tax applied (handled in payroll)."""

    def __init__(self, emp_id: str, name: str, stipend: float):
        super().__init__(emp_id, name, stipend)

    @property
    def stipend(self) -> float:
        return self._base_salary

    def calculate_salary(self) -> float:
        """Gross = stipend (fixed)."""
        return self._base_salary

    def role(self) -> str:
        return "Intern"
