from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
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

    def get_form_kwargs(self):
        """Get the kwargs for rendering the form."""
        kwargs = super(RequestReservationView, self).get_form_kwargs()
        kwargs.update(
            {
                "request": self.request,
            }
        )
        return kwargs

    def form_valid(self, form):
        """Save the form and add User data."""
        instance = form.save(commit=False)
        instance.user = self.request.user
        instance.save()
        messages.success(self.request, "Reservation request added successfully.")
        return redirect(reverse("venues:add_reservation"))

    def get_context_data(self, **kwargs):
        """Get the context data for rendering the template."""
        context = super(RequestReservationView, self).get_context_data(**kwargs)
        return context
