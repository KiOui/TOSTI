import json

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin

from orders import services
from orders.exceptions import OrderException
from .permissions import StaffRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.generic import TemplateView
from .models import Shift, Product
from .forms import ShiftForm
import urllib.parse

from .templatetags.order_now import (
    render_order_header,
    render_order_items,
)

User = get_user_model()


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
                product_list.append(Product.objects.get(pk=product_id))
            except (Product.DoesNotExist, ValueError):
                return "That product does not exist"
        try:
            services.place_orders(product_list, user, shift)
        except OrderException as err:
            return str(err)

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
                "already_ordered": services.has_already_ordered_in_shift(request.user, shift)
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


class JoinShiftView(StaffRequiredMixin, TemplateView):
    """Admin view for joining shifts."""

    template_name = "orders/join_shift.html"

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


class CreateShiftView(StaffRequiredMixin, TemplateView):
    """Page for starting a shift."""

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
        form.set_initial_users(User.objects.filter(pk=request.user.pk))

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


class ShiftAdminView(StaffRequiredMixin, TemplateView):
    """Admin view for starting shifts."""

    template_name = "orders/shift_admin.html"

    def get(self, request, **kwargs):
        """
        GET request for ShiftAdminView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: the Shift admin view page for seeing the current orders of a shift and modifying it
        """
        shift = kwargs.get("shift")

        return render(request, self.template_name, {"shift": shift})


class OrderUpdateView(StaffRequiredMixin, TemplateView):
    """View for updating orders via asynchronous POST requests."""

    def post(self, request, **kwargs):
        """
        POST method for OrderUpdateView.

        This view expects JSON of the following type:
        {
            order: [order_id],
            property: [ready | paid],
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


class ToggleShiftActivationView(StaffRequiredMixin, TemplateView):
    """Toggle the shift activation via a POST request."""

    def post(self, request, **kwargs):
        """
        POST request for ToggleShiftActivationView.

        Toggle the can_order variable of a shift to the value of the "active" parameter in the POST data
        :param request: the request
        :param kwargs: keyword arguments
        :return: a JsonResponse of the following format:
        {
            active: [shift.can_order]
        }
        """
        shift = kwargs.get("shift")
        active = request.POST.get("active", "false")

        try:
            shift = services.set_shift_active(shift, active == "true")
            return JsonResponse({"active": shift.can_order})
        except Exception as e:
            return JsonResponse({"error": str(e), "active": shift.can_order})


class AddShiftCapacityView(StaffRequiredMixin, TemplateView):
    """Add shift capacity view."""

    add_amount = 5

    def post(self, request, **kwargs):
        """
        POST request for AddShiftCapacityView.

        Add to the capacity of a shift via a POST request
        :param request: the request
        :param kwargs: keyword arguments
        :return: a JsonResponse of the following format:
        {
            error: False
        }
        """
        shift = kwargs.get("shift")
        try:
            services.increase_shift_capacity(shift, self.add_amount)
            return JsonResponse({"error": False})
        except Exception as e:
            return JsonResponse({"error": str(e)})


class AddShiftTimeView(StaffRequiredMixin, TemplateView):
    """Add shift time view."""

    add_amount_minutes = 5

    def post(self, request, **kwargs):
        """
        POST request for AddShiftTimeView.

        Add to the time of a shift via a POST request
        :param request: the request
        :param kwargs: keyword arguments
        :return: a JsonResponse of the following format:
        {
            error: False
        }
        """
        shift = kwargs.get("shift")

        try:
            services.increase_shift_time(shift, self.add_amount_minutes)
            return JsonResponse({"error": False})
        except Exception as e:
            return JsonResponse({"error": str(e)})


class RefreshHeaderView(TemplateView):
    """Refresh for the order header."""

    def post(self, request, **kwargs):
        """
        POST request for refreshing the order header.

        :param request: the request
        :param kwargs: keyword arguments
        :return: The header in the following JSON format:
        {
            data: [header]
        }
        """
        shift = kwargs.get("shift")
        header = get_template("orders/order_header.html").render(
            render_order_header(shift, refresh=True)
        )
        return JsonResponse({"data": header})


class RefreshProductOverviewView(TemplateView):
    """Refresh for the order header."""

    def post(self, request, **kwargs):
        """
        POST request for refreshing the product overview on the admin page.

        :param request: the request
        :param kwargs: keyword arguments
        :return: The product overview in the following JSON format:
        {
            data: [header]
        }
        """
        shift = kwargs.get("shift")
        overview = get_template("orders/item_overview.html").render(
            render_order_header(shift, refresh=True)
        )
        return JsonResponse({"data": overview})


class RefreshAdminFooterView(StaffRequiredMixin, TemplateView):
    """Refresh the administrator footer."""

    def post(self, request, **kwargs):
        """
        POST request for refreshing the admin footer.

        :param request: the request
        :param kwargs: keyword arguments
        :return: The footer in the following JSON format:
        {
            status: [shift.can_order]
        }
        """
        shift = kwargs.get("shift")
        return JsonResponse({"status": shift.can_order})


class RefreshShiftOrderView(TemplateView):
    """Refresh the orders view."""

    permission_required = "is_staff"

    def post(self, request, **kwargs):
        """
        POST request for refreshing the orders.

        :param request: the request
        :param kwargs: keyword arguments
        :return: The orders in the following JSON format:
        {
            data: [orders]
        }
        """
        shift = kwargs.get("shift")
        admin = request.POST.get("admin", "false") == "true"
        footer = get_template("orders/order_items.html").render(
            render_order_items(shift, refresh=True, admin=admin, user=request.user)
        )
        return JsonResponse({"data": footer})
