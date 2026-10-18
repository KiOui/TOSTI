import datetime
from collections import Counter
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.core.cache import cache
from django.template.loader import render_to_string
from constance.test import override_config
from django.test import TestCase
from django.utils import timezone

from associations.models import Association
from orders.models import Order, OrderVenue, Product, Shift
from thaliedje.models import Player, SpotifyArtist, SpotifyQueueItem, SpotifyTrack
from venues.models import Venue
from wrapped import services
from wrapped.slides import tower_illustration
from wrapped.periods import Period, current_period, tracked_since
from wrapped.personal import personal_wrapped, queue_illustration, top_percentage
from wrapped.personality import (
    MEANINGS,
    PERSONALITIES,
    _even_goals,
    personality,
    product_flavour,
    standing_out,
    tune,
    _best,
)

User = get_user_model()


def aware(*args):
    return timezone.make_aware(datetime.datetime(*args))


class PeriodTests(TestCase):
    def test_calendar_year(self):
        period = Period.starting_in(2026)
        self.assertEqual(
            (period.start, period.end),
            (datetime.date(2026, 1, 1), datetime.date(2026, 12, 31)),
        )
        self.assertEqual(period.label, "2026")
        self.assertEqual(Period.containing(datetime.date(2026, 12, 3)), period)

    @override_config(WRAPPED_YEAR_START_MONTH=9)
    def test_lecture_year(self):
        period = Period.starting_in(2026)
        self.assertEqual(
            (period.start, period.end),
            (datetime.date(2026, 9, 1), datetime.date(2027, 8, 31)),
        )
        self.assertEqual(period.label, "2026/2027")
        self.assertEqual(Period.containing(datetime.date(2027, 6, 30)), period)
        self.assertEqual(
            Period.containing(datetime.date(2026, 8, 31)).label, "2025/2026"
        )

    def test_current_period(self):
        for now in (aware(2026, 12, 8, 12), aware(2027, 1, 1, 12)):
            with mock.patch("django.utils.timezone.now", return_value=now):
                # Also on New Year's Day, it looks back at the year it started in.
                self.assertEqual(current_period(), Period.starting_in(2026))
        for now in (aware(2026, 12, 3, 12), aware(2027, 1, 2, 12)):
            with mock.patch("django.utils.timezone.now", return_value=now):
                self.assertIsNone(current_period())

    @override_config(
        WRAPPED_YEAR_START_MONTH=9,
        WRAPPED_SHOW_FROM=datetime.date(2027, 6, 20),
        WRAPPED_SHOW_UNTIL=datetime.date(2027, 7, 15),
    )
    def test_current_lecture_year(self):
        with mock.patch(
            "django.utils.timezone.now", return_value=aware(2027, 7, 1, 12)
        ):
            self.assertEqual(current_period().label, "2026/2027")
        with mock.patch(
            "django.utils.timezone.now", return_value=aware(2027, 7, 16, 12)
        ):
            self.assertIsNone(current_period())

    def test_is_available(self):
        with mock.patch(
            "django.utils.timezone.now", return_value=aware(2026, 10, 3, 12)
        ):
            self.assertTrue(services.is_available(Period.starting_in(2025)))
            self.assertFalse(services.is_available(Period.starting_in(2026)))
        with mock.patch(
            "django.utils.timezone.now", return_value=aware(2026, 12, 8, 12)
        ):
            self.assertTrue(services.is_available(Period.starting_in(2026)))


class WrappedDataTestCase(TestCase):
    fixtures = ["users.json", "venues.json"]

    @classmethod
    def setUpTestData(cls):
        venue = Venue.objects.get(pk=1)
        order_venue = OrderVenue.objects.create(venue=venue)
        start = aware(2025, 3, 4, 12)
        cls.shift = Shift.objects.create(
            venue=order_venue, start=start, end=start + datetime.timedelta(hours=4)
        )
        cls.tosti = Product.objects.create(name="Tosti ham-kaas", current_price=1.25)
        cls.coffee = Product.objects.create(name="Coffee", current_price=0.5)
        cls.tosti.available_at.add(order_venue)
        cls.coffee.available_at.add(order_venue)
        cls.association = Association.objects.create(name="Thalia")
        cls.user = User.objects.get(pk=2)
        User.objects.filter(pk=cls.user.pk).update(date_joined=aware(2025, 2, 1, 10))
        cls.player = Player.objects.create(slug="test-player", venue=venue)

    def setUp(self):
        cache.clear()

    def _order(self, product, created, **kwargs):
        order = Order.objects.create(
            shift=self.shift,
            product=product,
            user=self.user,
            user_association=self.association,
            paid=True,
            **kwargs,
        )
        # ``created`` is auto_now_add, so set it afterwards.
        Order.objects.filter(pk=order.pk).update(created=created)
        return order

    def _request(self, track, added):
        item = SpotifyQueueItem.objects.create(
            track=track, player=self.player, requested_by=None
        )
        SpotifyQueueItem.objects.filter(pk=item.pk).update(added=added)


