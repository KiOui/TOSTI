from django.apps import AppConfig
from django.urls import reverse


class FridgesConfig(AppConfig):
    """Configuration for the fridges app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "fridges"

    def menu_items(self, _):
        """Render menu items."""
        return [
            {
                "title": "Fridges",
                "url": reverse("fridges:index"),
                "location": "end",
                "order": 0,
            },
        ]
