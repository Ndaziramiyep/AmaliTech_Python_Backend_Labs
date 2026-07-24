# Weather API Stub

A mock Weather API service built using a strict **Test-Driven Development (TDD)** workflow.
Returns predictable weather data for known cities without calling a real external API.

## Features

- Forecasts for `Kigali`, `Nairobi`, `Addis Ababa`, `Dar es Salaam`
- `CityNotFoundError` for unknown cities
- `InvalidAPIKeyError` for invalid API keys
- Structured logging at INFO and ERROR levels
- 100% test coverage via `coverage.py`
- SOLID architecture — `WeatherService` depends on the abstract `WeatherProvider` interface
- Strict type hints enforced by `mypy --strict`
- Code style enforced by `black` and `ruff` via pre-commit hooks

## Project Structure

```
weather-api-stub/
├── src/
│   ├── exceptions.py          # CityNotFoundError, InvalidAPIKeyError
│   ├── models/
│   │   └── weather.py         # WeatherForecast frozen dataclass
│   ├── provider/
│   │   ├── base.py            # Abstract WeatherProvider (ABC)
│   │   └── mock.py            # MockWeatherProvider (predefined data)
│   └── service.py             # WeatherService (business logic)
├── tests/
│   ├── conftest.py            # Shared fixtures
│   ├── test_logging.py        # Logging behaviour tests
│   ├── test_main.py           # CLI integration tests
│   ├── test_provider.py       # MockWeatherProvider unit tests
│   └── test_services.py       # WeatherService unit tests
├── doc/
│   └── architecture.md        # Design rationale and SOLID breakdown
├── main.py                    # CLI entry point
├── .gitignore
├── .pre-commit-config.yaml
├── requirements.txt
└── README.md
```

## Quickstart

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the CLI
python main.py

# 4. Run tests with coverage
pytest --cov=src --cov-report=term-missing -v
```

## Example Session

```
=== Weather API Stub CLI ===
Enter API key (default='valid_key'): valid_key

Enter city name (or 'exit' to quit): Kigali
INFO: Forecast request received for city=Kigali
Forecast for Kigali: 25°C, Sunny

Enter city name (or 'exit' to quit): Paris
INFO: Forecast request received for city=Paris
Error: City 'Paris' not found in predefined data.

Enter city name (or 'exit' to quit): exit
Exiting Weather CLI. Goodbye!
```

## TDD Workflow

Every feature was built following the **Red → Green → Refactor** cycle:

| Cycle | What happened |
|-------|--------------|
| Red | Write a failing test for `get_forecast` returning a forecast |
| Green | Implement minimum `WeatherService.get_forecast` to pass |
| Refactor | Extract `WeatherProvider` ABC; inject via constructor |
| Red | Write failing test for `CityNotFoundError` |
| Green | Add `None` check and raise in service |
| Refactor | Move data to `MockWeatherProvider._data` dict |
| Red | Write failing test for `InvalidAPIKeyError` |
| Green | Add `is_valid_api_key()` guard in service |
| Refactor | Tighten type hints; add Google-style docstrings |
| Red | Write logging assertion tests |
| Green | Add `logger.info` / `logger.error` calls |
| Refactor | Centralise `basicConfig`; use named logger |

## Architecture

`WeatherService` depends on the abstract `WeatherProvider` interface (Dependency Inversion Principle).
Swapping `MockWeatherProvider` for a real HTTP provider requires zero changes to `WeatherService`.

```
WeatherService
    └── WeatherProvider (ABC)
            ├── MockWeatherProvider   ← used in tests and CLI
            └── RealWeatherProvider   ← drop-in replacement (future)
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | 9.0.1 | Test runner |
| `pytest-cov` | 4.1.0 | Coverage reporting |
| `pytest-mock` | 3.14.0 | Mocking support |
| `black` | 24.3.0 | Code formatting |
| `ruff` | 0.4.1 | Linting |
| `mypy` | 1.9.0 | Static type checking |
| `pre-commit` | 3.7.0 | Git hook management |

## Pre-commit Hooks

Hooks are scoped to this project only and run on every commit:

```bash
pre-commit install
pre-commit run --all-files
```

| Hook | Purpose |
|------|---------|
| `black` | Auto-formats code to a consistent style |
| `ruff` | Lints and auto-fixes common issues |
| `mypy --strict` | Enforces full type annotation coverage |

## Test Coverage

```
Name                       Stmts   Miss  Cover
----------------------------------------------
src\__init__.py                0      0   100%
src\exceptions.py              2      0   100%
src\models\__init__.py         0      0   100%
src\models\weather.py          3      0   100%
src\provider\__init__.py       0      0   100%
src\provider\base.py           4      0   100%
src\provider\mock.py          11      0   100%
src\service.py                19      0   100%
----------------------------------------------
TOTAL                         39      0   100%

20 passed in 0.09s
```
