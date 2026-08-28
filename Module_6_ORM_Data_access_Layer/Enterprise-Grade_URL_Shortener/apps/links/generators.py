"""Short-code generation strategies, kept separate from the service that consumes them."""

import random
import string
from abc import ABC, abstractmethod


class ShortCodeGenerator(ABC):
    """Defines the contract every short-code generation strategy must implement."""

    @abstractmethod
    def generate(self) -> str:
        """Return a newly generated candidate short code."""
        raise NotImplementedError


class RandomShortCodeGenerator(ShortCodeGenerator):
    """Generates short codes from a random mix of letters and digits."""

    ALPHABET = string.ascii_letters + string.digits

    def __init__(self, length: int = 6):
        """Store the desired length for generated short codes."""
        self.length = length

    def generate(self) -> str:
        """Return a random short code of the configured length."""
        return "".join(random.choices(self.ALPHABET, k=self.length))
