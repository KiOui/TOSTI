from django import forms

from borrel.models import BorrelReservation
from venues.selectors import active_venues


class BorrelReservationRequestForm(forms.ModelForm):
    """Borrel Reservation Request Form."""

    venue = forms.ChoiceField(choices=[(None, "---------")] + [(venue.id, venue.name) for venue in active_venues()], required=False)

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
