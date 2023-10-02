from django import forms
from django.contrib.auth import get_user_model

from age.models import AgeRegistration


User = get_user_model()


class AgeRegistrationAdminForm(forms.ModelForm):
    """Age Registration Admin Form."""

    class Meta:
        """Meta class."""

        model = AgeRegistration
        labels = {
            "verified_by_user": "Verified by",
        }
        fields = ["user", "minimum_age"]
