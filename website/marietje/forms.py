from django import forms
from .models import SpotifySettings


class SpotifyTokenForm(forms.Form):
    """Form for Spotify Client ID."""

    client_id = forms.CharField(required=True, label="Client ID")
    client_secret = forms.CharField(required=True, label="Client Secret")


class SpotifySettingsAdminForm(forms.ModelForm):
    """Form for the administration of Spotify Settings."""

    playback_device_id = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        """
        Initialise SpotifySettingsAdminForm.

        :param args: arguments
        :param kwargs: keyword arguments
        """
        super(SpotifySettingsAdminForm, self).__init__(*args, **kwargs)
        instance = kwargs.get("instance", None)
        if instance is not None:
            try:
                devices = instance.spotify.devices()
                self.fields["playback_device_id"].choices = [
                    (x["id"], x["name"]) for x in devices["devices"]
                ]
            except Exception:
                self.fields["playback_device_id"] = forms.CharField(
                    disabled=True,
                    required=False,
                    help_text="Unable to change devices as there was an error loading the playable devices",
                )
                if instance.playback_device_id is not None:
                    self.initial["playback_device_id"] = (instance.playback_device_id,)
                else:
                    self.initial["playback_device_id"] = "No device selected"

    class Meta:
        """Meta class."""

        model = SpotifySettings
        fields = "__all__"
