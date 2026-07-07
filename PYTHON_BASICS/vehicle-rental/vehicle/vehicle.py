"""Base module defining the abstract Vehicle class."""

from abc import ABC, abstractmethod


class Vehicle(ABC):
    """Abstract base class representing a rentable vehicle."""

    def __init__(self, vehicle_id: str, brand: str, base_price: float) -> None:
        """
        Initialize a Vehicle instance.

        Args:
            vehicle_id: Unique identifier for the vehicle.
            brand: Manufacturer or brand name.
            base_price: Daily rental rate in dollars.
        """
        if not vehicle_id or not vehicle_id.strip():
            raise ValueError("vehicle_id must be a non-empty string.")
        if not brand or not brand.strip():
            raise ValueError("brand must be a non-empty string.")
        if base_price <= 0:
            raise ValueError("base_price must be a positive number.")
        self.vehicle_id = vehicle_id.strip()
        self.brand = brand.strip()
        self.base_price = base_price
        self._is_rented = False

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def display_details(self) -> None:
        """Print full details of the vehicle."""

    @abstractmethod
    def calculate_rental_cost(self, days: int) -> float:
        """
        Return the total rental cost for the given number of days.

        Args:
            days: Must be a positive integer.

        Raises:
            ValueError: If days is less than 1.
        """

    # ------------------------------------------------------------------
    # Encapsulated rental state
    # ------------------------------------------------------------------

    @property
    def is_rented(self) -> bool:
        """Return True if the vehicle is currently rented."""
        return self._is_rented

    @is_rented.setter
    def is_rented(self, status: bool) -> None:
        self._is_rented = status

    # ------------------------------------------------------------------
    # Rental operations
    # ------------------------------------------------------------------

    def _validate_days(self, days: int) -> None:
        """Raise ValueError if days is not a positive integer."""
        if not isinstance(days, int) or days < 1:
            raise ValueError(f"days must be a positive integer, got {days!r}.")

    def rent(self) -> bool:
        """Mark vehicle as rented. Returns False if already rented."""
        if self._is_rented:
            return False
        self._is_rented = True
        return True

    def return_vehicle(self) -> bool:
        """Mark vehicle as returned. Returns False if not currently rented."""
        if not self._is_rented:
            return False
        self._is_rented = False
        return True

    def __str__(self) -> str:
        status = "Rented" if self._is_rented else "Available"
        return (
            f"[{self.__class__.__name__}] ID: {self.vehicle_id} | "
            f"Brand: {self.brand} | Rate: ${self.base_price}/day | Status: {status}"
        )
