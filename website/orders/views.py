import json

from django.views.generic import TemplateView
from guardian.mixins import PermissionRequiredMixin

from orders import services
from orders.exceptions import OrderException
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from .models import Product, Order
from .forms import CreateShiftForm
import urllib.parse

from .templatetags.order_now import (
    render_order_header,
    render_order_items,
)


class ShiftOverviewView(PermissionRequiredMixin, TemplateView):
    """Shift overview page."""

    template_name = "orders/shift_overview.html"

    permission_required = "orders.can_order_in_venue"
    return_403 = True
    accept_global_perms = True

    def get(self, request, **kwargs):
        """
        GET request of shift overview page.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the shift overview page
        """
        shift = kwargs.get("shift")

        return render(
            request,
            self.template_name,
            {"shift": shift, "can_manage_shift": request.user in shift.venue.get_users_with_shift_admin_perms()},
        )

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.get_object()
        return obj.venue

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("shift")


class ProductListView(PermissionRequiredMixin, TemplateView):
    """Product list view."""

    permission_required = "orders.can_order_in_venue"
    return_403 = True
    accept_global_perms = True

    @staticmethod
    def get_available_products(shift, user):
        """
        Get available products for a shift and a user in json format.

        :param shift: the shift
        :param user: the user
        :return: a json list of the products converted to json and an extra dictionary key (max_allowed) indicating
        how many more of the item a user can still order
        """
        items = Product.objects.filter(available=True, available_at=shift.venue, orderable=True)
        json_list = list()
        for item in items:
            json_obj = item.to_json()
            json_obj["max_allowed"] = item.user_max_order_amount(user, shift)
            json_list.append(json_obj)
        return json_list

    def post(self, request, **kwargs):
        """
        POST request for ProductListView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a json response with the products a user can order and the shift maximum
        """
        shift = kwargs.get("shift")
        option = request.POST.get("option", None)
        if option == "list":
            pass
        else:
            return JsonResponse({"error": "Operation unknown"})

        products = self.get_available_products(shift, request.user)
        return JsonResponse({"products": products, "shift_max": shift.user_max_order_amount(request.user)})

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.get_object()
        return obj.venue

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("shift")


class PlaceOrderView(PermissionRequiredMixin, TemplateView):
    """Order view."""

    template_name = "orders/place_order.html"

    permission_required = "orders.can_order_in_venue"
    return_403 = True
    accept_global_perms = True

    @staticmethod
    def add_orders(order_list, shift, user):
        """
        Add all orders in a list.

        :param order_list: a list of product ids
        :param shift: the shift to add the orders to
        :param user: the user for which the orders are
        :return: True if the addition succeeded, a string with an error message otherwise
        """
        product_list = []
        for product_id in order_list:
            try:
                product_list.append(Product.objects.get(pk=product_id, available=True, orderable=True))
            except (Product.DoesNotExist, ValueError):
                return "That product does not exist"
        try:
            services.place_orders(product_list, user, shift)
        except OrderException as err:
            return str(err)
        return True

    def get(self, request, **kwargs):
        """
        GET request for PlaceOrderView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: the product view with all ordered items of the user and all items that the user can order for this
        shift
        """
        shift = kwargs.get("shift")

        return render(
            request,
            self.template_name,
            {"shift": shift, "already_ordered": services.has_already_ordered_in_shift(request.user, shift)},
        )

    def post(self, request, **kwargs):
        """
        POST request for PlaceOrderView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: creates new orders that are specified in a cart_[shift_number] cookie or returns an error message
        """
        shift = kwargs.get("shift")
        cookie = request.COOKIES.get("cart_{}".format(shift.pk), None)
        if cookie is None:
            return render(request, self.template_name, {"shift": shift, "error": "No orders submitted"},)
        cookie = urllib.parse.unquote(cookie)
        try:
            cookie = json.loads(cookie)
        except json.JSONDecodeError:
            page = render(request, self.template_name, {"shift": shift, "error": "Error decoding cookie"},)
            page.delete_cookie("cart_{}".format(shift.pk))
            return page

        error_msg = self.add_orders(cookie, shift, request.user)
        if isinstance(error_msg, str):
            return render(request, self.template_name, {"shift": shift, "error": error_msg})
        else:
            response = redirect("orders:shift_overview", shift=shift)
            response.delete_cookie("cart_{}".format(shift.pk))
            return response

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.get_object()
        return obj.venue

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("shift")


