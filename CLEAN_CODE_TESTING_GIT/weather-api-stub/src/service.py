import logging

from src.exceptions import CityNotFoundError, InvalidAPIKeyError
from src.models.weather import WeatherForecast
from src.provider.base import WeatherProvider

logger = logging.getLogger("weather.service")
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")


class WeatherService:
    """Fetches forecasts through a WeatherProvider (mock or real API)."""

    def __init__(self, provider: WeatherProvider) -> None:
        self.provider = provider

    def get_forecast(self, city: str) -> WeatherForecast:
        """Return the forecast for city (raises InvalidAPIKeyError/CityNotFoundError)."""
        logger.info(f"Fetching weather forecast for {city}")

        # Check the key before touching the data source at all.
        try:
            self.provider.check_api_key()
        except InvalidAPIKeyError:
            logger.error(f"Invalid API key for city: {city}")
            raise

        try:
            return self.provider.get_forecast(city)
        except CityNotFoundError:
            logger.error(f"Error fetching forecast for city: {city}")
            raise
