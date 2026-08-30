from typing import Iterable, Optional

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser

from url_shortener.domain.interfaces import ShortCodeGenerator, UrlCacheBackend, UrlRepository
from url_shortener.models import Url
from url_shortener.services.code_generator import RandomShortCodeGenerator
from url_shortener.services.url_cache import RedisUrlCache
from url_shortener.services.url_repository import DjangoUrlRepository


class UrlShortenerService:
    """Coordinates short code generation, persistence, and caching for URLs."""

    def __init__(
        self,
        repository: Optional[UrlRepository] = None,
        code_generator: Optional[ShortCodeGenerator] = None,
        cache_backend: Optional[UrlCacheBackend] = None,
    ):
        self._repository = repository or DjangoUrlRepository()
        self._code_generator = code_generator or RandomShortCodeGenerator()
        self._cache = cache_backend or RedisUrlCache()
        self._cache_timeout = settings.URL_CACHE_TIMEOUT_SECONDS

    def create_short_url(
        self,
        original_url: str,
        owner: AbstractBaseUser,
        *,
        custom_alias: Optional[str] = None,
        tags: Optional[Iterable] = None,
        **extra,
    ) -> Url:
        short_code = custom_alias or self._generate_unique_code()
        url_obj = self._repository.create(
            original_url, short_code, owner, custom_alias=custom_alias, **extra
        )
        if tags:
            url_obj.tags.set(tags)
        self._cache.set(short_code, url_obj.original_url, timeout=self._cache_timeout)
        return url_obj

    def resolve(self, short_code: str) -> Optional[str]:
        cached_url = self._cache.get(short_code)
        if cached_url:
            return cached_url

        url_obj = Url.objects.active_urls().filter(short_code=short_code).first()
        if url_obj is None:
            return None

        self._cache.set(short_code, url_obj.original_url, timeout=self._cache_timeout)
        return url_obj.original_url

    def _generate_unique_code(self) -> str:
        short_code = self._code_generator.generate()
        while self._repository.exists_by_short_code(short_code):
            short_code = self._code_generator.generate()
        return short_code
