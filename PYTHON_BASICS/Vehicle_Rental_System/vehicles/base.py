"""
vehicles/base.py
----------------
Defines the abstract base class ``Vehicle`` that all vehicle types must extend.

Every concrete subclass must implement :meth:`rental_cost` to provide its own
pricing logic.  State transitions (available ↔ rented) are managed here so
subclasses do not need to repeat that logic.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from logger import get_logger

logger = get_logger(__name__)

_CURRENT_YEAR = datetime.now().year


class Vehicle(ABC):
    """Abstract base class representing a rentable vehicle.

    Args:
        vehicle_id: Unique alphanumeric identifier (e.g. ``"C001"``).
        make: Manufacturer name (e.g. ``"Toyota"``).
        model: Model name (e.g. ``"Camry"``).
        year: Manufacturing year; must be between 1886 and next calendar year.
        base_rate: Daily rental rate in USD; must be a positive number.

    Raises:
        ValueError: If any argument fails validation.
    """

    def __init__(self, vehicle_id: str, make: str, model: str, year: int, base_rate: float):
        if not vehicle_id or not vehicle_id.strip():
            raise ValueError("vehicle_id must be a non-empty string.")
        if not make or not make.strip():
            raise ValueError("make must be a non-empty string.")
        if not model or not model.strip():
            raise ValueError("model must be a non-empty string.")
        if not isinstance(year, int) or not (1886 <= year <= _CURRENT_YEAR + 1):
            raise ValueError(f"year must be an integer between 1886 and {_CURRENT_YEAR + 1}.")
        if base_rate <= 0:
            raise ValueError("base_rate must be a positive number.")

        self._vehicle_id = vehicle_id.strip()
        self._make = make.strip()
        self._model = model.strip()
        self._year = year
        self._base_rate = float(base_rate)
        self._is_available = True
        logger.debug("Vehicle created: %s", self)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def vehicle_id(self) -> str:
        """Unique identifier for this vehicle."""
        return self._vehicle_id

    @property
    def is_available(self) -> bool:
        """``True`` if the vehicle is available for rent."""
        return self._is_available

    @property
    def base_rate(self) -> float:
        """Daily base rental rate in USD."""
        return self._base_rate

    @base_rate.setter
    def base_rate(self, value: float):
        """Update the daily base rate.

        Args:
            value: New rate; must be a positive number.

        Raises:
            ValueError: If *value* is not positive.
        """
        if value <= 0:
            raise ValueError("base_rate must be a positive number.")
        logger.info("Base rate updated for %s: $%.2f -> $%.2f", self._vehicle_id, self._base_rate, value)
        self._base_rate = float(value)

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def rental_cost(self, days: int) -> float:
        """Calculate the total rental cost for the given number of days.

        Args:
            days: Number of rental days; must be a positive integer.

        Returns:
            Total cost in USD as a float.
        """

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def rent(self):
        """Mark this vehicle as rented.

        Raises:
            RuntimeError: If the vehicle is already rented.
        """
        if not self._is_available:
            logger.warning("Attempted to rent already-rented vehicle: %s", self._vehicle_id)
            raise RuntimeError(f"{self} is already rented.")
        self._is_available = False
        logger.info("Vehicle rented: %s", self._vehicle_id)

    def return_vehicle(self):
        """Mark this vehicle as available again.

        Raises:
            RuntimeError: If the vehicle was not rented.
        """
        if self._is_available:
            logger.warning("Attempted to return a vehicle that was not rented: %s", self._vehicle_id)
            raise RuntimeError(f"{self} was not rented.")
        self._is_available = True
        logger.info("Vehicle returned: %s", self._vehicle_id)

    def __str__(self) -> str:
        status = "Available" if self._is_available else "Rented"
        return f"[{self._vehicle_id}] {self._year} {self._make} {self._model} — {status}"
