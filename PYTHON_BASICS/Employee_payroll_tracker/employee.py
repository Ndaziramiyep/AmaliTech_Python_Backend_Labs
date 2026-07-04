"""
employee.py
Defines the Employee abstract base class and its concrete role subclasses.

Design:
- Employee is an ABC that enforces calculate_salary() and role() on every subclass.
- Property setters validate all numeric inputs at assignment time.
- is_tax_exempt is a property each subclass declares, keeping tax logic decoupled
  from the payroll module's isinstance checks.
"""

from abc import ABC, abstractmethod
from logger import get_logger

_log = get_logger(__name__)


class Employee(ABC):
    """
    Abstract base class representing a generic employee.

    Subclasses must implement:
        - calculate_salary() -> float
        - role()             -> str
        - is_tax_exempt      -> bool  (property)
    """

    def __init__(self, emp_id: str, name: str, base_salary: float) -> None:
        """
        Initialise shared employee attributes.

        Args:
            emp_id:      Unique employee identifier (e.g. 'FT001').
            name:        Full name of the employee.
            base_salary: Primary pay figure; must be > 0.
        """
        self.emp_id = emp_id
        self.name = name
        self.base_salary = base_salary  # validated via setter
        _log.debug("Created %s: id=%s, name=%s", self.__class__.__name__, emp_id, name)

    # ------------------------------------------------------------------
    # Validated property
    # ------------------------------------------------------------------

    @property
    def base_salary(self) -> float:
        """Gross base pay before any additions (bonus, hours, etc.)."""
        return self._base_salary

    @base_salary.setter
    def base_salary(self, value: float) -> None:
        if value <= 0:
            _log.error("Invalid base_salary=%.2f for employee", value)
            raise ValueError(f"base_salary must be > 0, got {value}")
        self._base_salary = float(value)

    # ------------------------------------------------------------------
    # Abstract interface — every subclass must implement these
    # ------------------------------------------------------------------

    @abstractmethod
    def calculate_salary(self) -> float:
        """Return the monthly gross salary for this employee."""

    @abstractmethod
    def role(self) -> str:
        """Return a human-readable role label (e.g. 'Full-Time Employee')."""

    @property
    @abstractmethod
    def is_tax_exempt(self) -> bool:
        """Return True if this employee type is exempt from income tax."""

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        return f"{self.role()} | {self.emp_id} — {self.name}"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"emp_id={self.emp_id!r}, name={self.name!r})"
        )


# ----------------------------------------------------------------------
# Concrete subclasses
# ----------------------------------------------------------------------


class FullTimeEmployee(Employee):
    """
    Salaried employee who receives a fixed monthly base salary plus an
    optional bonus.

    Gross pay = base_salary + bonus
    """

    def __init__(
        self,
        emp_id: str,
        name: str,
        base_salary: float,
        bonus: float = 0.0,
    ) -> None:
        """
        Args:
            emp_id:      Unique employee identifier.
            name:        Full name.
            base_salary: Fixed monthly salary; must be > 0.
            bonus:       Optional monthly bonus; must be >= 0.
        """
        super().__init__(emp_id, name, base_salary)
        self.bonus = bonus  # validated via setter

    @property
    def bonus(self) -> float:
        """Optional monthly bonus on top of base salary."""
        return self._bonus

    @bonus.setter
    def bonus(self, value: float) -> None:
        if value < 0:
            _log.error("Invalid bonus=%.2f", value)
            raise ValueError(f"bonus must be >= 0, got {value}")
        self._bonus = float(value)

    def calculate_salary(self) -> float:
        """Gross = base salary + bonus."""
        return self._base_salary + self._bonus

    def role(self) -> str:
        return "Full-Time Employee"

    @property
    def is_tax_exempt(self) -> bool:
        return False


class ContractEmployee(Employee):
    """
    Employee paid on an hourly basis.

    Gross pay = hourly_rate × hours_worked
    """

    def __init__(
        self,
        emp_id: str,
        name: str,
        hourly_rate: float,
        hours_worked: float,
    ) -> None:
        """
        Args:
            emp_id:       Unique employee identifier.
            name:         Full name.
            hourly_rate:  Pay per hour; must be > 0.
            hours_worked: Total hours worked this month; must be >= 0.
        """
        # hourly_rate is stored as base_salary for shared validation logic
        super().__init__(emp_id, name, hourly_rate)
        self.hours_worked = hours_worked  # validated via setter

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
        if value < 0:
            _log.error("Invalid hours_worked=%.2f", value)
            raise ValueError(f"hours_worked must be >= 0, got {value}")
        self._hours_worked = float(value)

    def calculate_salary(self) -> float:
        """Gross = hourly rate × hours worked."""
        return self._base_salary * self._hours_worked

    def role(self) -> str:
        return "Contract Employee"

    @property
    def is_tax_exempt(self) -> bool:
        return False


class Intern(Employee):
    """
    Intern receiving a fixed monthly stipend.

    Interns are subject to the same PAYE tax rules as other employees.
    Gross pay = stipend (unchanged)
    """

    def __init__(self, emp_id: str, name: str, stipend: float) -> None:
        """
        Args:
            emp_id:  Unique employee identifier.
            name:    Full name.
            stipend: Fixed monthly stipend; must be > 0.
        """
        super().__init__(emp_id, name, stipend)

    @property
    def stipend(self) -> float:
        """Fixed monthly stipend (alias for base_salary)."""
        return self._base_salary

    def calculate_salary(self) -> float:
        """Gross = stipend (fixed, no additions)."""
        return self._base_salary

    def role(self) -> str:
        return "Intern"

    @property
    def is_tax_exempt(self) -> bool:
        return False
