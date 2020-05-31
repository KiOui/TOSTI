from django import forms
from .models import SpotifySettings


class SpotifyTokenForm(forms.Form):
    """Form for Spotify Client ID."""

    client_id = forms.CharField(required=True, label="Client ID")
    client_secret = forms.CharField(required=True, label="Client Secret")


class SpotifySettingsAdminForm(forms.ModelForm):
    """Form for the administration of Spotify Settings."""

    playback_device_id = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        """
        Initialise SpotifySettingsAdminForm.

        :param args: arguments
        :param kwargs: keyword arguments
        """
        super(SpotifySettingsAdminForm, self).__init__(*args, **kwargs)
        instance = kwargs.get("instance", None)
        if instance is not None:
            self.__original_playback_device_id = instance.playback_device_id
            try:
                devices = instance.spotify.devices()
                choices = [(x["id"], x["name"]) for x in devices["devices"]]
                if (
                    instance.playback_device_id is not None
                    and instance.playback_device_id not in [x for (x, _) in choices]
                ):
                    choices.append(
                        (
                            instance.playback_device_id,
                            "{} (currently offline)".format(
                                instance.playback_device_name
                            ),
                        )
                    )
                    self.fields[
                        "playback_device_id"
                    ].help_text = "The currently selected device appears to be offline."
                choices = [("", "----------")] + choices
                self.fields["playback_device_id"].choices = choices
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
        else:
            self.__original_playback_device_id = None

    def clean_playback_device_id(self):
        """
        Clean playback device id.

        :return: the device id, or None if the device id is empty
        """
        device_id = self.cleaned_data.get("playback_device_id")
        if device_id == "":
            return None
        else:
            return device_id

    def save(self, commit=True):
        """
        Save this form.

        :param commit: whether or not to call the save method
        :return: an object of type SpotifySettings
        """
        obj = super(SpotifySettingsAdminForm, self).save(commit=False)
        if (
            obj.playback_device_id is not None
            and self.__original_playback_device_id != obj.playback_device_id
        ):
            devices = {x["id"]: x["name"] for x in obj.spotify.devices()["devices"]}
            if obj.playback_device_id not in devices.keys():
                raise forms.ValidationError(
                    "{} is not a valid device (it might have gone offline).".format(
                        obj.playback_device_id
                    )
                )
            else:
                obj.playback_device_name = devices[obj.playback_device_id]
        elif obj.playback_device_id is None:
            obj.playback_device_name = None
        if commit:
            obj.save()
        return obj

    class Meta:
        """Meta class."""

        model = SpotifySettings
        exclude = ["playback_device_name"]
