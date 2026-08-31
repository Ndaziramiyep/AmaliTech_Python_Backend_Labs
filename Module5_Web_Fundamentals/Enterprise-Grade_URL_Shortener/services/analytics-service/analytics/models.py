from django.db import models


class ClickEvent(models.Model):
    # url-service reports these by value on every redirect — this service
    # never queries url-service or auth-service back for context.
    short_code = models.CharField(max_length=10, db_index=True)
    owner_id = models.PositiveIntegerField(db_index=True)
    referrer = models.CharField(max_length=500, blank=True, default="")
    user_agent = models.CharField(max_length=500, blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    clicked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-clicked_at"]

    def __str__(self):
        return f"{self.short_code} @ {self.clicked_at}"
