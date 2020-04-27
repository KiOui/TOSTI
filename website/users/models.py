from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):
    """User manager object."""

    def _create_user(self, username, **extra_fields):
        """
        Create user given a username.

        :param username: the username
        :param extra_fields: optional extra fields
        :return: a new User object
        """
        user = self.model(username=username, **extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, username, **extra_fields):
        """
        Create a user given a username.

        :param username: the username
        :param extra_fields: optional extra fields
        :return: a new User object
        """
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, **extra_fields)

    def create_superuser(self, username, **extra_fields):
        """
        Create a superuser.

        :param username: the username
        :param extra_fields: optional extra fields
        :return: a new User object
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(username, **extra_fields)


class User(AbstractUser):
    """User object."""

    username = models.CharField(max_length=256, unique=True)

    objects = UserManager()

    USERNAME_FIELD = "username"

    REQUIRED_FIELDS = []

    def __str__(self):
        """
        Convert user to string.

        :return: the username of the user
        """
        return self.username
