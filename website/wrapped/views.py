from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.template.loader import render_to_string
from django.views import View

from wrapped import services
from wrapped.periods import Period


class StoryView(LoginRequiredMixin, View):
    """The slides of the Wrapped of a period, loaded into the Wrapped popup when it opens."""

    def get(self, request, year):
        """Render the slides of the period starting in ``year``."""
        period = Period.starting_in(year)
        if not services.is_available(period):
            raise Http404("This Wrapped is not available (yet).")
        story = services.get_story(request.user, period)
        if not story["has_slides"]:
            raise Http404("Nothing happened in the canteens this year.")
        return HttpResponse(
            render_to_string("wrapped/slides.html", story, request=request)
        )
