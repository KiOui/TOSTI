from django import forms
from django.forms import inlineformset_factory

from borrel.models import BorrelReservation, ReservationItem


class BorrelReservationRequestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        super(BorrelReservationRequestForm, self).__init__(*args, **kwargs)
        if request is not None and request.user.is_authenticated and request.user.profile.association is not None:
            self.fields["association"].initial = request.user.profile.association

    class Meta:
        model = BorrelReservation
        fields = ["title", "association", "start", "end", "comments"]
        widgets = {
            "comments": forms.Textarea(
                attrs={
                    "rows": 2,
                }
            ),
        }


class BorrelReservationItemForm(forms.ModelForm):
    class Meta:
        model = ReservationItem
        fields = ["product", "amount_reserved"]


BorrelReservationFormset = inlineformset_factory(
    parent_model=BorrelReservation,
    model=ReservationItem,
    form=BorrelReservationItemForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
