import random
import string

from url_shortener.domain.interfaces import ShortCodeGenerator

DEFAULT_CODE_LENGTH = 6


class RandomShortCodeGenerator(ShortCodeGenerator):
    """Generates a random alphanumeric short code of a fixed length."""

    def __init__(self, length: int = DEFAULT_CODE_LENGTH):
        self._length = length
        self._alphabet = string.ascii_letters + string.digits

    def generate(self) -> str:
        return "".join(random.choice(self._alphabet) for _ in range(self._length))
