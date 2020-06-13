from django.contrib import admin
from django.shortcuts import redirect

from .models import SpotifySettings, SpotifyTrack, SpotifyArtist, SpotifyQueueItem
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


@admin.register(SpotifyArtist)
class SpotifyArtistAdmin(admin.ModelAdmin):
    """Spotify Artist admin."""

    list_display = ["artist_name", "artist_id"]


@admin.register(SpotifyTrack)
class SpotifyTrackAdmin(admin.ModelAdmin):
    """Spotify Track admin."""

    list_display = ["track_name", "track_id"]


@admin.register(SpotifyQueueItem)
class SpotifyQueueItemAdmin(admin.ModelAdmin):
    """Spotify Queue item admin."""

    list_display = ["track", "spotify_settings_object", "requested_by", "added"]
