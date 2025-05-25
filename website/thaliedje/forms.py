from django import forms
from .models import Player, ThaliedjeControlEvent


class SpotifyTokenForm(forms.Form):
    """Admin Form for the Spotify API Client ID and Secret of a Player."""

    client_id = forms.CharField(required=True, label="Client ID")
    client_secret = forms.CharField(required=True, label="Client Secret")


class PlayerAdminForm(forms.ModelForm):
    """Custom admin form to manage configuration settings of a Player."""

    playback_device_id = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        """
        Initialise PlayerAdminForm (request playback devices and present a device-picker).

        :param args: arguments
        :param kwargs: keyword arguments
        """
        super(PlayerAdminForm, self).__init__(*args, **kwargs)
        instance = kwargs.get("instance", None)
        if instance is not None:
            self.__original_playback_device_id = instance.playback_device_id
            try:
                devices = instance.spotify.devices()
                choices = [(x["id"], x["name"]) for x in devices["devices"]]
                if (
                    instance.playback_device_id != ""
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
                    self.fields["playback_device_id"].help_text = (
                        "The currently selected device appears to be offline."
                    )
                if len(choices) == 0 and instance.playback_device_id == "":
                    self.fields["playback_device_id"].help_text = (
                        "No online Spotify clients were found."
                    )
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

    def save(self, commit=True):
        """
        Save this form.

        :param commit: whether or not to call the save method
        :return: an object of type Player
        """
        obj = super(PlayerAdminForm, self).save(commit=False)
        if (
            obj.playback_device_id != ""
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
        elif obj.playback_device_id == "":
            obj.playback_device_name = ""
        if commit:
            obj.save()
        return obj

    class Meta:
        """Meta class."""

        model = Player
        exclude = ["playback_device_name"]


class ThaliedjeControlEventForm(forms.ModelForm):
    """Form for ThaliedjeControlEvent."""

    class Meta:
        """Meta class."""

        model = ThaliedjeControlEvent
        fields = [
            "association_can_request",
            "association_can_control",
            "association_can_request_playlist",
            "selected_users_can_request",
            "selected_users_can_control",
            "selected_users_can_request_playlist",
            "everyone_can_request",
            "everyone_can_control",
            "everyone_can_request_playlist",
            "respect_blacklist",
            "check_throttling",
        ]

    def __init__(self, *args, **kwargs):
        """Initialise ThaliedjeControlEventForm."""
        super().__init__(*args, **kwargs)
        self.fields["association_can_request"].label = "Request songs"
        self.fields["association_can_control"].label = "Control player"
        self.fields["association_can_request_playlist"].label = "Request playlists"
        self.fields["selected_users_can_request"].label = "Request songs"
        self.fields["selected_users_can_control"].label = "Control player"
        self.fields["selected_users_can_request_playlist"].label = "Request playlists"
        self.fields["everyone_can_request"].label = "Request songs"
        self.fields["everyone_can_control"].label = "Control player"
        self.fields["everyone_can_request_playlist"].label = "Request playlists"
        self.fields["respect_blacklist"].label = "Respect blacklist"
        self.fields["check_throttling"].label = "Check throttling"
