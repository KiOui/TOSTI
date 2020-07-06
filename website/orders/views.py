import json

from django.contrib.auth import get_user_model
from guardian.decorators import permission_required_or_403, permission_required

from orders import services
from orders.exceptions import OrderException
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from .models import Shift, Product, OrderVenue
from .forms import ShiftForm
import urllib.parse

from .templatetags.order_now import (
    render_order_header,
    render_order_items,
)

User = get_user_model()


def shift_view(request, *args, **kwargs):
    """View for all active shifts."""
    active_shifts = [x for x in Shift.objects.all() if x.is_active]
    return render(request, "orders/shifts.html", {"shifts": active_shifts})


@permission_required("orders.can_order_in_venue", (OrderVenue, "pk", "venue_id"), accept_global_perms=True)
def _shift_overview_view(request, shift, *args, **kwargs):
    """Overview for a shift."""
    return render(request, "orders/shift_overview.html", {"shift": shift})


def shift_overview_view(request, shift, *args, **kwargs):
    """Overview for a shift."""
    kwargs["venue_id"] = shift.venue.pk
    return _shift_overview_view(request, shift, *args, **kwargs)


@permission_required("orders.can_order_in_venue", (OrderVenue, "pk", "venue_id"), accept_global_perms=True)
def _product_list_view(request, shift, *args, **kwargs):
    """View for products to order."""
    if request.method == "POST":
        option = request.POST.get("option", None)
        if option == "list":
            pass
        else:
            return JsonResponse({"error": "Operation unknown"})

        def get_available_products(shift, user):
            items = Product.objects.filter(available=True, available_at=shift.venue)
            json_list = list()
            for item in items:
                json_obj = item.to_json()
                json_obj["max_allowed"] = item.user_max_order_amount(user, shift)
                json_list.append(json_obj)
            return json_list

        products = get_available_products(shift, request.user)
        return JsonResponse({"products": products, "shift_max": shift.user_max_order_amount(request.user)})


def product_list_view(request, shift, *args, **kwargs):
    """View for products to order."""
    kwargs["venue_id"] = shift.venue.pk
    return _product_list_view(request, shift, *args, **kwargs)


@permission_required("orders.can_order_in_venue", (OrderVenue, "pk", "venue_id"), accept_global_perms=True)
def _order_view(request, shift, *args, **kwargs):
    """Place an order."""
    template_name = "orders/order.html"
    if request.method == "POST":
        cookie = request.COOKIES.get("cart_{}".format(shift.pk), None)
        if cookie is None:
            return render(request, template_name, {"shift": shift, "error": "No orders submitted"},)

        cookie = urllib.parse.unquote(cookie)
        try:
            cookie = json.loads(cookie)
        except json.JSONDecodeError:
            page = render(request, template_name, {"shift": shift, "error": "Error decoding cookie"},)
            page.delete_cookie("cart_{}".format(shift.pk))
            return page

        def add_orders(order_list, s, user):
            product_list = []
            for product_id in order_list:
                try:
                    product_list.append(Product.objects.get(pk=product_id))
                except (Product.DoesNotExist, ValueError):
                    return "That product does not exist"
            try:
                services.place_orders(product_list, user, s)
            except OrderException as err:
                return str(err)
            return True

        error_msg = add_orders(cookie, shift, request.user)

        if isinstance(error_msg, str):
            return render(request, template_name, {"shift": shift, "error": error_msg})
        else:
            response = redirect("orders:shift_overview", shift=shift)
            response.delete_cookie("cart_{}".format(shift.pk))
            return response
    else:
        return render(
            request,
            template_name,
            {"shift": shift, "already_ordered": services.has_already_ordered_in_shift(request.user, shift)},
        )


def order_view(request, shift, *args, **kwargs):
    """Place an order."""
    kwargs["venue_id"] = shift.venue.pk
    return _order_view(request, shift, *args, **kwargs)


@permission_required_or_403(
    "orders.can_manage_shift_in_venue", (OrderVenue, "pk", "venue_id"), accept_global_perms=True
)
def _create_shift_view(request, venue, *args, **kwargs):
    """Start a new shift in a venue."""
    if request.method == "POST":
        form = ShiftForm(request.POST, user=request.user)
        if form.is_valid():
            shift = form.save()
            return redirect("orders:shift_admin", shift=shift)
    else:
        form = ShiftForm(venue=venue, user=request.user)
        form.set_initial_users(User.objects.filter(pk=request.user.pk))

    return render(request, "orders/create_shift.html", {"user": request.user, "venue": venue, "form": form},)


def create_shift_view(request, venue, *args, **kwargs):
    """Start a new shift in a venue."""
    kwargs["venue_id"] = venue.pk
    return _create_shift_view(request, venue, *args, **kwargs)


@permission_required_or_403(
    "orders.can_manage_shift_in_venue", (OrderVenue, "pk", "venue_id"), accept_global_perms=True
)
def _join_shift_view(request, shift, *args, **kwargs):
    """Join an shift as admin."""
    if request.method == "POST":
        confirm = request.POST.get("confirm", None)
        if confirm == "Yes":
            services.add_user_to_assignees_of_shift(request.user, shift)
            return redirect("orders:shift_admin", shift=shift)
        elif confirm == "No":
            return redirect("index")
        else:
            return render(request, "orders/join_shift.html", {"shift": shift})
    else:
        assignees = shift.assignees.all()

        if request.user not in assignees:
            return render(request, "orders/join_shift.html", {"shift": shift})
        else:
            return redirect("orders:shift_admin", shift=shift)


