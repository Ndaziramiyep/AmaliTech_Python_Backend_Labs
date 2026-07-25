from abc import ABC, abstractmethod

from src.models.weather import WeatherForecast


class WeatherProvider(ABC):
    """Interface for a weather data source (mock or real API)."""

    @abstractmethod
    def check_api_key(self) -> None:  # pragma: no cover
        """Raise InvalidAPIKeyError if the configured key is rejected."""

    @abstractmethod
    def get_forecast(self, city: str) -> WeatherForecast:  # pragma: no cover
        """Return the forecast for city, or raise CityNotFoundError."""
