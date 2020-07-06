import pytz
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Shift, get_default_end_time_shift, get_default_start_time_shift
from datetime import datetime, timedelta


User = get_user_model()


class ShiftForm(forms.ModelForm):
    """Shift creation form."""

    def __init__(self, *args, venue=None, **kwargs):
        """
        Initialise the ProductForm.

        :param product: the product to order in this form
        :param args: arguments
        :param kwargs: keyword arguments
        """
        super(ShiftForm, self).__init__(*args, **kwargs)
        self.fields["venue"].initial = venue
        self.fields["assignees"].queryset = User.objects.filter(is_staff=True)
        timezone = pytz.timezone(settings.TIME_ZONE)
        now = timezone.localize(datetime.now())
        start_time = now - timedelta(seconds=now.second, microseconds=now.microsecond)
        self.fields["start_date"].initial = start_time
        if now >= get_default_end_time_shift() or now <= get_default_start_time_shift() - timedelta(minutes=30):
            self.fields["end_date"].initial = start_time + timedelta(hours=1)

    def set_initial_users(self, users):
        """
        Set the assignees initial field.

        :param users: the initial users to select
        :return: None
        """
        self.fields["assignees"].initial = users

    def clean(self):
        """
        Clean the ShiftForm.

        Makes sure that the dates in the form are not overlapping with other shifts.
        :return: cleaned data
        """
        cleaned_data = super(ShiftForm, self).clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        venue = cleaned_data.get("venue")
        overlapping_start = Shift.objects.filter(
            start_date__gte=start_date, start_date__lte=end_date, venue=venue,
        ).count()
        overlapping_end = Shift.objects.filter(end_date__gte=start_date, end_date__lte=end_date, venue=venue,).count()
        if overlapping_start > 0 or overlapping_end > 0:
            raise forms.ValidationError("Overlapping shifts for the same venue are not allowed.")

        return cleaned_data

    class Meta:
        """Meta class."""

        model = Shift
        fields = [
            "venue",
            "start_date",
            "end_date",
            "assignees",
        ]
