"""Business logic for recording click analytics, independent of the HTTP layer."""

from django.db.models import F

from .models import Click


class ClickTrackingService:
    """Records click events and keeps the parent URL's click count in sync."""

    @staticmethod
    def record(url, request):
        """Create a Click record from the incoming request and atomically bump the URL's click count."""
        Click.objects.create(
            url=url,
            ip_address=ClickTrackingService._client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            referrer=request.META.get("HTTP_REFERER") or None,
        )
        url.__class__.objects.filter(pk=url.pk).update(click_count=F("click_count") + 1)

    @staticmethod
    def _client_ip(request) -> str:
        """Return the best-guess client IP address, honoring a proxy forwarding header."""
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        return forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR", "")