def join_shift_view(request, shift, *args, **kwargs):
    """Join an shift as admin."""
    kwargs["venue_id"] = shift.venue.pk
    return _join_shift_view(request, shift, *args, **kwargs)


@permission_required_or_403(
    "orders.can_manage_shift_in_venue", (OrderVenue, "pk", "venue_id"), accept_global_perms=True
)
def _shift_admin_view(request, shift, *args, **kwargs):
    """Admin view of a shift."""
    return render(request, "orders/shift_admin.html", {"shift": shift})


def shift_admin_view(request, shift, *args, **kwargs):
    """Admin view of a shift."""
    kwargs["venue_id"] = shift.venue.pk
    return _shift_admin_view(request, shift, *args, **kwargs)


@permission_required_or_403(
    "orders.can_manage_shift_in_venue", (OrderVenue, "pk", "venue_id"), accept_global_perms=True
)
def _order_update_view(request, order, *args, **kwargs):
    """Update an order as admin."""
    if request.method == "POST":
        order_property = request.POST.get("property", None)
        value = request.POST.get("value", None)

        if order_property is None or value is None:
            return JsonResponse({"error": "Invalid request"})

        value = True if value == "true" else False

        if order_property == "ready":
            try:
                order = services.set_order_ready(order, value)
                return JsonResponse({"value": order.ready})
            except Exception as e:
                return JsonResponse({"error": str(e), "value": order.ready})
        elif order_property == "paid":
            try:
                order = services.set_order_paid(order, value)
                return JsonResponse({"value": order.paid})
            except Exception as e:
                return JsonResponse({"error": str(e), "value": order.paid})
        else:
            return JsonResponse({"error": "Property unknown"})


def order_update_view(request, order, *args, **kwargs):
    """Update an order as admin."""
    kwargs["venue_id"] = order.shift.venue.pk
    return _order_update_view(request, order, *args, **kwargs)


@permission_required_or_403(
    "orders.can_manage_shift_in_venue", (OrderVenue, "pk", "venue_id"), accept_global_perms=True
)
def _toggle_shift_activation_view(request, shift, *args, **kwargs):
    """Toggle shift accepting or not accepting orders."""
    if request.method == "POST":
        active = request.POST.get("active", "false")

        try:
            shift = services.set_shift_active(shift, active == "true")
            return JsonResponse({"active": shift.can_order})
        except Exception as e:
            return JsonResponse({"error": str(e), "active": shift.can_order})


def toggle_shift_activation_view(request, shift, *args, **kwargs):
    """Toggle shift accepting or not accepting orders."""
    kwargs["venue_id"] = shift.venue.pk
    return _toggle_shift_activation_view(request, shift, *args, **kwargs)


@permission_required_or_403(
    "orders.can_manage_shift_in_venue", (OrderVenue, "pk", "venue_id"), accept_global_perms=True
)
def _add_shift_capacity_view(request, shift, *args, **kwargs):
    """Add capacity to a shift."""
    add_amount = 5
    try:
        services.increase_shift_capacity(shift, add_amount)
        return JsonResponse({"error": False})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def add_shift_capacity_view(request, shift, *args, **kwargs):
    """Add capacity to a shift."""
    kwargs["venue_id"] = shift.venue.pk
    return _add_shift_capacity_view(request, shift, *args, **kwargs)


@permission_required_or_403(
    "orders.can_manage_shift_in_venue", (OrderVenue, "pk", "venue_id"), accept_global_perms=True
)
def _add_shift_time_view(request, shift, *args, **kwargs):
    """Add time to a shift."""
    add_amount_minutes = 5
    try:
        services.increase_shift_time(shift, add_amount_minutes)
        return JsonResponse({"error": False})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def add_shift_time_view(request, shift, *args, **kwargs):
    """Add time to a shift."""
    kwargs["venue_id"] = shift.venue.pk
    return _add_shift_time_view(request, shift, *args, **kwargs)


def refresh_header_view(request, shift):
    """Refresh the shift header."""
    header = get_template("orders/order_header.html").render(
        render_order_header({"request": request}, shift, refresh=True)
    )
    return JsonResponse({"data": header})


def refresh_product_overview_view(request, shift):
    """Refresh the product overview."""
    overview = get_template("orders/item_overview.html").render(
        render_order_header({"request": request}, shift, refresh=True)
    )
    return JsonResponse({"data": overview})


@permission_required_or_403(
    "orders.can_manage_shift_in_venue", (OrderVenue, "pk", "venue_id"), accept_global_perms=True
)
def _refresh_admin_footer_view(request, shift, *args, **kwargs):
    """Refresh the admin footer."""
    return JsonResponse({"status": shift.can_order})


def refresh_admin_footer_view(request, shift, *args, **kwargs):
    """Refresh the admin footer."""
    kwargs["venue_id"] = shift.venue.pk
    return _refresh_admin_footer_view(request, shift, *args, **kwargs)


@permission_required_or_403(
    "orders.can_manage_shift_in_venue", (OrderVenue, "pk", "venue_id"), accept_global_perms=True
)
def _refresh_shift_order_view(request, shift, *args, **kwargs):
    """Refresh the order view."""
    if request.method == "POST":
        admin = request.POST.get("admin", "false") == "true"
        footer = get_template("orders/order_items.html").render(
            render_order_items({"request": request}, shift, refresh=True, admin=admin, user=request.user)
        )
        return JsonResponse({"data": footer})


def refresh_shift_order_view(request, shift, *args, **kwargs):
    """Refresh the order view."""
    kwargs["venue_id"] = shift.venue.pk
    return _refresh_shift_order_view(request, shift, *args, **kwargs)
