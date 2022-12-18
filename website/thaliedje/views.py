from django.contrib import messages
from django.contrib.admin.models import CHANGE, ADDITION
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView, UpdateView

from tosti.utils import log_action
from venues.models import Reservation
from .forms import ThaliedjeControlEventForm
from .models import SpotifyQueueItem, ThaliedjeControlEvent
from .services import can_request_song, can_request_playlist, can_control_player, active_thaliedje_control_event


class IndexView(TemplateView):
    """Index view for thaliedje."""

    template_name = "thaliedje/index.html"


class NowPlayingView(TemplateView):
    """Now playing view with the player for a venue."""

    template_name = "thaliedje/now_playing.html"

    def get_context_data(self, **kwargs):
        """Get the context data for the view."""
        context = super().get_context_data(**kwargs)
        player = kwargs.get("player")
        context["player"] = player

        if not player.configured:
            context["disabled"] = True
            return context

        context["venue"] = player.venue

        venue_reservation = player.venue.reservations.filter(
            accepted=True, start__lte=timezone.now(), end__gte=timezone.now()
        ).first()
        if venue_reservation and self.request.user in venue_reservation.users_access.all():
            context["current_venue_reservation"] = venue_reservation

        control_event = active_thaliedje_control_event(player)
        if control_event and self.request.user in control_event.admins.all():
            context["current_control_event"] = control_event

        if self.request.user.is_authenticated:
            context["can_request_song"] = can_request_song(self.request.user, player)
            context["can_request_playlist"] = can_request_playlist(self.request.user, player)
            context["can_control_player"] = can_control_player(self.request.user, player)
        else:
            context["can_request_song"] = False
            context["can_request_playlist"] = False
            context["can_control_player"] = False
        return context


def render_account_history_tab(request, item, current_page_url):
    """Render the account history tab on the user page."""
    song_requests = SpotifyQueueItem.objects.filter(requested_by=request.user).order_by("-added")
    page = request.GET.get("page", 1) if (item["slug"] == request.GET.get("active", False)) else 1
    paginator = Paginator(song_requests, per_page=50)
    return render_to_string(
        "thaliedje/account_history.html",
        context={"page_obj": paginator.get_page(page), "current_page_url": current_page_url, "item": item},
    )


@method_decorator(login_required, name="dispatch")
class ThaliedjeControlEventView(UpdateView):
    """View for the ThaliedjeControlEvent model."""

    model = ThaliedjeControlEvent
    form_class = ThaliedjeControlEventForm
    template_name = "thaliedje/thaliedje_control_event.html"

    def get_queryset(self):
        """Get the queryset for the view."""
        return ThaliedjeControlEvent.objects.filter(active=True)

    def dispatch(self, request, *args, **kwargs):
        """Dispatch the request to the view."""
        if not request.user.is_authenticated or not self.get_object().admins.filter(pk=request.user.pk).exists():
            messages.error(request, "You don't have access to this page.")
            return redirect(reverse("index"))
        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name="dispatch")
class ThaliedjeControlEventJoinView(View):
    """Join a control event via the join code."""

    def get(self, *args, **kwargs):
        """Process a get request."""
        try:
            event = ThaliedjeControlEvent.objects.get(join_code=self.kwargs.get("code"))
        except ThaliedjeControlEvent.DoesNotExist:
            messages.add_message(self.request, messages.INFO, "Invalid code.")
            return redirect(reverse("index"))

        if not event.active:
            messages.add_message(self.request, messages.INFO, "This event is not active.")
            return redirect(reverse("index"))

        if self.request.user not in event.selected_users.all():
            event.selected_users.add(self.request.user)
            event.save()
            log_action(self.request.user, event, CHANGE, "Joined event via website.")
            messages.add_message(
                self.request, messages.INFO, f"You now have access to {event.player} during {event.event.title}."
            )

        return redirect(reverse("thaliedje:now-playing", kwargs={"player": event.player.pk}))


@method_decorator(login_required, name="dispatch")
class ThaliedjeControlEventCreateView(View):
    """Create a control event."""

    def get(self, *args, **kwargs):
        """Process a get request."""
        reservation_id = self.kwargs.get("pk")

        try:
            reservation = Reservation.objects.filter(
                accepted=True, start__lte=timezone.now(), end__gte=timezone.now(), venue__player__isnull=False
            ).get(pk=reservation_id)
        except Reservation.DoesNotExist:
            messages.add_message(self.request, messages.INFO, "Invalid event.")
            return redirect(reverse("index"))

        if not self.request.user.is_authenticated or self.request.user not in reservation.users_access.all():
            messages.add_message(self.request, messages.INFO, "You don't have access to this event.")
            return redirect(reverse("index"))

        event = ThaliedjeControlEvent.objects.create(
            event=reservation,
        )
        log_action(self.request.user, event, ADDITION, "Created event via website.")
        return redirect(reverse("thaliedje:event-control", kwargs={"pk": event.pk}))
