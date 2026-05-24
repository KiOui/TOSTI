"""Tests for the orders app's MCP toolset."""

from datetime import timedelta
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from orders.mcp import OrderTools
from orders.models import Order, OrderVenue, Product, Shift
from venues.models import Venue

User = get_user_model()


class _StubRequest:
    def __init__(self, user, auth=None):
        self.user = user
        self.auth = auth


class OrderToolsListShiftsTests(TestCase):
    fixtures = ["venues.json"]

    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="x")
        self.tools = OrderTools(request=_StubRequest(self.user))

    def test_list_active_shifts_only_returns_active_unfinalized(self):
        venue = Venue.objects.first()
        order_venue = OrderVenue.objects.create(venue=venue)
        now = timezone.now()
        active = Shift.objects.create(
            venue=order_venue,
            start=now - timedelta(minutes=10),
            end=now + timedelta(hours=1),
            can_order=True,
        )
        Shift.objects.create(
            venue=order_venue,
            start=now - timedelta(hours=3),
            end=now - timedelta(hours=2),
        )

        result = self.tools.list_active_shifts()
        ids = {s["id"] for s in result}
        self.assertIn(active.id, ids)
        for entry in result:
            self.assertIn("venue", entry)
            self.assertIn("start", entry)
            self.assertIn("end", entry)


class OrderToolsPlaceOrderTests(TestCase):
    fixtures = ["venues.json"]

    def setUp(self):
        self.user = User.objects.create_user(username="orderer", password="x")
        venue = Venue.objects.first()
        self.order_venue = OrderVenue.objects.create(venue=venue)
        now = timezone.now()
        self.shift = Shift.objects.create(
            venue=self.order_venue,
            start=now - timedelta(minutes=10),
            end=now + timedelta(hours=1),
            can_order=True,
        )
        self.product = Product.objects.create(
            name="Coffee",
            current_price=1.50,
            available=True,
            orderable=True,
            ignore_shift_restrictions=True,
        )
        self.product.available_at.add(self.order_venue)

    def test_unknown_shift_returns_error(self):
        tools = OrderTools(request=_StubRequest(self.user))
        result = tools.place_order(shift_id=999999, product_id=self.product.id)
        self.assertIn("error", result)
        self.assertIn("Shift", result["error"])

    def test_unknown_product_returns_error(self):
        tools = OrderTools(request=_StubRequest(self.user))
        result = tools.place_order(shift_id=self.shift.id, product_id=999999)
        self.assertIn("error", result)
        self.assertIn("Product", result["error"])

    def test_successful_order_creates_record(self):
        tools = OrderTools(request=_StubRequest(self.user))
        result = tools.place_order(shift_id=self.shift.id, product_id=self.product.id)
        self.assertNotIn("error", result)
        order = Order.objects.get(pk=result["order_id"])
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.product, self.product)
        self.assertEqual(order.shift, self.shift)

    def test_token_without_scope_blocks_order(self):
        token = MagicMock()
        token.is_valid = MagicMock(return_value=False)
        tools = OrderTools(request=_StubRequest(self.user, auth=token))
        result = tools.place_order(shift_id=self.shift.id, product_id=self.product.id)
        self.assertIn("error", result)
        self.assertIn("orders:order", result["error"])
        self.assertEqual(Order.objects.count(), 0)
