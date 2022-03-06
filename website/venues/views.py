from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, FormView, ListView

from tosti.filter import Filter
from venues.forms import ReservationForm
from venues.models import Reservation


class VenueCalendarView(TemplateView):
    """All venues calendar view."""

    template_name = "venues/calendar.html"
    reservation_buttons = Filter()

    def get(self, request, **kwargs):
        """Get the calendar view."""
        buttons = self.reservation_buttons.do_filter([])
        return render(request, self.template_name, {"buttons": buttons})


@method_decorator(login_required, name="dispatch")
class RequestReservationView(FormView):
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
        messages.success(self.request, "Venue reservation request added successfully.")
        return redirect(reverse("venues:add_reservation"))

    def get_context_data(self, **kwargs):
        """Get the context data for rendering the template."""
        context = super(RequestReservationView, self).get_context_data(**kwargs)
        return context


@method_decorator(login_required, name="dispatch")
class ListReservationsView(ListView):
    """List venue reservations."""

    model = Reservation
    template_name = "venues/reservation_list.html"

    def get_queryset(self):
        """Only allow access to user's own reservations."""
        return super().get_queryset().filter(user__pk=self.request.user.pk)
