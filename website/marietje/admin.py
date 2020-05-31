from django.contrib import admin
from .models import SpotifySettings
from .forms import SpotifySettingsAdminForm


class SpotifySettingsAdmin(admin.ModelAdmin):
    """Spotify Settings admin."""

    form = SpotifySettingsAdminForm


admin.site.register(SpotifySettings, SpotifySettingsAdmin)
