from django.test import TestCase
from ..settings import Settings as RegisteredSettings
from ..models import Setting


class SettingsTest(TestCase):
    def setUp(self):
        self.settings = RegisteredSettings()

    def test_add_setting_type_str(self):
        self.assertFalse(Setting.objects.filter(slug="test-setting").exists())
        self.settings.register_setting("test-setting", Setting.TYPE_STR, False, default_value="test")
        self.assertEqual(self.settings.get_value("test-setting"), "test")

    def test_add_setting_type_int(self):
        self.assertFalse(Setting.objects.filter(slug="test-setting").exists())
        self.settings.register_setting("test-setting", Setting.TYPE_INT, False, default_value=100)
        self.assertEqual(self.settings.get_value("test-setting"), 100)

    def test_add_setting_type_float(self):
        self.assertFalse(Setting.objects.filter(slug="test-setting").exists())
        self.settings.register_setting("test-setting", Setting.TYPE_FLOAT, False, default_value=100.12345)
        self.assertEqual(self.settings.get_value("test-setting"), 100.12345)

    def test_add_setting_nullable(self):
        self.assertFalse(Setting.objects.filter(slug="test-setting").exists())
        self.settings.register_setting("test-setting", Setting.TYPE_STR, True)
        self.assertIsNone(self.settings.get_value("test-setting"))

    def test_add_setting_type_str_null_default_value(self):
        self.assertFalse(Setting.objects.filter(slug="test-setting").exists())
        self.settings.register_setting("test-setting", Setting.TYPE_STR, True, default_value="Bla")
        self.assertEqual(self.settings.get_value("test-setting"), "Bla")

    def test_add_setting_wrong_type_value(self):
        def call_add_setting():
            self.settings.register_setting("test-setting", Setting.TYPE_INT, False, default_value="Bla")

        self.assertRaises(TypeError, call_add_setting)

    def test_add_setting_twice(self):
        self.settings.register_setting("test-setting", Setting.TYPE_INT, False, default_value=1)

        def add_setting_second_time():
            self.settings.register_setting("test-setting", Setting.TYPE_INT, False, default_value=2)

        self.assertRaises(Exception, add_setting_second_time)
        self.assertEqual(self.settings.get_value("test-setting"), 1)

    def test_add_setting_non_nullable_no_default_value(self):
        def add_setting_non_nullable():
            self.settings.register_setting("test-setting", Setting.TYPE_INT, False)

        self.assertRaises(Exception, add_setting_non_nullable)
        self.assertFalse(Setting.objects.filter(slug="test-setting").exists())

    def test_add_setting_already_in_db(self):
        setting = Setting.objects.create(slug="test-setting", type=Setting.TYPE_INT, value=1, nullable=False)
        self.settings.register_setting("test-setting", Setting.TYPE_INT, False, default_value=1)
        self.assertEqual(setting.id, self.settings.get_setting("test-setting").id)

    def test_add_setting_already_in_db_different_type(self):
        Setting.objects.create(slug="test-setting", type=Setting.TYPE_INT, value=1, nullable=False)
        self.settings.register_setting("test-setting", Setting.TYPE_STR, False, default_value="Bla")
        self.assertEqual(self.settings.get_value("test-setting"), "Bla")

    def test_change_setting_nullable_true_false(self):
        Setting.objects.create(slug="test-setting", type=Setting.TYPE_FLOAT, value=3.14, nullable=True)
        self.settings.register_setting("test-setting", Setting.TYPE_FLOAT, False, default_value=2.13)
        self.assertEqual(self.settings.get_value("test-setting"), 3.14)
        self.assertFalse(Setting.objects.get(slug="test-setting").nullable)

    def test_change_setting_nullable_true_false_default_value(self):
        Setting.objects.create(slug="test-setting", type=Setting.TYPE_FLOAT, value=None, nullable=True)
        self.settings.register_setting("test-setting", Setting.TYPE_FLOAT, False, default_value=2.13)
        self.assertEqual(self.settings.get_value("test-setting"), 2.13)
        self.assertFalse(Setting.objects.get(slug="test-setting").nullable)

    def test_change_setting_nullable_false_true(self):
        Setting.objects.create(slug="test-setting", type=Setting.TYPE_FLOAT, value=3.14, nullable=False)
        self.settings.register_setting("test-setting", Setting.TYPE_FLOAT, True, default_value=2.13)
        self.assertEqual(self.settings.get_value("test-setting"), 3.14)
        self.assertTrue(Setting.objects.get(slug="test-setting").nullable)

    def test_set_value(self):
        self.settings.register_setting("test-setting", Setting.TYPE_FLOAT, False, default_value=12345.6789)
        self.settings.set_value("test-setting", 9876.54321)
        self.assertEqual(self.settings.get_value("test-setting"), 9876.54321)

    def test_set_value_wrong_type(self):
        self.settings.register_setting("test-setting", Setting.TYPE_FLOAT, False, default_value=12345.6789)

        def set_value_wrong_type():
            self.settings.set_value("test-setting", 9876)

        self.assertRaises(TypeError, set_value_wrong_type)

    def test_setting_not_registered(self):
        def not_registered_setting():
            self.settings.get_setting("not-registered")

        self.assertRaises(ValueError, not_registered_setting)

    def test_forcefully_removed_setting_recreated(self):
        self.settings.register_setting("forcefully-removed", Setting.TYPE_INT, False, default_value=123)
        self.assertEqual(self.settings.get_value("forcefully-removed"), 123)

        Setting.objects.get(slug="forcefully-removed").delete()
        self.assertEqual(self.settings.get_value("forcefully-removed"), 123)

    def test_registered(self):
        self.settings.register_setting("registered", Setting.TYPE_INT, False, default_value=123)
        Setting.objects.create(slug="not-registered", type=Setting.TYPE_INT, nullable=False, value=123)
        self.assertTrue(self.settings.is_registered("registered"))
        self.assertFalse(self.settings.is_registered("not-registered"))
