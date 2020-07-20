from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import User as BaseUser, Group as BaseGroup
from django.db import models
from django.db.models import CASCADE


class UserManager(BaseUserManager):
    """User manager object."""

    def _create_user(self, username, **kwargs):
        """
        Create user given a username.

        :param username: the username
        :param kwargs: optional extra fields
        :return: a new User object
        """
        user = self.model(username=username, **kwargs)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, username, **kwargs):
        """
        Create a user given a username.

        :param username: the username
        :param kwargs: optional extra fields
        :return: a new User object
        """
        kwargs.setdefault("is_staff", False)
        kwargs.setdefault("is_superuser", False)
        return self._create_user(username, **kwargs)

    def create_superuser(self, username, **kwargs):
        """
        Create a superuser.

        :param username: the username
        :param kwargs: optional extra fields
        :return: a new User object
        """
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)
        return self._create_user(username, **kwargs)


class User(BaseUser):
    """User object."""

    objects = UserManager()

    USERNAME_FIELD = "username"

    REQUIRED_FIELDS = []

    def __str__(self):
        """
        Convert user to string.

        :return: the username of the user
        """
        if self.first_name:
            return self.get_full_name()
        else:
            return self.username

    def get_short_name(self):
        """
        Get the short name of a User object.

        :return: first name if it exists, otherwise username
        """
        return self.first_name if self.first_name != "" and self.first_name is not None else self.username

    class Meta:
        """Meta class for Users."""

        proxy = True


class GroupSettings(models.Model):
    """Extra settings for a Django Group."""

    group = models.OneToOneField(BaseGroup, on_delete=CASCADE, primary_key=True)
    is_auto_join_group = models.BooleanField(
        null=False, blank=False, default=False, help_text="If enabled, new users will automatically join this group."
    )
    gets_staff_permissions = models.BooleanField(
        null=False,
        blank=False,
        default=False,
        help_text="If enabled, all members added to this group will automatically get staff status after their next "
        "login. This staff status will not be automatically revoked, though, if the user leaves the group.",
    )

    def __str__(self):
        """Representation by group."""
        return str(self.group)

    class Meta:
        """Meta class for GroupSettings."""

        ordering = ["group__name"]
