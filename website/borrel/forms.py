from django import forms
from django.core.exceptions import ValidationError
from django.forms import models, DateTimeInput

from borrel.models import BorrelReservation, ReservationItem
from venues.models import Venue
from venues.services import add_reservation


class BorrelReservationRequestForm(forms.ModelForm):
    """Form to create a new borrel reservation, and venue reservation at the same time."""

    venue = forms.ChoiceField(
        choices=[(None, "---------")] + [(venue.id, venue.name) for venue in Venue.objects.active_venues()],
        required=False,
        help_text="Also reserve the venue for this period. Not required if no venue is used.",
    )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        self.user = request.user
        super().__init__(*args, **kwargs)
        # Automatically set association to user association
        if request is not None and request.user.is_authenticated and request.user.profile.association is not None:
            self.fields["association"].initial = self.user.profile.association

    def clean_venue(self):
        venue = self.cleaned_data["venue"]
        if venue and not self.cleaned_data["start"] and self.cleaned_data["end"]:
            raise ValidationError("To reserve a venue, both end and start time are required ")
        return venue

    def save(self, commit=True):
        value = super().save(commit)
        if commit and self.cleaned_data["venue"] and self.cleaned_data["start"] and self.cleaned_data["end"]:
            add_reservation(
                user=self.user,
                venue=Venue.objects.get(id=self.cleaned_data["venue"]),
                start=self.cleaned_data["start"],
                end=self.cleaned_data["end"],
                title=self.cleaned_data["title"],
            )
        return value

    class Meta:
        model = BorrelReservation
        fields = ["title", "association", "start", "end", "comments"]
        widgets = {
            "comments": forms.Textarea(
                attrs={
                    "rows": 2,
                }
            ),
            "start": DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "end": DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }


class BorrelReservationUpdateForm(forms.ModelForm):
    """Form to update borrel reservations."""

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        self.user = request.user
        super().__init__(*args, **kwargs)

    class Meta:
        model = BorrelReservation
        fields = ["title", "association", "start", "end", "comments"]
        widgets = {
            "comments": forms.Textarea(
                attrs={
                    "rows": 2,
                }
            ),
            "start": DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "end": DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }


class BorrelReservationSubmissionForm(forms.ModelForm):
    """A reservation form that only allows changing the remarks."""

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        self.user = request.user
        super().__init__(*args, **kwargs)
        self.fields["title"].disabled = True
        self.fields["start"].disabled = True
        self.fields["end"].disabled = True
        self.fields["association"].disabled = True

    class Meta:
        model = BorrelReservation
        fields = ["title", "association", "start", "end", "comments"]
        widgets = {
            "comments": forms.Textarea(
                attrs={
                    "rows": 2,
                }
            ),
            "start": DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "end": DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }


class BorrelReservationDisabledForm(BorrelReservationSubmissionForm):
    """A fully disabled form for reservations."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["comments"].disabled = True


class ReservationItemForm(models.ModelForm):
    """A reservation item form that allows you to reserve products."""

    class Meta:
        model = ReservationItem
        fields = [
            "product",
            "product_name",
            "product_description",
            "product_price_per_unit",
            "amount_reserved",
            "amount_used",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["amount_reserved"].required = False

        self.fields["product"].disabled = True
        self.fields["product_name"].disabled = True
        self.fields["product_description"].disabled = True
        self.fields["product_price_per_unit"].disabled = True

        self.fields["amount_used"].disabled = True


class ReservationItemSubmissionForm(ReservationItemForm):
    """A reservation item form that only allows changing the amount_used."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["amount_reserved"].disabled = True
        self.fields["amount_used"].required = True
        self.fields["amount_used"].disabled = False


class ReservationItemDisabledForm(ReservationItemForm):
    """A fully disabled form for reservation items."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["amount_reserved"].disabled = True
        self.fields["amount_used"].disabled = True
