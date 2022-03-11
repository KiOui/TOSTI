from . import models


class RegisteredSetting:
    """Registered Setting."""

    def __init__(self, slug: str, setting_type: int, nullable: bool, default_value):
        """Initialize Registered Setting."""
        if not nullable and default_value is None:
            raise Exception("{} is not nullable but does not have a default value.".format(slug))

        self.slug = slug
        self.setting_type = setting_type
        self.nullable = nullable
        self.default_value = default_value


class Settings:
    """
    Generic Settings class.

    This class holds all settings registered.
    """

    def __init__(self):
        """Initialize."""
        self.settings = {}

    @staticmethod
    def _change_nullable(setting: models.Setting, nullable: bool, default_value):
        """Change nullable value of setting."""
        if setting.nullable != nullable:
            if setting.nullable and not nullable:
                if setting.get_value() is None:
                    setting.set_value(default_value)
            setting.nullable = nullable
            setting.save()

    @staticmethod
    def _create_setting(slug, setting_type, nullable, default_value):
        """Create a new setting."""
        setting = models.Setting.objects.create(slug=slug, type=setting_type, nullable=nullable, value="")
        try:
            setting.set_value(default_value)
        except TypeError as e:
            setting.delete()
            raise e
        setting.save()
        return setting

    @staticmethod
    def test_type(setting_type, value):
        """Test whether a type matches the provided one."""
        if type(value) == int and setting_type == models.Setting.TYPE_INT:
            return True
        elif type(value) == str and setting_type == models.Setting.TYPE_STR:
            return True
        elif type(value) == float and setting_type == models.Setting.TYPE_FLOAT:
            return True
        else:
            return False

    def register_setting(self, slug: str, setting_type: int, nullable: bool, default_value=None):
        """Add a setting to the settings."""
        if self.is_registered(slug):
            raise Exception("{} is already registered".format(slug))
        if default_value is not None and not Settings.test_type(setting_type, default_value):
            raise TypeError(
                "Type of {} is {} but {} given".format(
                    slug, models.Setting.convert_index_to_type(setting_type), type(default_value)
                )
            )

        self.settings[slug] = RegisteredSetting(slug, setting_type, nullable, default_value)

    def is_registered(self, slug: str) -> bool:
        """Check if a setting is registered."""
        return slug in self.settings.keys()

    def _get_setting(self, slug: str, registered_setting: RegisteredSetting) -> models.Setting:
        """Lazily create a new setting."""
        if models.Setting.objects.filter(slug=slug).exists():
            # Setting already exists
            setting = models.Setting.objects.get(slug=slug)
            if setting.type != registered_setting.setting_type:
                setting.delete()
                setting = self._create_setting(
                    slug,
                    registered_setting.setting_type,
                    registered_setting.nullable,
                    registered_setting.default_value,
                )
            else:
                self._change_nullable(setting, registered_setting.nullable, registered_setting.default_value)
            return setting
        else:
            # Setting is new
            return self._create_setting(
                slug,
                registered_setting.setting_type,
                registered_setting.nullable,
                registered_setting.default_value,
            )

    def get_setting(self, slug: str) -> models.Setting:
        """Get a setting."""
        if not self.is_registered(slug):
            raise ValueError("Setting {} not in registered settings".format(slug))

        registered_setting = self.settings[slug]
        return self._get_setting(slug, registered_setting)

    def get_value(self, setting: str):
        """Get the value of a setting."""
        setting = self.get_setting(setting)
        return setting.get_value()

    def set_value(self, setting: str, value):
        """Set the value of a setting."""
        setting = self.get_setting(setting)
        setting.set_value(value)
        setting.save()


settings = Settings()
