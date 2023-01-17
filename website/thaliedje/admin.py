from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, register_converter
from guardian.admin import GuardedModelAdmin

from thaliedje.converters import PlayerPKConverter
from thaliedje.admin_views import (
    SpofityAuthorizeView,
    SpotifyTokenView,
    SpotifyAuthorizeSucceededView,
)
from .models import (
    SpotifyPlayer,
    ThaliedjeBlacklistedUser,
    ThaliedjeControlEvent,
    PlayerLogEntry,
    MarietjePlayer,
)
from .forms import PlayerAdminForm


@admin.register(MarietjePlayer)
class MarietjePlayerAdmin(GuardedModelAdmin):
    pass


@admin.register(SpotifyPlayer)
class SpotifyPlayerAdmin(GuardedModelAdmin):
    """Player admin for Players."""

    list_display = [
        "client_id",
        "display_name",
        "playback_device_name",
        "get_configured",
    ]
    list_display_links = [
        "client_id",
        "display_name",
        "playback_device_name",
    ]
    form = PlayerAdminForm
    view_on_site = True
    prepopulated_fields = {"slug": ("display_name",)}

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
        register_converter(PlayerPKConverter, "spotify_pk")
        urls = super().get_urls()
        custom_urls = [
            path(
                "authorize/",
                self.admin_site.admin_view(SpofityAuthorizeView.as_view()),
                name="authorize",
            ),
            path(
                "authorize/<spotify_pk:spotify>",
                self.admin_site.admin_view(SpofityAuthorizeView.as_view()),
                name="reauthorize",
            ),
            path("token/", SpotifyTokenView.as_view(), name="add_token"),
            path(
                "auth-succeeded/<spotify_pk:spotify>",
                SpotifyAuthorizeSucceededView.as_view(),
                name="authorization_succeeded",
            ),
        ]
        return custom_urls + urls


@admin.register(ThaliedjeBlacklistedUser)
class ThaliedjeBlacklistedUserAdmin(admin.ModelAdmin):
    """Admin for blacklisted users."""

    autocomplete_fields = ["user"]


@admin.register(ThaliedjeControlEvent)
class ThaliedjeControlEventAdmin(admin.ModelAdmin):
    """Admin for control events."""

    filter_horizontal = ["selected_users"]

    list_display = [
        "start",
        "end",
        "player",
        "event_title",
        "event_association",
    ]

    def event_title(self, obj):
        """Get the title of the event."""
        return obj.event.title

    event_title.short_description = "Event"

    def event_association(self, obj):
        """Get the association of the event."""
        return obj.event.association

    event_association.short_description = "Association"


@admin.register(PlayerLogEntry)
class PlayerLogEntryAdmin(admin.ModelAdmin):
    """Admin for log entries."""

    list_display = [
        "timestamp",
        "player",
        "action",
        "user",
        "description",
    ]

    list_filter = [
        "player",
        "action",
        ("timestamp", admin.DateFieldListFilter),
    ]

    def has_delete_permission(self, request, obj=None):
        """Disable delete permission."""
        return False

    def has_add_permission(self, request):
        """Disable add permission."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable change permission."""
        return False
