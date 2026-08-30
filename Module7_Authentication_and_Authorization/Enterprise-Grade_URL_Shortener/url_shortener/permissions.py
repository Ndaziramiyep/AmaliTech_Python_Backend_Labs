from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Grants access only to the URL's owner."""

    def has_object_permission(self, request, view, obj):
        return obj.owner_id == request.user.id


class IsPremiumUser(BasePermission):
    """Grants access only to premium (or admin tier) users."""

    message = "Analytics are available to premium accounts only."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_premium or user.tier == user.Tier.ADMIN))
