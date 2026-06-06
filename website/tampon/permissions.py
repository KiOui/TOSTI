from django.core.exceptions import PermissionDenied


class TamponCommitteeMixin:
    """Restrict access to tampon committee members."""

    def dispatch(self, request, *args, **kwargs):
        if not is_tampon_committee_member(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


def is_tampon_committee_member(user):
    """Return whether the user is allowed to see tampon notifications."""
    return user.is_authenticated and user.has_perm("tampon.manage_tamponnotification")
