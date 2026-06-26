from django.apps import apps
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.generic import TemplateView, RedirectView
from django.utils.decorators import method_decorator
from oauth2_provider.generators import generate_client_secret
from oauth2_provider.models import (
    AccessToken,
    Application,
    Grant,
    RefreshToken,
)
from oauth2_provider.scopes import get_scopes_backend

from tosti.forms import OAuthCredentialsForm


def _list_authorised_apps_for_user(user):
    """Return Applications the given user has at least one (non-expired) AccessToken for.

    Used to render the "Connected AI assistants & third-party apps" tab.
    Each entry summarises the union of scopes granted across the user's
    currently-valid tokens for that application, so the revoke button can
    drop them all at once.
    """
    token_qs = (
        AccessToken.objects.filter(user=user)
        .select_related("application")
        .order_by("application_id", "-created")
    )
    by_app: dict[int, dict] = {}
    all_scopes = get_scopes_backend().get_all_scopes()
    for token in token_qs:
        if token.application is None:
            continue
        if token.is_expired():
            continue
        entry = by_app.setdefault(
            token.application_id,
            {
                "application": token.application,
                "scopes": set(),
                "first_granted": token.created,
                "last_used": token.updated,
            },
        )
        entry["scopes"].update(token.scope.split())
        if token.created < entry["first_granted"]:
            entry["first_granted"] = token.created
        if token.updated > entry["last_used"]:
            entry["last_used"] = token.updated

    result = []
    for entry in by_app.values():
        scope_names = sorted(entry["scopes"])
        result.append(
            {
                "application": entry["application"],
                "scopes": [
                    {"name": s, "description": all_scopes.get(s, s)}
                    for s in scope_names
                ],
                "first_granted": entry["first_granted"],
                "last_used": entry["last_used"],
            }
        )
    result.sort(key=lambda e: e["last_used"], reverse=True)
    return result


def _revoke_user_app_authorisation(user, application):
    """Delete all AccessTokens, RefreshTokens and pending Grants the user holds for ``application``.

    This is the user-visible "revoke" action for the Connected apps tab.
    We do not delete the Application itself: self-registered MCP apps have
    ``user=None`` so deleting the row would also nuke it for any other
    user who happens to have authorised the same DCR-issued client_id.
    """
    AccessToken.objects.filter(user=user, application=application).delete()
    RefreshToken.objects.filter(user=user, application=application).delete()
    Grant.objects.filter(user=user, application=application).delete()


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(View):
    """Log the user out and redirect to the homepage."""

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        logout(request)
        return HttpResponseRedirect("/")


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
                self.request,
                messages.INFO,
                "Welcome to TOSTI! Please complete your account profile below.",
            )
            return reverse("users:account")
        if next_url:
            return next_url
        return reverse("index")


class DocumentationView(TemplateView):
    """Documentation page."""

    template_name = "tosti/documentation.html"


class OAuthIntegrationDocsView(TemplateView):
    """OAuth 2.0 integration guide: supported flows, scopes, and conventions.

    Generic developer doc — applies to any client, not just MCP / AI assistants.
    Linked from the documentation index and from the MCP landing page.
    """

    template_name = "tosti/oauth_integration.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pull the scope table from the live oauth2_provider config so the doc
        # stays in sync with what the discovery endpoint actually advertises.
        scopes = get_scopes_backend().get_all_scopes()
        context["scopes"] = sorted(scopes.items())
        return context


class MCPToolsDocsView(TemplateView):
    """Swagger-equivalent for the MCP endpoint: lists every registered tool.

    Introspects the django_mcp_server tool manager at request time so the page
    always reflects what ``/mcp`` actually exposes. Tools are grouped by the
    ``MCPToolset`` subclass that contributed them, with name, description, and
    JSON Schemas for input and output.
    """

    template_name = "tosti/mcp_tools.html"

    def get_context_data(self, **kwargs):
        import json

        from mcp_server import mcp_server as global_mcp_server

        context = super().get_context_data(**kwargs)
        tools = global_mcp_server._tool_manager.list_tools()

        grouped: dict[str, list[dict]] = {}
        for tool in tools:
            # _ToolsetMethodCaller carries the originating MCPToolset class;
            # tools that aren't backed by a toolset (e.g. the built-in
            # get_server_instructions) get bucketed under "Server".
            caller = getattr(tool, "fn", None)
            toolset_cls = getattr(caller, "class_", None)
            group_name = toolset_cls.__name__ if toolset_cls else "Server"
            group_doc = (toolset_cls.__doc__ or "").strip() if toolset_cls else ""

            if group_name not in grouped:
                grouped[group_name] = {"doc": group_doc, "tools": []}

            grouped[group_name]["tools"].append(
                {
                    "name": tool.name,
                    "description": (tool.description or "").strip(),
                    "input_schema": json.dumps(tool.parameters, indent=2, sort_keys=True),
                    "output_schema": (
                        json.dumps(tool.output_schema, indent=2, sort_keys=True)
                        if tool.output_schema
                        else None
                    ),
                }
            )

        # Sort: toolset groups alphabetically, with "Server" pinned last.
        ordered = []
        for name in sorted(grouped, key=lambda n: (n == "Server", n)):
            ordered.append(
                {
                    "name": name,
                    "doc": grouped[name]["doc"],
                    "tools": sorted(grouped[name]["tools"], key=lambda t: t["name"]),
                }
            )
        context["toolsets"] = ordered
        return context


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
                rendered_tabs.append(
                    {"name": tab["name"], "slug": tab["slug"], "content": tab_rendered}
                )

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


