from django import forms


class OrderForm(forms.Form):
    """Form for setting parameters."""

    product_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, product, *args, **kwargs):
        """
        Initialise the ParameterForm.

        :param parameters: a list of BaseParameter objects including the parameters to add to this form, field types are
        automatically set for the parameters
        :param args: arguments
        :param kwargs: keyword arguments
        """
        super(OrderForm, self).__init__(*args, **kwargs)
        self.fields['product_id'].initial = product.id
