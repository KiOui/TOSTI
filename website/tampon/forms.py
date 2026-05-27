from django import forms
from django.forms.widgets import Select

from tampon.models import TamponNotification, Room, Restock, StockData


class FloorSelect(Select):
    def create_option(self, name, value, label, selected, index, **kwargs):
        option = super().create_option(name, value, label, selected, index, **kwargs)
        if value:
            room = Room.objects.get(pk=int(str(value)))
            option["attrs"]["data-floor_number"] = room.floor_number
        return option


class TamponNotificationForm(forms.ModelForm):
    """Form for submitting T.A.M.P.O.N. notifications."""

    class Meta:
        model = TamponNotification
        fields = (
            "room",
            "notification_text",
        )
        widgets = {
            "room": FloorSelect(attrs={"class": "form-control"}),
            "notification_text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter notification text",
                }
            ),
        }
        labels = {
            "room": "Dispenser location",
            "notification_text": "Notification text",
        }

    def filter_room(self, room_id):
        """Filter the room queryset based on the provided room_id."""
        self.fields["room"].queryset = (
            Room.objects.filter(id=room_id, active=True)
            if room_id
            else Room.objects.filter(active=True).order_by(
                "floor_number",
                "room_number",
            )
        )
        self.fields["room"].empty_label = "Select a dispenser location"

    def __init__(self, *args, **kwargs):
        """Only show active rooms."""
        super().__init__(*args, **kwargs)
        self.filter_room(room_id=None)


class ResolveForm(forms.Form):
    def __init__(self, *args, **kwargs):
        """Dynamically create fields for each StockData item."""
        super().__init__(*args, **kwargs)
        for stock in StockData.objects.all():
            self.fields[f"stock_{stock.id}"] = forms.IntegerField(
                label=stock.name,
                initial=stock.restock_default,
                widget=forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "placeholder": f"Enter amount for {stock.name}",
                    }
                ),
            )
