from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django import forms

from users.models import UserGroup

User = get_user_model()


class UserAdminForm(forms.ModelForm):
    """Custom AdminForm for Users."""

    user_permissions = forms.ModelMultipleChoiceField(
        Permission.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("permissions", False),
    )
    groups = forms.ModelMultipleChoiceField(
        UserGroup.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("groups", False),
    )

    class Meta:
        """Meta class for the UserAdminForm."""

        model = User
        exclude = []


class UserAdmin(admin.ModelAdmin):
    """User admin model for the User object."""

    form = UserAdminForm

    search_fields = ["username"]
    fieldsets = (
        ("User", {"fields": ("username", "first_name", "last_name", "email")}),
        (
            "Details",
            {
                "fields": (
                    "date_joined",
                    "last_login",
                    "is_staff",
                    "is_active",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )
    list_display = [
        "username",
        "date_joined",
        "last_login",
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


class GroupAdminForm(forms.ModelForm):
    """Custom AdminForm for Groups."""

    permissions = forms.ModelMultipleChoiceField(
        Permission.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("permissions", False),
    )
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("users", False),
    )

    class Meta:
        """Meta class for the GroupAdminForm."""

        model = UserGroup
        exclude = []


class GroupAdmin(admin.ModelAdmin):
    """Custom admin for Groups."""

    form = GroupAdminForm

    class Meta:
        """Meta class for the GroupAdmin."""

        model = UserGroup
        exclude = []


admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
admin.site.register(UserGroup, GroupAdmin)
