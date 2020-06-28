from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import TemplateView

from thaliedje.forms import SpotifyTokenForm
from thaliedje.models import SpotifyAccount
from thaliedje.views import COOKIE_CLIENT_ID
from orders.permissions import StaffRequiredMixin


class SpofityAuthorizeView(StaffRequiredMixin, TemplateView):
    """Authorize a Django to access a Spotify account by entering OAuth credentials."""

    template_name = "thaliedje/admin/authorize.html"

    def get(self, request, **kwargs):
        """Get the form to add a new authorized Spotify Account."""
        form = SpotifyTokenForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, **kwargs):
        """
        Post the OAuth credentials to add a new authorized Spotify Account.

        :param request: the request
        :param kwargs: keyword arguments
        :return: either a render of the authorize page on error or a redirect to the authorization url otherwise
        """
        form = SpotifyTokenForm(request.POST)
        if form.is_valid():
            spotify_auth_code, _ = SpotifyAccount.objects.get_or_create(
                client_id=form.cleaned_data.get("client_id")
            )
            spotify_auth_code.client_secret = form.cleaned_data.get("client_secret")
            spotify_auth_code.redirect_uri = request.build_absolute_uri(
                reverse("admin:add_token")
            )
            spotify_auth_code.save()
            spotify_oauth = redirect(spotify_auth_code.auth.get_authorize_url())
            spotify_oauth.set_cookie(COOKIE_CLIENT_ID, spotify_auth_code.client_id)
            return spotify_oauth
        return render(request, self.template_name, {"form": form})


class SpotifyTokenView(StaffRequiredMixin, TemplateView):
    """Get a Spotify account token."""

    template_name = "thaliedje/admin/token.html"

    def get(self, request, **kwargs):
        """Get a Spotify account token from the Spotify OAuth credentials."""
        code = request.GET.get("code", None)
        if code is not None:
            client_id = request.COOKIES.get(COOKIE_CLIENT_ID, None)
            try:
                spotify_auth_code = SpotifyAccount.objects.get(client_id=client_id)
            except SpotifyAccount.DoesNotExist:
                return render(
                    request, self.template_name, {"error": "Client ID was not found."}
                )
            # Generate the first access token and store in cache
            access_token = spotify_auth_code.auth.get_access_token(code=code)
            if access_token is not None:
                response = redirect(
                    "admin:authorization_succeeded", spotify=spotify_auth_code
                )
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
                {
                    "error": "No Spotify code found, make sure you are reaching this"
                    "page via a Spotify redirect."
                },
            )


class SpotifyAuthorizeSucceededView(StaffRequiredMixin, TemplateView):
    """Authorization succeeded view."""

    template_name = "thaliedje/admin/authorize_succeeded.html"

    def get(self, request, **kwargs):
        """GET the view."""
        spotify = kwargs.get("spotify")
        return render(
            request,
            self.template_name,
            {"username": spotify.get_display_name, "spotify": spotify},
        )
