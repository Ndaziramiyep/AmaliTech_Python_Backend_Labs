import pytest
from pytest_mock import MockerFixture

from src.exceptions import CityNotFoundError, InvalidAPIKeyError
from src.models.weather import WeatherForecast
from src.provider.base import WeatherProvider
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


def test_get_forecast_delegates_to_provider(mocker: MockerFixture) -> None:
    """WeatherService should only talk to WeatherProvider's interface."""
    # spec=WeatherProvider keeps the mock honest: calling a method that
    # doesn't exist on the real interface would fail immediately.
    provider = mocker.Mock(spec=WeatherProvider)
    provider.check_api_key.return_value = None
    provider.get_forecast.return_value = WeatherForecast(
        temperature=30, description="Hot"
    )

    service = WeatherService(provider)
    result = service.get_forecast("Kigali")

    provider.check_api_key.assert_called_once()
    provider.get_forecast.assert_called_once_with("Kigali")
    assert result == WeatherForecast(temperature=30, description="Hot")


def test_get_forecast_short_circuits_on_invalid_key(mocker: MockerFixture) -> None:
    provider = mocker.Mock(spec=WeatherProvider)
    provider.check_api_key.side_effect = InvalidAPIKeyError("bad key")

    service = WeatherService(provider)
    with pytest.raises(InvalidAPIKeyError):
        service.get_forecast("Kigali")

    provider.get_forecast.assert_not_called()


def test_get_forecast_reraises_city_not_found(mocker: MockerFixture) -> None:
    provider = mocker.Mock(spec=WeatherProvider)
    provider.check_api_key.return_value = None
    provider.get_forecast.side_effect = CityNotFoundError("City not found: Atlantis")

    service = WeatherService(provider)
    with pytest.raises(CityNotFoundError):
        service.get_forecast("Atlantis")
