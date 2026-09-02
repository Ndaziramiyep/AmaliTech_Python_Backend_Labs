from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """Allows read access to anyone; only a Url's owner or a staff/admin user may write to it."""

    message = "You do not have permission to modify or delete another user's URL."

    def has_permission(self, request, view):
        """Allows any read request through; write requests still need an authenticated user."""
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """Allows any read request through; write requests require ownership or staff/admin."""
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user.is_staff or obj.owner_id == request.user.id)
