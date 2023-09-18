from django.apps import AppConfig


class AgeConfig(AppConfig):
    """Age App Config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "age"

    def ready(self):
        """
        Ready method.

        :return: None
        """
        from users.views import AccountFilterView
        from age.views import (
            AgeOverviewView,
        )

        from age import signals  # noqa

        def filter_user_page(user_page_list: list):
            """Add age overview tab on accounts page."""
            user_page_list.append(
                {
                    "name": "Age",
                    "slug": "age",
                    "view": AgeOverviewView.as_view(),
                }  # noqa
            )
            return user_page_list

        AccountFilterView.user_data_tabs.add_filter(filter_user_page, 2)
