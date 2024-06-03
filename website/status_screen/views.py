from django.http import Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from orders.templatetags.start_shift import currently_active_shift_for_venue


class StatusScreen(TemplateView):
    """Status screen for a Shift."""

    template_name = "status_screen/status_screen.html"

    def get(self, request, **kwargs):
        """GET request for status screen view."""
        shift = kwargs.get("shift")
        return render(request, self.template_name, {"shift": shift})


class VenueRedirectView(View):
    """Redirect to the current shift of a venue."""

    def get(self, request, **kwargs):
        """Redirect a user to the active status screen of a shift."""
        venue = kwargs.get("venue")
        shift = currently_active_shift_for_venue(venue)
        if shift is None:
            raise Http404()
        else:
            return redirect(reverse("status_screen:status", kwargs={"shift": shift}))
