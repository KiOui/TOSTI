from django import forms

from associations.models import Association


class AccountForm(forms.Form):
    """Form for showing account details."""

    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={"readonly": "readonly"}),
        required=False,
    )
    first_name = forms.CharField(
        label="First name", widget=forms.TextInput(attrs={"readonly": "readonly"}), required=False
    )
    last_name = forms.CharField(
        label="Last name", widget=forms.TextInput(attrs={"readonly": "readonly"}), required=False
    )
    full_name = forms.CharField(label="Full name", widget=forms.TextInput(attrs={"readonly": "readonly"}), required=False)
    email = forms.EmailField(
        label="Email address", widget=forms.TextInput(attrs={"readonly": "readonly"}), required=False
    )
    association = forms.ModelChoiceField(queryset=Association.objects.all(), required=False)
