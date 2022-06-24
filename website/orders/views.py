from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.views.generic import TemplateView
from guardian.mixins import PermissionRequiredMixin

from orders import services
from django.shortcuts import render, redirect
from .models import Order
from .forms import CreateShiftForm
from .services import user_is_blacklisted


class ShiftOverviewView(TemplateView):
    """Shift overview page."""

    template_name = "orders/shift_overview.html"

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
                "has_order_permissions": not user_is_blacklisted(request.user),
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


class ExplainerView(TemplateView):
    """Explainer view."""

    template_name = "orders/explainer.html"


class AdminExplainerView(TemplateView):
    """Admin Explainer view."""

    template_name = "orders/explainer_admin.html"


def render_ordered_items_tab(request, item, current_page_url):
    """Render the ordered items tab on the user page."""
    ordered_items = Order.objects.filter(user=request.user).order_by("-created")
    page = request.GET.get("page", 1) if (item["slug"] == request.GET.get("active", False)) else 1
    paginator = Paginator(ordered_items, per_page=50)
    return render_to_string(
        "orders/account_history.html",
        context={"page_obj": paginator.get_page(page), "current_page_url": current_page_url, "item": item},
    )
