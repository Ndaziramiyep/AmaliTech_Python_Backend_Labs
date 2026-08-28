"""User model for the URL Shortener microservice."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extends Django's built-in user with a unique email and a subscription tier."""

    class Tier(models.TextChoices):
        """Enumerates the subscription tiers a user account can belong to."""

        FREE = "free", "Free"
        PREMIUM = "premium", "Premium"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    is_premium = models.BooleanField(default=False)
    tier = models.CharField(max_length=10, choices=Tier.choices, default=Tier.FREE)

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        """Return the user's email as its human-readable representation."""
        return self.email
