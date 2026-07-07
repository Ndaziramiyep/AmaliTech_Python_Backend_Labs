"""Module containing the RentalSystem class that manages the vehicle fleet."""

from vehicle.vehicle import Vehicle


class RentalSystem:
    """Manages a fleet of vehicles and handles rental operations."""

    def __init__(self) -> None:
        """Initialize an empty rental system."""
        self._vehicles: list[Vehicle] = []

    # ------------------------------------------------------------------
    # Fleet management
    # ------------------------------------------------------------------

    def add_vehicle(self, vehicle: Vehicle) -> None:
        """Add a vehicle to the fleet. Rejects duplicate vehicle IDs."""
        if self._find_vehicle(vehicle.vehicle_id, silent=True) is not None:
            print(f"  Vehicle '{vehicle.vehicle_id}' already exists in the fleet.")
            return
        self._vehicles.append(vehicle)

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def show_all(self) -> None:
        """Print every vehicle in the fleet."""
        print("\nAll Vehicles:")
        if not self._vehicles:
            print("  Fleet is empty.")
            return
        for vehicle in self._vehicles:
            print(f"  {vehicle}")

    def show_available(self) -> None:
        """Print only vehicles that are currently available."""
        print("\nAvailable Vehicles:")
        available = [v for v in self._vehicles if not v.is_rented]
        if available:
            for vehicle in available:
                print(f"  {vehicle}")
        else:
            print("  No vehicles available.")

    def show_rented(self) -> None:
        """Print only vehicles that are currently rented out."""
        print("\nRented Vehicles:")
        rented = [v for v in self._vehicles if v.is_rented]
        if rented:
            for vehicle in rented:
                print(f"  {vehicle}")
        else:
            print("  No vehicles currently rented.")

    # ------------------------------------------------------------------
    # Rental operations
    # ------------------------------------------------------------------

    def rent_vehicle(self, vehicle_id: str) -> None:
        """
        Rent a vehicle by its ID.

        Args:
            vehicle_id: The ID of the vehicle to rent.
        """
        vehicle = self._find_vehicle(vehicle_id)
        if vehicle is None:
            return
        if vehicle.rent():
            print(f"  '{vehicle_id}' rented successfully.")
        else:
            print(f"  '{vehicle_id}' is already rented.")

    def return_vehicle(self, vehicle_id: str) -> None:
        """
        Return a rented vehicle by its ID.

        Args:
            vehicle_id: The ID of the vehicle to return.
        """
        vehicle = self._find_vehicle(vehicle_id)
        if vehicle is None:
            return
        if vehicle.return_vehicle():
            print(f"  '{vehicle_id}' returned successfully.")
        else:
            print(f"  '{vehicle_id}' is not currently rented.")

    def calculate_cost(self, vehicle_id: str, days: int) -> None:
        """
        Print the rental cost for a vehicle over a given number of days.

        Args:
            vehicle_id: The ID of the vehicle.
            days: Number of rental days.
        """
        vehicle = self._find_vehicle(vehicle_id)
        if vehicle is None:
            return
        try:
            cost = vehicle.calculate_rental_cost(days)
        except ValueError as exc:
            print(f"  Invalid input: {exc}")
            return
        print(f"  Cost for '{vehicle_id}' over {days} day(s): ${cost:.2f}")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_vehicle(self, vehicle_id: str, silent: bool = False) -> Vehicle | None:
        """
        Locate a vehicle by ID.

        Args:
            vehicle_id: The ID to search for.
            silent: If True, suppress the "not found" message.

        Returns:
            The matching Vehicle, or None if not found.
        """
        if not vehicle_id or not vehicle_id.strip():
            if not silent:
                print("  Vehicle ID cannot be empty.")
            return None
        for vehicle in self._vehicles:
            if vehicle.vehicle_id == vehicle_id.strip():
                return vehicle
        if not silent:
            print(f"  Vehicle '{vehicle_id}' not found.")
        return None
