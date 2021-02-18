import requests
from django import forms
from django.conf import settings


class TantalusProductAdminForm(forms.ModelForm):

    tantalus_id = forms.ChoiceField(required=True)

    def __init__(self, *args, **kwargs):
        super(TantalusProductAdminForm, self).__init__(*args, **kwargs)
        s = requests.session()

        r = s.post(settings.TANTALUS_ENDPOINT_URL + "login",
                   json={"username": settings.TANTALUS_USERNAME, "password": settings.TANTALUS_PASSWORD})
        try:
            r.raise_for_status()
            r = s.get(settings.TANTALUS_ENDPOINT_URL + "products")
            r.raise_for_status()
            print(r.json())
        except requests.HTTPError as e:
            pass
