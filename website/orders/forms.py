import pytz
from django import forms
from django.conf import settings
from guardian.shortcuts import get_objects_for_user

from .models import Shift, get_default_end_time_shift, get_default_start_time_shift
from datetime import datetime, timedelta


class CreateShiftForm(forms.ModelForm):
    """Shift creation form."""

    def __init__(self, *args, user, venue=None, **kwargs):
        """
        Initialise the CreateShiftForm.

        :param product: the product to order in this form
        :param args: arguments
        :param kwargs: keyword arguments
        """
        super(CreateShiftForm, self).__init__(*args, **kwargs)
        self.user = user
        self.fields["venue"].initial = venue
        self.fields["venue"].queryset = get_objects_for_user(self.user, "orders.can_manage_shift_in_venue")

        self.fields["start_date"].widget.input_type = "datetime-local"
        self.fields["end_date"].widget.input_type = "datetime-local"

        timezone = pytz.timezone(settings.TIME_ZONE)
        now = timezone.localize(datetime.now())
        start_time = now - timedelta(seconds=now.second, microseconds=now.microsecond)
        self.fields["start_date"].initial = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        if now >= get_default_end_time_shift() or now <= get_default_start_time_shift() - timedelta(minutes=30):
            self.fields["end_date"].initial = (start_time + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")

    def clean_venue(self):
        """Check whether venue is has an accepted value."""
        venue = self.cleaned_data["venue"]
        if self.user not in venue.get_users_with_shift_admin_perms():
            raise forms.ValidationError("You don't have permissions to start a shift in this venue!")
        return venue

    class Meta:
        """Meta class."""

        model = Shift
        fields = [
            "venue",
            "start_date",
            "end_date",
        ]
