from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, register_converter

from marietje.converters import SpotifyAccountConverter
from marietje.admin_views import (
    SpofityAuthorizeView,
    SpotifyTokenView,
    SpotifyAuthorizeSucceededView,
)
from .models import SpotifyAccount
from .forms import SpotifyAccountAdminForm


@admin.register(SpotifyAccount)
class SpotifyAccountAdmin(admin.ModelAdmin):
    """Spotify account admin."""

    list_display = [
        "display_name",
        "playback_device_name",
        "client_id",
        "get_configured",
    ]
    form = SpotifyAccountAdminForm

    def get_configured(self, obj):
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

    register_converter(SpotifyAccountConverter, "spotify")

    def get_urls(self):
        """Get admin urls."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "authorize/",
                self.admin_site.admin_view(SpofityAuthorizeView.as_view()),
                name="authorize",
            ),
            path("token/", SpotifyTokenView.as_view(), name="add_token"),
            path(
                "auth-succeeded/<spotify:spotify>",
                SpotifyAuthorizeSucceededView.as_view(),
                name="authorization_succeeded",
            ),
        ]
        return custom_urls + urls
