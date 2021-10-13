from django.views.generic import TemplateView


class VenueCalendarView(TemplateView):
    """All venues calendar view."""

    template_name = "venues/calendar.html"
