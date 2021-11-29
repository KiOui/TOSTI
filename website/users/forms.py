from django import forms
from urllib.parse import quote

from associations.models import Association


class AccountForm(forms.Form):
    """Form for showing account details."""

    username = forms.CharField(
        label="Username",
        help_text="This is your username used to log you in to this website.",
        widget=forms.TextInput(attrs={"readonly": "readonly"}),
        required=False,
    )
    first_name = forms.CharField(
        label="First name", widget=forms.TextInput(attrs={"readonly": "readonly"}), required=False
    )
    last_name = forms.CharField(
        label="Last name", widget=forms.TextInput(attrs={"readonly": "readonly"}), required=False
    )
    email = forms.EmailField(
        label="Email address", widget=forms.TextInput(attrs={"readonly": "readonly"}), required=False
    )
    association = forms.ModelChoiceField(queryset=Association.objects.all(), required=False)
