from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import TemplateView, FormView

from venues.forms import ReservationForm


class VenueCalendarView(TemplateView):
    """All venues calendar view."""

    template_name = "venues/calendar.html"


class RequestReservationView(LoginRequiredMixin, FormView):
    """Request Reservation view."""

    template_name = "venues/reservation_request.html"
    form_class = ReservationForm

    def get_success_url(self):
        """Get the success URL."""
        success_parameters = {"success": "true"}
        query_string = urlencode(success_parameters)
        return "{}?{}".format(reverse("venues:add_reservation"), query_string)

    def get_form_kwargs(self):
        """Get the kwargs for rendering the form."""
        """Update kwargs with the request."""
        kwargs = super(RequestReservationView, self).get_form_kwargs()
        kwargs.update(
            {
                "request": self.request,
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        """Get the context data for rendering the template."""
        context = super(RequestReservationView, self).get_context_data(**kwargs)
        context.update({"success": self.request.GET.get("success", None)})
        return context
