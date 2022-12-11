from django.test import TestCase

from announcements import models
from announcements.services import sanitize_closed_announcements, validate_closed_announcements


class OrderServicesTests(TestCase):
    def test_sanitize_closed_announcements_none(self):
        self.assertEquals([], sanitize_closed_announcements(None))

    def test_sanitize_closed_announcements_non_string(self):
        self.assertEquals([], sanitize_closed_announcements(5))

    def test_sanitize_closed_announcements_non_json(self):
        self.assertEquals([], sanitize_closed_announcements("this,is,not,json"))

    def test_sanitize_closed_announcements_non_list(self):
        self.assertEquals([], sanitize_closed_announcements("{}"))

    def test_sanitize_closed_announcements_list_of_ints(self):
        self.assertEquals([1, 8, 4], sanitize_closed_announcements("[1, 8, 4]"))

    def test_sanitize_closed_announcements_list_of_different_types(self):
        self.assertEquals(
            [1, 8, 4], sanitize_closed_announcements('[1, "bla", 8, 4, 123.4, {"a": "b"}, ["This is also a list"]]')
        )

    def test_validate_closed_announcements_all_exist(self):
        announcement_1 = models.Announcement.objects.create(title="Announcement 1", content="blablabla")
        announcement_2 = models.Announcement.objects.create(title="Announcement 2", content="blablabla")
        announcement_3 = models.Announcement.objects.create(title="Announcement 3", content="blablabla")
        self.assertEqual(
            {announcement_1.id, announcement_2.id, announcement_3.id}, set(validate_closed_announcements([1, 2, 3]))
        )

    def test_validate_closed_announcements_some_do_not_exist(self):
        announcement_1 = models.Announcement.objects.create(title="Announcement 1", content="blablabla")
        announcement_2 = models.Announcement.objects.create(title="Announcement 2", content="blablabla")
        announcement_3 = models.Announcement.objects.create(title="Announcement 3", content="blablabla")
        self.assertEqual(
            {announcement_1.id, announcement_2.id, announcement_3.id},
            set(validate_closed_announcements([1, 2, 3, 4, 5, 6])),
        )
