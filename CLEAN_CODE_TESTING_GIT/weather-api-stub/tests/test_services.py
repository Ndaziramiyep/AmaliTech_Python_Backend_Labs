import pytest
from src.exceptions import CityNotFoundError, InvalidAPIKeyError
from src.provider.mock import MockWeatherProvider
from src.service import WeatherService


@pytest.fixture
def provider() -> MockWeatherProvider:
    return MockWeatherProvider()


@pytest.fixture
def weather_service(provider: MockWeatherProvider) -> WeatherService:
    return WeatherService(provider)


def test_valid_city(weather_service: WeatherService) -> None:
    forecast = weather_service.get_forecast("Kigali")
    assert forecast.temperature == 25
    assert forecast.description == "Sunny"


def test_unknown_city(weather_service: WeatherService) -> None:
    with pytest.raises(CityNotFoundError):
        weather_service.get_forecast("Paris")


def test_invalid_api_key() -> None:
    provider = MockWeatherProvider(api_key="wrong")
    service = WeatherService(provider)
    with pytest.raises(InvalidAPIKeyError):
        service.get_forecast("Kigali")


@pytest.mark.parametrize("city", ["Kigali", "Nairobi", "Addis Ababa", "Dar es Salaam"])
def test_all_supported_cities(weather_service: WeatherService, city: str) -> None:
    forecast = weather_service.get_forecast(city)
    assert forecast.temperature > 0
    assert isinstance(forecast.description, str)
