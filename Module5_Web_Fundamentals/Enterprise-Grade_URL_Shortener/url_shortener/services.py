import string
import random
from .models import Url

class UrlShortenerService:
    CODE_LENGTH = 6

    @staticmethod
    def generate_short_code():
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(UrlShortenerService.CODE_LENGTH))

    @staticmethod
    def create_short_url(original_url):
        while True:
            short_code = UrlShortenerService.generate_short_code()
            if not Url.objects.filter(short_url=short_code).exists():
                break

        return Url.objects.create(
            original_url=original_url,
            short_url=short_code
        )

