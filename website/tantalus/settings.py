from settings.models import Setting
from settings.settings import settings

settings.register_setting("tantalus_endpoint_url", Setting.TYPE_STR, True)
settings.register_setting("tantalus_username", Setting.TYPE_STR, True)
settings.register_setting("tantalus_password", Setting.TYPE_STR, True)
