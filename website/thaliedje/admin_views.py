from django.contrib.admin import site
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import TemplateView

from thaliedje.forms import SpotifyTokenForm
from thaliedje.models import Player

COOKIE_CLIENT_ID = "client_id"


class SpofityAuthorizeView(PermissionRequiredMixin, TemplateView):
    """Authorize a Django to access a Spotify account by entering OAuth credentials."""

    permission_required = "thaliedje.add_player"
    template_name = "thaliedje/admin/authorize.html"

    instance_type = Player
    view_name = "Authorize Spotify Account"

    def get(self, request, **kwargs):
        """Get the form to add a new authorized Spotify Account."""
        player = kwargs.get("spotify", None)
        render_data = {
            "view_name": self.view_name,
            "opts": self.instance_type._meta,
            "has_view_permission": site.has_permission(request),
            "site_header": site.site_header,
            "site_url": site.site_url,
            "app_label": self.instance_type._meta.app_label,
            "original": player,
            "is_popup": False,
            "is_nav_sidebar_enabled": site.enable_nav_sidebar,
            "available_apps": site.get_app_list(request),
        }

        if player is not None:
            render_data["form"] = SpotifyTokenForm(
                initial={
                    "client_id": player.client_id,
                    "client_secret": player.client_secret,
                }  # noqa
            )
        else:
            render_data["form"] = SpotifyTokenForm()
        return render(request, self.template_name, render_data)

    def post(self, request, **kwargs):
        """
        Post the OAuth credentials to add a new authorized Spotify Account.

        :param request: the request
        :param kwargs: keyword arguments
        :return: either a render of the authorize page on error or a redirect to the authorization url otherwise
        """
        form = SpotifyTokenForm(request.POST)
        if form.is_valid():
            spotify_auth_code, _ = Player.objects.get_or_create(client_id=form.cleaned_data.get("client_id"))
            spotify_auth_code.client_secret = form.cleaned_data.get("client_secret")
            spotify_auth_code.redirect_uri = request.build_absolute_uri(reverse("admin:add_token"))
            spotify_auth_code.save()
            spotify_oauth = redirect(spotify_auth_code.auth.get_authorize_url())
            spotify_oauth.set_cookie(COOKIE_CLIENT_ID, spotify_auth_code.client_id)
            return spotify_oauth
        player = kwargs.get("spotify", None)
        render_data = {
            "view_name": self.view_name,
            "opts": self.instance_type._meta,
            "has_view_permission": site.has_permission(request),
            "site_header": site.site_header,
            "site_url": site.site_url,
            "app_label": self.instance_type._meta.app_label,
            "original": player,
            "is_popup": False,
            "is_nav_sidebar_enabled": site.enable_nav_sidebar,
            "available_apps": site.get_app_list(request),
            "form": form,
        }
        return render(request, self.template_name, render_data)


class SpotifyTokenView(PermissionRequiredMixin, TemplateView):
    """Get a Spotify account token."""

    permission_required = "thaliedje.add_player"
    template_name = "thaliedje/admin/token.html"

    def get(self, request, **kwargs):
        """Get a Spotify account token from the Spotify OAuth credentials."""
        code = request.GET.get("code", None)
        if code is not None:
            client_id = request.COOKIES.get(COOKIE_CLIENT_ID, None)
            try:
                spotify_auth_code = Player.objects.get(client_id=client_id)
            except Player.DoesNotExist:
                return render(request, self.template_name, {"error": "Client ID was not found."})
            # Generate the first access token and store in cache
            access_token = spotify_auth_code.auth.get_access_token(code=code)
            if access_token is not None:
                response = redirect("admin:authorization_succeeded", spotify=spotify_auth_code)
            else:
                response = render(
                    request,
                    self.template_name,
                    {"error": "Access token retrieval failed, please try again."},
                )
            response.delete_cookie(COOKIE_CLIENT_ID)
            return response
        else:
            return render(
                request,
                self.template_name,
                {"error": "No Spotify code found, make sure you are reaching this page via a Spotify redirect."},
            )


class SpotifyAuthorizeSucceededView(PermissionRequiredMixin, TemplateView):
    """Authorization succeeded view."""

    permission_required = "thaliedje.add_player"
    template_name = "thaliedje/admin/authorize_succeeded.html"

    instance_type = Player
    view_name = "Authorization succeeded"

    def get(self, request, **kwargs):
        """GET the view."""
        spotify = kwargs.get("spotify")
        render_data = {
            "view_name": self.view_name,
            "opts": self.instance_type._meta,
            "has_view_permission": site.has_permission(request),
            "site_header": site.site_header,
            "site_url": site.site_url,
            "app_label": self.instance_type._meta.app_label,
            "original": spotify,
            "is_popup": False,
            "is_nav_sidebar_enabled": site.enable_nav_sidebar,
            "available_apps": site.get_app_list(request),
        }
        return render(request, self.template_name, render_data)
