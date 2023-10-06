from django.apps import AppConfig
from django.urls import reverse


class ThaliedjeConfig(AppConfig):
    """The default app config for the Thaliedje app."""

    name = "thaliedje"

    def user_account_tabs(self, _):
        """Register user account tabs."""
        from thaliedje.views import AccountHistoryTabView

        return [
            {
                "name": "Requested songs",
                "slug": "requested_songs",
                "view": AccountHistoryTabView.as_view(),
                "order": 4,
            }
        ]

    def announcements(self, request):
        """Register announcements."""
        from thaliedje.models import ThaliedjeBlacklistedUser

        if (
            request.user is not None
            and request.user.is_authenticated
            and ThaliedjeBlacklistedUser.objects.filter(user=request.user).exists()
        ):
            return ["You are&nbsp;<b>blacklisted</b>&nbsp;from thaliedje!"]

        return []

    def menu_items(self, _):
        """Register menu items."""
        return [
            {
                "title": "Thaliedje",
                "url": reverse("thaliedje:index"),
                "location": "start",
                "order": 2,
            },
        ]
