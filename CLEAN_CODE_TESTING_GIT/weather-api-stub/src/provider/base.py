from abc import ABC, abstractmethod
from typing import Optional

from src.models.weather import WeatherForecast


class WeatherProvider(ABC):
    """Abstract weather provider interface."""

    @abstractmethod
    def is_valid_api_key(self) -> bool:
        """Check if the API key is valid."""
        pass

    @abstractmethod
    def get_forecast(self, city: str) -> Optional[WeatherForecast]:
        """Return forecast for a given city."""
        pass
