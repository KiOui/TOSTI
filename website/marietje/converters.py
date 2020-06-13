from django.urls.converters import IntConverter
from .models import SpotifySettings


class SpotifyAuthCodeConverter(IntConverter):
    """Converter for SpotifyAuthCode model."""

    def to_python(self, value):
        """
        Cast integer to SpotifyAuthCode.

        :param value: the public key of the SpotifyAuthCode
        :return: a SpotifyAuthCode or ValueError
        """
        try:
            return SpotifySettings.objects.get(id=int(value))
        except SpotifySettings.DoesNotExist:
            raise ValueError

    def to_url(self, obj):
        """
        Cast an object of SpotifyAuthCode to a string.

        :param obj: the SpotifyAuthCode object
        :return: the public key of the SpotifyAuthCode object in string format
        """
        return str(obj.pk)