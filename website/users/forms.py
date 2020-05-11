from django import forms
from urllib.parse import quote


class LoginForm(forms.Form):
    """Form for running a profile."""

    username = forms.CharField(label="Science username")
    remember = forms.BooleanField(label="Remember username", initial=True)

    def clean_username(self):
        """
        Clean the username field in this form.

        :return: the cleaned username variable
        """
        username = self.cleaned_data.get("username")
        return quote(username)
