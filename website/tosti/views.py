from django.views.generic import TemplateView


class IndexView(TemplateView):
    """Empty view."""

    def get(self, request, **kwargs):
        """GET request for empty index view."""
        pass
