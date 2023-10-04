from django.apps import AppConfig
from django.urls import reverse


def user_has_borrel_brevet_lazy(request):
    from borrel.models import BasicBorrelBrevet

    try:
        _ = request.user.basic_borrel_brevet
    except BasicBorrelBrevet.DoesNotExist:
        return False
    return True


class BorrelConfig(AppConfig):
    """Borrel Config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "borrel"

    def ready(self):
        """Ready method."""
        from borrel import signals  # noqa

    def new_reservation_buttons(self, request):
        """Render new reservation buttons."""
        if user_has_borrel_brevet_lazy(request):
            return [
                {
                    "name": "Add borrel reservation",
                    "href": reverse("borrel:add_reservation"),
                    "order": 1,
                }  # noqa
            ]
        return []

    def menu_items(self, request):
        """Render menu items."""

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
