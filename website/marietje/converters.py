from django.urls.converters import IntConverter
from .models import Player


class PlayerConverter(IntConverter):
    """Converter for Player model."""

    def to_python(self, value):
        """
        Cast integer to Player.

        :param value: the primary key of the Player
        :return: a Player or ValueError
        """
        try:
            return Player.objects.get(id=int(value))
        except Player.DoesNotExist:
            raise ValueError

    def to_url(self, obj):
        """
        Cast an object of Player to a string.

        :param obj: the Player object
        :return: the primary key of the Player object in string format
        """
        return str(obj.pk)
