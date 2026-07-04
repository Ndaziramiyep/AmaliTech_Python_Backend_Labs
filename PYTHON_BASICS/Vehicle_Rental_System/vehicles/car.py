from .base import Vehicle


class Car(Vehicle):
    def __init__(self, vehicle_id: str, make: str, model: str, year: int,
                 base_rate: float, num_passengers: int):
        super().__init__(vehicle_id, make, model, year, base_rate)
        self._num_passengers = num_passengers

    @property
    def num_passengers(self):
        return self._num_passengers

    def rental_cost(self, days: int) -> float:
        """Base rate + $5/day surcharge for vehicles with more than 4 passengers."""
        surcharge = 5.0 if self._num_passengers > 4 else 0.0
        return (self._base_rate + surcharge) * days
