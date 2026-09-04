import logging

from django.conf import settings
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class IsInternalService(BasePermission):
    """Grants access only if the request carries the shared X-Internal-Key header."""

    message = "Missing or invalid internal service key."

    def has_permission(self, request, view):
        """Check the request's X-Internal-Key header against the configured shared secret."""
        provided = request.META.get("HTTP_X_INTERNAL_KEY", "")
        valid = bool(provided) and provided == settings.INTERNAL_API_KEY
        if not valid:
            logger.warning(
                "Rejected request to internal-only endpoint %s from %s: missing or invalid X-Internal-Key",
                request.path, request.META.get("REMOTE_ADDR"),
            )
        return valid


class IsPremiumOrAdmin(BasePermission):
    """Grants access only to Premium or Admin/staff users — detailed analytics is a paid feature."""

    message = "Detailed analytics requires a Premium or Admin subscription tier."

    def has_permission(self, request, view):
        """Check the caller's tier/is_staff claim from their JWT."""
        user = request.user
        return bool(user.is_authenticated and (user.is_staff or user.tier in ("Premium", "Admin")))
