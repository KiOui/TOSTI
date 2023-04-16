from django import forms

from silvasoft.models import CachedRelation, CachedProduct


class SilvasoftAssociationAdminForm(forms.ModelForm):
    """Silvasoft Association Admin Form."""

    silvasoft_customer_number = forms.ChoiceField(required=True)

    def __init__(self, *args, **kwargs):
        """Initialize Silvasoft Association Admin Form."""
        super(SilvasoftAssociationAdminForm, self).__init__(*args, **kwargs)
        if CachedRelation.objects.all().count() == 0:
            self.fields["silvasoft_customer_number"] = forms.IntegerField(
                min_value=1,
                help_text="There are no relations from Silvasoft registered in T.O.S.T.I. Please press the"
                " 'Refresh relations' button at the bottom of the screen.",
            )
        else:
            choices = [(x.customer_number, x.name) for x in CachedRelation.objects.all()]
            self.fields["silvasoft_customer_number"].choices = choices
            self.fields["silvasoft_customer_number"].help_text = (
                "The relations displayed here are cached in "
                "T.O.S.T.I. If you want to refresh these relations, "
                "please press the 'Refresh relations' button at the "
                "bottom of the screen."
            )


class SilvasoftOrderVenueAdminForm(forms.ModelForm):
    """Silvasoft Order Venue Admin Form."""

    silvasoft_customer_number = forms.ChoiceField(required=True)

    def __init__(self, *args, **kwargs):
        """Initialize Silvasoft Order Venue Admin Form."""
        super(SilvasoftOrderVenueAdminForm, self).__init__(*args, **kwargs)
        if CachedRelation.objects.all().count() == 0:
            self.fields["silvasoft_customer_number"] = forms.IntegerField(
                min_value=1,
                help_text="There are no relations from Silvasoft registered in T.O.S.T.I. Please press the"
                " 'Refresh relations' button at the bottom of the screen.",
            )
        else:
            choices = [(x.customer_number, x.name) for x in CachedRelation.objects.all()]
            self.fields["silvasoft_customer_number"].choices = choices
            self.fields["silvasoft_customer_number"].help_text = (
                "The relations displayed here are cached in "
                "T.O.S.T.I. If you want to refresh these relations, "
                "please press the 'Refresh relations' button at the "
                "bottom of the screen."
            )


class SilvasoftOrderProductAdminForm(forms.ModelForm):
    """Silvasoft Order Product Admin Form."""

    silvasoft_product_number = forms.ChoiceField(required=True)

    def __init__(self, *args, **kwargs):
        """Initialize Silvasoft Order Product Admin."""
        super(SilvasoftOrderProductAdminForm, self).__init__(*args, **kwargs)
        if CachedProduct.objects.all().count() == 0:
            self.fields["silvasoft_product_number"] = forms.IntegerField(
                min_value=1,
                help_text="There are no products from Silvasoft registered in T.O.S.T.I. Please press the"
                " 'Refresh products' button at the bottom of the screen.",
            )
        else:
            choices = [(x.product_number, x.name) for x in CachedProduct.objects.all()]
            self.fields["silvasoft_product_number"].choices = choices
            self.fields["silvasoft_product_number"].help_text = (
                "The products displayed here are cached in "
                "T.O.S.T.I. If you want to refresh these products, "
                "please press the 'Refresh products' button at the "
                "bottom of the screen."
            )


class SilvasoftBorrelProductAdminForm(forms.ModelForm):
    """Silvasoft Borrel Product Admin Form."""

    silvasoft_product_number = forms.ChoiceField(required=True)

    def __init__(self, *args, **kwargs):
        """Initialize Silvasoft Borrel Product Admin."""
        super(SilvasoftBorrelProductAdminForm, self).__init__(*args, **kwargs)
        if CachedProduct.objects.all().count() == 0:
            self.fields["silvasoft_product_number"] = forms.IntegerField(
                min_value=1,
                help_text="There are no products from Silvasoft registered in T.O.S.T.I. Please press the"
                " 'Refresh products' button at the bottom of the screen.",
            )
        else:
            choices = [(x.product_number, x.name) for x in CachedProduct.objects.all()]
            self.fields["silvasoft_product_number"].choices = choices
            self.fields["silvasoft_product_number"].help_text = (
                "The products displayed here are cached in "
                "T.O.S.T.I. If you want to refresh these products, "
                "please press the 'Refresh products' button at the "
                "bottom of the screen."
            )
