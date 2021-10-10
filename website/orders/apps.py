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
        from orders.views import render_ordered_items_tab

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

        AccountView.user_data_tabs.add_filter(filter_user_page)
