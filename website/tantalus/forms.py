import logging

from django import forms

from tantalus.services import get_tantalus_client, TantalusException


class TantalusProductAdminForm(forms.ModelForm):
    """Tantalus Product Admin Form."""

    tantalus_id = forms.ChoiceField(required=True)

    def __init__(self, *args, **kwargs):
        """Initialize Tantalus Product Admin Form by getting product data from Tantalus."""
        super(TantalusProductAdminForm, self).__init__(*args, **kwargs)
        try:
            tantalus_client = get_tantalus_client()
            choices = [(x["id"], x["name"]) for x in tantalus_client.get_products()]
            self.fields["tantalus_id"].choices = choices
        except TantalusException as e:
            logging.error(
                "The following Exception occurred while trying to access Tantalus on the administration "
                "dashboard: {}".format(e)
            )
            self.fields["tantalus_id"] = forms.IntegerField(
                min_value=1,
                help_text="Could not retrieve data from Tantalus, you are still able to enter the Tantalus id "
                "yourself. Check the logs for more information.",
            )


class TantalusOrderVenueAdminForm(forms.ModelForm):
    """Tantalus Order Venue Admin Form."""

    endpoint_id = forms.ChoiceField(required=True)

    def __init__(self, *args, **kwargs):
        """Initialize Tantalus Product Admin Form by getting product data from Tantalus."""
        super(TantalusOrderVenueAdminForm, self).__init__(*args, **kwargs)
        try:
            tantalus_client = get_tantalus_client()
            choices = [(x["id"], x["name"]) for x in tantalus_client.get_endpoints()]
            self.fields["endpoint_id"].choices = choices
        except TantalusException as e:
            logging.error(
                "The following Exception occurred while trying to access Tantalus on the administration "
                "dashboard: {}".format(e)
            )
            self.fields["endpoint_id"] = forms.IntegerField(
                min_value=1,
                help_text="Could not retrieve data from Tantalus, you are still able to enter the endpoint id "
                "yourself. Check the logs for more information.",
            )
