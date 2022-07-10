from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.admin.options import get_content_type_for_model


from django.forms import model_to_dict


class ModelDiffCalculator:
    """Get the diff of a model."""

    def __init__(self, initial):
        """Initialize the diff calculator."""
        self.__initial = self._dict(initial)
        self._new_object = None

    def set_changed_model(self, new_object):
        """Set the new object and calculate the diff."""
        data = self._dict(new_object)
        if self._new_object is not None:
            self.__initial = data
        self._new_object = data
        return self

    @property
    def diff(self):
        """Get the diff of the model."""
        if not self._new_object:
            return {}
        d1 = self.__initial
        d2 = self._new_object
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        return dict(diffs)

    @property
    def has_changed(self):
        """Return True if the model has changed."""
        return bool(self.diff)

    @property
    def changed_fields(self):
        """Get the changed fields."""
        return list(self.diff.keys())

    def get_field_diff(self, field_name):
        """Get the diff of a field."""
        return self.diff.get(field_name, None)

    def _dict(self, model):
        """Get the dict of a model."""
        return model_to_dict(model, fields=[field.name for field in model._meta.fields])


def log_action(user, object, flag=ADDITION, message=None):
    """Create an admin log."""
    return LogEntry.objects.log_action(
        user_id=user.pk,
        content_type_id=get_content_type_for_model(object).pk,
        object_id=object.pk,
        object_repr=str(object),
        action_flag=flag,
        change_message=message,
    )
