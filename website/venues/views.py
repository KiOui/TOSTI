from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, FormView, ListView
from django_ical.views import ICalFeed

from tosti.filter import Filter
from venues import services
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
        services.send_reservation_request_email(instance)
        return redirect(reverse("venues:add_reservation"))


@method_decorator(login_required, name="dispatch")
class ListReservationsView(ListView):
    """List venue reservations."""

    model = Reservation
    template_name = "venues/reservation_list.html"

    def get_queryset(self):
        """Only allow access to user's own reservations."""
        return super().get_queryset().filter(user__pk=self.request.user.pk)


class ReservationFeed(ICalFeed):
    """Output an iCal feed containing all reservations."""

    def product_id(self, obj):
        """Get product ID."""
        return f"-//{Site.objects.get_current().domain}//ReservationCalendar"

    def title(self, obj):
        """Get calendar title."""
        return "T.O.S.T.I. Reservation calendar"

    def items(self, obj):
        """Get calendar items."""
        return Reservation.objects.filter(accepted=True).order_by("-start")

    def item_title(self, item):
        """Get item title."""
        if item.association is not None:
            return f"{item.association}: {item.title}"
        else:
            return item.title

    def item_description(self, item):
        """Get item description."""
        return (
            f"Title: {item.title}<br>"
            f"Comments: {item.comment}<br>"
            f'<a href="{self.item_link(item)}">View on T.O.S.T.I.</a>'
        )

    def item_start_datetime(self, item):
        """Get start datetime."""
        return item.start

    def item_end_datetime(self, item):
        """Get end datetime."""
        return item.end

    def item_link(self, item):
        """Get item link."""
        return "https://{}{}".format(
            Site.objects.get_current().domain,
            reverse("admin:venues_reservation_change", kwargs={"object_id": item.id}),
        )

    def item_location(self, item):
        """Get item location."""
        return f"{item.venue}"


class ReservationVenueFeed(ReservationFeed):
    """Output an iCal feed containing reservations for a venue."""

    def product_id(self, obj):
        """Get product ID."""
        return f"-//{Site.objects.get_current().domain}//ReservationCalendar//{obj.name}"

    def get_object(self, request, *args, **kwargs):
        """Get the object."""
        return kwargs.get("venue")

    def items(self, obj):
        """Get calendar items."""
        return Reservation.objects.filter(accepted=True, venue=obj).order_by("-start")

    def title(self, obj):
        """Get calendar title."""
        return f"T.O.S.T.I. Reservation calendar ({obj})"
