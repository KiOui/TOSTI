"""MCP tools exposed by the venues app."""

from mcp_server import MCPToolset

from tosti.mcp import require_scope
from venues import services
from venues.forms import ReservationForm
from venues.models import Venue


class VenueTools(MCPToolset):
    """Venue lookup and reservation tools.

    Reservation creation is delegated to ``venues.services.create_reservation``
    so the MCP path and any other consumer share the same validation and email
    side effect.
    """

    # See ``tosti.mcp.stamp_tool_annotations`` for what these do.
    tool_annotations = {
        "list_venues": {
            "readOnlyHint": True,
            "openWorldHint": False,
            "title": "List venues",
        },
        "create_venue_reservation": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
            "title": "Create a venue reservation",
        },
    }

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

        form = ReservationForm(
            data={
                "venue": venue.pk,
                "start": start,
                "end": end,
                "title": title,
                "comments": comments,
            }
        )

        if not form.is_valid():
            e = form.errors.get_json_data()
            if "venue" in e.keys():
                e["venue_slug"] = e["venue"]
                del e["venue"]
            return {"error": e}

        instance = form.save(commit=False)
        instance.user_created = self.request.user
        instance.save()

        services.send_reservation_request_email(instance)

        return {
            "reservation_id": instance.id,
            "venue": str(venue),
            "title": title,
            "start": instance.start.isoformat(),
            "end": instance.end.isoformat(),
            "accepted": instance.accepted,
        }
