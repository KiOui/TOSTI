import json

from django.apps import apps
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import TemplateView, RedirectView
from oauth2_provider.generators import generate_client_secret
from oauth2_provider.models import Application

from tosti.forms import OAuthCredentialsForm


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

    def get(self, request, **kwargs):
        """GET request."""
        explainer_tabs = []
        for app in apps.get_app_configs():
            if hasattr(app, "explainer_tabs"):
                app_explainer_tabs = app.explainer_tabs(request)
                explainer_tabs += app_explainer_tabs

        explainer_tabs = sorted(explainer_tabs, key=lambda tab: tab["order"])

        rendered_tabs = []
        for tab in explainer_tabs:
            tab_rendered = tab["renderer"](request, tab)
            if tab_rendered is not None:
                rendered_tabs.append({"name": tab["name"], "slug": tab["slug"], "content": tab_rendered})

        return render(request, self.template_name, {"rendered_tabs": rendered_tabs})


class StatisticsView(LoginRequiredMixin, TemplateView):
    """Statistics View."""

    template_name = "tosti/statistics.html"

    def get(self, request, **kwargs):
        """GET Statistics View."""

        statistics_blocks = []
        for app in apps.get_app_configs():
            if hasattr(app, "statistics"):
                app_statistics = app.statistics(request)
                if app_statistics is not None:
                    statistics_blocks.append(app_statistics)

        statistics_blocks = sorted(statistics_blocks, key=lambda tab: tab["order"])

        return render(
            request,
            self.template_name,
            {
                "statistics_blocks": statistics_blocks,
            },
        )


class OAuthCredentialsRequestView(TemplateView):
    """View for requesting OAuth credentials for the API."""

    template_name = "users/account.html"

    def get_paginator_page(self, request, page):
        """Get paginator page."""
        registered_applications = Application.objects.filter(user=request.user).order_by("-created")
        paginator = Paginator(registered_applications, per_page=50)
        paginator_page = paginator.get_page(page)

        for application in paginator_page:
            application.modify_form = OAuthCredentialsForm(instance=application)

        return paginator_page

    def render_tab(
        self,
        request,
        paginator_page_with_modify_forms,
        create_form=None,
        create_form_open=False,
        created_application=None,
        open_modify_form_id=None,
    ):
        """Render the tab."""
        if create_form is None:
            create_form = OAuthCredentialsForm()

        return render_to_string(
            "tosti/oauth_credentials.html",
            context={
                "page_obj": paginator_page_with_modify_forms,
                "create_form": create_form,
                "create_form_open": create_form_open,
                "created_application": created_application,
                "open_modify_form_id": open_modify_form_id,
            },
            request=request,
        )

    def get(self, request, **kwargs):
        """GET request for OAuth credentials."""
        paginator_page = self.get_paginator_page(request, request.GET.get("page", 1))
        return render(
            request,
            self.template_name,
            {
                "active": kwargs.get("active"),
                "tabs": kwargs.get("tabs"),
                "rendered_tab": self.render_tab(request, paginator_page),
            },
        )

    def do_create(self, request, **kwargs):
        """Create a new OAuth Application."""
        create_form = OAuthCredentialsForm(request.POST)
        if create_form.is_valid():
            client_secret = generate_client_secret()
            application = Application.objects.create(
                user=request.user,
                redirect_uris=create_form.cleaned_data.get("redirect_uris"),
                client_type=Application.CLIENT_PUBLIC,
                authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
                name=create_form.cleaned_data.get("name"),
                client_secret=client_secret,
            )
            application.client_secret = client_secret
            messages.add_message(
                request,
                messages.SUCCESS,
                "Successfully created a new application, press the details button to show the application details.",
            )
            paginator_page = self.get_paginator_page(request, request.POST.get("page", 1))
            return render(
                request,
                self.template_name,
                {
                    "active": kwargs.get("active"),
                    "tabs": kwargs.get("tabs"),
                    "rendered_tab": self.render_tab(request, paginator_page, created_application=application),
                },
            )
        else:
            paginator_page = self.get_paginator_page(request, request.POST.get("page", 1))
            return render(
                request,
                self.template_name,
                {
                    "active": kwargs.get("active"),
                    "tabs": kwargs.get("tabs"),
                    "rendered_tab": self.render_tab(
                        request, paginator_page, create_form=create_form, create_form_open=True
                    ),
                },
            )

    def do_update(self, request, **kwargs):
        """Update an OAuth application."""
        id_to_modify = request.POST.get("id", None)
        try:
            application_to_modify = Application.objects.get(id=id_to_modify, user=request.user)
        except Application.DoesNotExist:
            return HttpResponseNotFound()

        modify_form = OAuthCredentialsForm(request.POST, instance=application_to_modify)

        if modify_form.is_valid():
            application_to_modify.redirect_uris = modify_form.cleaned_data.get("redirect_uris")
            application_to_modify.name = modify_form.cleaned_data.get("name")
            application_to_modify.save()
            messages.add_message(request, messages.SUCCESS, "Successfully updated the application.")

            paginator_page = self.get_paginator_page(request, request.POST.get("page", 1))

            for application in paginator_page:
                if application.id == application_to_modify.id:
                    application.modify_form = modify_form

            return render(
                request,
                self.template_name,
                {
                    "active": kwargs.get("active"),
                    "tabs": kwargs.get("tabs"),
                    "rendered_tab": self.render_tab(request, paginator_page),
                },
            )
        else:
            paginator_page = self.get_paginator_page(request, request.POST.get("page", 1))

            for application in paginator_page:
                if application.id == application_to_modify.id:
                    application.modify_form = modify_form

            return render(
                request,
                self.template_name,
                {
                    "active": kwargs.get("active"),
                    "tabs": kwargs.get("tabs"),
                    "rendered_tab": self.render_tab(
                        request, paginator_page, open_modify_form_id=application_to_modify.id
                    ),
                },
            )

    def do_destroy(self, request, **kwargs):
        """Destroy an OAuth Application."""
        id_to_destroy = request.POST.get("id", None)
        try:
            application_to_destroy = Application.objects.get(id=id_to_destroy, user=request.user)
        except Application.DoesNotExist:
            return HttpResponseNotFound()

        application_to_destroy.delete()

        messages.add_message(request, messages.SUCCESS, "OAuth credentials deleted successfully.")

        paginator_page = self.get_paginator_page(request, 1)

        return render(
            request,
            self.template_name,
            {
                "active": kwargs.get("active"),
                "tabs": kwargs.get("tabs"),
                "rendered_tab": self.render_tab(request, paginator_page),
            },
        )

    def post(self, request, **kwargs):
        """POST request for OAuth credentials."""
        action = request.POST.get("action", None)
        if action == "create":
            return self.do_create(request, **kwargs)
        elif action == "update":
            return self.do_update(request, **kwargs)
        elif action == "destroy":
            return self.do_destroy(request, **kwargs)
        else:
            return HttpResponseNotFound()


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
