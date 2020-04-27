from django import forms


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
        self.fields['product_id'].initial = product.id


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
        self.fields['order_id'].initial = order.id
