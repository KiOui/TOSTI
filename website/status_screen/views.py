from django.views.generic import TemplateView
from django.utils import timezone

from orders.models import Shift
from venues.models import Reservation


class StatusScreenView(TemplateView):
    """All venues calendar view."""

    template_name = "status_screen/status_screen.html"

    def get_context_data(self, **kwargs):
        venue = self.kwargs["venue"]
        return {
            "venue": venue,
            "player": venue.player,
            "shift": Shift.objects.filter(venue__venue=venue, start__lte=timezone.now(), end__gte=timezone.now()).first(),
            "current_event": Reservation.objects.filter(venue=venue, accepted=True, start__lte=timezone.now(), end__gte=timezone.now()).first(),
            "next_event": Reservation.objects.filter(venue=venue, accepted=True, start__gte=timezone.now()).order_by("start").first(),
        }
