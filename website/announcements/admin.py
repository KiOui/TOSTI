from django.contrib import admin

from announcements.models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """Manage the admin pages for the announcements."""

    list_display = ("title", "since", "until", "visible")

    def visible(self, obj):
        """Is the object visible."""
        return obj.is_visible

    visible.boolean = True
