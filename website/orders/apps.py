from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """AppConfig for orders app."""

    name = "orders"

    def ready(self):
        """Register signals."""
        from orders import signals  # noqa

    def user_account_tabs(self, _):
        """Register user account tabs."""
        from orders.views import (
            AccountHistoryTabView,
        )

        return [
            {
                "name": "Ordered items",
                "slug": "ordered_items",
                "view": AccountHistoryTabView.as_view(),
                "order": 3,
            }
        ]

    def explainer_tabs(self, _):
        """Register explainer tabs."""
        from orders.views import (
            explainer_page_how_to_order_tab,
            explainer_page_how_to_manage_shift_tab,
            explainer_page_how_to_hand_in_deposit,
            explainer_page_how_to_process_deposit,
        )

        return [
            {
                "name": "Order",
                "slug": "how-to-order",
                "renderer": explainer_page_how_to_order_tab,
                "order": 1,
            },
            {
                "name": "Manage a shift",
                "slug": "how-to-manage-shift",
                "renderer": explainer_page_how_to_manage_shift_tab,
                "order": 2,
            },
            {
                "name": "Hand in deposit",
                "slug": "how-to-hand-in-deposit",
                "renderer": explainer_page_how_to_hand_in_deposit,
                "order": 3,
            },
            {
                "name": "Process deposit",
                "slug": "how-to-process-deposit",
                "renderer": explainer_page_how_to_process_deposit,
                "order": 4,
            },
        ]

    def announcements(self, request):
        """Register announcements."""
        from orders.models import OrderBlacklistedUser

        if (
            request.user is not None
            and request.user.is_authenticated
            and OrderBlacklistedUser.objects.filter(user=request.user).exists()
        ):
            return ["You are&nbsp;<b>blacklisted</b>&nbsp;for placing orders!"]

        return []

    def statistics(self, request):
        """Register the statistics."""
        from orders.views import statistics

        return {
            "content": statistics(request),
            "order": 0,
        }
