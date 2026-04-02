"""
Custom DRF permissions — role-based access control.
"""

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Only allow users with the 'admin' role."""

    def has_permission(self, request, view):
        return getattr(request.user, "is_admin", False)


class IsAdminOrReadOnly(BasePermission):
    """Admin gets full access; 'usuario' role is read-only."""

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return getattr(request.user, "is_admin", False)
