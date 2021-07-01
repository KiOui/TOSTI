from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, register_converter
from guardian.admin import GuardedModelAdmin

from thaliedje.converters import PlayerConverter
from thaliedje.admin_views import (
    SpofityAuthorizeView,
    SpotifyTokenView,
    SpotifyAuthorizeSucceededView,
)
from .models import Player
from .forms import PlayerAdminForm


@admin.register(Player)
class PlayerAdmin(GuardedModelAdmin):
    """Player admin for Players."""

    list_display = [
        "display_name",
        "playback_device_name",
        "client_id",
        "get_configured",
    ]
    form = PlayerAdminForm
    view_on_site = True

    def get_configured(self, obj):
        """Get whether a Player  is configured."""
        return obj.configured

    get_configured.short_description = "Configured"
    get_configured.boolean = True

    def add_view(self, request, form_url="", extra_context=None):
        """
        Add view of the Spotify Account Admin.

        This function redirects to the authorize page
        :param request: the request
        :param form_url: the from_url
        :param extra_context: extra context
        :return: a redirect to the authorize page
        """
        return redirect("admin:authorize")

    def get_urls(self):
        """Get admin urls."""
        register_converter(PlayerConverter, "spotify")
        urls = super().get_urls()
        custom_urls = [
            path("authorize/", self.admin_site.admin_view(SpofityAuthorizeView.as_view()), name="authorize",),
            path("authorize/<spotify:spotify>", self.admin_site.admin_view(SpofityAuthorizeView.as_view()), name="reauthorize",),
            path("token/", SpotifyTokenView.as_view(), name="add_token"),
            path(
                "auth-succeeded/<spotify:spotify>",
                SpotifyAuthorizeSucceededView.as_view(),
                name="authorization_succeeded",
            ),
        ]
        return custom_urls + urls
