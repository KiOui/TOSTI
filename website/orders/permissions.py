from django.contrib.auth.mixins import LoginRequiredMixin


class StaffRequiredMixin(LoginRequiredMixin):
    """Mixin for requiring staff permissions."""

    def dispatch(self, request, *args, **kwargs):
        """
        Dispatch method.

        :param request: the request
        :param args: arguments
        :param kwargs: keyword arguments
        :return: no permission error if user is not staff, permissions otherwise
        """
        if not request.user.is_authenticated or not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
