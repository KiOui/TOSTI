from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import User as BaseUser, Group as BaseGroup, AbstractUser
from django.db import models
from django.db.models import CASCADE
from associations.models import Association


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


class User(AbstractUser):
    """User object."""

    objects = UserManager()

    USERNAME_FIELD = "username"

    REQUIRED_FIELDS = ["name", "email"]

    username = models.CharField(max_length=8, unique=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)

    association = models.ForeignKey(
        Association, related_name="users", null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        """
        Convert user to string.

        :return: the username of the user
        """
        return f"{self.name} ({self.association}" if self.name and self.association else self.username


class GroupSettings(models.Model):
    """Extra settings for a Django Group."""

    group = models.OneToOneField(BaseGroup, on_delete=CASCADE, primary_key=True)
    is_auto_join_group = models.BooleanField(
        default=False, help_text="If enabled, new users will automatically join this group."
    )
    gets_staff_permissions = models.BooleanField(
        default=False,
        help_text=(
            "If enabled, all members added to this group will automatically get staff"
            " status after their next login. This staff status will not be automatically"
            " revoked, though, if the user leaves the group."
        ),
    )

    class Meta:
        """Meta class for GroupSettings."""

        ordering = ["group__name"]

    def __str__(self):
        """Representation by group."""
        return str(self.group)
