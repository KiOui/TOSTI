from django.views.generic import ListView

from fridges.models import Fridge


class IndexView(ListView):
    """View for showing all fridges."""

    template_name = "fridges/index.html"
    model = Fridge
    context_object_name = "fridges"

    def get_queryset(self):
        """Get the queryset."""
        return Fridge.objects.filter(is_active=True).order_by("name")
