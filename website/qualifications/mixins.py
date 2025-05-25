from django.contrib.auth.mixins import AccessMixin

from qualifications.models import BasicBorrelBrevet


class BasicBorrelBrevetRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and has a registered BasicBorrelBrevet."""

    permission_denied_message = "You do not have a registered BasisBorrelBrevet"

    def dispatch(self, request, *args, **kwargs):
        """Dispatch method."""
        if (
            not request.user.is_authenticated
            or not BasicBorrelBrevet.objects.filter(user=request.user).exists()
        ):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
