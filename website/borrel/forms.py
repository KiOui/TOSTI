from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import models, DateTimeInput
from django.utils import timezone

from borrel.models import BorrelReservation, ReservationItem
from venues.models import Venue, Reservation


class BorrelReservationForm(forms.ModelForm):
    """Form to create a new borrel reservation, and venue reservation at the same time."""

    venue = forms.ModelChoiceField(
        queryset=Venue.objects.active_venues(),
        required=False,
        help_text="If you directly want to reserve a venue as well, choose it here. "
        "It will have the same start and end time.",
    )

    def __init__(self, *args, **kwargs):
        """Init the form."""
        request = kwargs.pop("request", None)
        self.user = request.user
        super().__init__(*args, **kwargs)
        # Automatically set association to user association
        if request is not None and request.user.is_authenticated and request.user.association is not None:
            self.fields["association"].initial = self.user.association

    def clean(self):
        """Validate whether a Reservation for the venue already exists."""
        venue = self.cleaned_data.get("venue", None)
        start = self.cleaned_data.get("start", None)
        end = self.cleaned_data.get("end", None)
        if venue is not None and start is not None and end is not None:
            if (
                Reservation.objects.filter(venue=venue)
                .filter(accepted=True)
                .filter(
                    Q(start__lte=start, end__gt=start)
                    | Q(start__lt=end, end__gte=end)
                    | Q(start__gte=start, end__lte=end)
                )
                .exists()
            ):
                raise ValidationError("There is already another overlapping reservation for this venue.")

    def clean_venue(self):
        """Validate the venue field."""
        venue = self.cleaned_data["venue"]
        if venue and self.cleaned_data.get("end", None) is None:
            raise ValidationError("To reserve a venue, an end time is required")
        return venue

    def clean_start(self):
        """Validate start field."""
        start = self.cleaned_data["start"]
        now = timezone.now()
        if start <= now:
            raise ValidationError("Reservation should be in the future")
        return start

    def clean_end(self):
        """Validate end field."""
        end = self.cleaned_data.get("end", None)
        start = self.cleaned_data.get("start", None)
        if start is not None and end is not None and end <= start:
            raise ValidationError("End date should be after start date")
        return end

    def save(self, commit=True):
        """Save the form."""
        value = super().save(commit)
        if (
            commit
            and self.cleaned_data.get("venue", None) is not None
            and self.cleaned_data.get("end", None) is not None
        ):
            reservation = Reservation.objects.create(
                user=self.user,
                venue=self.cleaned_data["venue"],
                start=self.cleaned_data["start"],
                end=self.cleaned_data["end"],
                title=self.cleaned_data["title"],
                association=self.cleaned_data["association"],
            )
            value.venue_reservation = reservation
            value.save()
        return value

    class Meta:
        """Meta class for the form."""

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
        help_texts = {
            "start": "When do you need your reserved items.",
            "end": "When will you return your reserved items (if applicable).",
        }


class BorrelReservationUpdateForm(forms.ModelForm):
    """Form to update borrel reservations."""

    def __init__(self, *args, **kwargs):
        """Init the form."""
        request = kwargs.pop("request", None)
        self.user = request.user
        super().__init__(*args, **kwargs)

    class Meta:
        """Meta class for the form."""

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
        """Init the form."""
        request = kwargs.pop("request", None)
        self.user = request.user
        super().__init__(*args, **kwargs)
        self.fields["title"].disabled = True
        self.fields["start"].disabled = True
        self.fields["end"].disabled = True
        self.fields["association"].disabled = True

    class Meta:
        """Meta class for the form."""

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
        """Init the form."""
        super().__init__(*args, **kwargs)
        self.fields["comments"].disabled = True


class ReservationItemForm(models.ModelForm):
    """A reservation item form that allows you to reserve products."""

    amount_after = forms.IntegerField()
    amount_before = forms.IntegerField()

    class Meta:
        """Meta class for the form."""

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
        """Init the form."""
        super().__init__(*args, **kwargs)
        self.fields["amount_reserved"].required = False

        self.fields["product"].disabled = True
        self.fields["product_name"].disabled = True
        self.fields["product_description"].disabled = True
        self.fields["product_price_per_unit"].disabled = True

        self.fields["amount_before"].disabled = True
        self.fields["amount_after"].disabled = True
        self.fields["amount_used"].disabled = True
        self.fields["amount_before"].required = False
        self.fields["amount_after"].required = False
        self.fields["amount_used"].required = False

        product = self.instance.product

        if product and not product.can_be_reserved:
            self.fields["amount_reserved"].disabled = True
            self.fields["amount_reserved"].required = False


class ReservationItemSubmissionForm(ReservationItemForm):
    """A reservation item form that only allows changing the amount_used."""

    def __init__(self, *args, **kwargs):
        """Init the form."""
        super().__init__(*args, **kwargs)
        self.fields["amount_reserved"].disabled = True

        product = self.instance.product
        if product and product.can_be_submitted:
            self.fields["amount_before"].disabled = False
            self.fields["amount_after"].disabled = False
            self.fields["amount_used"].required = True
            self.fields["amount_used"].disabled = False


class ReservationItemDisabledForm(ReservationItemForm):
    """A fully disabled form for reservation items."""

    def __init__(self, *args, **kwargs):
        """Init the form."""
        super().__init__(*args, **kwargs)
        self.fields["amount_reserved"].disabled = True
        self.fields["amount_before"].disabled = True
        self.fields["amount_after"].disabled = True
        self.fields["amount_used"].disabled = True

