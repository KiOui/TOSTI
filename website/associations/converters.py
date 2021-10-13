from django.urls.converters import IntConverter

from .models import Association


class AssociationConverter(IntConverter):
    """Converter for Association model."""

    def to_python(self, value):
        """
        Cast integer to Association.

        :param value: the primary key of the Association
        :return: a Association or ValueError
        """
        try:
            return Association.objects.get(pk=int(value))
        except Association.DoesNotExist:
            raise ValueError

    def to_url(self, obj):
        """
        Cast an object of Association to a string.

        :param obj: the Association object
        :return: the primary key of the Association object in string format
        """
        return str(obj.pk)