class CollectSlidesTests(WrappedDataTestCase):
    def test_no_data(self):
        self.assertEqual(services.collect_slides(Period.starting_in(2023)), [])

    def test_slides(self):
        for _ in range(3):
            self._order(
                self.tosti,
                aware(2025, 3, 4, 12, 30),
                ready_at=aware(2025, 3, 4, 12, 35),
            )
        self._order(self.coffee, aware(2025, 3, 5, 9, 0))
        # Orders of another year are ignored.
        self._order(self.coffee, aware(2024, 3, 5, 9, 0))

        artist = SpotifyArtist.objects.create(artist_name="ABBA", artist_id="abba")
        track = SpotifyTrack.objects.create(
            track_id="dancing-queen", track_name="Dancing Queen"
        )
        track.track_artists.add(artist)
        self._request(track, aware(2025, 6, 1, 13))
        self._request(track, aware(2025, 6, 2, 13))

        slides = {
            slide["kicker"]: slide
            for slide in services.collect_slides(Period.starting_in(2025))
        }

        self.assertEqual(slides["Orders"]["value"], "4")
        self.assertEqual(slides["Orders"]["count_to"], 4)
        self.assertIn("1 shift.", slides["Orders"]["text"])
        self.assertEqual(slides["Tostis"]["value"], "3")
        self.assertIn("6 centimetres", slides["Tostis"]["text"])
        self.assertEqual(slides["Crowd favourites"]["value"], "Tosti ham-kaas")
        self.assertIsNone(slides["Crowd favourites"]["count_to"])
        self.assertEqual(slides["Rush hour"]["value"], "4 March")
        self.assertEqual(slides["The busiest weekday"]["value"], "Tuesday")
        self.assertEqual(slides["Speedy service"]["value"], "5.0 min")
        self.assertEqual(slides["Association leaderboard"]["value"], "Thalia")
        self.assertEqual(slides["Thaliedje"]["value"], "2")
        self.assertEqual(slides["Song of the year"]["value"], "Dancing Queen")
        self.assertEqual(slides["Song of the year"]["ranking"][0]["value"], "2×")
        self.assertEqual(
            slides["Song of the year"]["ranking"][0]["label"], "Dancing Queen – ABBA"
        )
        self.assertEqual(slides["Artist of the year"]["value"], "ABBA")
        self.assertEqual(slides["Newcomers"]["value"], "1")
        # Only the last login is stored, but everyone who ordered or requested a song logged in that year.
        self.assertIn(
            "In total, 1 person logged in this year.", slides["Newcomers"]["text"]
        )

    def test_busiest_weekday_is_an_average(self):
        # Tuesday 4 March: 3 orders. Mondays 10 and 17 March: 4 orders, and none (but the canteen was open).
        for _ in range(3):
            self._order(self.tosti, aware(2025, 3, 4, 12, 30))
        for _ in range(4):
            self._order(self.tosti, aware(2025, 3, 10, 12, 30))
        start = aware(2025, 3, 17, 12)
        Shift.objects.create(
            venue=self.shift.venue, start=start, end=start + datetime.timedelta(hours=4)
        )

        slides = {
            slide["kicker"]: slide
            for slide in services.collect_slides(Period.starting_in(2025))
        }
        weekday = slides["The busiest weekday"]
        self.assertEqual(weekday["value"], "Tuesday")
        self.assertIn("3 orders on average", weekday["text"])
        bars = {bar["label"]: bar for bar in weekday["bars"]}
        self.assertEqual(list(bars), ["Mon", "Tue", "Wed", "Thu", "Fri"])
        self.assertEqual((bars["Tue"]["height"], bars["Tue"]["top"]), (100, True))
        self.assertEqual((bars["Mon"]["height"], bars["Mon"]["top"]), (67, False))
        self.assertEqual(bars["Wed"]["height"], 0)
        self.assertEqual(
            weekday["ranking"],
            [
                {"label": "Average on Tuesdays", "value": "3 orders"},
                {"label": "Average on Mondays", "value": "2 orders"},
            ],
        )
        # The busiest single day is still a Monday.
        self.assertEqual(slides["Rush hour"]["value"], "10 March")

    def test_newcomers_this_year(self):
        User.objects.filter(pk=self.user.pk).update(
            date_joined=aware(2026, 2, 1, 10), last_login=aware(2026, 11, 1, 10)
        )
        User.objects.exclude(pk=self.user.pk).update(
            date_joined=aware(2024, 2, 1, 10), last_login=aware(2026, 10, 1, 10)
        )
        with mock.patch(
            "django.utils.timezone.now", return_value=aware(2026, 12, 3, 12)
        ):
            slides = {
                slide["kicker"]: slide
                for slide in services.collect_slides(Period.starting_in(2026))
            }
        self.assertEqual(slides["Newcomers"]["value"], "1")
        self.assertIn(
            "In total, 2 people logged in this year.", slides["Newcomers"]["text"]
        )

    def test_logged_in_this_year(self):
        User.objects.update(date_joined=aware(2024, 2, 1, 10), last_login=None)
        User.objects.filter(pk=self.user.pk).update(date_joined=aware(2025, 2, 1, 10))
        other = User.objects.exclude(pk=self.user.pk).first()
        # One logged in this year, one ordered (and logged in again since), one requested a song anonymously.
        User.objects.filter(pk=other.pk).update(last_login=aware(2025, 5, 1, 10))
        self._order(self.tosti, aware(2025, 3, 4, 12, 30))
        User.objects.filter(pk=self.user.pk).update(last_login=aware(2026, 1, 5, 10))
        self._request(
            SpotifyTrack.objects.create(track_id="t", track_name="T"),
            aware(2025, 6, 1, 13),
        )

        slides = {
            slide["kicker"]: slide
            for slide in services.collect_slides(Period.starting_in(2025))
        }
        self.assertIn(
            "In total, 2 people logged in this year.", slides["Newcomers"]["text"]
        )

    def test_slides_do_not_contain_personal_data(self):
        self._order(self.tosti, aware(2025, 3, 4, 12, 30))
        rendered = str(services.collect_slides(Period.starting_in(2025)))
        self.assertNotIn(self.user.username, rendered)
        self.assertNotIn(self.user.get_full_name() or self.user.username, rendered)


