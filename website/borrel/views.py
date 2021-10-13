from django.shortcuts import render
from django.views.generic import TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin

from borrel.forms import ReservationRequestForm
from borrel.mixins import BasicBorrelBrevetRequiredMixin


class AllCalendarView(TemplateView):
    """All venues calendar view."""

    template_name = "borrel/calendar.html"


class VenueCalendarView(TemplateView):
    """Specific Venue calendar view."""

    template_name = "borrel/venue_calendar.html"

    def get(self, request, **kwargs):
        venue = kwargs.get("venue")
        return render(request, self.template_name, {"venue": venue})


class ReservationRequestCreateView(BasicBorrelBrevetRequiredMixin, FormView):
    """Create view for Reservation Request."""

    template_name = "borrel/reservation_request_create.html"
    form_class = ReservationRequestForm

    def get_form_kwargs(self):
        kwargs = super(ReservationRequestCreateView, self).get_form_kwargs()
        kwargs.update({
            "request": self.request,
        })
        return kwargs


