from django.core.exceptions import ValidationError
from django.test import TestCase
from ..models import Setting


class SettingsTest(TestCase):
    def test_setting_convert_index_to_type(self):
        self.assertEqual(Setting.convert_index_to_type(1), Setting.TYPE_INT_TEXT)
        self.assertEqual(Setting.convert_index_to_type(2), Setting.TYPE_STR_TEXT)
        self.assertEqual(Setting.convert_index_to_type(3), Setting.TYPE_FLOAT_TEXT)
        self.assertRaises(ValueError, Setting.convert_index_to_type, 4)

    def test_setting_clean(self):
        setting = Setting.objects.create(slug="test", value="test value", type=Setting.TYPE_STR, nullable=True)
        # No validation error.
        setting.clean()
        setting.value = None
        setting.nullable = False
        self.assertRaises(ValidationError, setting.clean)

    def test_setting_get_value(self):
        setting_int = Setting.objects.create(slug="test-int", value="4", type=Setting.TYPE_INT, nullable=True)
        setting_str = Setting.objects.create(slug="test-str", value="test value", type=Setting.TYPE_STR, nullable=True)
        setting_float = Setting.objects.create(
            slug="test-float", value="1.23456", type=Setting.TYPE_FLOAT, nullable=True
        )
        setting_none = Setting.objects.create(slug="test-none", value=None, type=Setting.TYPE_STR, nullable=True)
        self.assertEqual(setting_int.get_value(), 4)
        self.assertEqual(setting_str.get_value(), "test value")
        self.assertEqual(setting_float.get_value(), 1.23456)
        self.assertIsNone(setting_none.get_value())

    def test_setting_set_value(self):
        setting_int = Setting.objects.create(slug="test-int", value=None, type=Setting.TYPE_INT, nullable=True)
        setting_str = Setting.objects.create(slug="test-str", value=None, type=Setting.TYPE_STR, nullable=True)
        setting_float = Setting.objects.create(slug="test-float", value=None, type=Setting.TYPE_FLOAT, nullable=True)
        setting_none = Setting.objects.create(slug="test-none", value=None, type=Setting.TYPE_STR, nullable=True)
        setting_int.set_value(5)
        self.assertEqual(setting_int.value, "5")
        setting_str.set_value("test value")
        self.assertEqual(setting_str.value, "test value")
        setting_float.set_value(1.23456)
        self.assertEqual(setting_float.value, "1.23456")
        setting_none.set_value(None)
        self.assertIsNone(setting_none.value)
        self.assertRaises(TypeError, setting_int.set_value, "blablabla")

    def test_setting___str__(self):
        setting = Setting.objects.create(slug="test", value=None, type=Setting.TYPE_STR, nullable=True)
        self.assertEqual(setting.__str__(), "test")
