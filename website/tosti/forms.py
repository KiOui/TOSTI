from django import forms
from oauth2_provider.models import Application


class OAuthCredentialsForm(forms.ModelForm):
    """OAuth Credentials Form."""

    class Meta:
        """Meta class for OAuth Credentials Form."""

        model = Application
        fields = [
            "name",
            "redirect_uris",
        ]
