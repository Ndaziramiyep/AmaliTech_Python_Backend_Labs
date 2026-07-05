"""
vehicles/truck.py
-----------------
Defines the ``Truck`` subclass of :class:`~vehicles.base.Vehicle`.

Pricing adds a $10/ton/day surcharge based on the truck's payload capacity,
reflecting the increased wear and fuel costs of heavier loads.
"""

from .base import Vehicle


class Truck(Vehicle):
    """A rentable cargo truck.

    Args:
        vehicle_id: Unique identifier, e.g. ``"T001"``.
        make: Manufacturer name.
        model: Model name.
        year: Manufacturing year.
        base_rate: Daily base rental rate in USD.
        payload_tons: Maximum payload in metric tons; must be between 0.1 and 50.

    Raises:
        ValueError: If *payload_tons* is outside the valid range.
    """

    def __init__(
        self,
        vehicle_id: str,
        make: str,
        model: str,
        year: int,
        base_rate: float,
        payload_tons: float,
    ) -> None:
        if not isinstance(payload_tons, (int, float)) or not (0.1 <= payload_tons <= 50):
            raise ValueError("payload_tons must be a number between 0.1 and 50.")
        super().__init__(vehicle_id, make, model, year, base_rate)
        self._payload_tons: float = float(payload_tons)

    @property
    def payload_tons(self) -> float:
        """Maximum payload capacity in metric tons."""
        return self._payload_tons

    @property
    def type_label(self) -> str:
        """Vehicle type label."""
        return "Truck"

    def rental_cost(self, days: int) -> float:
        """Calculate rental cost with a payload-based surcharge.

        A $10/ton/day surcharge is applied based on the truck's payload capacity.

        Args:
            days: Number of rental days; must be a positive integer.

        Returns:
            Total rental cost in USD.

        Raises:
            ValueError: If *days* is not a positive integer.
        """
        if not isinstance(days, int) or days <= 0:
            raise ValueError("days must be a positive integer.")
        return (self._base_rate + self._payload_tons * 10.0) * days

    def __repr__(self) -> str:
        return (
            f"Truck(vehicle_id={self._vehicle_id!r}, make={self._make!r}, "
            f"model={self._model!r}, year={self._year}, "
            f"base_rate={self._base_rate}, payload_tons={self._payload_tons})"
        )
