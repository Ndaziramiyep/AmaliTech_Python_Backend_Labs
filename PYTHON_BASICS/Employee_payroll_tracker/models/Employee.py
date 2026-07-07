"""models/Employee.py — Abstract base class for all employee types."""

from abc import ABC, abstractmethod


class Employee(ABC):
    """Abstract base for all employee types; enforces calculate_salary, role, and is_tax_exempt."""

    def __init__(self, emp_id: str, name: str, base_salary: float) -> None:
        """Initialise shared employee attributes with validated inputs."""
        if not emp_id or not emp_id.strip():
            raise ValueError("emp_id cannot be empty.")
        if not name or not name.strip():
            raise ValueError("name cannot be empty.")
        self.emp_id = emp_id.strip().upper()
        self.name = name.strip()
        self.base_salary = base_salary  # routed through setter for validation

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def base_salary(self) -> float:
        """Monthly base pay before any additions."""
        return self._base_salary

    @base_salary.setter
    def base_salary(self, value: float) -> None:
        """Raise ValueError if value is not a positive number."""
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"base_salary must be a number, got {type(value).__name__}.")
        if value <= 0:
            raise ValueError(f"base_salary must be > 0, got {value}.")
        self._base_salary = float(value)

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def calculate_salary(self) -> float:
        """Return the monthly gross salary."""

    @abstractmethod
    def role(self) -> str:
        """Return a human-readable role label."""

    @property
    @abstractmethod
    def is_tax_exempt(self) -> bool:
        """Return True if this employee type pays no income tax."""

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        return f"{self.role()} | {self.emp_id} — {self.name}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(emp_id={self.emp_id!r}, name={self.name!r})"
