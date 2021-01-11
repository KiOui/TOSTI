from rest_framework.permissions import BasePermission


class HasGuardianPermission(BasePermission):
    """Permission for checking if a user has certain guardian based permissions."""

    def has_permission(self, request, view):
        """Check if a user has a certain guardian permissions."""
        return request.user.has_perm(view.permission_required, view.get_permission_object())
