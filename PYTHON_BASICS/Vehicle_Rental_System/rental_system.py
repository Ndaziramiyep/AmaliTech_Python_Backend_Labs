"""
rental_system.py
----------------
Manages the vehicle fleet and all rental transactions.

:class:`RentalSystem` is the central coordinator — it holds the fleet
inventory, processes rent/return requests, and delegates pricing to each
vehicle's own :meth:`~vehicles.base.Vehicle.rental_cost` implementation.
Rental history is stored as immutable :class:`~models.RentalRecord` instances.
"""

from models import RentalRecord
from vehicles.base import Vehicle
from logger import get_logger

logger = get_logger(__name__)


class RentalSystem:
    """Central manager for the vehicle rental fleet.

    Attributes:
        _fleet: All registered vehicles keyed by ``vehicle_id``.
        _active_rentals: Ongoing rentals keyed by rental ID.
        _rental_history: Completed rentals as a list of :class:`~models.RentalRecord`.
    """

    def __init__(self) -> None:
        self._fleet: dict[str, Vehicle] = {}
        self._active_rentals: dict[str, RentalRecord] = {}
        self._rental_history: list[RentalRecord] = []
        self._rental_counter: int = 1
        logger.debug("RentalSystem initialised.")

    # --- Fleet management ---

    def add_vehicle(self, vehicle: Vehicle) -> None:
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

    def get_vehicle(self, vehicle_id: str) -> Vehicle | None:
        """Look up a vehicle by ID.

        Args:
            vehicle_id: The vehicle's unique identifier.

        Returns:
            The matching :class:`~vehicles.base.Vehicle`, or ``None`` if not found.
        """
        return self._fleet.get(vehicle_id.strip().upper())

    def available_vehicles(self) -> list[Vehicle]:
        """Return a list of all currently available vehicles.

        Returns:
            Vehicles whose :attr:`~vehicles.base.Vehicle.is_available` is ``True``,
            sorted by vehicle ID.
        """
        return sorted(
            [v for v in self._fleet.values() if v.is_available],
            key=lambda v: v.vehicle_id,
        )

    def display_availability(self) -> None:
        """Print the current availability status of every vehicle in the fleet."""
        if not self._fleet:
            print("\n  No vehicles in the fleet yet.")
            logger.debug("display_availability called on empty fleet.")
            return

        available = [v for v in self._fleet.values() if v.is_available]
        rented = [v for v in self._fleet.values() if not v.is_available]

        sep = "-" * 55
        print(f"\n{sep}")
        print(f"  {'FLEET AVAILABILITY':^51}")
        print(sep)
        print(f"  {'ID':<8} {'Year':<6} {'Make & Model':<22} {'Type':<6} {'Status':<10} {'Rate/day'}")
        print(sep)

        for vehicle in sorted(self._fleet.values(), key=lambda v: v.vehicle_id):
            status = "Available" if vehicle.is_available else "Rented"
            print(
                f"  {vehicle.vehicle_id:<8} {vehicle.year:<6} "
                f"{vehicle.make + ' ' + vehicle.model:<22} "
                f"{vehicle.type_label:<6} {status:<10} ${vehicle.base_rate:.2f}"
            )

        print(sep)
        print(f"  Total: {len(self._fleet)} | Available: {len(available)} | Rented: {len(rented)}\n")
        logger.debug("Fleet availability displayed (%d vehicles).", len(self._fleet))

    # --- Rental operations ---

    def rent_vehicle(self, vehicle_id: str, days: int) -> str:
        """Rent a vehicle for a given number of days.

        Args:
            vehicle_id: ID of the vehicle to rent.
            days: Number of rental days; must be a positive integer.

        Returns:
            The generated rental ID string, e.g. ``"R0001"``.

        Raises:
            ValueError: If *vehicle_id* is not found or *days* is invalid.
            RuntimeError: If the vehicle is already rented.
        """
        if not vehicle_id or not vehicle_id.strip():
            raise ValueError("vehicle_id must be a non-empty string.")
        if not isinstance(days, int) or days <= 0:
            raise ValueError("days must be a positive integer.")

        vehicle = self.get_vehicle(vehicle_id)
        if vehicle is None:
            logger.warning("Rent attempted for unknown vehicle ID: %s", vehicle_id)
            raise ValueError(f"No vehicle with ID '{vehicle_id}' found.")

        vehicle.rent()
        rental_id = f"R{self._rental_counter:04d}"
        self._rental_counter += 1
        cost = vehicle.rental_cost(days)
        record = RentalRecord(rental_id, vehicle.vehicle_id, days, cost)
        self._active_rentals[rental_id] = record

        logger.info(
            "Rental created: %s | vehicle=%s | days=%d | cost=$%.2f",
            rental_id, vehicle.vehicle_id, days, cost,
        )
        sep = "-" * 42
        print(f"\n  Rental confirmed!")
        print(f"  {sep}")
        print(f"  Rental ID   : {rental_id}")
        print(f"  Vehicle     : {vehicle.year} {vehicle.make} {vehicle.model} [{vehicle.vehicle_id}]")
        print(f"  Duration    : {days} day(s)")
        print(f"  Total Cost  : ${cost:.2f}")
        print(f"  Date        : {record.rental_date}")
        print(f"  {sep}\n")
        return rental_id

    def return_vehicle(self, rental_id: str) -> None:
        """Process the return of a rented vehicle.

        Args:
            rental_id: The rental ID issued at rent time.

        Raises:
            ValueError: If *rental_id* does not match any active rental.
        """
        if not rental_id or not rental_id.strip():
            raise ValueError("rental_id must be a non-empty string.")

        record = self._active_rentals.pop(rental_id.strip().upper(), None)
        if record is None:
            logger.warning("Return attempted for unknown rental ID: %s", rental_id)
            raise ValueError(f"No active rental with ID '{rental_id}'.")

        vehicle = self._fleet[record.vehicle_id]
        vehicle.return_vehicle()
        self._rental_history.append(record)

        logger.info(
            "Rental closed: %s | vehicle=%s | days=%d",
            rental_id, record.vehicle_id, record.days,
        )
        sep = "-" * 42
        print(f"\n  Vehicle returned successfully!")
        print(f"  {sep}")
        print(f"  Rental ID   : {record.rental_id}")
        print(f"  Vehicle     : {vehicle.year} {vehicle.make} {vehicle.model} [{vehicle.vehicle_id}]")
        print(f"  Duration    : {record.days} day(s)")
        print(f"  Total Cost  : ${record.total_cost:.2f}")
        print(f"  {sep}\n")

    def display_active_rentals(self) -> None:
        """Print all currently active (unreturned) rentals."""
        if not self._active_rentals:
            print("\n  No active rentals.\n")
            return
        sep = "-" * 55
        print(f"\n{sep}")
        print(f"  {'ACTIVE RENTALS':^51}")
        print(sep)
        for record in self._active_rentals.values():
            print(f"  {record}")
        print(f"{sep}\n")

    def display_rental_history(self) -> None:
        """Print all completed (returned) rentals."""
        if not self._rental_history:
            print("\n  No rental history yet.\n")
            return
        sep = "-" * 55
        print(f"\n{sep}")
        print(f"  {'RENTAL HISTORY':^51}")
        print(sep)
        for record in self._rental_history:
            print(f"  {record}")
        total_revenue = sum(r.total_cost for r in self._rental_history)
        print(sep)
        print(f"  Total revenue from completed rentals: ${total_revenue:.2f}\n")
