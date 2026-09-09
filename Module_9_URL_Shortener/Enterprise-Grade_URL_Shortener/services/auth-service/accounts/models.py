from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extends Django's AbstractUser with a unique email and a subscription tier."""

    TIER_FREE = "Free"
    TIER_PREMIUM = "Premium"
    TIER_ADMIN = "Admin"
    TIER_CHOICES = [
        (TIER_FREE, "Free"),
        (TIER_PREMIUM, "Premium"),
        (TIER_ADMIN, "Admin"),
    ]

    email = models.EmailField(unique=True)
    is_premium = models.BooleanField(default=False)
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default=TIER_FREE)

    def save(self, *args, **kwargs):
        """Keeps is_premium and is_staff consistent with the tier field before saving."""
        self.is_premium = self.tier == self.TIER_PREMIUM
        if self.tier == self.TIER_ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)
