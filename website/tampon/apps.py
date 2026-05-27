from django.apps import AppConfig
from django.urls import reverse


class TamponConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tampon"

    def menu_items(self, _):
        return [
            {
                "title": "Tampon",
                "url": reverse("tampon:index"),
                "location": "start",
                "order": 4,
            },
        ]
