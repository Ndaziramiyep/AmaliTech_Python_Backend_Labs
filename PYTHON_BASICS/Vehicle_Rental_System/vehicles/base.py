from abc import ABC, abstractmethod


class Vehicle(ABC):
    def __init__(self, vehicle_id: str, make: str, model: str, year: int, base_rate: float):
        self._vehicle_id = vehicle_id
        self._make = make
        self._model = model
        self._year = year
        self._base_rate = base_rate
        self._is_available = True

    @property
    def vehicle_id(self):
        return self._vehicle_id

    @property
    def is_available(self):
        return self._is_available

    @property
    def base_rate(self):
        return self._base_rate

    @base_rate.setter
    def base_rate(self, value: float):
        if value <= 0:
            raise ValueError("Base rate must be positive.")
        self._base_rate = value

    @abstractmethod
    def rental_cost(self, days: int) -> float:
        """Calculate total rental cost for given number of days."""

    def rent(self):
        if not self._is_available:
            raise RuntimeError(f"{self} is already rented.")
        self._is_available = False

    def return_vehicle(self):
        if self._is_available:
            raise RuntimeError(f"{self} was not rented.")
        self._is_available = True

    def __str__(self):
        status = "Available" if self._is_available else "Rented"
        return f"[{self._vehicle_id}] {self._year} {self._make} {self._model} — {status}"
