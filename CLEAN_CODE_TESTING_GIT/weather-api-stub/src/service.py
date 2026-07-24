import logging

from src.exceptions import CityNotFoundError, InvalidAPIKeyError
from src.models.weather import WeatherForecast
from src.provider.base import WeatherProvider

logger = logging.getLogger("weather.service")
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")


class WeatherService:
    """Service that provides weather forecasts using a provider.

    Depends on the abstract WeatherProvider interface, enabling easy
    substitution of the underlying data source (mock or real API).
    """

    def __init__(self, provider: WeatherProvider) -> None:
        """Initialise the service with a weather provider.

        Args:
            provider: Any concrete implementation of WeatherProvider.
        """
        self.provider = provider

    def get_forecast(self, city: str) -> WeatherForecast:
        """Return the weather forecast for a given city.

        Args:
            city: Name of the city to query.

        Returns:
            A WeatherForecast dataclass instance.

        Raises:
            InvalidAPIKeyError: If the provider's API key is invalid.
            CityNotFoundError: If the city is not in the predefined data set.
        """
        logger.info(f"Fetching weather forecast for {city}")

        if not self.provider.is_valid_api_key():
            logger.error(f"Invalid API key for city: {city}")
            raise InvalidAPIKeyError("API key is invalid")

        forecast = self.provider.get_forecast(city)
        if forecast is None:
            logger.error(f"Error fetching forecast for city: {city}")
            raise CityNotFoundError(f"City not found: {city}")

        return forecast
