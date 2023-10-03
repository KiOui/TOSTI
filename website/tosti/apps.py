from django.apps import AppConfig


class TostiConfig(AppConfig):
    """The default app config for the Tosti app."""

    name = "tosti"

    def ready(self):
        """Ready method."""
        from users.views import AccountFilterView
        from tosti.views import OAuthCredentialsRequestView

        def filter_user_page(user_page_list: list):
            """Add requested songs as a tab to users page."""
            user_page_list.append(
                {
                    "name": "OAuth Credentials",
                    "slug": "oauth_credentials",
                    "view": OAuthCredentialsRequestView.as_view(),
                }  # noqa
            )
            return user_page_list

        AccountFilterView.user_data_tabs.add_filter(filter_user_page, 5)
