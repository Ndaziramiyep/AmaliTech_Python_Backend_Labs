from dataclasses import dataclass


@dataclass(frozen=True)
class WeatherForecast:
    """Immutable weather forecast response model.

    Attributes:
        temperature: Current temperature in degrees Celsius.
        description: Short human-readable weather description.
    """

    temperature: float
    description: str
