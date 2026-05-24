from django.apps import AppConfig
from django.urls import reverse


class TamponConfig(AppConfig):
    """Configuration for the tampon app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tampon"

    def menu_items(self, request):
        """Register a user-menu entry pointing at the T.A.M.P.O.N. page."""
        if not request.user.is_authenticated:
            return []
        return [
            {
                "title": "Tampon",
                "url": reverse("tampon:index"),
                "location": "user",
                "order": 50,
            },
        ]
