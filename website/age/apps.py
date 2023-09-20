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
        from tosti.views import ExplainerView
        from age.views import AgeOverviewView, explainer_page_how_to_verify_age_with_yivi

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

        def filter_explainer_page(explainer_page_list: list):
            """Add explainer pages."""
            explainer_page_list.append(
                {
                    "name": "How to verify your age with Yivi?",
                    "slug": "how-to-verify-your-age-with-yivi",
                    "renderer": explainer_page_how_to_verify_age_with_yivi,
                }
            )
            return explainer_page_list

        ExplainerView.explainer_tabs.add_filter(filter_explainer_page)
        AccountFilterView.user_data_tabs.add_filter(filter_user_page, 2)
