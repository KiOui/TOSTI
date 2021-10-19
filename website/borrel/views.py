from django.shortcuts import render
from django.views.generic import TemplateView, FormView

from borrel.forms import BorrelReservationRequestForm, BorrelReservationFormset
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


class ReservationRequestCreateView(FormView):
    """Create view for Reservation Request."""

    template_name = "borrel/reservation_request_create.html"
    form_class = BorrelReservationRequestForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["items"] = BorrelReservationFormset(self.request.POST)
        else:
            context["items"] = BorrelReservationFormset()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        items = context["items"]
        if not items.is_valid():
            obj = form.save()
            items.instance = obj
            items.save()
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super(ReservationRequestCreateView, self).get_form_kwargs()
        kwargs.update(
            {
                "request": self.request,
            }
        )
        return kwargs
