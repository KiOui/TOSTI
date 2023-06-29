from django.urls.converters import SlugConverter

from fridges.models import Fridge


class FridgeConverter(SlugConverter):
    """SlugConverter for Fridge model."""

    def to_python(self, value):
        """Convert slug to Fridge model."""
        try:
            return Fridge.objects.get(slug=value)
        except Fridge.DoesNotExist:
            raise ValueError

    def to_url(self, obj):
        """Convert Fridge model to slug."""
        return obj.slug
