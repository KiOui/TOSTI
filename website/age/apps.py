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
        from age import signals  # noqa

    def user_account_tabs(self, _):
        """Render user account tabs."""
        from age.views import AgeOverviewView

        return [
            {
                "name": "Age",
                "slug": "age",
                "view": AgeOverviewView.as_view(),
                "order": 1,
            }  # noqa
        ]

    def explainer_tabs(self, _):
        from age.views import explainer_page_how_to_verify_age_with_yivi

        return [
            {
                "name": "Verify your age with Yivi",
                "slug": "verify-your-age-with-yivi",
                "renderer": explainer_page_how_to_verify_age_with_yivi,
                "order": 10,
            }
        ]
