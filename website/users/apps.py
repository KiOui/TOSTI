from django.apps import AppConfig


class UsersConfig(AppConfig):
    """AppConfig."""

    name = "users"

    def ready(self):
        """Register signals."""
        import users.signals  # noqa
        from users.views import AccountFilterView, AccountView

        def filter_user_page(user_page_list: list):
            """Add Ordered items tab on accounts page."""
            user_page_list.append(
                {
                    "name": "Account",
                    "slug": "account",
                    "view": AccountView.as_view(),
                }  # noqa
            )
            return user_page_list

        AccountFilterView.user_data_tabs.add_filter(filter_user_page)
