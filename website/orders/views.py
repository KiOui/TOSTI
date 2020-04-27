from django.shortcuts import render
from django.views.generic import TemplateView
from .models import Shift, Product, Order
from .forms import ProductForm, OrderRemoveForm


class ShiftView(TemplateView):

    template_name = "orders/shifts.html"

    def get(self, request, **kwargs):

        active_shifts = [x for x in Shift.objects.all() if x.is_active]

        return render(request, self.template_name, {"shifts": active_shifts})


class OrderView(TemplateView):

    template_name = "orders/order.html"

    @staticmethod
    def add_order(shift, product_id, user):
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
        try:
            order = Order.objects.get(pk=order_id, user=user, shift=shift)
        except Order.DoesNotExist:
            return "That order does not exist"
        order.delete()
        return True

    @staticmethod
    def get_orders_with_forms(user, shift):
        ordered_items = Order.objects.filter(user=user, shift=shift)
        for order in ordered_items:
            order.form = OrderRemoveForm(order=order)
        return ordered_items

    @staticmethod
    def get_products_with_forms(shift):
        items = Product.objects.filter(available=True, available_at=shift.venue)
        for item in items:
            item.form = ProductForm(product=item)
        return items

    def get(self, request, **kwargs):
        shift = kwargs.get('shift')
        ordered_items = self.get_orders_with_forms(request.user, shift)
        items = self.get_products_with_forms(shift)

        parameters = {
            "shift": shift,
            "items": items,
            "ordered_items": ordered_items
        }

        return render(request, self.template_name, parameters)

    def post(self, request, **kwargs):
        shift = kwargs.get('shift')
        ordered_items = self.get_orders_with_forms(request.user, shift)
        items = self.get_products_with_forms(shift)

        parameters = {
            "shift": shift,
            "items": items,
            "ordered_items": ordered_items
        }

        product_id = request.POST.get('product_id', None)
        order_id = request.POST.get('order_id', None)

        if product_id is not None:
            error = self.add_order(shift, product_id, request.user)
            if isinstance(error, str):
                parameters['error'] = error
            else:
                parameters['ordered_items'] = self.get_orders_with_forms(request.user, shift)
        elif order_id is not None:
            error = self.delete_order(shift, order_id, request.user)
            if isinstance(error, str):
                parameters['error'] = error
            else:
                parameters['ordered_items'] = self.get_orders_with_forms(request.user, shift)

        return render(request, self.template_name, parameters)
