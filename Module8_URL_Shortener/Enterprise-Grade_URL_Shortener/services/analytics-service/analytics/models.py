from django.db import models


class ClickEvent(models.Model):
    """A single recorded click on a short link, reported by url-service."""

    # url-service reports these by value on every redirect — this service
    # never queries url-service or auth-service back for context.
    # max_length=50 matches url-service's custom_alias, which can be visited
    # (and reported here) instead of the 10-char generated short_url.
    short_code = models.CharField(max_length=50, db_index=True)
    owner_id = models.PositiveIntegerField(db_index=True)
    referrer = models.CharField(max_length=500, blank=True, default="")
    user_agent = models.CharField(max_length=500, blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    # Populated from the reporting client's IP via a GeoIP lookup, if one is
    # configured — url-service doesn't do this today, so these stay null.
    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    clicked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Order click events newest-first by default."""

        ordering = ["-clicked_at"]

    def __str__(self):
        """Return the short code and click timestamp as a readable label."""
        return f"{self.short_code} @ {self.clicked_at}"
