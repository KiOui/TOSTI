from django import forms
from django.forms.widgets import Select

from tampon.models import TamponNotification, Room, Restock, StockData


class FloorSelect(Select):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._room_cache = {}

    def set_room_cache(self, queryset):
        """Cache all Room instances from the queryset once."""
        self._room_cache = {room.id: room for room in queryset}

    def create_option(self, name, value, label, selected, index, **kwargs):
        option = super().create_option(name, value, label, selected, index, **kwargs)
        # Use cached instance instead of DB lookup
        if value and value in self._room_cache:
            room = self._room_cache[value]
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
        # Update widget cache when queryset changes
        room_widget = self.fields["room"].widget
        if isinstance(room_widget, FloorSelect):
            room_widget.set_room_cache(self.fields["room"].queryset)

    def __init__(self, *args, **kwargs):
        """Only show active rooms and cache them in the widget."""
        super().__init__(*args, **kwargs)
        self.filter_room(room_id=None)
        # Cache the room queryset in the widget to avoid N+1 queries
        room_widget = self.fields["room"].widget
        if isinstance(room_widget, FloorSelect):
            room_widget.set_room_cache(self.fields["room"].queryset)


class ResolveForm(forms.Form):
    def __init__(self, *args, **kwargs):
        """Dynamically create fields for each StockData item."""
        super().__init__(*args, **kwargs)
        for stock in StockData.objects.all():
            self.fields[f"stock_{stock.id}"] = forms.IntegerField(
                label=stock.name,
                initial=stock.restock_default,
                min_value=0,
                widget=forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "placeholder": f"Enter amount for {stock.name}",
                    }
                ),
            )
