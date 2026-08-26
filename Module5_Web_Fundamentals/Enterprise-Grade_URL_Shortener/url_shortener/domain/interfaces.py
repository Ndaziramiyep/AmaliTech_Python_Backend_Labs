from abc import ABC, abstractmethod
from typing import Optional

from url_shortener.models import Url


class ShortCodeGenerator(ABC):
    """Produces short codes for new URLs."""

    @abstractmethod
    def generate(self) -> str:
        ...


class UrlRepository(ABC):
    """Persists and retrieves shortened URLs."""

    @abstractmethod
    def exists_by_short_code(self, short_code: str) -> bool:
        ...

    @abstractmethod
    def create(self, original_url: str, short_code: str) -> Url:
        ...

    @abstractmethod
    def get_by_short_code(self, short_code: str) -> Optional[Url]:
        ...


class UrlCacheBackend(ABC):
    """Caches short_code -> original_url lookups."""

    @abstractmethod
    def get(self, short_code: str) -> Optional[str]:
        ...

    @abstractmethod
    def set(self, short_code: str, original_url: str, timeout: int) -> None:
        ...
