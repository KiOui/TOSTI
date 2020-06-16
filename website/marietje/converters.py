from django.urls.converters import IntConverter
from .models import SpotifyAccount


class SpotifyAccountConverter(IntConverter):
    """Converter for SpotifyAccount model."""

    def to_python(self, value):
        """
        Cast integer to SpotifyAccount.

        :param value: the public key of the SpotifyAccount
        :return: a SpotifyAccount or ValueError
        """
        try:
            return SpotifyAccount.objects.get(id=int(value))
        except SpotifyAccount.DoesNotExist:
            raise ValueError

    def to_url(self, obj):
        """
        Cast an object of SpotifyAccount to a string.

        :param obj: the SpotifyAccount object
        :return: the public key of the SpotifyAccount object in string format
        """
        return str(obj.pk)
