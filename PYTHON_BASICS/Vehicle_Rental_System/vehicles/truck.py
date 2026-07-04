from .base import Vehicle


class Truck(Vehicle):
    def __init__(self, vehicle_id: str, make: str, model: str, year: int,
                 base_rate: float, payload_tons: float):
        super().__init__(vehicle_id, make, model, year, base_rate)
        self._payload_tons = payload_tons

    @property
    def payload_tons(self):
        return self._payload_tons

    def rental_cost(self, days: int) -> float:
        """Base rate + $10/ton/day payload surcharge."""
        return (self._base_rate + self._payload_tons * 10.0) * days
