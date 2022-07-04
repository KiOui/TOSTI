from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import TemplateView, CreateView
from guardian.mixins import PermissionRequiredMixin
from guardian.shortcuts import get_objects_for_user

from orders import services
from django.shortcuts import render, redirect

from .models import Order, Shift
from .forms import CreateShiftForm
from .services import user_is_blacklisted


class ShiftOverviewView(LoginRequiredMixin, TemplateView):
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

        return render(
            request,
            self.template_name,
            {
                "shift": shift,
                "can_manage_shift": request.user in shift.venue.get_users_with_shift_admin_perms(),
                "has_order_permissions": request.user.is_authenticated and not user_is_blacklisted(request.user),
            },
        )

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.get_object()
        return obj.venue

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("shift")


class CreateShiftView(PermissionRequiredMixin, CreateView):
    """Create shift view."""

    template_name = "orders/create_shift.html"

    permission_required = "orders.can_manage_shift_in_venue"
    return_403 = True
    accept_global_perms = True
    form_class = CreateShiftForm
    model = Shift

    def get_success_url(self):
        """Get the success URL."""
        return reverse("orders:shift_admin", kwargs={"shift": self.object})

    def form_valid(self, form):
        """Form valid."""
        response = super(CreateShiftView, self).form_valid(form)
        self.object.assignees.add(self.request.user.id)
        self.object.save()
        return response

    def get_form_kwargs(self):
        """Get form kwargs."""
        kwargs = super(CreateShiftView, self).get_form_kwargs()
        extra_kwargs = {
            "venue": self.kwargs.get("venue"),
            "user": self.request.user,
        }
        return {**kwargs, **extra_kwargs}

    def get_context_data(self, **kwargs):
        """Get context data."""
        kwargs = super(CreateShiftView, self).get_context_data(**kwargs)
        extra_kwargs = {
            "venue": kwargs.get("venue"),
        }
        return {**kwargs, **extra_kwargs}

    def get_object(self, queryset=None):
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
        if request.user not in shift.assignees.all():
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


def render_ordered_items_tab(request, item, current_page_url):
    """Render the ordered items tab on the user page."""
    ordered_items = Order.objects.filter(user=request.user).order_by("-created")
    page = request.GET.get("page", 1) if (item["slug"] == request.GET.get("active", False)) else 1
    paginator = Paginator(ordered_items, per_page=50)
    return render_to_string(
        "orders/account_history.html",
        context={"page_obj": paginator.get_page(page), "current_page_url": current_page_url, "item": item},
    )


def explainer_page_how_to_order_tab(request, item):
    """Render the explainer how to order tab."""
    return render_to_string("orders/explainer.html", context={"request": request, "item": item})


def explainer_page_how_to_manage_shift_tab(request, item):
    """Render the explainer how to manage shift tab."""
    if (
        request.user.is_authenticated
        and get_objects_for_user(request.user, "orders.can_manage_shift_in_venue").exists()
    ):
        return render_to_string("orders/explainer_admin.html", context={"request": request, "item": item})
    else:
        return None
