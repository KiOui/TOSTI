from django import forms

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

    class Meta:
        """Meta class."""

        model = Reservation
        fields = ["title", "association", "start_time", "end_time", "venue", "comment"]
