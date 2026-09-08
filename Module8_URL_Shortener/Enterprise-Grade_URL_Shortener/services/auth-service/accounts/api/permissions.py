import logging

from django.conf import settings
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class IsInternalGateway(BasePermission):
    """Grants access only if the request carries the gateway's shared X-Internal-Token header."""

    message = "Missing or invalid internal service token."

    def has_permission(self, request, view):
        """Check the request's X-Internal-Token header against the configured shared secret, raising 401 (not 403) if it's missing/invalid — even when the caller's JWT is otherwise valid."""
        provided = request.META.get("HTTP_X_INTERNAL_TOKEN", "")
        valid = bool(provided) and provided == settings.INTERNAL_SERVICE_TOKEN
        if not valid:
            logger.warning(
                "Rejected request to internal-only endpoint %s from %s: missing or invalid X-Internal-Token",
                request.path, request.META.get("REMOTE_ADDR"),
            )
            raise NotAuthenticated(self.message)
        return valid
