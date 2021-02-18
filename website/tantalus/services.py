import requests
from django.conf import settings


class TantalusException(Exception):

    pass


class TantalusClient:

    def __init__(self):
        s = requests.session()

        r = s.post(settings.TANTALUS_ENDPOINT_URL + "login",
                   json={"username": settings.TANTALUS_USERNAME, "password": settings.TANTALUS_PASSWORD})
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise TantalusException(e)

        self._session = s
