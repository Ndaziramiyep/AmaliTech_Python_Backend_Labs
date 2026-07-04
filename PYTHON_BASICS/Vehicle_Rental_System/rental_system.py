"""
rental_system.py
----------------
Manages the vehicle fleet and all rental transactions.

The :class:`RentalSystem` class is the central coordinator — it holds the
fleet inventory, processes rent/return requests, and delegates pricing to
each vehicle's own :meth:`~vehicles.base.Vehicle.rental_cost` implementation.
"""

from vehicles.base import Vehicle
from logger import get_logger

logger = get_logger(__name__)


class RentalSystem:
    """Central manager for the vehicle rental fleet.

    Maintains two internal collections:

    - ``_fleet``: all registered vehicles keyed by ``vehicle_id``.
    - ``_active_rentals``: ongoing rentals keyed by auto-generated rental ID.
    """

    def __init__(self):
        self._fleet: dict[str, Vehicle] = {}
        self._active_rentals: dict[str, tuple[Vehicle, int]] = {}
        self._rental_counter = 1
        logger.debug("RentalSystem initialised.")

    # ------------------------------------------------------------------
    # Fleet management
    # ------------------------------------------------------------------

    def add_vehicle(self, vehicle: Vehicle):
        """Register a vehicle in the fleet.

        Args:
            vehicle: A concrete :class:`~vehicles.base.Vehicle` instance.

        Raises:
            ValueError: If a vehicle with the same ID already exists.
        """
        if vehicle.vehicle_id in self._fleet:
            logger.warning("Duplicate vehicle ID rejected: %s", vehicle.vehicle_id)
            raise ValueError(f"A vehicle with ID '{vehicle.vehicle_id}' already exists.")
        self._fleet[vehicle.vehicle_id] = vehicle
        logger.info("Vehicle added to fleet: %s", vehicle)

    def display_availability(self):
        """Print the current availability status of every vehicle in the fleet."""
        if not self._fleet:
            print("\nNo vehicles in the fleet yet.")
            logger.debug("display_availability called on empty fleet.")
            return
        print("\n--- Fleet Availability ---")
        for vehicle in self._fleet.values():
            print(vehicle)
        print("--------------------------\n")
        logger.debug("Fleet availability displayed (%d vehicles).", len(self._fleet))

    # ------------------------------------------------------------------
    # Rental operations
    # ------------------------------------------------------------------

    def rent_vehicle(self, vehicle_id: str, days: int) -> str:
        """Rent a vehicle for a given number of days.

        Args:
            vehicle_id: ID of the vehicle to rent.
            days: Number of rental days; must be a positive integer.

        Returns:
            The generated rental ID string (e.g. ``"R0001"``).

        Raises:
            ValueError: If *vehicle_id* is not found or *days* is invalid.
            RuntimeError: If the vehicle is already rented.
        """
        if not vehicle_id or not vehicle_id.strip():
            raise ValueError("vehicle_id must be a non-empty string.")
        if not isinstance(days, int) or days <= 0:
            raise ValueError("days must be a positive integer.")

        vehicle = self._fleet.get(vehicle_id.strip())
        if vehicle is None:
            logger.warning("Rent attempted for unknown vehicle ID: %s", vehicle_id)
            raise ValueError(f"No vehicle with ID '{vehicle_id}' found.")

        vehicle.rent()
        rental_id = f"R{self._rental_counter:04d}"
        self._rental_counter += 1
        self._active_rentals[rental_id] = (vehicle, days)
        cost = vehicle.rental_cost(days)
        logger.info("Rental created: %s | vehicle=%s | days=%d | cost=$%.2f",
                    rental_id, vehicle_id, days, cost)
        print(f"Rental confirmed [{rental_id}]: {vehicle} | {days} day(s) | Cost: ${cost:.2f}")
        return rental_id

    def return_vehicle(self, rental_id: str):
        """Process the return of a rented vehicle.

        Args:
            rental_id: The rental ID issued at rent time.

        Raises:
            ValueError: If *rental_id* does not match any active rental.
        """
        if not rental_id or not rental_id.strip():
            raise ValueError("rental_id must be a non-empty string.")

        rental = self._active_rentals.pop(rental_id.strip(), None)
        if rental is None:
            logger.warning("Return attempted for unknown rental ID: %s", rental_id)
            raise ValueError(f"No active rental with ID '{rental_id}'.")

        vehicle, days = rental
        vehicle.return_vehicle()
        logger.info("Rental closed: %s | vehicle=%s | days=%d", rental_id, vehicle.vehicle_id, days)
        print(f"Vehicle returned [{rental_id}]: {vehicle} | Rental duration: {days} day(s)")
