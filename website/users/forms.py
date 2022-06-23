from django import forms

from associations.models import Association


class AccountForm(forms.Form):
    """Form for showing account details."""

    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={"readonly": "readonly"}),
        required=False,
    )
    name = forms.CharField(label="Name", widget=forms.TextInput(attrs={"readonly": "readonly"}), required=False)
    email = forms.EmailField(
        label="Email address", widget=forms.TextInput(attrs={"readonly": "readonly"}), required=False
    )
    association = forms.ModelChoiceField(queryset=Association.objects.all(), required=False)