class ConnectedAppsView(TemplateView):
    """View listing third-party apps the user has authorised (incl. AI assistants).

    These are applications the user has granted an OAuth2 token to — most
    often an MCP client that self-registered via RFC 7591
    and then went through the user's consent screen. The user can revoke
    each app's access in one click; we drop their tokens (not the
    Application row itself, since DCR-created Applications have
    ``user=None`` and may be shared across users).
    """

    template_name = "users/account.html"

    def get(self, request, **kwargs):
        """Render the Connected apps tab."""
        return render(
            request,
            self.template_name,
            {
                "active": kwargs.get("active"),
                "tabs": kwargs.get("tabs"),
                "rendered_tab": self._render_tab(request),
            },
        )

    def post(self, request, **kwargs):
        """Handle the Revoke action."""
        action = request.POST.get("action", None)
        if action != "revoke":
            return HttpResponseNotFound()
        application_id = request.POST.get("application_id")
        try:
            application = Application.objects.get(id=application_id)
        except Application.DoesNotExist:
            return HttpResponseNotFound()
        # Only allow revoking if the user actually has a token for it.
        if not AccessToken.objects.filter(
            user=request.user, application=application
        ).exists() and not RefreshToken.objects.filter(
            user=request.user, application=application
        ).exists():
            return HttpResponseNotFound()
        _revoke_user_app_authorisation(request.user, application)
        messages.add_message(
            request,
            messages.SUCCESS,
            f"Revoked access for '{application.name or application.client_id}'. "
            "The application will need your consent again next time it tries to connect.",
        )
        return render(
            request,
            self.template_name,
            {
                "active": kwargs.get("active"),
                "tabs": kwargs.get("tabs"),
                "rendered_tab": self._render_tab(request),
            },
        )

    def _render_tab(self, request):
        return render_to_string(
            "tosti/connected_apps.html",
            context={"entries": _list_authorised_apps_for_user(request.user)},
            request=request,
        )


class OAuthCredentialsRequestView(TemplateView):
    """View for requesting OAuth credentials for the API."""

    template_name = "users/account.html"

    def get_paginator_page(self, request, page):
        """Get paginator page."""
        registered_applications = Application.objects.filter(
            user=request.user
        ).order_by("-created")
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
            paginator_page = self.get_paginator_page(
                request, request.POST.get("page", 1)
            )
            return render(
                request,
                self.template_name,
                {
                    "active": kwargs.get("active"),
                    "tabs": kwargs.get("tabs"),
                    "rendered_tab": self.render_tab(
                        request, paginator_page, created_application=application
                    ),
                },
            )
        else:
            paginator_page = self.get_paginator_page(
                request, request.POST.get("page", 1)
            )
            return render(
                request,
                self.template_name,
                {
                    "active": kwargs.get("active"),
                    "tabs": kwargs.get("tabs"),
                    "rendered_tab": self.render_tab(
                        request,
                        paginator_page,
                        create_form=create_form,
                        create_form_open=True,
                    ),
                },
            )

    def do_update(self, request, **kwargs):
        """Update an OAuth application."""
        id_to_modify = request.POST.get("id", None)
        try:
            application_to_modify = Application.objects.get(
                id=id_to_modify, user=request.user
            )
        except Application.DoesNotExist:
            return HttpResponseNotFound()

        modify_form = OAuthCredentialsForm(request.POST, instance=application_to_modify)

        if modify_form.is_valid():
            application_to_modify.redirect_uris = modify_form.cleaned_data.get(
                "redirect_uris"
            )
            application_to_modify.name = modify_form.cleaned_data.get("name")
            application_to_modify.save()
            messages.add_message(
                request, messages.SUCCESS, "Successfully updated the application."
            )

            paginator_page = self.get_paginator_page(
                request, request.POST.get("page", 1)
            )

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
            paginator_page = self.get_paginator_page(
                request, request.POST.get("page", 1)
            )

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
                        request,
                        paginator_page,
                        open_modify_form_id=application_to_modify.id,
                    ),
                },
            )

    def do_destroy(self, request, **kwargs):
        """Destroy an OAuth Application."""
        id_to_destroy = request.POST.get("id", None)
        try:
            application_to_destroy = Application.objects.get(
                id=id_to_destroy, user=request.user
            )
        except Application.DoesNotExist:
            return HttpResponseNotFound()

        application_to_destroy.delete()

        messages.add_message(
            request, messages.SUCCESS, "OAuth credentials deleted successfully."
        )

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


def explainer_page_mcp_tab(request, item):
    """Render the explainer tab for connecting an MCP client."""
    return render_to_string(
        "tosti/explainer_mcp.html", context={"request": request, "item": item}
    )
