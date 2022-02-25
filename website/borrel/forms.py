from django import forms
from django.forms import models

from borrel.models import BorrelReservation, ReservationItem
from venues.models import Venue


class BorrelReservationRequestForm(forms.ModelForm):
    """Borrel Reservation Request Form."""

    venue = forms.ChoiceField(
        choices=[(None, "---------")] + [(venue.id, venue.name) for venue in Venue.objects.active_venues()],
        required=False,
    )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        super(BorrelReservationRequestForm, self).__init__(*args, **kwargs)

        self.fields["start"].widget.input_type = "datetime-local"
        self.fields["end"].widget.input_type = "datetime-local"

        # Automatically set Association
        if request is not None and request.user.is_authenticated and request.user.profile.association is not None:
            self.fields["association"].initial = request.user.profile.association

    class Meta:
        model = BorrelReservation
        fields = ["venue", "title", "association", "start", "end", "comments"]
        widgets = {
            "comments": forms.Textarea(
                attrs={
                    "rows": 2,
                }
            ),
        }


class ReservationItemForm(models.ModelForm):
    class Meta:
        model = ReservationItem
        fields = ["product", "amount_reserved"]


class ReservationItemSubmissionForm(models.ModelForm):
    class Meta:
        model = ReservationItem
        fields = ["product", "amount_reserved", "amount_used"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["amount_reserved"].disabled = True
