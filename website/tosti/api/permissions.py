from rest_framework.permissions import BasePermission


class HasPermissionOnObject(BasePermission):
    """Permission for checking if a user has certain object based permissions."""

    def has_permission(self, request, view):
        """Check if a user has a certain object permissions."""
        perm_obj = view.get_permission_object()
        if perm_obj is None:
            raise ValueError
        else:
            return request.user.has_perm(view.permission_required, perm_obj)
