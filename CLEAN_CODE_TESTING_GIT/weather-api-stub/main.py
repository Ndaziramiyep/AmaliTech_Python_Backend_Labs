
from src.exceptions import CityNotFoundError, InvalidAPIKeyError
from src.provider.mock import MockWeatherProvider
from src.service import WeatherService


def main():
    print("=== Weather API Stub CLI ===")
    api_key = input("Enter API key (default='valid_key'): ").strip() or "valid_key"
    provider = MockWeatherProvider(api_key=api_key)
    service = WeatherService(provider)

    while True:
        city = input("\nEnter city name (or 'exit' to quit): ").strip()
        if city.lower() == "exit":
            print("Exiting Weather CLI. Goodbye!")
            break

        try:
            print(f"INFO: Forecast request received for city={city}")
            forecast = service.get_forecast(city)
            print(f"Forecast for {city}: {forecast.temperature}°C, {forecast.description}")
        except CityNotFoundError:
            print(f"Error: City '{city}' not found in predefined data.")
        except InvalidAPIKeyError:
            print("Error: Invalid API key.")
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
