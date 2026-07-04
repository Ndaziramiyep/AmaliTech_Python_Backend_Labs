from vehicles.base import Vehicle


class RentalSystem:
    def __init__(self):
        self._fleet: dict[str, Vehicle] = {}
        self._active_rentals: dict[str, tuple[Vehicle, int]] = {}  # rental_id -> (vehicle, days)
        self._rental_counter = 1

    def add_vehicle(self, vehicle: Vehicle):
        self._fleet[vehicle.vehicle_id] = vehicle

    def display_availability(self):
        print("\n--- Fleet Availability ---")
        for vehicle in self._fleet.values():
            print(vehicle)
        print("--------------------------\n")

    def rent_vehicle(self, vehicle_id: str, days: int) -> str:
        vehicle = self._fleet.get(vehicle_id)
        if vehicle is None:
            raise ValueError(f"No vehicle with ID '{vehicle_id}' found.")
        vehicle.rent()
        rental_id = f"R{self._rental_counter:04d}"
        self._rental_counter += 1
        self._active_rentals[rental_id] = (vehicle, days)
        cost = vehicle.rental_cost(days)
        print(f"Rental confirmed [{rental_id}]: {vehicle} | {days} day(s) | Cost: ${cost:.2f}")
        return rental_id

    def return_vehicle(self, rental_id: str):
        rental = self._active_rentals.pop(rental_id, None)
        if rental is None:
            raise ValueError(f"No active rental with ID '{rental_id}'.")
        vehicle, days = rental
        vehicle.return_vehicle()
        print(f"Vehicle returned [{rental_id}]: {vehicle} | Rental duration: {days} day(s)")
