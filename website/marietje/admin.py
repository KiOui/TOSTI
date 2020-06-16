from django.contrib import admin
from django.shortcuts import redirect

from .models import SpotifyAccount
from .forms import SpotifyAccountAdminForm


@admin.register(SpotifyAccount)
class SpotifyAccountAdmin(admin.ModelAdmin):
    """Spotify account admin."""

    list_display = ["display_name", "playback_device_name", "client_id"]
    form = SpotifyAccountAdminForm

    def add_view(self, request, form_url="", extra_context=None):
        """
        Add view of the Spotify Account Admin.

        This function redirects to the authorize page
        :param request: the request
        :param form_url: the from_url
        :param extra_context: extra context
        :return: a redirect to the authorize page
        """
        return redirect("marietje:authorize")
