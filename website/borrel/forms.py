from django import forms

from borrel.models import ReservationRequest
from venues.models import Venue


class ReservationRequestForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super(ReservationRequestForm, self).__init__(*args, **kwargs)
        self.fields['venue'].queryset = Venue.objects.filter(can_be_reserved=True)
        if request is not None and request.user.is_authenticated and request.user.profile.association is not None:
            self.fields['association'].initial = request.user.profile.association

    class Meta:
        model = ReservationRequest
        fields = ["title", "association", "start_time", "end_time", "venue", "comment"]
