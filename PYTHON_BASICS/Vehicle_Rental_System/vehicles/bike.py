"""
vehicles/bike.py
----------------
Defines the ``Bike`` subclass of :class:`~vehicles.base.Vehicle`.

Pricing applies a 10% surcharge for bikes with engine displacement above 500cc,
reflecting higher insurance and fuel costs for high-performance motorcycles.
"""

from .base import Vehicle


class Bike(Vehicle):
    """A rentable motorcycle or scooter.

    Args:
        vehicle_id: Unique identifier, e.g. ``"B001"``.
        make: Manufacturer name.
        model: Model name.
        year: Manufacturing year.
        base_rate: Daily base rental rate in USD.
        engine_cc: Engine displacement in cubic centimetres; must be between 50 and 2500.

    Raises:
        ValueError: If *engine_cc* is outside the valid range.
    """

    def __init__(
        self,
        vehicle_id: str,
        make: str,
        model: str,
        year: int,
        base_rate: float,
        engine_cc: int,
    ) -> None:
        if not isinstance(engine_cc, int) or not (50 <= engine_cc <= 2500):
            raise ValueError("engine_cc must be an integer between 50 and 2500.")
        super().__init__(vehicle_id, make, model, year, base_rate)
        self._engine_cc: int = engine_cc

    @property
    def engine_cc(self) -> int:
        """Engine displacement in cubic centimetres."""
        return self._engine_cc

    @property
    def type_label(self) -> str:
        """Vehicle type label."""
        return "Bike"

    def rental_cost(self, days: int) -> float:
        """Calculate rental cost with a high-displacement surcharge.

        A 10% rate multiplier is applied for engines above 500cc.

        Args:
            days: Number of rental days; must be a positive integer.

        Returns:
            Total rental cost in USD.

        Raises:
            ValueError: If *days* is not a positive integer.
        """
        if not isinstance(days, int) or days <= 0:
            raise ValueError("days must be a positive integer.")
        multiplier = 1.10 if self._engine_cc > 500 else 1.0
        return self._base_rate * multiplier * days

    def __repr__(self) -> str:
        return (
            f"Bike(vehicle_id={self._vehicle_id!r}, make={self._make!r}, "
            f"model={self._model!r}, year={self._year}, "
            f"base_rate={self._base_rate}, engine_cc={self._engine_cc})"
        )
