from src.provider.mock import MockWeatherProvider


def test_valid_api_key():
    provider = MockWeatherProvider()
    assert provider.is_valid_api_key()


def test_invalid_api_key():
    provider = MockWeatherProvider(api_key="bad")
    assert not provider.is_valid_api_key()
