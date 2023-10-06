from django.apps import AppConfig
from django.urls import reverse


def user_has_borrel_brevet_lazy(request):
    """Check if user has borrel brevet (but only import the model on execution)."""
    from borrel.models import BasicBorrelBrevet

    try:
        _ = request.user.basic_borrel_brevet
    except BasicBorrelBrevet.DoesNotExist:
        return False
    except AttributeError:  # for AnonymousUser
        return False
    return True


class BorrelConfig(AppConfig):
    """Borrel Config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "borrel"

    def ready(self):
        """Register signals."""
        from borrel import signals  # noqa

    def new_reservation_buttons(self, request):
        """Register new reservation buttons."""
        if user_has_borrel_brevet_lazy(request):
            return [
                {
                    "name": "Add borrel reservation",
                    "href": reverse("borrel:add_reservation"),
                    "order": 1,
                }
            ]
        return []

    def menu_items(self, request):
        """Register menu items."""
        if not request.user.is_authenticated or not user_has_borrel_brevet_lazy(request):
            return []

        return [
            {
                "title": "Borrel reservations",
                "url": reverse("borrel:list_reservations"),
                "location": "user",
                "order": 2,
            },
        ]

    def statistics(self, request):
        """Register the statistics."""
        from borrel.views import statistics

        content = statistics(request)

        if content is None:
            return None

        return {
            "content": content,
            "order": 4,
        }
