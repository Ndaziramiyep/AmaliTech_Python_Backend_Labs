"""Business logic for creating shortened URLs, independent of the HTTP layer."""

from .generators import RandomShortCodeGenerator, ShortCodeGenerator
from .models import URL


class URLShortenerService:
    """Coordinates short-code generation and URL persistence."""

    def __init__(self, generator: ShortCodeGenerator = None):
        """Inject a short-code generation strategy, defaulting to the random generator."""
        self.generator = generator or RandomShortCodeGenerator()

    def _generate_unique_code(self) -> str:
        """Keep generating candidate codes until one is not already taken."""
        code = self.generator.generate()
        while URL.objects.filter(short_code=code).exists():
            code = self.generator.generate()
        return code

    def create_short_url(self, owner, original_url, **extra_fields) -> URL:
        """Create and return a new shortened URL owned by the given user."""
        return URL.objects.create(
            owner=owner,
            original_url=original_url,
            short_code=self._generate_unique_code(),
            **extra_fields,
        )
