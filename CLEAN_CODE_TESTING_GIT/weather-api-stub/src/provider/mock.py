from typing import Dict

from src.exceptions import CityNotFoundError, InvalidAPIKeyError
from src.models.weather import WeatherForecast
from src.provider.base import WeatherProvider


class MockWeatherProvider(WeatherProvider):
    """Fake provider with predefined weather data, for tests/local dev."""

    # Fixed lookup table standing in for a real weather API's response data.
    _data: Dict[str, WeatherForecast] = {
        "Kigali": WeatherForecast(temperature=25, description="Sunny"),
        "Nairobi": WeatherForecast(temperature=22, description="Cloudy"),
        "Addis Ababa": WeatherForecast(temperature=20, description="Rainy"),
        "Dar es Salaam": WeatherForecast(temperature=28, description="Sunny"),
    }

    def __init__(self, api_key: str = "valid_key") -> None:
        self.api_key = api_key

    def check_api_key(self) -> None:
        """Raise InvalidAPIKeyError unless api_key is the accepted value."""
        if self.api_key != "valid_key":
            raise InvalidAPIKeyError("API key is invalid")

    def get_forecast(self, city: str) -> WeatherForecast:
        """Look up city in the predefined data set, or raise CityNotFoundError."""
        try:
            return self._data[city]
        except KeyError:
            raise CityNotFoundError(f"City not found: {city}") from None
