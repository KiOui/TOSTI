from django.http import Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from thaliedje.models import Player

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
        
class VenueStatusScreen(View):
    """Show music and active shift status of a venue."""

    orders_template_name = "status_screen/venue_status_screen.html"
    music_template_name = "status_screen/venue_music_screen.html"

    def get(self, request, **kwargs):
        """GET request for the status screen of a venue."""
        order_venue = kwargs.get("order_venue")
        active_shift = currently_active_shift_for_venue(order_venue)

        player = Player.objects.get(venue=order_venue.venue)

        if active_shift:
            return render(request, self.orders_template_name, {"shift": active_shift, "order_venue": order_venue})
        else:
            return render(request, self.music_template_name, {"player": player, "order_venue": order_venue})
