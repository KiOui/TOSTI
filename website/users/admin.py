from django.contrib import admin
from django.contrib.auth.admin import (
    UserAdmin as BaseUserAdmin,
    GroupAdmin as BaseGroupAdmin,
)
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django import forms

User = get_user_model()


class UserAdminForm(forms.ModelForm):
    """Custom AdminForm for Users."""

    user_permissions = forms.ModelMultipleChoiceField(
        Permission.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("permissions", False),
    )
    groups = forms.ModelMultipleChoiceField(
        Group.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("groups", False),
    )

    class Meta:
        """Meta class for the UserAdminForm."""

        model = User
        exclude = []


class UserAdmin(BaseUserAdmin):
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

    def __init__(self, *args, **kwargs):
        """Correctly initialize the form, because users is not a field of Groups, but the other way around."""
        super(GroupAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["users"].initial = self.instance.user_set.all()

    def save_m2m(self):
        """On save, add selected users to the group."""
        self.instance.user_set.set(self.cleaned_data["users"])

    def save(self, *args, **kwargs):
        """Default save."""
        instance = super(GroupAdminForm, self).save()
        self.save_m2m()
        return instance

    class Meta:
        """Meta class for the GroupAdminForm."""

        model = Group
        exclude = []


class GroupAdmin(BaseGroupAdmin):
    """Custom admin for Groups."""

    form = GroupAdminForm

    class Meta:
        """Meta class for the GroupAdmin."""


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
