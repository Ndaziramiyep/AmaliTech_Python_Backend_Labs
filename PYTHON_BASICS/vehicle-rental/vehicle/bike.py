"""Module defining the Bike vehicle type."""

from .vehicle import Vehicle

class Bike(Vehicle):
    """A bike available for daily rental at a 10 % discount."""

    DISCOUNT = 0.10

    def __init__(self, vehicle_id: str, brand: str, base_price: float) -> None:
        """
        Initialize a Bike instance.

        Args:
            vehicle_id: Unique identifier for the bike.
            brand: Manufacturer or brand name.
            base_price: Daily rental rate in dollars (before discount).
        """
        super().__init__(vehicle_id, brand, base_price)

    def display_details(self) -> None:
        """Print detailed information about this bike."""
        print("Bike Details:")
        print(f"  Vehicle ID : {self.vehicle_id}")
        print(f"  Brand      : {self.brand}")
        print(f"  Rate/Day   : ${self.base_price} ({int(self.DISCOUNT * 100)}% discount applied)")
        print(f"  Status     : {'Rented' if self.is_rented else 'Available'}")

    def calculate_rental_cost(self, days: int) -> float:
        """Return total rental cost with a 10 % discount applied."""
        self._validate_days(days)
        return self.base_price * days * (1 - self.DISCOUNT)
