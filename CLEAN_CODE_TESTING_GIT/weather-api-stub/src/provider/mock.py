from typing import Dict, Optional

from src.models.weather import WeatherForecast
from src.provider.base import WeatherProvider


class MockWeatherProvider(WeatherProvider):
    """Mock provider returning predefined weather data for known cities.

    Intended for testing and local development. No real API calls are made.
    """

    _data: Dict[str, WeatherForecast] = {
        "Kigali": WeatherForecast(temperature=25, description="Sunny"),
        "Nairobi": WeatherForecast(temperature=22, description="Cloudy"),
        "Addis Ababa": WeatherForecast(temperature=20, description="Rainy"),
        "Dar es Salaam": WeatherForecast(temperature=28, description="Sunny"),
    }

    def __init__(self, api_key: str = "valid_key") -> None:
        """Initialise the mock provider.

        Args:
            api_key: The API key to validate against. Defaults to 'valid_key'.
        """
        self.api_key = api_key

    def is_valid_api_key(self) -> bool:
        """Return True only when the key equals the accepted value.

        Returns:
            True if api_key is 'valid_key', False otherwise.
        """
        return self.api_key == "valid_key"

    def get_forecast(self, city: str) -> Optional[WeatherForecast]:
        """Look up predefined forecast data for a city.

        Args:
            city: Name of the city to look up.

        Returns:
            A WeatherForecast instance, or None if the city is not in the data set.
        """
        return self._data.get(city)
