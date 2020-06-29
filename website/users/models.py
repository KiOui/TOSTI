from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import User as BaseUser, Group as BaseGroup

from django.db import models


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
        return (
            self.first_name
            if self.first_name != "" and self.first_name is not None
            else self.username
        )

    class Meta:
        """Meta class for Users."""

        proxy = True


BaseGroup.add_to_class(
    "auto_join_new_users",
    models.BooleanField(
        default=True,
        help_text="If selected, new users will automatically be added to this group.",
    ),
)


class Group(BaseGroup):
    """Our own custom group"""

    class Meta:
        """Meta class for groups"""

        proxy = True