@override_config(WRAPPED_PERSONAL_FROM=datetime.date(2025, 1, 1))
class PersonalWrappedTests(WrappedDataTestCase):
    def setUp(self):
        super().setUp()
        self.other_user = User.objects.get(pk=1)
        self.cheese = Product.objects.create(name="Tosti cheese", current_price=1)
        self.ham_cheese = Product.objects.create(
            name="Tosti ham-cheese", current_price=1
        )
        artist = SpotifyArtist.objects.create(artist_name="ABBA", artist_id="abba")
        self.track = SpotifyTrack.objects.create(
            track_id="dancing-queen", track_name="Dancing Queen"
        )
        self.track.track_artists.add(artist)

    def _visit(self, day, product, first=True):
        """Let the user order on a day in their own shift, before (or after) another user."""
        start = aware(day.year, day.month, day.day, 12)
        shift = Shift.objects.create(
            venue=self.shift.venue, start=start, end=start + datetime.timedelta(hours=2)
        )
        orderers = (
            [self.user, self.other_user] if first else [self.other_user, self.user]
        )
        for minute, user in enumerate(orderers):
            order = Order.objects.create(
                shift=shift, product=product, user=user, paid=True
            )
            Order.objects.filter(pk=order.pk).update(
                created=start + datetime.timedelta(minutes=minute)
            )

    def _user_request(self, user, added):
        item = SpotifyQueueItem.objects.create(
            track=self.track, player=self.player, requested_by=user
        )
        SpotifyQueueItem.objects.filter(pk=item.pk).update(added=added)

    def _visits(self, month):
        # Three Mondays and a Wednesday: 3 cheese, 1 ham-cheese, always first in line.
        for day, product in (
            (6, self.cheese),
            (13, self.cheese),
            (20, self.cheese),
            (22, self.ham_cheese),
        ):
            self._visit(datetime.date(2025, month, day), product)

    def test_full_year(self):
        self._visits(1)
        self._user_request(self.user, aware(2025, 1, 6, 12, 30))

        personal = personal_wrapped(self.user, Period.starting_in(2025))
        slides = {slide["kicker"]: slide for slide in personal["slides"]}

        self.assertFalse(personal["partial"])
        self.assertEqual(slides["Your visits"]["value"], 4)
        self.assertEqual(
            slides["Your visits"]["ranking"],
            [
                {"label": "Days you ordered", "value": "4 days"},
                {"label": "Days you requested a song", "value": "1 day"},
            ],
        )
        self.assertIn(
            "Days you did both only count once.", slides["Your visits"]["text"]
        )
        self.assertEqual(slides["Your streak"]["value"], "3 weeks")
        self.assertEqual(slides["Your favourite day"]["value"], "Monday")
        self.assertEqual(
            slides["Your favourite day"]["text"], "You mostly came by on Mondays."
        )
        bars = {bar["label"]: bar for bar in slides["Your favourite day"]["bars"]}
        self.assertEqual(list(bars), ["Mon", "Tue", "Wed", "Thu", "Fri"])
        self.assertEqual((bars["Mon"]["height"], bars["Mon"]["top"]), (100, True))
        self.assertEqual((bars["Wed"]["height"], bars["Wed"]["top"]), (33, False))
        self.assertEqual(slides["Your order"]["value"], "Tosti cheese")
        self.assertIn("75%", slides["Your order"]["text"])
        self.assertEqual(slides["Your order"]["ranking"][0]["value"], "3×")
        self.assertEqual(slides["Your tosti tower"]["value"], "8 centimetres")
        self.assertIn("your 4 tostis", slides["Your tosti tower"]["text"])
        self.assertEqual(slides["Your spot in line"]["value"], "#1")
        self.assertIn("first in line 4 times", slides["Your spot in line"]["text"])
        self.assertEqual(slides["Your soundtrack"]["value"], 1)
        self.assertEqual(slides["Your top artist"]["value"], "ABBA")
        personality_slide = slides["Your TOSTI personality"]
        self.assertIn(
            personality_slide["value"], {name for name, _ in PERSONALITIES.values()}
        )
        self.assertEqual(
            personality_slide["meaning"],
            MEANINGS[
                next(
                    key
                    for key, (name, _) in PERSONALITIES.items()
                    if name == personality_slide["value"]
                )
            ],
        )
        self.assertTrue(
            personality_slide["art"].startswith("wrapped/img/personalities/")
        )
        self.assertEqual(
            personal["share_art"], personality_slide["art"].replace(".svg", ".png")
        )
        self.assertIn("Cheese lover", personality_slide["tags"])
        self.assertIn("Team North", personality_slide["tags"])
        self.assertEqual(
            personal["share"][0],
            {"label": "TOSTI personality", "value": personality_slide["value"]},
        )

    def test_partial_year_says_since_when(self):
        self._visits(9)
        self._user_request(self.user, aware(2025, 9, 6, 12, 30))

        personal = personal_wrapped(self.user, Period.starting_in(2025))
        slides = {slide["kicker"]: slide for slide in personal["slides"]}

        self.assertTrue(personal["partial"])
        self.assertEqual(slides["Your visits"]["value"], 4)
        self.assertIn("you came by since September", slides["Your visits"]["text"])
        self.assertIn("since September", slides["Your favourite day"]["text"])
        self.assertEqual(slides["Your order"]["ranking"][0]["value"], "3×")
        self.assertIn("orders since September", slides["Your order"]["text"])
        self.assertIn("tostis since September", slides["Your tosti tower"]["text"])
        self.assertIn("queue since September", slides["Your spot in line"]["text"])
        self.assertIn("first in line 4 times", slides["Your spot in line"]["text"])
        self.assertEqual(slides["Your soundtrack"]["value"], 1)
        self.assertIn("Thaliedje since September", slides["Your soundtrack"]["text"])
        self.assertIn(
            "artist since September, 1 time", slides["Your top artist"]["text"]
        )
        self.assertIn(
            slides["Your TOSTI personality"]["value"],
            {name for name, _ in PERSONALITIES.values()},
        )
        self.assertIn(
            {"label": "Days in the canteen since September", "value": 4},
            personal["share"],
        )

        story = services.get_story(self.user, Period.starting_in(2025))
        self.assertTrue(story["personal_partial"])
        self.assertEqual(story["personal_since"], datetime.date(2025, 9, 6))

    def test_favourite_day_tie(self):
        self._visit(datetime.date(2025, 1, 6), self.cheese)
        self._visit(datetime.date(2025, 1, 8), self.cheese)
        slides = {
            slide["kicker"]: slide
            for slide in personal_wrapped(self.user, Period.starting_in(2025))["slides"]
        }
        self.assertEqual(slides["Your favourite day"]["value"], "Monday & Wednesday")
        self.assertEqual(
            slides["Your favourite day"]["text"],
            "You mostly came by on Mondays and Wednesdays.",
        )

    def test_calendar(self):
        self._visits(9)
        # The canteen was open on a day the user didn't come by.
        self._order(self.tosti, aware(2025, 9, 9, 12))
        Order.objects.filter(created=aware(2025, 9, 9, 12)).update(user=None)

        with mock.patch(
            "django.utils.timezone.now", return_value=aware(2025, 12, 3, 12)
        ):
            personality = personal_wrapped(self.user, Period.starting_in(2025))[
                "slides"
            ][-1]
        calendar = personality["calendar"]

        self.assertEqual(
            [month["name"] for month in calendar],
            ["September", "October", "November", "December"],
        )
        september = {day["day"]: day["state"] for day in calendar[0]["days"]}
        self.assertEqual(
            len(calendar[0]["blanks"]), 0
        )  # 1 September 2025 was a Monday.
        self.assertEqual(september[5], "outside")  # Before the first known visit.
        self.assertEqual(september[6], "visited")
        self.assertEqual(september[9], "open")
        self.assertEqual(september[10], "closed")
        december = {day["day"]: day["state"] for day in calendar[3]["days"]}
        self.assertEqual(december[4], "outside")  # In the future.

    def test_story_mixes_personal_and_community_slides(self):
        self._visits(1)
        self._order(self.coffee, aware(2025, 1, 6, 12, 30))
        story = services.get_story(self.user, Period.starting_in(2025))
        kickers = [slide["kicker"] for slide in story["slides"]]

        # Related slides follow each other, and the personality is the finale.
        self.assertLess(kickers.index("Orders"), kickers.index("Your visits"))
        self.assertLess(kickers.index("Rush hour"), kickers.index("Your favourite day"))
        self.assertLess(
            kickers.index("Your favourite day"), kickers.index("Crowd favourites")
        )
        self.assertLess(kickers.index("Crowd favourites"), kickers.index("Your order"))
        self.assertEqual(kickers[-1], "Your TOSTI personality")
        themes = {slide["kicker"]: slide["theme"] for slide in story["slides"]}
        self.assertEqual(themes["Your visits"], "personal")
        self.assertNotEqual(themes["Orders"], "personal")

    def test_canteens(self):
        self._visits(1)
        south = OrderVenue.objects.create(venue=Venue.objects.get(pk=2))
        start = aware(2025, 1, 7, 12)
        shift = Shift.objects.create(
            venue=south, start=start, end=start + datetime.timedelta(hours=2)
        )
        order = Order.objects.create(
            shift=shift, product=self.cheese, user=self.user, paid=True
        )
        Order.objects.filter(pk=order.pk).update(created=start)

        slides = {
            slide["kicker"]: slide
            for slide in personal_wrapped(self.user, Period.starting_in(2025))["slides"]
        }
        self.assertEqual(slides["Your canteen"]["value"], "North")
        self.assertIn("80% of your orders", slides["Your canteen"]["text"])
        self.assertEqual(
            slides["Your canteen"]["ranking"],
            [
                {"label": "North", "value": "4×"},
                {"label": "South", "value": "1×"},
            ],
        )
        self.assertIn("Team North", slides["Your TOSTI personality"]["tags"])

        community = {
            slide["kicker"]: slide
            for slide in services.collect_slides(Period.starting_in(2025))
        }
        self.assertEqual(community["The canteen battle"]["value"], "North")
        self.assertIn("89% of all orders", community["The canteen battle"]["text"])
        self.assertEqual(
            community["The canteen battle"]["ranking"][1],
            {"label": "South", "value": "1 order"},
        )

    @override_config(WRAPPED_PERSONAL_FROM=datetime.date(2026, 1, 1))
    def test_only_personality_before_personal_from(self):
        self._visits(9)
        self._user_request(self.user, aware(2025, 9, 6, 12, 30))

        personal = personal_wrapped(self.user, Period.starting_in(2025))
        self.assertEqual(
            [slide["kicker"] for slide in personal["slides"]],
            ["Your TOSTI personality"],
        )
        personality_slide = personal["slides"][0]
        self.assertIn(
            personality_slide["value"], {name for name, _ in PERSONALITIES.values()}
        )
        self.assertIn("since 6 September only", personality_slide["footnote"])
        self.assertIn("data minimisation", personality_slide["footnote"])
        self.assertFalse(personal["partial"])
        self.assertEqual(
            personal["share"][0],
            {"label": "TOSTI personality", "value": personality_slide["value"]},
        )
        self.assertTrue(
            all(
                line["label"] in {"TOSTI personality", "Known for"}
                for line in personal["share"]
            )
        )

        story = services.get_story(self.user, Period.starting_in(2025))
        self.assertEqual(len(story["personal_slides"]), 1)
        self.assertFalse(story["personal_partial"])
        self.assertEqual(story["share"]["title"], "My TOSTI Wrapped")

    @override_config(WRAPPED_PERSONAL_FROM=datetime.date(2026, 1, 1))
    def test_no_footnote_when_the_whole_year_is_known(self):
        self._visits(1)
        personal = personal_wrapped(self.user, Period.starting_in(2025))
        self.assertEqual(
            [slide["kicker"] for slide in personal["slides"]],
            ["Your TOSTI personality"],
        )
        self.assertNotIn("footnote", personal["slides"][0])

    @override_config(
        WRAPPED_YEAR_START_MONTH=9, WRAPPED_PERSONAL_FROM=datetime.date(2025, 9, 1)
    )
    def test_personal_from_in_lecture_years(self):
        self._visits(1)
        self.assertEqual(
            [
                slide["kicker"]
                for slide in personal_wrapped(self.user, Period.starting_in(2024))[
                    "slides"
                ]
            ],
            ["Your TOSTI personality"],
        )
        self._visits(10)
        self.assertGreater(
            len(personal_wrapped(self.user, Period.starting_in(2025))["slides"]), 1
        )

    def _bake(self, day, tostis=0):
        """Let the user be a baker in a shift on a day, in which ``tostis`` tostis are ordered by someone else."""
        start = aware(day.year, day.month, day.day, 12)
        shift = Shift.objects.create(
            venue=self.shift.venue, start=start, end=start + datetime.timedelta(hours=4)
        )
        shift.assignees.add(self.user)
        for _ in range(tostis):
            Order.objects.create(
                shift=shift, product=self.cheese, user=self.other_user, paid=True
            )
        Order.objects.filter(shift=shift).update(created=start)
        return shift

    def test_baker(self):
        self._bake(datetime.date(2025, 3, 3), tostis=10)
        self._bake(datetime.date(2025, 3, 10), tostis=5)
        shift = self._bake(datetime.date(2025, 3, 12))
        Order.objects.create(
            shift=shift, product=self.coffee, user=self.other_user, paid=True
        )

        slides = {
            slide["kicker"]: slide
            for slide in personal_wrapped(self.user, Period.starting_in(2025))["slides"]
        }
        baker = slides["Behind the counter"]
        self.assertEqual(baker["value"], 3)
        self.assertIn("shifts you were a baker, mostly on Mondays", baker["text"])
        self.assertIn("you grilled 15 tostis", baker["text"])
        bars = {bar["label"]: bar for bar in baker["bars"]}
        self.assertEqual((bars["Mon"]["height"], bars["Mon"]["top"]), (100, True))
        self.assertEqual((bars["Wed"]["height"], bars["Wed"]["top"]), (50, False))
        self.assertEqual(bars["Tue"]["height"], 0)

    def test_baker_without_orders_of_their_own(self):
        self._bake(datetime.date(2025, 3, 3), tostis=1)
        personal = personal_wrapped(self.user, Period.starting_in(2025))
        self.assertEqual(
            [slide["kicker"] for slide in personal["slides"]], ["Behind the counter"]
        )
        self.assertIn("1 tosti.", personal["slides"][0]["text"])
        self.assertEqual(
            personal["share"], [{"label": "Shifts as a baker", "value": 1}]
        )

    def test_no_baker_slide_for_others(self):
        self._bake(datetime.date(2025, 3, 3), tostis=1)
        self._visits(3)
        self.assertNotIn(
            "Behind the counter",
            [
                slide["kicker"]
                for slide in personal_wrapped(
                    self.other_user, Period.starting_in(2025)
                )["slides"]
            ],
        )

    @override_config(WRAPPED_PERSONAL_FROM=datetime.date(2026, 1, 1))
    def test_baker_slide_with_only_the_personality(self):
        # Shifts aren't anonymised, so they're complete even when the orders are not.
        self._bake(datetime.date(2025, 3, 3))
        self._visits(9)
        personal = personal_wrapped(self.user, Period.starting_in(2025))
        self.assertEqual(
            [slide["kicker"] for slide in personal["slides"]],
            ["Your TOSTI personality", "Behind the counter"],
        )
        self.assertIn({"label": "Shifts as a baker", "value": 1}, personal["share"])

    @override_config(WRAPPED_PERSONAL_DATA_SINCE=datetime.date(2025, 9, 1))
    def test_only_counts_from_personal_data_since(self):
        self._visits(1)
        self._visits(9)
        personal = personal_wrapped(self.user, Period.starting_in(2025))
        slides = {slide["kicker"]: slide for slide in personal["slides"]}

        self.assertTrue(personal["partial"])
        self.assertEqual(slides["Your visits"]["value"], 4)
        self.assertIn("since September", slides["Your visits"]["text"])
        calendar = slides["Your TOSTI personality"]["calendar"]
        self.assertEqual(
            [month["name"] for month in calendar],
            ["September", "October", "November", "December"],
        )

    @override_config(
        WRAPPED_PERSONAL_FROM=datetime.date(2026, 1, 1),
        WRAPPED_PERSONAL_DATA_SINCE=datetime.date(2025, 9, 1),
    )
    def test_personality_footnote_names_personal_data_since(self):
        self._visits(1)
        self._visits(9)
        personality_slide = personal_wrapped(self.user, Period.starting_in(2025))[
            "slides"
        ][0]
        self.assertIn("since 1 September only", personality_slide["footnote"])
        self.assertEqual(personality_slide["calendar"][0]["name"], "September")

    def test_personal_slides_only_about_the_user(self):
        self._order(self.tosti, aware(2025, 3, 4, 12, 30))
        self._user_request(self.user, aware(2025, 6, 1, 13))
        self.assertEqual(
            personal_wrapped(self.other_user, Period.starting_in(2025))["slides"], []
        )

    def test_anonymised_data_is_not_personal(self):
        self._request(self.track, aware(2025, 6, 1, 13))
        self.assertEqual(
            personal_wrapped(self.user, Period.starting_in(2025))["slides"], []
        )

    def test_top_percentage(self):
        self._order(self.tosti, aware(2025, 3, 4, 12, 30))
        self._order(self.tosti, aware(2025, 3, 4, 12, 31))
        Order.objects.create(
            shift=self.shift, product=self.coffee, user=self.other_user, paid=True
        )
        Order.objects.filter(user=self.other_user).update(created=aware(2025, 3, 4, 12))
        orders = Order.objects.filter(created__year=2025)
        self.assertEqual(top_percentage(orders, "user", 2), 50)
        self.assertEqual(top_percentage(orders, "user", 1), 100)

    def test_tracked_since(self):
        self._order(self.tosti, aware(2025, 1, 10, 12))
        self.assertIsNone(tracked_since(Period.starting_in(2025)))
        Order.objects.update(user=None)
        self._order(self.tosti, aware(2025, 9, 10, 12))
        self.assertEqual(
            tracked_since(Period.starting_in(2025)), datetime.date(2025, 9, 10)
        )

    def test_tracked_since_personal_data_since(self):
        self._order(self.tosti, aware(2025, 1, 10, 12))
        with override_config(WRAPPED_PERSONAL_DATA_SINCE=datetime.date(2025, 9, 18)):
            self.assertEqual(
                tracked_since(Period.starting_in(2025)), datetime.date(2025, 9, 18)
            )
        # Only for the period the day falls in.
        with override_config(WRAPPED_PERSONAL_DATA_SINCE=datetime.date(2024, 9, 18)):
            self.assertIsNone(tracked_since(Period.starting_in(2025)))
        # Whichever is later.
        Order.objects.update(user=None)
        self._order(self.tosti, aware(2025, 10, 1, 12))
        with override_config(WRAPPED_PERSONAL_DATA_SINCE=datetime.date(2025, 9, 18)):
            self.assertEqual(
                tracked_since(Period.starting_in(2025)), datetime.date(2025, 10, 1)
            )

    def test_story_share(self):
        self._order(self.tosti, aware(2025, 3, 4, 12, 30))
        story = services.get_story(self.other_user, Period.starting_in(2025))
        self.assertEqual(story["personal_slides"], [])
        self.assertEqual(story["share"]["title"], "TOSTI Wrapped")
        self.assertEqual(
            story["share"]["lines"][0], {"label": "Tostis grilled", "value": "1"}
        )
        self.assertIsNone(story["share"]["art"])

        story = services.get_story(self.user, Period.starting_in(2025))
        self.assertEqual(story["share"]["title"], "My TOSTI Wrapped")
        self.assertEqual(story["share"]["lines"][0]["label"], "TOSTI personality")
        self.assertRegex(story["share"]["art"], r"wrapped/img/personalities/\w+\.png$")
        self.assertIn(
            {"label": "Days in the canteen since March", "value": "1"},
            story["share"]["lines"],
        )