class CreateShiftView(PermissionRequiredMixin, TemplateView):
    """Create shift view."""

    template_name = "orders/create_shift.html"

    permission_required = "orders.can_manage_shift_in_venue"
    return_403 = True
    accept_global_perms = True

    def get(self, request, **kwargs):
        """
        GET request for CreateShiftView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a page with all current shifts and a form for starting a new shift
        """
        venue = kwargs.get("venue")

        form = CreateShiftForm(venue=venue, user=request.user)

        return render(request, self.template_name, {"venue": venue, "form": form})

    def post(self, request, **kwargs):
        """
        POST request for CreateShiftView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a page with all current shifts and a form for starting a new shift, if the form was filled in
        correctly a new shift is started.
        """
        venue = kwargs.get("venue")

        form = CreateShiftForm(request.POST, user=request.user)

        if form.is_valid():
            shift = form.save()
            shift.assignees.add(request.user.id)
            shift.save()
            return redirect("orders:shift_admin", shift=shift)

        return render(request, self.template_name, {"venue": venue, "form": form})

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("venue")


class JoinShiftView(PermissionRequiredMixin, TemplateView):
    """Join shift view."""

    template_name = "orders/join_shift.html"

    permission_required = "orders.can_manage_shift_in_venue"
    return_403 = True
    accept_global_perms = True

    def get(self, request, **kwargs):
        """
        GET request for JoinShiftView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: the Join shift view page for asking the user whether or not to join the shift
        """
        shift = kwargs.get("shift")

        assignees = shift.assignees.all()

        if request.user not in assignees:
            return render(request, self.template_name, {"shift": shift})
        else:
            return redirect("orders:shift_admin", shift=shift)

    def post(self, request, **kwargs):
        """
        POST request for JoinShiftView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: the Join shift view page for asking the user whether or not to join the shift, if they agree this view
        will redirect to the shift admin page, otherwise it will redirect to the index page
        """
        shift = kwargs.get("shift")

        confirm = request.POST.get("confirm", None)
        if confirm == "Yes":
            services.add_user_to_assignees_of_shift(request.user, shift)
            return redirect("orders:shift_admin", shift=shift)
        elif confirm == "No":
            return redirect("index")
        else:
            return render(request, self.template_name, {"shift": shift})

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.get_object()
        return obj.venue

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("shift")


class ShiftAdminView(PermissionRequiredMixin, TemplateView):
    """Admin view for starting shifts."""

    template_name = "orders/shift_admin.html"

    permission_required = "orders.can_manage_shift_in_venue"
    return_403 = True
    accept_global_perms = True

    def get(self, request, **kwargs):
        """
        GET request for ShiftAdminView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: the Shift admin view page for seeing the current orders of a shift and modifying it
        """
        shift = kwargs.get("shift")

        return render(request, self.template_name, {"shift": shift})

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.get_object()
        return obj.venue

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("shift")


class OrderUpdateView(PermissionRequiredMixin, TemplateView):
    """Order update view."""

    permission_required = "orders.can_manage_shift_in_venue"
    return_403 = True
    accept_global_perms = True

    def post(self, request, **kwargs):
        """
        POST request for OrderUpdateView.

        Updates the status of an order
        :param request: the request
        :param kwargs: keyword arguments
        :return: a json response with an error or the value of the updated status
        """
        order_property = request.POST.get("property", None)
        value = request.POST.get("value", None)

        if order_property is None or value is None:
            return JsonResponse({"error": "Invalid request"})

        value = True if value == "true" else False

        order = kwargs.get("order")

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

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.get_object()
        return obj.shift.venue

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("order")


