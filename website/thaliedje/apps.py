from django.apps import AppConfig
from django.urls import reverse


class ThaliedjeConfig(AppConfig):
    """The default app config for the Thaliedje app."""

    name = "thaliedje"

    def ready(self):
        """Ready method."""
        from users.views import AccountFilterView
        from thaliedje.views import AccountHistoryTabView

        def filter_user_page(user_page_list: list):
            """Add requested songs as a tab to users page."""
            user_page_list.append(
                {
                    "name": "Requested songs",
                    "slug": "requested_songs",
                    "view": AccountHistoryTabView.as_view(),
                }  # noqa
            )
            return user_page_list

        AccountFilterView.user_data_tabs.add_filter(filter_user_page, 4)

    def announcements(self, request):
        """Add announcements."""
        from thaliedje.models import ThaliedjeBlacklistedUser

        if (
            request.user is not None
            and request.user.is_authenticated
            and ThaliedjeBlacklistedUser.objects.filter(user=request.user).exists()
        ):
            return ["You are&nbsp;<b>blacklisted</b>&nbsp;from thaliedje!"]

        return []

    def menu_items(self, _):
        """Render menu items."""
        return [
            {
                "title": "Thaliedje",
                "url": reverse("thaliedje:index"),
                "location": "end",
                "order": 1,
            },
        ]
