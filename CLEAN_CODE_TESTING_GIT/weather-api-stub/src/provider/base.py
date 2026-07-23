from abc import ABC, abstractmethod
from typing import Optional

from src.models.weather import WeatherForecast


class WeatherProvider(ABC):
    """Abstract base class defining the weather provider interface.

    Concrete implementations must supply a data source (mock or real API)
    and validate the API key used to access it.
    """

    @abstractmethod
    def is_valid_api_key(self) -> bool:  # pragma: no cover
        """Check whether the configured API key is valid.

        Returns:
            True if the key is accepted, False otherwise.
        """

    @abstractmethod
    def get_forecast(self, city: str) -> Optional[WeatherForecast]:  # pragma: no cover
        """Return the weather forecast for the given city.

        Args:
            city: Name of the city to look up.

        Returns:
            A WeatherForecast instance, or None if the city is unknown.
        """
