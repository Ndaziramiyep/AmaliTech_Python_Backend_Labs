import pytest
from src.provider.mock import MockWeatherProvider
from src.service import WeatherService


@pytest.fixture
def provider():
    return MockWeatherProvider()


@pytest.fixture
def weather_service(provider):
    return WeatherService(provider)
