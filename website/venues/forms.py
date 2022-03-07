from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import DateTimeInput
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

    def clean_start(self):
        """Validate the start field."""
        start = self.cleaned_data.get("start")
        now = timezone.now()
        if start <= now:
            raise ValidationError("Reservation should be in the future")
        return start

    def clean(self):
        """
        Clean data.

        Check whether there is no overlapping Reservation.
        """
        if self.cleaned_data.get("start") is not None and self.cleaned_data.get("end") is not None:
            start = self.cleaned_data.get("start").astimezone(timezone.get_current_timezone())
            end = self.cleaned_data.get("end").astimezone(timezone.get_current_timezone())

            if (
                Reservation.objects.filter(venue=self.cleaned_data.get("venue"))
                .filter(accepted=True)
                .filter(
                    Q(start__lte=start, end__gt=start)
                    | Q(start__lt=end, end__gte=end)
                    | Q(start__gte=start, end__lte=end)
                )
                .exists()
            ):
                raise ValidationError("An overlapping reservation for this venue already exists.")

    class Meta:
        """Meta class."""

        model = Reservation
        fields = ["venue", "association", "start", "end", "title", "comment"]
        widgets = {
            "start": DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "end": DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }
