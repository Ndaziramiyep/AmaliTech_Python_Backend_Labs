"""Click model used to record analytics events for shortened URLs."""

from django.db import models

from apps.links.models import URL


class Click(models.Model):
    """Records a single click event against a shortened URL for analytics purposes."""

    url = models.ForeignKey(URL, on_delete=models.CASCADE, related_name="clicks")
    clicked_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    user_agent = models.TextField()
    referrer = models.URLField(max_length=2000, null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["clicked_at"])]
        ordering = ["-clicked_at"]

    def __str__(self):
        """Return a human-readable summary combining the URL's code and the click timestamp."""
        return f"{self.url.short_code} @ {self.clicked_at}"
