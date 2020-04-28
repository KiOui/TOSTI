from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from .models import Shift, Product, Order
from .forms import ProductForm, OrderRemoveForm, ShiftForm


class ShiftView(TemplateView):
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


class OrderView(TemplateView):
    """View for displaying items that can be ordered and already ordered items."""

    template_name = "orders/order.html"

    @staticmethod
    def add_order(shift, product_id, user):
        """
        Add an order for a specific product id, shift and user.

        :param shift: the shift to add the order to
        :param product_id: the product id of the product that the order must have
        :param user: the user that ordered the product
        :return: a string with an error message if the order could not be placed, True otherwise
        """
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return "That product does not exist"

        if not shift.user_can_order_amount(user):
            return "You can not order more products"
        if not product.user_can_order_amount(user, shift):
            return "You can not order more {}".format(product.name)
        if not shift.can_order:
            return "You can not order products for this shift"
        if not product.available:
            return "This product is not available"
        Order.objects.create(user=user, shift=shift, product=product)
        return True

    @staticmethod
    def delete_order(shift, order_id, user):
        """
        Delete an order for a specific product id, shift and user.

        :param shift: the shift of the order
        :param order_id: the id of the order to delete
        :param user: the user that ordered the order
        :return: a string with an error message if the order could not be deleted, True otherwise
        """
        try:
            order = Order.objects.get(pk=order_id, user=user, shift=shift)
        except Order.DoesNotExist:
            return "That order does not exist"
        if not shift.can_order:
            return "You can't delete orders for this shift"
        order.delete()
        return True

    @staticmethod
    def get_orders_with_forms(user, shift):
        """
        Get a QuerySet of the orders with the .form parameter set to an OrderRemoveForm.

        :param user: the user to get the orders for
        :param shift: the shift to get the orders for
        :return: a QuerySet of orders with an extra variable per order .form that contains an OrderRemoveForm for that
        order
        """
        ordered_items = Order.objects.filter(user=user, shift=shift)
        for order in ordered_items:
            order.form = OrderRemoveForm(order=order)
        return ordered_items

    @staticmethod
    def get_products_with_forms(shift):
        """
        Get a QuerySet of products with the .form parameter set to a ProductForm.

        :param shift: the shift to get the products for
        :return: a QuerySet of products with an extra variable per product .form that contains a ProductForm for that
        product
        """
        items = Product.objects.filter(available=True, available_at=shift.venue)
        for item in items:
            item.form = ProductForm(product=item)
        return items

    def get(self, request, **kwargs):
        """
        GET request for Order view.

        :param request: the request
        :param kwargs: keyword arguments
        :return: the product view with all ordered items of the user and all items that the user can order for this
        shift
        """
        shift = kwargs.get("shift")
        ordered_items = self.get_orders_with_forms(request.user, shift)
        items = self.get_products_with_forms(shift)

        parameters = {"shift": shift, "items": items, "ordered_items": ordered_items}

        return render(request, self.template_name, parameters)

    def post(self, request, **kwargs):
        """
        POST request for Order view.

        :param request: the request
        :param kwargs: keyword arguments
        :return: the product view with all ordered items of the user, all items that the user can order for this shift
        and an error message if an error occurred while processing a form request for the user
        """
        shift = kwargs.get("shift")
        ordered_items = self.get_orders_with_forms(request.user, shift)
        items = self.get_products_with_forms(shift)

        parameters = {"shift": shift, "items": items, "ordered_items": ordered_items}

        product_id = request.POST.get("product_id", None)
        order_id = request.POST.get("order_id", None)

        if product_id is not None:
            error = self.add_order(shift, product_id, request.user)
            if isinstance(error, str):
                parameters["error"] = error
            else:
                parameters["ordered_items"] = self.get_orders_with_forms(
                    request.user, shift
                )
        elif order_id is not None:
            error = self.delete_order(shift, order_id, request.user)
            if isinstance(error, str):
                parameters["error"] = error
            else:
                parameters["ordered_items"] = self.get_orders_with_forms(
                    request.user, shift
                )

        return render(request, self.template_name, parameters)


class ShiftStartView(TemplateView):

    template_name = "orders/startshift.html"

    def get(self, request, **kwargs):
        active_shifts = [x for x in Shift.objects.all() if x.is_active]

        form = ShiftForm()

        return render(request, self.template_name, {'shifts': active_shifts, 'form': form})

    def post(self, request, **kwargs):
        active_shifts = [x for x in Shift.objects.all() if x.is_active]

        form = ShiftForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('index')

        return render(request, self.template_name, {'shifts': active_shifts, 'form': form})


class ShiftAdminView(TemplateView):

    template_name = "orders/shift_admin.html"

    def get(self, request, **kwargs):
        shift = kwargs.get('shift')

        form = ShiftForm(instance=shift)

        return render(request, self.template_name, {'shift': shift, 'form': form})


class ShiftStatusView(TemplateView):

    def post(self, request, **kwargs):
        shift = kwargs.get('shift')

        orders = Order.objects.filter(shift=shift).order_by('user', 'created')
        json_data = []
        for order in orders:
            json_data.append(order.to_json())
        return JsonResponse({'data': json_data})


class OrderUpdateView(TemplateView):

    def post(self, request, **kwargs):
        order_id = request.POST.get('order', None)
        property = request.POST.get('property', None)
        value = request.POST.get('value', None)

        if order_id is None or property is None or value is None:
            return JsonResponse({"error": "Invalid request"})

        value = True if value == "true" else False

        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return JsonResponse({'error': "That order does not exist"})

        if property == "delivered":
            order.delivered = value
            order.save()
            return JsonResponse({})
        elif property == "paid":
            order.paid = value
            order.save()
            return JsonResponse({})
        else:
            return JsonResponse({"error": "Property unknown"})
