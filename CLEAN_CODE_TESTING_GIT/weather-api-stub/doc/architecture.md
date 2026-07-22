# Architecture

## High-Level Design
The WeatherService depends on an abstract WeatherProvider interface.
This allows the service to remain decoupled from the data source (mock or real API).

## SOLID Principles Applied
- **Single Responsibility:** WeatherService handles business logic only.
- **Open/Closed:** New providers can be added without modifying existing code.
- **Dependency Inversion:** Service depends on abstractions, not concrete implementations.

## Folder Structure
weather-api-stub/
├── src/
│   ├── main.py
│   ├── service.py
│   ├── provider/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── mock.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── weather.py
│   └── exceptions.py
├── tests/
│   ├── conftest.py
│   ├── test_services.py
│   ├── test_provider.py
│   └── test_main.py
├── docs/
│   └── README.md
├── requirements.txt
└── .pre-commit-config.yaml
