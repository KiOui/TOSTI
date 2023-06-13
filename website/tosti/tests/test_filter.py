from django.test import TestCase

from tosti.filter import Filter


class TostiFilterTests(TestCase):
    def setUp(self) -> None:
        def change_filter_add_list_item(list_to_change):
            list_to_change.append("test-item-1")
            return list_to_change

        self.change_filter_add_list_item = change_filter_add_list_item

        def change_filter_add_list_item_2(list_to_change):
            list_to_change.append("test-item-2")
            return list_to_change

        self.change_filter_add_list_item_2 = change_filter_add_list_item_2

        def change_filter_add_list_item_3(list_to_change):
            list_to_change.append("test-item-3")
            return list_to_change

        self.change_filter_add_list_item_3 = change_filter_add_list_item_3
        self.filter = Filter()

    def test_filter_add_filter(self):
        self.filter.add_filter(self.change_filter_add_list_item, 2)
        result = self.filter.do_filter([])
        self.assertEqual(result[0], "test-item-1")
        self.filter.add_filter(self.change_filter_add_list_item_2, 3)
        result = self.filter.do_filter([])
        self.assertEqual(result[0], "test-item-1")
        self.assertEqual(result[1], "test-item-2")
        self.filter.add_filter(self.change_filter_add_list_item_3, 1)
        result = self.filter.do_filter([])
        self.assertEqual(result[0], "test-item-3")
        self.assertEqual(result[1], "test-item-1")
        self.assertEqual(result[2], "test-item-2")
        self.filter.add_filter(self.change_filter_add_list_item_3)
        result = self.filter.do_filter([])
        self.assertEqual(result[0], "test-item-3")
        self.assertEqual(result[1], "test-item-1")
        self.assertEqual(result[2], "test-item-2")
        self.assertEqual(result[3], "test-item-3")

    def test_filter_do_filter(self):
        self.filter.add_filter(self.change_filter_add_list_item)
        start_list = ["item-already-in-list"]
        return_value = self.filter.do_filter(start_list)
        self.assertTrue("item-already-in-list" in return_value)
        self.assertTrue("test-item-1" in return_value)
        self.filter.add_filter(self.change_filter_add_list_item_2)
        return_value = self.filter.do_filter([])
        self.assertTrue("test-item-1" in return_value)
        self.assertTrue("test-item-2" in return_value)
