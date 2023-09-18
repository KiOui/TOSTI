import uuid

from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Is18YearsOld(models.Model):
    """Class to check whether someone has a legal drinking age."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="is_18_years_old")
    created_at = models.DateTimeField(auto_now_add=True)


class SessionMapping(models.Model):
    """Session mapping class for Yivi."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_token = models.CharField(max_length=20, unique=True)
