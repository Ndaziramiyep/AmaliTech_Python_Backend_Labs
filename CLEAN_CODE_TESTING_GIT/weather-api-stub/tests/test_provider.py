import pytest

from src.models.weather import WeatherForecast
from src.provider.mock import MockWeatherProvider


@pytest.fixture
def provider() -> MockWeatherProvider:
    """Return a MockWeatherProvider with a valid API key."""
    return MockWeatherProvider()


def test_valid_api_key(provider: MockWeatherProvider) -> None:
    assert provider.is_valid_api_key() is True


def test_invalid_api_key() -> None:
    assert MockWeatherProvider(api_key="bad").is_valid_api_key() is False


@pytest.mark.parametrize("city", ["Kigali", "Nairobi", "Addis Ababa", "Dar es Salaam"])
def test_get_forecast_known_city(provider: MockWeatherProvider, city: str) -> None:
    result = provider.get_forecast(city)
    assert isinstance(result, WeatherForecast)
    assert result.temperature > 0


def test_get_forecast_unknown_city_returns_none(provider: MockWeatherProvider) -> None:
    assert provider.get_forecast("Atlantis") is None
