import json

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from .models import Shift, Product, Order
from .forms import ShiftForm
import urllib.parse


class ShiftView(LoginRequiredMixin, TemplateView):
    """View for displaying all active shifts."""

    template_name = "orders/shifts.html"

    def get(self, request, **kwargs):
        """
        GET request for Shift view.

        :param request: the request
        :param kwargs: keyword arguments
        :return: the shift view with all active shifts
        """
        active_shifts = [x for x in Shift.objects.all() if x.is_active]

        return render(request, self.template_name, {"shifts": active_shifts})


class OrderView(LoginRequiredMixin, TemplateView):
    """View for displaying items that can be ordered and already ordered items."""

    template_name = "orders/order.html"

    @staticmethod
    def can_order(shift, product_id, user):
        """
        Add an order for a specific product id, shift and user.

        :param shift: the shift to add the order to
        :param product_id: the product id of the product that the order must have
        :param user: the user that ordered the product
        :return: a string with an error message if the order could not be placed, True otherwise
        """
        try:
            product = Product.objects.get(pk=product_id)
        except (Product.DoesNotExist, ValueError):
            return "That product does not exist"

        if not shift.user_can_order_amount(user):
            return "You can not order more products"
        if not product.user_can_order_amount(user, shift):
            return "You can not order more {}".format(product.name)
        if not shift.can_order:
            return "You can not order products for this shift"
        if not product.available:
            return "Product {} is not available".format(product.name)
        return True

    @staticmethod
    def add_orders(order_list, shift, user):
        """
        Add all orders in a list.

        :param order_list: a list of product ids
        :param shift: the shift to add the orders to
        :param user: the user for which the orders are
        :return: True if the addition succeeded, a string with an error message otherwise
        """
        if not shift.user_can_order_amount(user, amount=len(order_list)):
            return "You can't order that much products in this shift"
        for order in order_list:
            error_msg = OrderView.can_order(shift, order, user)
            if isinstance(error_msg, str):
                return error_msg

        for order in order_list:
            Order.objects.create(
                user=user, shift=shift, product=Product.objects.get(pk=order)
            )

        return True

    def get(self, request, **kwargs):
        """
        GET request for OrderView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: the product view with all ordered items of the user and all items that the user can order for this
        shift
        """
        shift = kwargs.get("shift")

        return render(
            request,
            self.template_name,
            {
                "shift": shift,
                "already_ordered": Order.objects.filter(
                    user=request.user, shift=shift
                ).count()
                > 0,
            },
        )

    def post(self, request, **kwargs):
        """
        POST request for OrderView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: creates new orders that are specified in a cart_[shift_number] cookie or returns an error message
        """
        shift = kwargs.get("shift")
        cookie = request.COOKIES.get("cart_{}".format(shift.pk), None)
        if cookie is None:
            return render(
                request,
                self.template_name,
                {"shift": shift, "error": "No orders submitted"},
            )
        cookie = urllib.parse.unquote(cookie)
        try:
            cookie = json.loads(cookie)
        except json.JSONDecodeError:
            page = render(
                request,
                self.template_name,
                {"shift": shift, "error": "Error decoding cookie"},
            )
            page.delete_cookie("cart_{}".format(shift.pk))
            return page

        error_msg = self.add_orders(cookie, shift, request.user)
        if isinstance(error_msg, str):
            return render(
                request, self.template_name, {"shift": shift, "error": error_msg}
            )
        else:
            response = redirect("orders:shift_overview", shift=shift)
            response.delete_cookie("cart_{}".format(shift.pk))
            return response


class OrderStatusView(LoginRequiredMixin, TemplateView):
    """Order status view."""

    template_name = "orders/order_status.html"

    @staticmethod
    def get_ordered_items(shift, user):
        """
        Get all ordered items of a user in JSON format.

        :param shift: the shift
        :param user: the user
        :return: a list of ordered items in JSON format
        """
        ordered_items = Order.objects.filter(user=user, shift=shift)
        json_list = list()
        for item in ordered_items:
            json_list.append(item.to_json())
        return json_list

    def get(self, request, **kwargs):
        """
        GET request for OrderStatusView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the order_status page
        """
        shift = kwargs.get("shift")

        return render(request, self.template_name, {"shift": shift})

    def post(self, request, **kwargs):
        """
        POST for OrderStatusView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a JsonResponse with all ordered items in a list
        """
        shift = kwargs.get("shift")

        ordered_items = OrderStatusView.get_ordered_items(shift, request.user)

        return JsonResponse({"ordered_items": ordered_items})


