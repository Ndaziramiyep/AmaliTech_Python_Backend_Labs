"""Employee base class and concrete role subclasses."""

from abc import ABC, abstractmethod


class Employee(ABC):
    """Abstract base for all employee types."""

    def __init__(self, emp_id: str, name: str, base_salary: float) -> None:
        if not emp_id or not emp_id.strip():
            raise ValueError("emp_id cannot be empty.")
        if not name or not name.strip():
            raise ValueError("name cannot be empty.")
        self.emp_id = emp_id.strip().upper()
        self.name = name.strip()
        self.base_salary = base_salary

    @property
    def base_salary(self) -> float:
        return self._base_salary

    @base_salary.setter
    def base_salary(self, value: float) -> None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(
                f"base_salary must be a number, got {type(value).__name__}."
            )
        if value <= 0:
            raise ValueError(f"base_salary must be > 0, got {value}.")
        self._base_salary = float(value)

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

    def __str__(self) -> str:
        return f"{self.role()} | {self.emp_id} — {self.name}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(emp_id={self.emp_id!r }, name={self.name!r})"


class FullTimeEmployee(Employee):
    """Salaried employee; gross = base_salary + bonus."""

    def __init__(
        self, emp_id: str, name: str, base_salary: float, bonus: float = 0.0
    ) -> None:
        super().__init__(emp_id, name, base_salary)
        self.bonus = bonus

    @property
    def bonus(self) -> float:
        return self._bonus

    @bonus.setter
    def bonus(self, value: float) -> None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"bonus must be a number, got {type(value).__name__}.")
        if value < 0:
            raise ValueError(f"bonus must be >= 0, got {value}.")
        self._bonus = float(value)

    def calculate_salary(self) -> float:
        return self._base_salary + self._bonus

    def role(self) -> str:
        return "Full-Time Employee"

    @property
    def is_tax_exempt(self) -> bool:
        return False


class ContractEmployee(Employee):
    """Hourly-paid employee; gross = hourly_rate × hours_worked."""

    def __init__(
        self, emp_id: str, name: str, hourly_rate: float, hours_worked: float
    ) -> None:
        super().__init__(emp_id, name, hourly_rate)
        self.hours_worked = hours_worked

    @property
    def hourly_rate(self) -> float:
        return self._base_salary

    @property
    def hours_worked(self) -> float:
        return self._hours_worked

    @hours_worked.setter
    def hours_worked(self, value: float) -> None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(
                f"hours_worked must be a number, got {type(value).__name__}."
            )
        if value < 0:
            raise ValueError(f"hours_worked must be >= 0, got {value}.")
        self._hours_worked = float(value)

    def calculate_salary(self) -> float:
        return self._base_salary * self._hours_worked

    def role(self) -> str:
        return "Contract Employee"

    @property
    def is_tax_exempt(self) -> bool:
        return False


class Intern(Employee):
    """Intern on a fixed monthly stipend."""

    def __init__(self, emp_id: str, name: str, stipend: float) -> None:
        super().__init__(emp_id, name, stipend)

    @property
    def stipend(self) -> float:
        return self._base_salary

    def calculate_salary(self) -> float:
        return self._base_salary

    def role(self) -> str:
        return "Intern"

    @property
    def is_tax_exempt(self) -> bool:
        return False
