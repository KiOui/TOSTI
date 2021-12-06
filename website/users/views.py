from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView

from tosti.filter import Filter
from .forms import AccountForm


class AccountView(LoginRequiredMixin, TemplateView):
    """Account view."""

    template_name = "users/account.html"

    user_data_tabs = Filter()

    def get(self, request, **kwargs):
        """
        GET request for the account view.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the account view
        """
        form = AccountForm(
            initial={
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "username": request.user.username,
                "email": request.user.email,
                "association": request.user.profile.association,
            }
        )
        active = request.GET.get("active", "users")
        tabs = self.user_data_tabs.do_filter([])
        rendered_tab = None
        for tab in tabs:
            if active == tab["slug"]:
                rendered_tab = tab["renderer"](request, tab, reverse("users:account"))
        return render(
            request, self.template_name, {"form": form, "active": active, "tabs": tabs, "rendered_tab": rendered_tab}
        )

    def post(self, request, **kwargs):
        """
        POST request for the account view.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the account view
        """
        form = AccountForm(request.POST)
        tabs = self.user_data_tabs.do_filter([])
        if form.is_valid():
            request.user.profile.association = form.cleaned_data.get("association")
            request.user.profile.save()
        return render(
            request, self.template_name, {"form": form, "active": "users", "tabs": tabs, "rendered_tab": None}
        )
