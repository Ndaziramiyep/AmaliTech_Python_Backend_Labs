import logging

from src.exceptions import CityNotFoundError, InvalidAPIKeyError
from src.provider.mock import MockWeatherProvider

logger = logging.getLogger("weather.service")
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")


class WeatherService:
    """Service that provides weather forecasts using a provider."""

    def __init__(self, provider: MockWeatherProvider):
        self.provider = provider

    def get_forecast(self, city: str):
        logger.info(f"Fetching weather forecast for {city}")

        if not self.provider.is_valid_api_key():
            logger.error(f"Invalid API key for city: {city}")
            raise InvalidAPIKeyError("API key is invalid")

        forecast = self.provider.get_forecast(city)
        if forecast is None:
            logger.error(f"Error fetching forecast for city: {city}")
            raise CityNotFoundError(f"City not found: {city}")

        return forecast
