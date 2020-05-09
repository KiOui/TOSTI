from django import forms
from django.contrib.auth import get_user_model
from .models import Shift


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
        overlapping_end = Shift.objects.filter(
            end_date__gte=start_date, end_date__lte=end_date, venue=venue,
        ).count()
        if overlapping_start > 0 or overlapping_end > 0:
            raise forms.ValidationError(
                "Overlapping shifts for the same venue are not allowed."
            )

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
