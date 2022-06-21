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
        self.filter.add_filter(self.change_filter_add_list_item)
        self.assertTrue(self.change_filter_add_list_item in self.filter.filters)
        self.filter.add_filter(self.change_filter_add_list_item_2)
        self.assertTrue(self.change_filter_add_list_item_2 in self.filter.filters)
        self.filter.add_filter(self.change_filter_add_list_item_3, 4)
        self.assertEqual(self.change_filter_add_list_item_3, self.filter.filters[2])

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
