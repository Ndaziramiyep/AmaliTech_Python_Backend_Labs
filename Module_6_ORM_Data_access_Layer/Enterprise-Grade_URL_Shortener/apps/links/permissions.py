"""Object-level permissions for the links app."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwner(BasePermission):
    """Restricts write access to a URL's owning user."""

    def has_object_permission(self, request, view, obj):
        """Return whether the request is read-only or made by the object's owner."""
        return request.method in SAFE_METHODS or obj.owner_id == request.user.id
