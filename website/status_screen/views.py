from django.shortcuts import render
from django.views.generic import TemplateView


class StatusScreen(TemplateView):
    """Status screen for a Shift."""

    template_name = "status_screen/status_screen.html"

    def get(self, request, **kwargs):
        """GET request for status screen view."""
        shift = kwargs.get("shift")
        return render(request, self.template_name, {"shift": shift})
