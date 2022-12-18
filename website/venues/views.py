from django.contrib import messages
from django.contrib.admin.models import ADDITION, DELETION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView, FormView, ListView, DeleteView, UpdateView
from django_ical.views import ICalFeed

from tosti.filter import Filter
from tosti.utils import log_action
from venues import services
from venues.forms import ReservationForm, ReservationUpdateForm, ReservationDisabledForm
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
        instance.user_created = self.request.user
        instance.save()
        log_action(self.request.user, instance, ADDITION, "Created reservation via website.")
        messages.success(self.request, "Venue reservation request added successfully.")
        services.send_reservation_request_email(instance)
        return redirect(reverse("venues:list_reservations"))


@method_decorator(login_required, name="dispatch")
class ListReservationsView(ListView):
    """List venue reservations."""

    model = Reservation
    template_name = "venues/reservation_list.html"
    paginate_by = 20

    def get_queryset(self):
        """Only list reservations you have access to."""
        if not self.request.user.is_authenticated:
            return super().get_queryset().none()
        return super().get_queryset().filter(pk__in=self.request.user.reservations_access.values("pk"))


class ReservationUpdateView(UpdateView):
    """View and update a reservation."""

    template_name = "venues/reservation_view.html"
    model = Reservation

    def get_queryset(self):
        """Only allow reservations you have access to."""
        if not self.request.user.is_authenticated:
            return super().get_queryset().none()
        return super().get_queryset().filter(pk__in=self.request.user.reservations_access.values("pk"))

    def get_form_class(self):
        """Determine which form class to use for the main form."""
        if self.get_object().can_be_changed:
            return ReservationUpdateForm
        else:
            return ReservationDisabledForm

    def get_success_url(self):
        """Redirect to the details of the reservation."""
        return reverse("venues:view_reservation", kwargs={"pk": self.get_object().pk})

    def dispatch(self, request, *args, **kwargs):
        """Check if this reservation can be changed."""
        if not self.get_object().can_be_changed:
            messages.add_message(self.request, messages.ERROR, "You cannot change this reservation anymore.")
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Process the form."""
        obj = form.save()
        obj.user_updated = self.request.user
        obj.save()
        log_action(self.request.user, obj, CHANGE, "Updated reservation via website.")
        messages.add_message(self.request, messages.SUCCESS, "Your borrel reservation has been updated.")
        return redirect(self.get_success_url())


class ReservationCancelView(DeleteView):
    """Delete a reservation."""

    model = Reservation
    template_name = "venues/reservation_cancel.html"
    success_url = reverse_lazy("venues:list_reservations")

    def get_queryset(self):
        """Only allow reservations you have access to."""
        if not self.request.user.is_authenticated:
            return super().get_queryset().none()
        return super().get_queryset().filter(pk__in=self.request.user.reservations_access.values("pk"))

    def dispatch(self, request, *args, **kwargs):
        """Display a warning if the reservation cannot be cancelled."""
        if not self.get_object().can_be_changed:
            messages.add_message(self.request, messages.ERROR, "You cannot cancel this reservation anymore.")
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """Delete the reservation."""
        obj = self.get_object()
        log_action(self.request.user, obj, DELETION, "Cancelled reservation via website.")
        messages.add_message(self.request, messages.SUCCESS, "Your reservation has been cancelled.")
        return super().delete(request, *args, **kwargs)


@method_decorator(login_required, name="dispatch")
class JoinReservationView(View):
    """Join a reservations via the join code."""

    def get(self, *args, **kwargs):
        """Process a get request."""
        try:
            reservation = Reservation.objects.get(join_code=self.kwargs.get("code"))
        except Reservation.DoesNotExist:
            messages.add_message(self.request, messages.INFO, "Invalid code.")
            return redirect(reverse("index"))

        if self.request.user not in reservation.users_access.all():
            reservation.users_access.add(self.request.user)
            reservation.save()
            log_action(self.request.user, reservation, CHANGE, "Joined reservation via website.")
            messages.add_message(self.request, messages.INFO, "You now have access to this reservation.")

        return redirect(reverse("venues:view_reservation", kwargs={"pk": reservation.pk}))


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
