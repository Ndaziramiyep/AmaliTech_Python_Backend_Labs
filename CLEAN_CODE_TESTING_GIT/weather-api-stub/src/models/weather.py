from dataclasses import dataclass


@dataclass(frozen=True)
class WeatherForecast:
    """Weather forecast response model."""

    temperature: float
    description: str