def person(**overrides):
    """Features of someone, as ``wrapped.personality.features`` returns them."""
    features = {
        "visit_days": 3,
        "longest_week_streak": 1,
        "max_visits_in_14_days": 1,
        "orders": 6,
        "flavours": Counter({"cheese": 6}),
        "top_product_share": 1,
        "products": 1,
        "canteens": Counter({"North": 6}),
        "top_canteen_share": 1,
        "queue_shifts": 3,
        "queue_relative": 0.5,
        "queue_first": 0,
        "songs": 0,
    }
    features.update(overrides)
    return features


CONTEXT = {"open_days": list(range(20)), "open_weeks": list(range(5)), "days": 31}


class PersonalityTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_every_personality_has_a_meaning(self):
        self.assertEqual(set(MEANINGS), set(PERSONALITIES))

    def test_every_personality_has_an_illustration(self):
        # An SVG for the slide, and a PNG of it for the share image.
        for key in PERSONALITIES:
            for extension in ("svg", "png"):
                self.assertIsNotNone(
                    finders.find(f"wrapped/img/personalities/{key}.{extension}"),
                    f"{key}.{extension}",
                )

    def test_product_flavour(self):
        self.assertEqual(product_flavour("Tosti Ham-Cheese"), "ham-cheese")
        self.assertEqual(
            product_flavour("Free tosti ham-cheese for tosticie"), "ham-cheese"
        )
        self.assertEqual(product_flavour("Free tosti cheese for tosticie"), "cheese")

    def test_even_goals(self):
        # The DJ can't get its share, so the others split what it leaves.
        goals = _even_goals(100, {"a": 100, "b": 100, "dj": 5})
        self.assertAlmostEqual(goals["dj"], 4.5)
        self.assertAlmostEqual(goals["a"], 47.75)
        self.assertAlmostEqual(goals["b"], 47.75)

    def test_personalities_are_spread_evenly(self):
        everyone = [
            person(
                visit_days=1 + index % 9,
                longest_week_streak=1 + index % 5,
                queue_relative=(index * 37 % 100) / 100,
                top_canteen_share=0.5 if index % 7 == 0 else 1,
                top_product_share=0.5 if index % 11 == 0 else 1,
                songs=index % 13 // 6 * 4,
            )
            for index in range(300)
        ]
        populations, boosts = tune(everyone, CONTEXT)
        counts = Counter(
            _best(standing_out(f, populations, CONTEXT), boosts) for f in everyone
        )
        # No personality takes over: every one gets at most a fifth of everyone.
        self.assertLessEqual(max(counts.values()), 300 / 5)
        self.assertGreaterEqual(len(counts), 6)

    @mock.patch("wrapped.personality.period_context", return_value=CONTEXT)
    def test_personality_and_tags(self, *args):
        everyone = [person(queue_relative=index / 100) for index in range(100)]
        with mock.patch(
            "wrapped.personality.everyones_features", return_value=everyone
        ):
            you = personality(
                person(queue_relative=0, queue_first=3),
                Period.starting_in(2025),
                None,
                " since September",
            )

        self.assertEqual(you["name"], "The Early Bird")
        self.assertIn("You were earlier in line than", you["description"])
        self.assertIn("since September", you["description"])
        self.assertIn("Cheese lover", you["tags"])
        self.assertIn("Team North", you["tags"])

    @mock.patch("wrapped.personality.period_context", return_value=CONTEXT)
    def test_nothing_stands_out(self, *args):
        with mock.patch("wrapped.personality.everyones_features", return_value=[]):
            self.assertEqual(
                personality(person(), Period.starting_in(2025), None)["name"],
                "The Rare Sighting",
            )


