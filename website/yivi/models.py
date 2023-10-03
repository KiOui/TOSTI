import uuid

from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Session(models.Model):
    """Session mapping class for Yivi."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_token = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
