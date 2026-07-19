from typing import Dict, Optional

from src.models.weather import WeatherForecast
from src.provider.base import WeatherProvider


class MockWeatherProvider(WeatherProvider):
    """Mock provider returning predefined weather data."""

    _data: Dict[str, WeatherForecast] = {
        "Kigali": WeatherForecast(25, "Sunny"),
        "Nairobi": WeatherForecast(22, "Cloudy"),
        "Addis Ababa": WeatherForecast(20, "Rainy"),
        "Dar es Salaam": WeatherForecast(28, "Sunny"),
    }

    def __init__(self, api_key: str = "valid_key"):
        self.api_key = api_key

    def is_valid_api_key(self) -> bool:
        return self.api_key == "valid_key"

    def get_forecast(self, city: str) -> Optional[WeatherForecast]:
        return self._data.get(city)
