"""MCP tools exposed by the venues app."""

from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime

from mcp_server import MCPToolset

from tosti.mcp import require_scope
from venues import services
from venues.models import Venue


class VenueTools(MCPToolset):
    """Venue lookup and reservation tools.

    Reservation creation is delegated to ``venues.services.create_reservation``
    so the MCP path and any other consumer share the same validation and email
    side effect.
    """

    def list_venues(self) -> list[dict]:
        """List all venues that can be reserved or where shifts can run.

        Returns one entry per venue with its ``id``, human-readable ``name``,
        URL ``slug``, and whether it can be reserved.
        """
        return [
            {
                "id": v.id,
                "name": v.name,
                "slug": v.slug,
                "can_be_reserved": v.can_be_reserved,
            }
            for v in Venue.objects.all()
        ]

    def create_venue_reservation(
        self,
        venue_slug: str,
        title: str,
        start: str,
        end: str,
        comments: str = "",
    ) -> dict:
        """Request a reservation for a venue.

        ``start`` and ``end`` are ISO-8601 timestamps (e.g.
        ``2026-04-25T19:00:00+02:00``). Reservations start unaccepted; a
        manager has to approve them. Requires the ``write`` OAuth2 scope.

        Destructive: the LLM should confirm with the user before calling.
        """
        scope_error = require_scope(self.request, "write")
        if scope_error:
            return {"error": scope_error}

        try:
            venue = Venue.objects.get(slug=venue_slug)
        except Venue.DoesNotExist:
            return {"error": f"Venue '{venue_slug}' not found."}

        start_dt = parse_datetime(start)
        end_dt = parse_datetime(end)
        if start_dt is None or end_dt is None:
            return {"error": "start/end must be ISO-8601 timestamps."}

        try:
            reservation = services.create_reservation(
                venue=venue,
                user=self.request.user,
                title=title,
                start=start_dt,
                end=end_dt,
                comments=comments,
            )
        except ValidationError as e:
            messages = e.messages if hasattr(e, "messages") else [str(e)]
            return {"error": "; ".join(str(m) for m in messages)}

        return {
            "reservation_id": reservation.id,
            "venue": str(venue),
            "title": title,
            "start": reservation.start.isoformat(),
            "end": reservation.end.isoformat(),
            "accepted": reservation.accepted,
        }
