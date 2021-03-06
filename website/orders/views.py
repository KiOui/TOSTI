import json

from django.views.generic import TemplateView
from guardian.mixins import PermissionRequiredMixin

from orders import services
from orders.exceptions import OrderException
from django.shortcuts import render, redirect
from .models import Product
from .forms import CreateShiftForm
import urllib.parse


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
            {
                "shift": shift,
                "can_manage_shift": request.user in shift.venue.get_users_with_shift_admin_perms(),
                "has_order_permissions": request.user in shift.venue.get_users_with_order_perms(),
            },
        )

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
        if request.user not in shift.get_assignees():
            return redirect("orders:shift_join", shift=shift)

        return render(
            request,
            self.template_name,
            {"shift": shift, "has_change_order_permissions": request.user in shift.get_users_with_change_perms()},
        )

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


class ExplainerView(TemplateView):
    """Explainer view."""

    template_name = "orders/explainer.html"


class AdminExplainerView(TemplateView):
    """Admin Explainer view."""

    template_name = "orders/explainer_admin.html"
