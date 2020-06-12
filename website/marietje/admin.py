from django.contrib import admin
from django.shortcuts import redirect

from .models import SpotifySettings
from .forms import SpotifySettingsAdminForm


@admin.register(SpotifySettings)
class SpotifySettingsAdmin(admin.ModelAdmin):
    """Spotify Settings admin."""

    list_display = ["display_name", "playback_device_name", "client_id"]
    form = SpotifySettingsAdminForm

    def add_view(self, request, form_url="", extra_context=None):
        """
        Add view of the Spotify Settings Admin.

        This function redirects to the authorize page
        :param request: the request
        :param form_url: the from_url
        :param extra_context: extra context
        :return: a redirect to the authorize page
        """
        return redirect("marietje:authorize")
