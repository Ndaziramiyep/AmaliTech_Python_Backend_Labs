from typing import Optional

from django.contrib.auth.models import AbstractBaseUser

from url_shortener.domain.interfaces import UrlRepository
from url_shortener.models import Url


class DjangoUrlRepository(UrlRepository):
    """Persists shortened URLs using the Django ORM."""

    def exists_by_short_code(self, short_code: str) -> bool:
        return Url.objects.filter(short_code=short_code).exists()

    def create(self, original_url: str, short_code: str, owner: AbstractBaseUser, **extra) -> Url:
        return Url.objects.create(
            original_url=original_url, short_code=short_code, owner=owner, **extra
        )

    def get_by_short_code(self, short_code: str) -> Optional[Url]:
        return Url.objects.with_related().filter(short_code=short_code).first()