class OrderRemoveView(PermissionRequiredMixin, TemplateView):
    """Order remove view."""

    permission_required = "orders.can_manage_shift_in_venue"
    return_403 = True
    accept_global_perms = True

    def post(self, request, **kwargs):
        """
        POST request for OrderRemoveView.

        Remove an order
        :param request: the request
        :param kwargs: keyword arguments
        :return: a json response with an error or success message
        """
        order = kwargs.get("order")
        order.delete()
        return JsonResponse({"error": False})

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.get_object()
        return obj.shift.venue

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("order")


class ToggleShiftActivationView(PermissionRequiredMixin, TemplateView):
    """Toggle the shift activation via a POST request."""

    permission_required = "orders.can_manage_shift_in_venue"
    return_403 = True
    accept_global_perms = True

    def post(self, request, **kwargs):
        """
        POST request for ToggleShiftActivationView.

        Toggle the can_order variable of a shift to the value of the "active" parameter in the POST data
        :param request: the request
        :param kwargs: keyword arguments
        :return: a JsonResponse of the following format:
            active: [shift.can_order]
        """
        shift = kwargs.get("shift")
        active = request.POST.get("active", "false")

        try:
            shift = services.set_shift_active(shift, active == "true")
            return JsonResponse({"active": shift.can_order})
        except Exception as e:
            return JsonResponse({"error": str(e), "active": shift.can_order})

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.get_object()
        return obj.venue

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("shift")


class AddShiftCapacityView(PermissionRequiredMixin, TemplateView):
    """Add shift capacity view."""

    add_amount = 5

    permission_required = "orders.can_manage_shift_in_venue"
    return_403 = True
    accept_global_perms = True

    def post(self, request, **kwargs):
        """
        POST request for AddShiftCapacityView.

        Add to the capacity of a shift via a POST request
        :param request: the request
        :param kwargs: keyword arguments
        :return: a JsonResponse of the following format:
            error: False
        """
        shift = kwargs.get("shift")

        try:
            services.increase_shift_capacity(shift, self.add_amount)
            return JsonResponse({"error": False})
        except Exception as e:
            return JsonResponse({"error": str(e)})

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.get_object()
        return obj.venue

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("shift")


class AddShiftTimeView(PermissionRequiredMixin, TemplateView):
    """Add shift time view."""

    add_amount_minutes = 5

    permission_required = "orders.can_manage_shift_in_venue"
    return_403 = True
    accept_global_perms = True

    def post(self, request, **kwargs):
        """
        POST request for AddShiftTimeView.

        Add to the time of a shift via a POST request
        :param request: the request
        :param kwargs: keyword arguments
        :return: a JsonResponse of the following format:
            error: False
        """
        shift = kwargs.get("shift")
        try:
            services.increase_shift_time(shift, self.add_amount_minutes)
            return JsonResponse({"error": False})
        except Exception as e:
            return JsonResponse({"error": str(e)})

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.get_object()
        return obj.venue

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("shift")


class RefreshShiftHeaderView(TemplateView):
    """Refresh for the order header."""

    template_name = "orders/shift_header.html"

    def post(self, request, **kwargs):
        """
        POST request for refreshing the order header.

        :param request: the request
        :param kwargs: keyword arguments
        :return: The header in the following JSON format:
            data: [header]
        """
        shift = kwargs.get("shift")
        header = get_template(self.template_name).render(
            render_order_header({"request": request}, shift, refresh=True)
        )
        return JsonResponse({"data": header})


class RefreshShiftSummaryView(TemplateView):
    """Refresh for the shift summary."""

    template_name = "orders/shift_summary.html"

    def post(self, request, **kwargs):
        """
        POST request for refreshing the product summary on the shift admin page.

        :param request: the request
        :param kwargs: keyword arguments
        :return: The product overview in the following JSON format:
            data: [header]
        """
        shift = kwargs.get("shift")
        overview = get_template(self.template_name).render(
            render_order_header({"request": request}, shift, refresh=True)
        )
        return JsonResponse({"data": overview})


class RefreshAdminFooterView(PermissionRequiredMixin, TemplateView):
    """Refresh the administrator footer."""

    permission_required = "orders.can_manage_shift_in_venue"
    return_403 = True
    accept_global_perms = True

    def post(self, request, **kwargs):
        """
        POST request for refreshing the admin footer.

        :param request: the request
        :param kwargs: keyword arguments
        :return: The footer in the following JSON format:
            status: [shift.can_order]
        """
        shift = kwargs.get("shift")
        return JsonResponse({"status": shift.can_order})

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.get_object()
        return obj.venue

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("shift")


