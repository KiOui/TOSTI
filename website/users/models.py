from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import Group as BaseGroup, AbstractUser
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
        if "password" in kwargs.keys():
            user.set_password(kwargs.pop("password"))
        else:
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

    REQUIRED_FIELDS = ["email"]

    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=False)
    full_name = models.CharField(max_length=100)

    override_display_name = models.CharField(max_length=100, blank=True, null=True)
    override_short_name = models.CharField(max_length=50, blank=True, null=True)

    association = models.ForeignKey(
        Association, related_name="users", null=True, blank=True, on_delete=models.SET_NULL
    )

    def extract_first_and_last_name_from_username(self):
        """Update the user's first and last name based on their display name."""
        if self.full_name and not self.first_name and not self.last_name:
            first_name = self.full_name[self.full_name.find("(") + 1 : self.full_name.find(")")]  # noqa: E203
            last_name = self.full_name.split(",")[0]

            insert = self.full_name[self.full_name.rfind(".") + 1 : self.full_name.find("(")].strip()  # noqa: E203
            if len(insert) > 0:
                last_name = insert + " " + last_name

            self.first_name = first_name
            self.last_name = last_name

    def save(self, *args, **kwargs):
        """Override save method."""
        # Ugly hack to fix capitalization of username
        self.username = self.username.lower()
        self.email = self.email.lower()

        if self.pk is None:
            try:
                self.pk = self.objects.get(username=self.username).pk
            except self.DoesNotExist:
                pass

        self.extract_first_and_last_name_from_username()
        return super(User, self).save(*args, **kwargs)

    def __str__(self):
        """
        Convert user to string.

        :return: the username of the user
        """
        if self.override_display_name and self.association:
            return f"{self.override_display_name} ({self.association})"

        if self.override_display_name:
            return self.override_display_name

        if self.first_name and self.last_name and self.association:
            return f"{self.first_name} {self.last_name} ({self.association})"
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.full_name:
            return self.full_name
        return self.username

    def get_short_name(self):
        """Get short name."""
        if self.override_short_name:
            return self.override_short_name

        if self.first_name:
            return self.first_name
        elif self.full_name:
            return self.full_name
        else:
            return self.username


class GroupSettings(models.Model):
    """Extra settings for a Django Group."""

    group = models.OneToOneField(BaseGroup, on_delete=CASCADE, primary_key=True, related_name="settings")
    gets_staff_permissions = models.BooleanField(
        default=False,
        help_text=(
            "If enabled, all members added to this group will automatically get staff"
            " status after their next login. This staff status will not be automatically"
            " revoked, though, if the user leaves the group."
        ),
    )
    display_on_website = models.BooleanField(
        default=False, help_text=("If enabled, the members of this group will be displayed on a webpage.")
    )

    class Meta:
        """Meta class for GroupSettings."""

        ordering = ["group__name"]

    def __str__(self):
        """Representation by group."""
        return str(self.group)
