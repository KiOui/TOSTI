from django.apps import AppConfig


class ThaliedjeConfig(AppConfig):
    """The default app config for the Thaliedje app."""

    name = "thaliedje"

    def ready(self):
        """Ready method."""
        from users.views import AccountView
        from thaliedje.views import render_account_history_tab

        def filter_user_page(user_page_list: list):
            """Add requested songs as a tab to users page."""
            user_page_list.append(
                {"name": "Requested songs", "slug": "requested_songs", "renderer": render_account_history_tab,}  # noqa
            )
            return user_page_list

        AccountView.user_data_tabs.add_filter(filter_user_page)