class RefreshShiftOrderView(PermissionRequiredMixin, TemplateView):
    """Refresh the orders view."""

    permission_required = "orders.can_order_in_venue"
    return_403 = True
    accept_global_perms = True

    template_name = "orders/shift_orders.html"

    def post(self, request, **kwargs):
        """
        POST request for refreshing the orders.

        :param request: the request
        :param kwargs: keyword arguments
        :return: The orders in the following JSON format:
            data: [orders]
        """
        shift = kwargs.get("shift")
        admin = request.POST.get("admin", "false") == "true"
        footer = get_template(self.template_name).render(
            render_order_items({"request": request}, shift, refresh=True, admin=admin, user=request.user)
        )
        return JsonResponse({"data": footer})

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.get_object()
        return obj.venue

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("shift")


class ShiftScannerView(PermissionRequiredMixin, TemplateView):
    """Scanner view for the shift admin."""

    permission_required = "orders.can_manage_shift_in_venue"
    return_403 = True
    accept_global_perms = True

    def post(self, request, **kwargs):
        """
        POST request for the shift scanner view.

        Checks if a barcode exists in the database and adds it if it does.
        :param request: the request
        :param kwargs: keyword arguments
        :return: a JsonResponse with the response message
        """
        shift = self.kwargs.get("shift")
        barcode = request.POST.get("barcode", None)
        if barcode:
            try:
                product = Product.objects.get(barcode=barcode, available=True, available_at=shift.venue)
                Order.objects.create(shift=shift, product=product, type=Order.TYPE_SCANNED, paid=True, ready=True)
                return JsonResponse({"error": False, "product": product.to_json()})
            except Product.DoesNotExist:
                return JsonResponse({"error": True, "errormsg": "The product was not found."})
        else:
            return JsonResponse({"error": True, "errormsg": "No barcode defined."})

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.get_object()
        return obj.venue

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("shift")


class ProductSearchView(PermissionRequiredMixin, TemplateView):
    """Search view."""

    permission_required = "orders.can_manage_shift_in_venue"
    return_403 = True
    accept_global_perms = True

    def post(self, request, **kwargs):
        """
        POST request for the shift search view.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a JsonResponse with the response message
        """
        shift = self.kwargs.get("shift")
        query = request.POST.get("query", None)
        if query:
            string_query = services.query_product_name(query)
            barcode_query = services.query_product_barcode(query)
            all_query = set(string_query)
            all_query.update(barcode_query)
            product_list = get_template("orders/search_results.html").render({"products": all_query, "shift": shift})
            return JsonResponse({"error": False, "data": product_list})
        else:
            return JsonResponse({"error": True, "errormsg": "No query defined."})

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.get_object()
        return obj.venue

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("shift")


class ProductAddView(PermissionRequiredMixin, TemplateView):
    """Add product view."""

    permission_required = "orders.can_manage_shift_in_venue"
    return_403 = True
    accept_global_perms = True

    def post(self, request, **kwargs):
        """
        POST request for the add product view.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a JsonResponse with the response message
        """
        shift = self.kwargs.get("shift")
        product_id = request.POST.get("product", None)
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return JsonResponse({"error": True, "errormsg": "That product does not exist."})
            try:
                services.add_order(product, shift, Order.TYPE_SCANNED, paid=True, ready=True)
            except OrderException as e:
                return JsonResponse({"error": True, "errormsg": str(e)})
            return JsonResponse({"error": False, "successmsg": "{} added to the shift.".format(product.name)})
        else:
            return JsonResponse({"error": True, "errormsg": "No product defined."})

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.get_object()
        return obj.venue

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("shift")


class ExplainerView(TemplateView):
    """Explainer view."""

    template_name = "orders/explainer.html"


class AdminExplainerView(TemplateView):
    """Admin Explainer view."""

    template_name = "orders/explainer_admin.html"
