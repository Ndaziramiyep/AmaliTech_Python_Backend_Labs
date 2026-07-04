from .base import Vehicle


class Bike(Vehicle):
    def __init__(self, vehicle_id: str, make: str, model: str, year: int,
                 base_rate: float, engine_cc: int):
        super().__init__(vehicle_id, make, model, year, base_rate)
        self._engine_cc = engine_cc

    @property
    def engine_cc(self):
        return self._engine_cc

    def rental_cost(self, days: int) -> float:
        """10% surcharge for bikes above 500cc."""
        multiplier = 1.10 if self._engine_cc > 500 else 1.0
        return self._base_rate * multiplier * days
