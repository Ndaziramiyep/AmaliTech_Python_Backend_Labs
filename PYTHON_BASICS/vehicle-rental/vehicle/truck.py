"""Module defining the Truck vehicle type."""

from .vehicle import Vehicle


class Truck(Vehicle):
    """A truck available for daily rental with a 15 % heavy-vehicle surcharge."""

    SURCHARGE = 0.15 

    def __init__(self, vehicle_id: str, brand: str, base_price: float) -> None:
        """
        Initialize a Truck instance.

        Args:
            vehicle_id: Unique identifier for the truck.
            brand: Manufacturer or brand name.
            base_price: Daily rental rate in dollars (before surcharge).
        """
        super().__init__(vehicle_id, brand, base_price)

    def display_details(self) -> None:
        """Print detailed information about this truck."""
        print("Truck Details:")
        print(f"  Vehicle ID : {self.vehicle_id}")
        print(f"  Brand      : {self.brand}")
        print(f"  Rate/Day   : ${self.base_price} ({int(self.SURCHARGE * 100)}% surcharge applied)")
        print(f"  Status     : {'Rented' if self.is_rented else 'Available'}")

    def calculate_rental_cost(self, days: int) -> float:
        """Return total rental cost with a 15 % surcharge applied."""
        self._validate_days(days)
        return self.base_price * days * (1 + self.SURCHARGE)
