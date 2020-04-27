from django.shortcuts import render
from django.views.generic import TemplateView
from .models import Shift, Product, Order
from .forms import OrderForm


class ShiftView(TemplateView):

    template_name = "orders/shifts.html"

    def get(self, request, **kwargs):

        active_shifts = [x for x in Shift.objects.all() if x.is_active]

        return render(request, self.template_name, {"shifts": active_shifts})


class OrderView(TemplateView):

    template_name = "orders/order.html"

    def get(self, request, **kwargs):

        shift = kwargs.get('shift')

        items = Product.objects.filter(available=True, available_at=shift.venue)
        for item in items:
            item.form = OrderForm(product=item)

        return render(request, self.template_name, {"shift": shift, "items": items})

    def post(self, request, **kwargs):
        shift = kwargs.get('shift')
        items = Product.objects.filter(available=True, available_at=shift.venue)

        product_id = request.POST.get('product_id', None)

        if product_id is not None:
            try:
                product = Product.objects.get(pk=product_id)
            except Product.DoesNotExist:
                return render(request, self.template_name, {"shift": shift, "items": items, "error": "That product does not exist"})

            ordered_item_amount = Order.objects.filter(user=request.user, shift=shift)

        return render(request, self.template_name, {"shift": shift, "items": items})
