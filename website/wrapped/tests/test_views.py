import datetime
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from constance.test import override_config
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from orders.models import Order, OrderVenue, Product, Shift
from venues.models import Venue
from wrapped import services

User = get_user_model()

DECEMBER = timezone.make_aware(datetime.datetime(2026, 12, 8, 12))
OCTOBER = timezone.make_aware(datetime.datetime(2026, 10, 3, 12))
SLIDES = [
    {"order": 20, "kicker": "Orders", "value": 1234, "text": "items were ordered."}
]


def story_url(year):
    return reverse("wrapped:story", kwargs={"year": year})


@mock.patch(
    "wrapped.services.SLIDE_GENERATORS",
    [lambda period: [dict(slide) for slide in SLIDES]],
)
class StoryViewTests(TestCase):
    fixtures = ["users.json", "venues.json"]

    def setUp(self):
        cache.clear()
        self.user = User.objects.get(pk=2)

    def _get(self, url, now, user=None):
        # Log in at the mocked time, so the session has not expired yet.
        with mock.patch("django.utils.timezone.now", return_value=now):
            self.client.force_login(user or self.user)
            return self.client.get(url)

    def test_login_required(self):
        self.assertEqual(self.client.get(story_url(2025)).status_code, 302)

    def test_past_year(self):
        response = self._get(story_url(2025), OCTOBER)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1,234")
        # Only the slides, to load into the popup: not a whole page.
        self.assertNotContains(response, "<html")

    def test_current_year_only_in_december(self):
        self.assertEqual(self._get(story_url(2026), OCTOBER).status_code, 404)
        self.assertEqual(self._get(story_url(2026), DECEMBER).status_code, 200)

    @override_config(
        WRAPPED_YEAR_START_MONTH=9,
        WRAPPED_SHOW_FROM=datetime.date(2027, 6, 20),
        WRAPPED_SHOW_UNTIL=datetime.date(2027, 7, 15),
    )
    def test_lecture_year(self):
        july = timezone.make_aware(datetime.datetime(2027, 7, 1, 12))
        response = self._get(story_url(2026), july)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2026/2027")
        self.assertContains(response, "See you next year!")
        # The next lecture year isn't available yet.
        self.assertEqual(self._get(story_url(2027), july).status_code, 404)

    @override_config(WRAPPED_PERSONAL_FROM=datetime.date(2026, 1, 1))
    def test_personal_stats_only_for_the_user(self):
        start = timezone.make_aware(datetime.datetime(2026, 12, 2, 12))
        shift = Shift.objects.create(
            venue=OrderVenue.objects.create(venue=Venue.objects.get(pk=1)),
            start=start,
            end=start + datetime.timedelta(hours=4),
        )
        product = Product.objects.create(name="Tosti", current_price=1)
        product.available_at.add(shift.venue)
        order = Order.objects.create(
            shift=shift, product=product, user=self.user, paid=True
        )
        Order.objects.filter(pk=order.pk).update(created=start)

        self.assertContains(
            self._get(story_url(2026), DECEMBER), "Your TOSTI personality"
        )
        self.assertNotContains(
            self._get(story_url(2026), DECEMBER, user=User.objects.get(pk=1)),
            "Your TOSTI personality",
        )

    def test_only_personality_with_footnote_this_year(self):
        start = timezone.make_aware(datetime.datetime(2026, 12, 2, 12))
        shift = Shift.objects.create(
            venue=OrderVenue.objects.create(venue=Venue.objects.get(pk=1)),
            start=start,
            end=start + datetime.timedelta(hours=4),
        )
        product = Product.objects.create(name="Tosti", current_price=1)
        product.available_at.add(shift.venue)
        order = Order.objects.create(
            shift=shift, product=product, user=self.user, paid=True
        )
        Order.objects.filter(pk=order.pk).update(created=start)

        response = self._get(story_url(2026), DECEMBER)
        self.assertContains(response, "Your TOSTI personality")
        self.assertContains(response, "since 2 December only")
        self.assertNotContains(response, "Your visits")


@mock.patch(
    "wrapped.services.SLIDE_GENERATORS",
    [lambda period: [dict(slide) for slide in SLIDES]],
)
class WrappedPopupTests(TestCase):
    fixtures = ["users.json"]

    def setUp(self):
        cache.clear()
        self.user = User.objects.get(pk=2)

    def _index(self, now, login=True):
        with mock.patch("django.utils.timezone.now", return_value=now):
            if login:
                self.client.force_login(self.user)
            response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_popup_in_december(self):
        html = self._index(DECEMBER)
        self.assertIn('id="wrapped-popup"', html)
        self.assertIn('data-invite="true"', html)
        self.assertIn(f'data-story-url="{story_url(2026)}"', html)
        self.assertIn("data-wrapped-invite", html)
        # The slides are only loaded when the popup opens.
        self.assertNotIn("1,234", html)

    def test_menu_item_opens_popup(self):
        self.assertIn('href="#wrapped"', self._index(DECEMBER))

    def test_no_popup_outside_december(self):
        html = self._index(OCTOBER)
        self.assertNotIn('id="wrapped-popup"', html)
        self.assertNotIn('href="#wrapped"', html)

    def test_no_popup_for_anonymous_users(self):
        self.assertNotIn('id="wrapped-popup"', self._index(DECEMBER, login=False))

    def test_no_invitation_once_seen(self):
        self.client.cookies[services.SEEN_COOKIE] = "2026-01-01"
        html = self._index(DECEMBER)
        # Still there to open from the menu.
        self.assertIn('id="wrapped-popup"', html)
        self.assertIn('data-invite="false"', html)

    def test_invitation_again_next_year(self):
        self.client.cookies[services.SEEN_COOKIE] = "2025-01-01"
        self.assertIn('data-invite="true"', self._index(DECEMBER))
