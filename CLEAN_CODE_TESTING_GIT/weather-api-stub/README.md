# Weather API Stub

A mock Weather API service built using **Test-Driven Development (TDD)**.
It provides **predefined weather data** for known cities without calling a real API.

## Features
- Returns forecasts for predefined cities (`Kigali`, `Nairobi`, `Addis Ababa`, `Dar es Salaam`)
- Raises `CityNotFoundError` for unknown cities
- Raises `InvalidAPIKeyError` for invalid API keys
- Structured logging with INFO and ERROR levels
- Strict TDD workflow with near 100% test coverage
- SOLID architecture with dependency inversion

## Quickstart

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run the CLI**:
```bash
python -m src.main
```

3. **Run tests with coverage**:
```bash
pytest --cov=src
```

4. **Run a specific test**:
```bash
pytest tests/test_main.py -v
```

## Project Structure

```
weather-api-stub/
├── src/                          # Application code
│   ├── __init__.py
│   ├── main.py                   # CLI entry point
│   ├── weather_service.py        # Business logic
│   └── weather_repository.py     # Data layer
├── tests/                        # Unit tests
│   ├── __init__.py
│   ├── test_weather_service.py
│   ├── test_weather_repository.py
│   └── test_main.py
├── docs/                         # Detailed documentation
│   └── README.md
├── requirements.txt
├── .pre-commit-config.yaml
└── README.md
```

## Example Usage

```bash
$ python -m src.main
Enter city name: Kigali
Enter API key: valid_api_key_123

Weather in Kigali:
  Temperature: 22°C
  Condition: Partly Cloudy
  Humidity: 65%
```

## Documentation
For full design rationale, architecture diagrams, TDD workflow, and testing strategy, see **[docs/](docs/)**.
