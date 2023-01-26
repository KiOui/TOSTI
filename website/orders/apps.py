from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """AppConfig for orders app."""

    name = "orders"

    def ready(self):
        """
        Ready method.

        :return: None
        """
        from orders import signals  # noqa
        from users.views import AccountView
        from orders.views import (
            render_ordered_items_tab,
            explainer_page_how_to_order_tab,
            explainer_page_how_to_manage_shift_tab,
        )
        from tosti.views import ExplainerView

        def filter_user_page(user_page_list: list):
            """Add Ordered items tab on accounts page."""
            user_page_list.append(
                {
                    "name": "Ordered items",
                    "slug": "ordered_items",
                    "renderer": render_ordered_items_tab,
                }  # noqa
            )
            return user_page_list

        def filter_explainer_page(explainer_page_list: list):
            """Add explainer pages."""
            explainer_page_list.append(
                {
                    "name": "How to order?",
                    "slug": "how-to-order",
                    "renderer": explainer_page_how_to_order_tab,
                }
            )
            explainer_page_list.append(
                {
                    "name": "How to manage a shift?",
                    "slug": "how-to-manage-shift",
                    "renderer": explainer_page_how_to_manage_shift_tab,
                }
            )
            return explainer_page_list

        AccountView.user_data_tabs.add_filter(filter_user_page)
        ExplainerView.explainer_tabs.add_filter(filter_explainer_page)

    def announcements(self, request):
        """Add announcements."""
        from orders.models import OrderBlacklistedUser

        if (
            request.user is not None
            and request.user.is_authenticated
            and OrderBlacklistedUser.objects.filter(user=request.user).exists()
        ):
            return ["You are&nbsp;<b>blacklisted</b>&nbsp;for creating orders!"]

        return []
