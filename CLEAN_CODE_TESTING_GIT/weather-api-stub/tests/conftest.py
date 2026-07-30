import pytest
from src.provider.mock import MockWeatherProvider
from src.service import WeatherService


@pytest.fixture
def provider() -> MockWeatherProvider:
    return MockWeatherProvider()


@pytest.fixture
def weather_service(provider: MockWeatherProvider) -> WeatherService:
    return WeatherService(provider)
