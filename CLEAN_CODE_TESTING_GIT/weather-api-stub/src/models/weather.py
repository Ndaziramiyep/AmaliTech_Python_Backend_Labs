from dataclasses import dataclass


@dataclass(frozen=True)
class WeatherForecast:
    """Immutable forecast: temperature (°C) and a short description."""

    temperature: float
    description: str
