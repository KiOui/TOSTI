from django import forms


class SpotifyTokenForm(forms.Form):
    """Form for Spotify Client ID."""

    client_id = forms.CharField(required=True, label="Client ID")
    client_secret = forms.CharField(required=True, label="Client Secret")
