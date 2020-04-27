from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()


class UserAdmin(admin.ModelAdmin):
    """User admin model for the User object."""

    search_fields = ["username"]

    class Meta:
        """Meta class for the UserAdmin model."""

        model = User


admin.site.register(User, UserAdmin)
