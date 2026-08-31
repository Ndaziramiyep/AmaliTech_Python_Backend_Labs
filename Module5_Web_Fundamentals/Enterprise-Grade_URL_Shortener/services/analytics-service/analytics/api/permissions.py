from django.conf import settings
from rest_framework.permissions import BasePermission


class IsInternalService(BasePermission):
    """
    Grants access only if the request carries the shared X-Internal-Key
    header. Protects endpoints meant to be called by other services
    (url-service) rather than end users or the public internet.
    """

    message = "Missing or invalid internal service key."

    def has_permission(self, request, view):
        provided = request.META.get("HTTP_X_INTERNAL_KEY", "")
        return bool(provided) and provided == settings.INTERNAL_API_KEY
