import logging

from src.exceptions import CityNotFoundError
from src.provider.mock import MockWeatherProvider
from src.service import WeatherService


def test_get_forecast_logs_request(caplog):
    provider = MockWeatherProvider()
    service = WeatherService(provider)
    city = "Kigali"

    with caplog.at_level(logging.INFO):
        service.get_forecast(city)

    assert f"Fetching weather forecast for {city}" in caplog.text


def test_get_forecast_logs_error(caplog):
    provider = MockWeatherProvider()
    service = WeatherService(provider)
    city = "Atlantis"

    with caplog.at_level(logging.ERROR):
        try:
            service.get_forecast(city)
        except CityNotFoundError:
            pass

    assert f"Error fetching forecast for city: {city}" in caplog.text
