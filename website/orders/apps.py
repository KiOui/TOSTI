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
        from users.views import AccountFilterView
        from orders.views import (
            AccountHistoryTabView,
            explainer_page_how_to_order_tab,
            explainer_page_how_to_manage_shift_tab,
            explainer_page_how_to_hand_in_deposit,
            explainer_page_how_to_process_deposit,
        )
        from tosti.views import ExplainerView

        def filter_user_page(user_page_list: list):
            """Add Ordered items tab on accounts page."""
            user_page_list.append(
                {
                    "name": "Ordered items",
                    "slug": "ordered_items",
                    "view": AccountHistoryTabView.as_view(),
                }  # noqa
            )
            return user_page_list

        def filter_explainer_page(explainer_page_list: list):
            """Add explainer pages."""
            explainer_page_list.append(
                {
                    "name": "Order",
                    "slug": "how-to-order",
                    "renderer": explainer_page_how_to_order_tab,
                }
            )
            explainer_page_list.append(
                {
                    "name": "Manage a shift",
                    "slug": "how-to-manage-shift",
                    "renderer": explainer_page_how_to_manage_shift_tab,
                }
            )
            explainer_page_list.append(
                {
                    "name": "Hand in deposit",
                    "slug": "how-to-hand-in-deposit",
                    "renderer": explainer_page_how_to_hand_in_deposit,
                }
            )
            explainer_page_list.append(
                {
                    "name": "Process deposit",
                    "slug": "how-to-process-deposit",
                    "renderer": explainer_page_how_to_process_deposit,
                }
            )
            return explainer_page_list

        AccountFilterView.user_data_tabs.add_filter(filter_user_page, 3)
        ExplainerView.explainer_tabs.add_filter(filter_explainer_page)

    def announcements(self, request):
        """Add announcements."""
        from orders.models import OrderBlacklistedUser

        if (
            request.user is not None
            and request.user.is_authenticated
            and OrderBlacklistedUser.objects.filter(user=request.user).exists()
        ):
            return ["You are&nbsp;<b>blacklisted</b>&nbsp;for placing orders!"]

        return []
