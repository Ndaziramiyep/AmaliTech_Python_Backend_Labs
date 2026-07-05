"""
models.py
---------
Shared data structures used across the Vehicle Rental System.
"""

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class RentalRecord:
    """Immutable record of a single rental transaction.

    Attributes:
        rental_id: Auto-generated unique rental identifier (e.g. ``"R0001"``).
        vehicle_id: ID of the rented vehicle.
        days: Number of days the vehicle is rented for.
        total_cost: Pre-calculated total rental cost in USD.
        rental_date: Calendar date the rental was created.
    """

    rental_id: str
    vehicle_id: str
    days: int
    total_cost: float
    rental_date: date = field(default_factory=date.today)

    def __str__(self) -> str:
        return (
            f"[{self.rental_id}] Vehicle: {self.vehicle_id} | "
            f"{self.days} day(s) | Cost: ${self.total_cost:.2f} | Date: {self.rental_date}"
        )
