"""
vehicles/car.py
---------------
Defines the ``Car`` subclass of :class:`~vehicles.base.Vehicle`.

Pricing applies a $5/day surcharge for cars that seat more than 4 passengers.
"""

from .base import Vehicle


class Car(Vehicle):
    """A rentable car.

    Args:
        vehicle_id: Unique identifier (e.g. ``"C001"``).
        make: Manufacturer name.
        model: Model name.
        year: Manufacturing year.
        base_rate: Daily base rental rate in USD.
        num_passengers: Maximum passenger capacity; must be between 1 and 15.

    Raises:
        ValueError: If *num_passengers* is outside the valid range.
    """

    def __init__(self, vehicle_id: str, make: str, model: str, year: int,
                 base_rate: float, num_passengers: int):
        if not isinstance(num_passengers, int) or not (1 <= num_passengers <= 15):
            raise ValueError("num_passengers must be an integer between 1 and 15.")
        super().__init__(vehicle_id, make, model, year, base_rate)
        self._num_passengers = num_passengers

    @property
    def num_passengers(self) -> int:
        """Maximum passenger capacity of this car."""
        return self._num_passengers

    def rental_cost(self, days: int) -> float:
        """Calculate rental cost with a passenger surcharge.

        A $5/day surcharge is applied when passenger capacity exceeds 4.

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
