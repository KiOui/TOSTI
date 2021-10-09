from django.shortcuts import render
from django.views.generic import TemplateView

from venues.models import Venue


class TestView(TemplateView):
    """Test view."""

    template_name = "venues/test.html"

    def get(self, request, **kwargs):
        """
        GET request for IndexView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the index page
        """
        return render(request, self.template_name, {"venue": Venue.objects.get(pk=1)})
