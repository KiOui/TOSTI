from django.shortcuts import render
from django.views.generic import TemplateView
from .models import Shift


class ShiftView(TemplateView):

    template_name = "orders/shifts.html"

    def get(self, request, **kwargs):

        active_shifts = [x for x in Shift.objects.all() if x.is_active]

        return render(request, self.template_name, {"shifts": active_shifts})


class OrderView(TemplateView):

    template_name = "orders/order.html"

    def get(self, request, **kwargs):

        shift = kwargs.get('shift')

        return render(request, self.template_name, {"shift": shift})
