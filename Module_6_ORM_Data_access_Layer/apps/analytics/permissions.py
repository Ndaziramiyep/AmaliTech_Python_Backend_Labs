"""Permissions gating access to premium-only analytics."""

from rest_framework.permissions import BasePermission


class IsPremiumUser(BasePermission):
    """Grants access only to authenticated users on the premium or admin tier."""

    def has_permission(self, request, view):
        """Return whether the requesting user is authenticated and premium or admin tier."""
        user = request.user
        return bool(
            user and user.is_authenticated and (user.is_premium or user.tier == user.Tier.ADMIN)
        )
