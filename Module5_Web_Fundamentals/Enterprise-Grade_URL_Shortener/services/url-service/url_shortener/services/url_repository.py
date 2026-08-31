from typing import Optional

from url_shortener.domain.interfaces import UrlRepository
from url_shortener.models import Url


class DjangoUrlRepository(UrlRepository):
    """Persists shortened URLs using the Django ORM."""

    def exists_by_short_code(self, short_code: str) -> bool:
        return Url.objects.filter(short_url=short_code).exists()

    def create(self, original_url: str, short_code: str, owner) -> Url:
        return Url.objects.create(
            original_url=original_url,
            short_url=short_code,
            owner_id=owner.id,
            owner_email=owner.email,
        )

    def get_by_short_code(self, short_code: str) -> Optional[Url]:
        return Url.objects.filter(short_url=short_code).first()
