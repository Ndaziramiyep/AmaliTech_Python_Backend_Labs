import logging

from django.conf import settings
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class IsInternalService(BasePermission):
    """Grants access only if the request carries the shared X-Internal-Key header — same contract as analytics-service's permission of the same name."""

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
