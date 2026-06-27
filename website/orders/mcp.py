"""MCP tools exposed by the orders app."""

from mcp_server import MCPToolset

from orders import services as orders_services
from orders.exceptions import OrderException
from orders.models import Order, Product, Shift
from tosti.mcp import require_scope
from django.utils import timezone


class OrderTools(MCPToolset):
    """Shift listing and order placement tools.

    Thin wrappers around ``orders.services``; business logic lives there so
    the API views and the MCP tools share one implementation.
    """

    # See ``tosti.mcp.stamp_tool_annotations`` for what these do.
    tool_annotations = {
        "list_active_shifts": {
            "readOnlyHint": True,
            "openWorldHint": False,
            "title": "List active shifts",
        },
        "list_available_products": {
            "readOnlyHint": True,
            "openWorldHint": False,
            "title": "List available products in a shift",
        },
        "place_order": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
            "title": "Place an order",
        },
    }

    def list_active_shifts(self) -> list[dict]:
        """List currently active shifts where you can place an order.

        A shift is "active" when the current time is between its start and end
        and it has not been finalized.
        """
        current_time = timezone.now()

        return [
            {
                "id": s.id,
                "venue": str(s.venue),
                "start": s.start.isoformat() if s.start else None,
                "end": s.end.isoformat() if s.end else None,
                "can_order": s.can_order,
            }
            for s in Shift.objects.filter(
                start__lte=current_time, end__gte=current_time, finalized=False
            )
        ]

    def list_available_products(self, shift_id: int) -> dict:
        """Retrieve the available products in a Shift.
        
        ``shift_id`` matches the ID of an active shift returned by ``list_active_shifts`.
        The result includes products available for ordering in the shift.
        """
        try:
            shift = Shift.objects.get(pk=shift_id)
        except Shift.DoesNotExist:
            return {"error": f"Shift {shift_id} not found."}

        return [
            {
                "id": p.id,
                "name": p.name,
                "current_price": p.current_price,
            }
            for p in Product.objects.filter(
                available_at=shift.venue, orderable=True, available=True
            )
        ]

    def place_order(self, shift_id: int, product_id: int) -> dict:
        """Place a single-item order on the user's behalf in an active shift.

        Resolve ``shift_id`` from ``list_active_shifts`` and ``product_id``
        from a product list. Requires the ``orders:order`` OAuth2 scope.

        Destructive: the LLM should confirm with the user before calling.
        """
        scope_error = require_scope(self.request, "orders:order")
        if scope_error:
            return {"error": scope_error}

        try:
            shift = Shift.objects.get(pk=shift_id)
        except Shift.DoesNotExist:
            return {"error": f"Shift {shift_id} not found."}
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return {"error": f"Product {product_id} not found."}

        try:
            order = orders_services.add_user_order(
                product=product,
                shift=shift,
                user=self.request.user,
                priority=Order.PRIORITY_NORMAL,
            )
        except OrderException as e:
            return {"error": str(e)}

        return {
            "order_id": order.id,
            "product": str(product),
            "shift_id": shift.id,
            "venue": str(shift.venue),
        }
