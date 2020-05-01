from django import forms
from .models import Shift


class ProductForm(forms.Form):
    """Form for ordering products."""

    product_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, product, *args, **kwargs):
        """
        Initialise the ProductForm.

        :param product: the product to order in this form
        :param args: arguments
        :param kwargs: keyword arguments
        """
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields["product_id"].initial = product.id


class OrderRemoveForm(forms.Form):
    """Order remove form."""

    order_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, order, *args, **kwargs):
        """
        Initialise the OrderRemoveForm.

        :param order: the order to remove in this form
        :param args: arguments
        :param kwargs: keyword arguments
        """
        super(OrderRemoveForm, self).__init__(*args, **kwargs)
        self.fields["order_id"].initial = order.id


class ShiftForm(forms.ModelForm):
    """Shift creation form."""

    def clean(self):
        """
        Clean the ShiftForm.

        Makes sure that the dates in the form are not overlapping with other shifts.
        :return: cleaned data
        """
        cleaned_data = super(ShiftForm, self).clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        venue = cleaned_data.get("venue")
        overlapping_start = Shift.objects.filter(
            start_date__gte=start_date, start_date__lte=end_date, venue=venue,
        ).count()
        overlapping_end = Shift.objects.filter(
            end_date__gte=start_date, end_date__lte=end_date, venue=venue,
        ).count()
        if overlapping_start > 0 or overlapping_end > 0:
            raise forms.ValidationError(
                "Overlapping shifts for the same venue are not allowed."
            )

        return cleaned_data

    class Meta:
        """Meta class."""

        model = Shift
        fields = [
            "venue",
            "start_date",
            "end_date",
            "orders_allowed",
            "max_orders_per_user",
            "max_orders_total",
            "assignees",
        ]
