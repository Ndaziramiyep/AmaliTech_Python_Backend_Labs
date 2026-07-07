"""Module defining the Car vehicle type."""

from .vehicle import Vehicle


class Car(Vehicle):
    """A car available for daily rental."""

    def __init__(self, vehicle_id: str, brand: str, base_price: float) -> None:
        """
        Initialize a Car instance.

        Args:
            vehicle_id: Unique identifier for the car.
            brand: Manufacturer or brand name.
            base_price: Daily rental rate in dollars.
        """
        super().__init__(vehicle_id, brand, base_price)

    def display_details(self) -> None:
        """Print detailed information about this car."""
        print("Car Details:")
        print(f"  Vehicle ID : {self.vehicle_id}")
        print(f"  Brand      : {self.brand}")
        print(f"  Rate/Day   : ${self.base_price}")
        print(f"  Status     : {'Rented' if self.is_rented else 'Available'}")

    def calculate_rental_cost(self, days: int) -> float:
        """Return total rental cost (base_price × days)."""
        self._validate_days(days)
        return self.base_price * days
