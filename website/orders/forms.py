import pytz
from django import forms
from django.conf import settings
from guardian.shortcuts import get_objects_for_user

from users.models import User
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

        all_assignees = set()
        for v in self.fields["venue"].queryset:
            all_assignees.update([x.pk for x in v.get_users_with_shift_admin_perms()])

        all_assignees = User.objects.filter(pk__in=all_assignees)

        self.fields["assignees"].queryset = all_assignees.order_by("first_name", "last_name")

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
        Clean the CreateShiftForm.

        Makes sure that the dates in the form are not overlapping with other shifts.
        :return: cleaned data
        """
        cleaned_data = super(CreateShiftForm, self).clean()
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
            "assignees",
        ]
