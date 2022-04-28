from rest_framework.permissions import BasePermission


class IsOnBakersList(BasePermission):
    """Permission for checking if a user is on the bakers list of a Shift."""

    def has_permission(self, request, view):
        """Check if a user has a certain object permissions."""
        shift = view.get_shift()
        return request.user in shift.assignees.all()