class IllustrationTests(TestCase):
    def test_tower(self):
        self.assertEqual(len(tower_illustration(3)["stack"]), 3)
        self.assertFalse(tower_illustration(3)["clouds"])
        # A tall tower is capped and disappears in the clouds.
        self.assertEqual(len(tower_illustration(1000)["stack"]), 8)
        self.assertTrue(tower_illustration(1000)["clouds"])

    def test_queue(self):
        self.assertTrue(queue_illustration(0)["people"][0]["you"])
        self.assertTrue(queue_illustration(1)["people"][-1]["you"])
        self.assertEqual(
            sum(person["you"] for person in queue_illustration(0.5)["people"]), 1
        )


class SlideTemplateTests(TestCase):
    def test_slide_without_ranking_has_no_list(self):
        # A dict has an ``items`` method, so the template must not look up a key with that name.
        html = render_to_string(
            "wrapped/slide.html",
            {
                "slide": {
                    "kicker": "Your favourite",
                    "value": "Tosti",
                    "text": "You ordered it 4 times.",
                }
            },
        )
        self.assertNotIn("<ol", html)

    def test_illustrations_render(self):
        for illustration in (
            tower_illustration(3),
            tower_illustration(1000),
            queue_illustration(0.5),
            {
                "type": "battle",
                "sides": [
                    {"label": "North", "share": 60},
                    {"label": "South", "share": 40},
                ],
            },
        ):
            html = render_to_string(
                "wrapped/slide.html",
                {
                    "slide": {
                        "kicker": "K",
                        "value": "V",
                        "text": "",
                        "illustration": illustration,
                    }
                },
            )
            self.assertIn('aria-hidden="true"', html)

    def test_icon_renders(self):
        html = render_to_string(
            "wrapped/slide.html",
            {
                "slide": {
                    "kicker": "K",
                    "value": "V",
                    "text": "",
                    "icon": "fa-music",
                    "icon_animation": "bounce",
                }
            },
        )
        self.assertIn("fa-music wrapped-icon wrapped-icon-bounce", html)

    def test_slide_with_ranking(self):
        html = render_to_string(
            "wrapped/slide.html",
            {
                "slide": {
                    "kicker": "Top",
                    "value": "Tosti",
                    "text": "",
                    "ranking": [{"label": "Tosti", "value": "4"}],
                }
            },
        )
        self.assertIn("<ol", html)
