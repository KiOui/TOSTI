from django.urls.converters import SlugConverter, IntConverter
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
            return Player.objects.select_subclasses().get(slug=value)
        except Player.DoesNotExist:
            raise ValueError("Player does not exist")

    def to_url(self, obj):
        """
        Cast an object of Player to a string.

        :param obj: the Player object
        :return: the slug of the Player object
        """
        return obj.slug


class PlayerPKConverter(IntConverter):
    """Converter for Player model via PK."""

    def to_python(self, pk):
        """
        Cast pk to Player.

        :param pk: the pk of the Player
        :return: a Player or ValueError
        """
        try:
            return Player.objects.select_subclasses().get(pk=pk)
        except Player.DoesNotExist:
            raise ValueError("Player does not exist")

    def to_url(self, obj):
        """
        Cast an object of Player to a string.

        :param obj: the Player object
        :return: the pk of the Player object
        """
        return obj.pk
