from django.urls.converters import SlugConverter
from .models import Player


class PlayerConverter(SlugConverter):
    """Converter for Player model."""

    def to_python(self, value):
        """
        Cast slug to Player.

        :param value: the slug of the Player
        :return: a Player or ValueError
        """
        try:
            return Player.objects.get(slug=value)
        except Player.DoesNotExist:
            raise ValueError

    def to_url(self, obj):
        """
        Cast an object of Player to a string.

        :param obj: the Player object
        :return: the slug of the Player object
        """
        return obj.slug
