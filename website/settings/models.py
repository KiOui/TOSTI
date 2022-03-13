from django.core.exceptions import ValidationError
from django.db import models


class Setting(models.Model):
    """Setting model."""

    TYPE_INT = 1
    TYPE_STR = 2
    TYPE_FLOAT = 3

    TYPE_INT_TEXT = "integer"
    TYPE_STR_TEXT = "string"
    TYPE_FLOAT_TEXT = "float"

    TYPES = (
        (TYPE_INT, TYPE_INT_TEXT),
        (TYPE_STR, TYPE_STR_TEXT),
        (TYPE_FLOAT, TYPE_FLOAT_TEXT),
    )

    slug = models.SlugField(max_length=100, unique=True)
    value = models.TextField(null=True, blank=True)
    type = models.PositiveIntegerField(choices=TYPES, default=TYPE_STR)
    nullable = models.BooleanField(default=False)

    @staticmethod
    def convert_index_to_type(index: int):
        """Convert a type index to a type string."""
        if index == Setting.TYPE_INT:
            return Setting.TYPE_INT_TEXT
        elif index == Setting.TYPE_STR:
            return Setting.TYPE_STR_TEXT
        elif index == Setting.TYPE_FLOAT:
            return Setting.TYPE_FLOAT_TEXT
        else:
            raise ValueError("Index {} not registered as a valid type".format(index))

    def clean(self):
        """Check if value is not None when setting is not nullable."""
        if not self.nullable and self.value is None:
            raise ValidationError("When setting is not nullable, a value should be specified.")
        return super(Setting, self).clean()

    def get_value(self):
        """Get the value cast to correct type."""
        if self.nullable and self.value is None:
            return None

        if self.type == self.TYPE_INT:
            return int(self.value)
        elif self.type == self.TYPE_FLOAT:
            return float(self.value)
        else:
            return str(self.value)

    def set_value(self, value):
        """Set value."""
        if value is None and self.nullable:
            self.value = None
        elif type(value) == int and self.type == self.TYPE_INT:
            self.value = str(value)
        elif type(value) == str and self.type == self.TYPE_STR:
            self.value = str(value)
        elif type(value) == float and self.type == self.TYPE_FLOAT:
            self.value = str(value)
        else:
            raise TypeError(
                "Type of {} is {} but {} given".format(
                    self.slug, Setting.convert_index_to_type(self.type), type(value)
                )
            )

    def __str__(self):
        """Convert this object to string."""
        return self.slug
