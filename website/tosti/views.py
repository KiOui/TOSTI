from django.shortcuts import render
from django.views.generic import TemplateView

from venues.models import Venue
from orders.models import Shift


class IndexView(TemplateView):
    """Index view."""

    template_name = "tosti/index.html"

    def get(self, request, **kwargs):
        """
        GET request for IndexView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the index page
        """
        venues = Venue.objects.filter(active=True)

        for venue in venues:
            shifts = [x for x in Shift.objects.filter(venue=venue) if x.can_order]

            if len(shifts) == 1:
                venue.shift = shifts[0]
            else:
                venue.shift = None

        return render(request, self.template_name, {"venues": venues})


class PrivacyView(TemplateView):
    """Privacy policy view."""

    template_name = "tosti/privacy.html"
