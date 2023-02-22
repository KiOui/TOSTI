import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import TemplateView, RedirectView

from tosti.filter import Filter
from tosti.services import (
    generate_order_statistics,
    generate_orders_per_venue_statistics,
    generate_most_requested_songs,
    generate_users_with_most_song_requests,
    generate_users_per_association,
    generate_product_category_ordered_per_association,
)
from borrel.models import ProductCategory as BorrelProductCategory
from constance import config


class IndexView(TemplateView):
    """Index view."""

    template_name = "tosti/index.html"

    def get(self, request, **kwargs):
        """
        GET request for IndexView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the index page
        """
        return render(request, self.template_name)


class PrivacyView(TemplateView):
    """Privacy policy view."""

    template_name = "tosti/privacy.html"


class AfterLoginRedirectView(RedirectView):
    """Redirect users to the welcome page after first login."""

    def get_redirect_url(self, *args, **kwargs):
        """Get the url to redirect to."""
        next_url = self.request.GET.get("next")
        if self.request.user.is_authenticated and not self.request.user.association:
            messages.add_message(
                self.request, messages.INFO, "Welcome to TOSTI! Please complete your account profile below."
            )
            return reverse("users:account")
        if next_url:
            return next_url
        return reverse("index")


class DocumentationView(TemplateView):
    """Documentation page."""

    template_name = "tosti/documentation.html"


class ExplainerView(TemplateView):
    """Explainer page."""

    template_name = "tosti/explainers.html"
    explainer_tabs = Filter()

    def get(self, request, **kwargs):
        """GET request."""
        tabs = self.explainer_tabs.do_filter([])
        rendered_tabs = []
        for tab in tabs:
            tab_rendered = tab["renderer"](request, tab)
            if tab_rendered is not None:
                rendered_tabs.append({"name": tab["name"], "slug": tab["slug"], "content": tab_rendered})
        return render(request, self.template_name, {"rendered_tabs": rendered_tabs})


class StatisticsView(LoginRequiredMixin, TemplateView):
    """Statistics View."""

    template_name = "tosti/statistics.html"

    def get(self, request, **kwargs):
        """GET Statistics View."""
        ordered_items_distribution = json.dumps(generate_order_statistics())
        orders_per_venue = json.dumps(generate_orders_per_venue_statistics())
        most_requested_songs = json.dumps(generate_most_requested_songs())
        users_with_most_requests = json.dumps(generate_users_with_most_song_requests())
        users_per_association = json.dumps(generate_users_per_association())
        try:
            borrel_product_category = BorrelProductCategory.objects.get(id=config.STATISTICS_BORREL_CATEGORY)
            borrel_product_category_ordered_per_association = json.dumps(
                generate_product_category_ordered_per_association(borrel_product_category)
            )
        except BorrelProductCategory.DoesNotExist:
            borrel_product_category_ordered_per_association = None
            borrel_product_category = None

        return render(
            request,
            self.template_name,
            {
                "ordered_items_distribution": ordered_items_distribution,
                "orders_per_venue": orders_per_venue,
                "most_requested_songs": most_requested_songs,
                "users_with_most_requests": users_with_most_requests,
                "users_per_association": users_per_association,
                "borrel_product_category_ordered_per_association": borrel_product_category_ordered_per_association,
                "borrel_product_category": borrel_product_category,
            },
        )


def handler403(request, exception):
    """
    Handle a 403 (permission denied) exception.

    :param request: the request
    :param exception: the exception
    :return: a render of the 403 page
    """
    if request.user.is_authenticated:
        return render(request, "tosti/403.html", status=403)
    else:
        return redirect("login")


def handler404(request, exception):
    """
    Handle a 404 (page not found) exception.

    :param request: the request
    :param exception: the exception
    :return: a render of the 404 page
    """
    return render(request, "tosti/404.html", status=404)


def handler500(request, *args, **kwargs):
    """
    Handle a 50x (server fault) exception.

    :param request: the request
    :return: a render of the 500 page
    """
    return render(request, "tosti/500.html", status=500)
