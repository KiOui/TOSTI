from datetime import datetime, timedelta

import freezegun
from django.test import TestCase

from tosti.cache import Cache, CacheInstance


class TostiCacheTests(TestCase):
    def setUp(self) -> None:
        def test_method_return_dict():
            return {"test-key": "test-value"}

        self.test_method_return_dict = test_method_return_dict

        def test_method_return_int():
            return 1234

        self.test_method_return_int = test_method_return_int

        self.cache = Cache()

    def test_cache_instance_create(self):
        with freezegun.freeze_time():
            cache_instance = CacheInstance("value", 5000)
            self.assertEqual(cache_instance.valid_until, datetime.now() + timedelta(milliseconds=5000))

    def test_cache_instance_is_valid(self):
        current_time = datetime.now()
        with freezegun.freeze_time(current_time):
            cache_instance = CacheInstance("value", 100)
            self.assertTrue(cache_instance.is_valid())

        with freezegun.freeze_time(current_time + timedelta(milliseconds=99)):
            self.assertTrue(cache_instance.is_valid())

        with freezegun.freeze_time(current_time + timedelta(milliseconds=100)):
            self.assertFalse(cache_instance.is_valid())

        with freezegun.freeze_time(current_time + timedelta(milliseconds=1000)):
            self.assertFalse(cache_instance.is_valid())

    def test_cache_update_cache(self):
        current_time = datetime.now()
        with freezegun.freeze_time(current_time):
            with self.subTest("Update cache first call"):
                self.cache.update_cache("cache-key", "test-value", 5000)
                self.assertTrue("cache-key" in self.cache._instance_cache.keys())
                cache_value = self.cache._instance_cache["cache-key"]
                self.assertEqual(cache_value.valid_until, current_time + timedelta(milliseconds=5000))
                self.assertEqual(cache_value.value, "test-value")
            with self.subTest("Update cache overwrite call"):
                self.cache.update_cache("cache-key", "test-value-2", 2000)
                self.assertTrue("cache-key" in self.cache._instance_cache.keys())
                cache_value = self.cache._instance_cache["cache-key"]
                self.assertEqual(cache_value.valid_until, current_time + timedelta(milliseconds=2000))
                self.assertEqual(cache_value.value, "test-value-2")
            with self.subTest("Update cache add call"):
                self.cache.update_cache("cache-key-2", "test-value-3", 4000)
                self.assertTrue("cache-key" in self.cache._instance_cache.keys())
                self.assertTrue("cache-key-2" in self.cache._instance_cache.keys())
                cache_value = self.cache._instance_cache["cache-key-2"]
                self.assertEqual(cache_value.valid_until, current_time + timedelta(milliseconds=4000))
                self.assertEqual(cache_value.value, "test-value-3")

    def test_cache_check_cache(self):
        current_time = datetime.now()
        with self.subTest("Cache valid moment created"):
            with freezegun.freeze_time(current_time):
                self.cache.update_cache("cache-key", "test-value", 5000)
                valid, value = self.cache.check_cache("cache-key")
                self.assertTrue(valid)
                self.assertEqual(value, "test-value")
                valid, value = self.cache.check_cache("non-existent-cache-key")
                self.assertFalse(valid)
                self.assertIsNone(value)

        with self.subTest("Cache valid within time range"):
            with freezegun.freeze_time(current_time + timedelta(milliseconds=3000)):
                valid, value = self.cache.check_cache("cache-key")
                self.assertTrue(valid)
                self.assertEqual(value, "test-value")

        with self.subTest("Cache invalid after time range"):
            with freezegun.freeze_time(current_time + timedelta(milliseconds=5000)):
                valid, value = self.cache.check_cache("cache-key")
                self.assertFalse(valid)
                self.assertIsNone(value)

    def test_cache_reset(self):
        with freezegun.freeze_time(datetime.now()):
            self.cache.update_cache("cache-key", "cache-value", 5000)
            self.cache.reset()
            self.assertFalse("cache-key" in self.cache._instance_cache.keys())

    def test_cache_call_method_cached(self):
        current_time = datetime.now()
        with self.subTest("Normal method call"):
            with freezegun.freeze_time(current_time):
                value_method_call = self.cache.call_method_cached(
                    self.test_method_return_dict, "dict-key", True, True, valid_ms=5000, reset_cache=False
                )
                valid, value = self.cache.check_cache("dict-key")
                self.assertTrue(valid)
                self.assertEqual(value, value_method_call)
                self.assertEqual(value_method_call, self.test_method_return_dict())

        with self.subTest("Method call cache hit"):
            with freezegun.freeze_time(current_time + timedelta(milliseconds=3000)):
                value_method_call = self.cache.call_method_cached(
                    self.test_method_return_int, "dict-key", True, False, valid_ms=5000, reset_cache=False
                )
                valid, value = self.cache.check_cache("dict-key")
                self.assertTrue(valid)
                self.assertEqual(value, value_method_call)
                self.assertNotEqual(value_method_call, self.test_method_return_int())

        with self.subTest("Method call cache expired"):
            with freezegun.freeze_time(current_time + timedelta(milliseconds=5000)):
                value_method_call = self.cache.call_method_cached(
                    self.test_method_return_int, "dict-key", True, True, valid_ms=5000, reset_cache=False
                )
                valid, value = self.cache.check_cache("dict-key")
                self.assertTrue(valid)
                self.assertEqual(value, value_method_call)
                self.assertEqual(value_method_call, self.test_method_return_int())

        with self.subTest("Reset cache"):
            with freezegun.freeze_time(current_time + timedelta(milliseconds=7000)):
                value_method_call = self.cache.call_method_cached(
                    self.test_method_return_dict, "dict-key", False, False, valid_ms=5000, reset_cache=True
                )
                valid, value = self.cache.check_cache("dict-key")
                self.assertFalse(valid)
                self.assertEqual(value_method_call, self.test_method_return_dict())

        with self.subTest("Reset cache check current value"):
            with freezegun.freeze_time(current_time):
                value_method_call = self.cache.call_method_cached(
                    self.test_method_return_dict, "dict-key", True, True, valid_ms=5000, reset_cache=False
                )
                value_method_call_second_time = self.cache.call_method_cached(
                    self.test_method_return_int(), "dict-key", True, True, valid_ms=5000, reset_cache=True
                )
                valid, value = self.cache.check_cache("dict-key")
                self.assertFalse(valid)
                self.assertIsNone(value)
                self.assertEqual(value_method_call_second_time, value_method_call)
                self.assertEqual(value_method_call, self.test_method_return_dict())
