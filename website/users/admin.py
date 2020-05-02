from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()


class UserAdmin(admin.ModelAdmin):
    """User admin model for the User object."""

    search_fields = ["username"]
    fieldsets = (
        ("User", {"fields": ("username", "first_name", "last_name", "email")}),
        (
            "Details",
            {
                "fields": (
                    "date_joined",
                    "is_staff",
                    "is_active",
                    "is_superuser",
                    "user_permissions",
                ),
            },
        ),
    )
    list_display = [
        "username",
        "date_joined",
        "is_active",
        "is_staff",
        "is_superuser",
    ]

    list_filter = [
        "is_active",
        "is_staff",
        "is_superuser",
        "is_staff",
    ]
    model = User

    class Meta:
        """Meta class for the UserAdmin model."""


admin.site.register(User, UserAdmin)