class ProductListView(LoginRequiredMixin, TemplateView):
    """Product list view for getting all available products per shift."""

    @staticmethod
    def get_available_products(shift, user):
        """
        Get available products for a shift and a user in json format.

        :param shift: the shift
        :param user: the user
        :return: a json list of the products converted to json and an extra dictionary key (max_allowed) indicating
        how many more of the item a user can still order
        """
        items = Product.objects.filter(available=True, available_at=shift.venue)
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
        :return: a JSON response including the following:
        {
            products: [list of products],
            shift_max: [maximum items for this shift]
        }
        """
        shift = kwargs.get("shift")
        option = request.POST.get("option", None)

        if option == "list":
            pass
        else:
            return JsonResponse({"error": "Operation unknown"})

        products = self.get_available_products(shift, request.user)
        return JsonResponse(
            {
                "products": products,
                "shift_max": shift.user_max_order_amount(request.user),
            }
        )


class CreateShiftView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Page for starting a shift."""

    permission_required = "is_staff"

    template_name = "orders/create_shift.html"

    def get(self, request, **kwargs):
        """
        GET request for ShiftStartView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a page with all current shifts and a form for starting a new shift
        """
        venue = kwargs.get("venue")

        form = ShiftForm(venue=venue)

        return render(request, self.template_name, {"venue": venue, "form": form})

    def post(self, request, **kwargs):
        """
        POST request for ShiftStartView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a page with all current shifts and a form for starting a new shift, if the form was filled in
        correctly a new shift is started.
        """
        venue = kwargs.get("venue")

        form = ShiftForm(request.POST)

        if form.is_valid():
            shift = form.save()
            return redirect("orders:shift_admin", shift=shift)

        return render(request, self.template_name, {"venue": venue, "form": form})


class ShiftAdminView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Admin view for starting shifts."""

    template_name = "orders/shift_admin.html"

    permission_required = "is_staff"

    def get(self, request, **kwargs):
        """
        GET request for ShiftAdminView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: the Shift admin view page for seeing the current orders of a shift and modifying it
        """
        shift = kwargs.get("shift")

        return render(request, self.template_name, {"shift": shift})


class ShiftStatusView(TemplateView):
    """View for getting the orders of a shift."""

    def post(self, request, **kwargs):
        """
        POST request for ShiftStatusView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a response of the following format:
        {
            data: [orders]
        }
        """
        shift = kwargs.get("shift")

        orders = Order.objects.filter(shift=shift).order_by("user", "created")
        json_data = []
        for order in orders:
            json_order = order.to_json()
            if order.user == request.user:
                json_order["own"] = True
            else:
                json_order["own"] = False
            json_data.append(json_order)
        return JsonResponse({"data": json_data})


class OrderUpdateView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """View for updating orders via asynchronous POST requests."""

    permission_required = "is_staff"

    def post(self, request, **kwargs):
        """
        POST method for OrderUpdateView.

        This view expects JSON of the following type:
        {
            order: [order_id],
            property: [delivered | paid],
            value: [true | false]
        }
        :param request: the request
        :param kwargs: the keyword arguments
        :return: A response of the following format on success:
        {
            value: [true | false]
        }
        A response of the following format on failure:
        {
            error: [error message]
        }
        """
        order_id = request.POST.get("order", None)
        order_property = request.POST.get("property", None)
        value = request.POST.get("value", None)

        if order_id is None or order_property is None or value is None:
            return JsonResponse({"error": "Invalid request"})

        value = True if value == "true" else False

        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return JsonResponse({"error": "That order does not exist"})

        if order_property == "delivered":
            order.delivered = value
            order.save()
            return JsonResponse({"value": order.delivered})
        elif order_property == "paid":
            order.paid = value
            order.save()
            return JsonResponse({"value": order.paid})
        else:
            return JsonResponse({"error": "Property unknown"})


class ShiftOverview(TemplateView, LoginRequiredMixin):
    """Shift overview page."""

    template_name = "orders/shift_overview.html"

    def get(self, request, **kwargs):
        """
        GET request of shift overview page.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the shift overview page
        """
        shift = kwargs.get("shift")

        return render(request, self.template_name, {"shift": shift})
