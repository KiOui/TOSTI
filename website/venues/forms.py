from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from .models import Reservation
from .models import Venue


class ReservationForm(forms.ModelForm):
    """Reservation Form."""

    def __init__(self, *args, **kwargs):
        """Initialise Reservation Form."""
        request = kwargs.pop("request", None)
        super(ReservationForm, self).__init__(*args, **kwargs)
        self.fields["venue"].queryset = Venue.objects.filter(can_be_reserved=True)
        if request is not None and request.user.is_authenticated and request.user.profile.association is not None:
            self.fields["association"].initial = request.user.profile.association

    def clean(self):
        """
        Clean data.

        Check whether there is no overlapping Reservation.
        """
        if self.cleaned_data.get("start_time") is not None and self.cleaned_data.get("end_time") is not None:
            start_time = self.cleaned_data.get("start_time").astimezone(timezone.get_current_timezone())
            end_time = self.cleaned_data.get("end_time").astimezone(timezone.get_current_timezone())

            if (
                Reservation.objects.filter(venue=self.cleaned_data.get("venue"))
                .filter(accepted=True)
                .filter(
                    Q(start_time__lte=start_time, end_time__gt=start_time)
                    | Q(start_time__lt=end_time, end_time__gte=end_time)
                    | Q(start_time__gte=start_time, end_time__lte=end_time)
                )
                .exists()
            ):
                raise ValidationError("An overlapping reservation for this venue already exists.")

    class Meta:
        """Meta class."""

        model = Reservation
        fields = ["title", "association", "start_time", "end_time", "venue", "comment"]
