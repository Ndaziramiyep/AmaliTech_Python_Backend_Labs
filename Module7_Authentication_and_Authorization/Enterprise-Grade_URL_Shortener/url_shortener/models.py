from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from url_shortener.managers import URLManager


class User(AbstractUser):
    class Tier(models.TextChoices):
        FREE = 'free', 'Free'
        PREMIUM = 'premium', 'Premium'
        ADMIN = 'admin', 'Admin'

    FREE_TIER_ACTIVE_URL_LIMIT = 10

    email = models.EmailField(unique=True)
    is_premium = models.BooleanField(default=False)
    tier = models.CharField(max_length=10, choices=Tier.choices, default=Tier.FREE)

    def __str__(self):
        return self.email

    def has_premium_access(self) -> bool:
        return self.is_premium or self.tier == self.Tier.ADMIN


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Url(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='urls',
    )
    original_url = models.URLField(max_length=2000)
    short_code = models.CharField(max_length=10, unique=True, db_index=True)
    custom_alias = models.CharField(max_length=10, unique=True, null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='urls', blank=True)

    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    favicon = models.CharField(max_length=2000, null=True, blank=True)

    click_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = URLManager()

    class Meta:
        indexes = [
            models.Index(fields=['short_code']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.original_url

    def is_expired(self) -> bool:
        return self.expires_at is not None and self.expires_at <= timezone.now()


class Click(models.Model):
    url = models.ForeignKey(Url, on_delete=models.CASCADE, related_name='clicks')
    clicked_at = models.DateTimeField(default=timezone.now, db_index=True)
    ip_address = models.GenericIPAddressField()
    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    user_agent = models.TextField()
    referrer = models.URLField(max_length=2000, null=True, blank=True)

    class Meta:
        ordering = ['-clicked_at']

    def __str__(self):
        return f'{self.url.short_code} @ {self.clicked_at}'
