import pytz
from django import forms
from django.conf import settings
from django.forms import DateTimeInput
from guardian.shortcuts import get_objects_for_user
from constance import config

from .models import Shift, get_default_end_time_shift, get_default_start_time_shift
from datetime import datetime, timedelta

from .services import user_can_manage_shifts_in_venue


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
        timezone = pytz.timezone(settings.TIME_ZONE)
        now = timezone.localize(datetime.now())
        start_time = now - timedelta(seconds=now.second, microseconds=now.microsecond)
        self.fields["start"].initial = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        if now >= get_default_end_time_shift() or now <= get_default_start_time_shift() - timedelta(minutes=30):
            self.fields["end"].initial = (start_time + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
        self.fields["max_orders_total"].initial = config.SHIFTS_DEFAULT_MAX_ORDERS_TOTAL

    def clean_venue(self):
        """Check whether venue is has an accepted value."""
        venue = self.cleaned_data.get("venue")
        if not user_can_manage_shifts_in_venue(self.user, venue):
            raise forms.ValidationError("You don't have permissions to start a shift in this venue!")
        return venue

    class Meta:
        """Meta class."""

        model = Shift
        fields = [
            "venue",
            "start",
            "end",
            "max_orders_total",
        ]
        widgets = {
            "start": DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "end": DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }
