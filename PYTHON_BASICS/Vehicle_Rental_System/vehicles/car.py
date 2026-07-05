"""
vehicles/car.py
---------------
Defines the ``Car`` subclass of :class:`~vehicles.base.Vehicle`.

Pricing applies a $5/day surcharge for cars that seat more than 4 passengers,
reflecting the higher operational cost of larger vehicles.
"""

from .base import Vehicle


class Car(Vehicle):
    """A rentable passenger car.

    Args:
        vehicle_id: Unique identifier, e.g. ``"C001"``.
        make: Manufacturer name.
        model: Model name.
        year: Manufacturing year.
        base_rate: Daily base rental rate in USD.
        num_passengers: Maximum seating capacity; must be between 1 and 15.

    Raises:
        ValueError: If *num_passengers* is outside the valid range.
    """

    def __init__(
        self,
        vehicle_id: str,
        make: str,
        model: str,
        year: int,
        base_rate: float,
        num_passengers: int,
    ) -> None:
        if not isinstance(num_passengers, int) or not (1 <= num_passengers <= 15):
            raise ValueError("num_passengers must be an integer between 1 and 15.")
        super().__init__(vehicle_id, make, model, year, base_rate)
        self._num_passengers: int = num_passengers

    @property
    def num_passengers(self) -> int:
        """Maximum seating capacity of this car."""
        return self._num_passengers

    @property
    def type_label(self) -> str:
        """Vehicle type label."""
        return "Car"

    def rental_cost(self, days: int) -> float:
        """Calculate rental cost with a large-vehicle surcharge.

        A flat $5/day surcharge applies when seating capacity exceeds 4.

        Args:
            days: Number of rental days; must be a positive integer.

        Returns:
            Total rental cost in USD.

        Raises:
            ValueError: If *days* is not a positive integer.
        """
        if not isinstance(days, int) or days <= 0:
            raise ValueError("days must be a positive integer.")
        surcharge = 5.0 if self._num_passengers > 4 else 0.0
        return (self._base_rate + surcharge) * days

    def __repr__(self) -> str:
        return (
            f"Car(vehicle_id={self._vehicle_id!r}, make={self._make!r}, "
            f"model={self._model!r}, year={self._year}, "
            f"base_rate={self._base_rate}, num_passengers={self._num_passengers})"
        )
