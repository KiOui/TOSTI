from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from associations.models import Association
from tantalus import services
from borrel.models import BorrelReservation, ReservationItem, Product
from tantalus.models import TantalusAssociation, TantalusBorrelProduct
from tantalus.services import TantalusException

User = get_user_model()


class TantalusServicesTests(TestCase):
    fixtures = ["users.json", "associations.json", "borrel.json", "tantalus.json"]

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.get(pk=1)
        association = Association.objects.get(pk=1)
        cls.tantalus_association = TantalusAssociation.objects.get(association=association)
        cls.association = association
        product_1 = Product.objects.get(pk=1)
        product_2 = Product.objects.get(pk=2)
        product_3 = Product.objects.get(pk=3)
        product_4 = Product.objects.get(pk=4)
        product_5 = Product.objects.get(pk=5)
        product_6 = Product.objects.get(pk=6)
        cls.tantalus_product_1 = TantalusBorrelProduct.objects.get(product=product_1)
        cls.tantalus_product_2 = TantalusBorrelProduct.objects.get(product=product_2)
        cls.tantalus_product_3 = TantalusBorrelProduct.objects.get(product=product_3)
        cls.tantalus_product_4 = TantalusBorrelProduct.objects.get(product=product_4)
        cls.tantalus_product_6 = TantalusBorrelProduct.objects.get(product=product_6)
        cls.product_1 = product_1
        cls.product_2 = product_2
        cls.product_3 = product_3
        cls.product_4 = product_4
        cls.product_5 = product_5
        cls.product_6 = product_6

    def setUp(self):
        self.borrel_reservation = BorrelReservation.objects.create(
            title="Test Borrel Reservation",
            start=timezone.now() + timedelta(hours=2),
            end=timezone.now() + timedelta(hours=8),
            user_created=self.user,
            user_updated=self.user,
            association=self.association,
        )
        self.reservation_item_1 = ReservationItem.objects.create(
            reservation=self.borrel_reservation, product=self.product_1, amount_reserved=5
        )
        self.reservation_item_2 = ReservationItem.objects.create(
            reservation=self.borrel_reservation, product=self.product_2, amount_reserved=18
        )
        self.reservation_item_3 = ReservationItem.objects.create(
            reservation=self.borrel_reservation, product=self.product_3, amount_reserved=9
        )
        self.reservation_item_4 = ReservationItem.objects.create(
            reservation=self.borrel_reservation, product=self.product_4, amount_reserved=1
        )
        self.reservation_items = [
            self.reservation_item_1,
            self.reservation_item_2,
            self.reservation_item_3,
            self.reservation_item_4,
        ]

    def set_amounts_used(self):
        for reservation_item in self.reservation_items:
            reservation_item.amount_used = reservation_item.amount_reserved
            reservation_item.save()

    @patch("tantalus.services.get_tantalus_client")
    def test_synchronize_borrelreservation_to_tantalus(self, _get_tantalus_client_mock: MagicMock):
        self.set_amounts_used()
        tantalus_client_mock = MagicMock()
        tantalus_client_mock.register_transaction.return_value = True
        _get_tantalus_client_mock.return_value = tantalus_client_mock
        services.synchronize_borrelreservation_to_tantalus(self.borrel_reservation)
        tantalus_client_mock.register_transaction.assert_called_with(
            self.tantalus_association,
            self.borrel_reservation.submitted_at,
            description=self.borrel_reservation.title,
            sell=[
                {
                    "id": self.tantalus_product_1.tantalus_id,
                    "amount": 5,
                },
                {
                    "id": self.tantalus_product_2.tantalus_id,
                    "amount": 18,
                },
                {
                    "id": self.tantalus_product_3.tantalus_id,
                    "amount": 9,
                },
                {
                    "id": self.tantalus_product_4.tantalus_id,
                    "amount": 1,
                },
            ],
        )

    @patch("tantalus.services.TantalusClient.can_create_client")
    def test_synchronize_borrelreservation_to_tantalus_no_tantalus_client(self, _can_create_client_mock: MagicMock):
        _can_create_client_mock.return_value = False

        def throw_exception():
            services.synchronize_borrelreservation_to_tantalus(self.borrel_reservation)

        self.assertRaises(TantalusException, throw_exception)

    @patch("tantalus.services.get_tantalus_client")
    def test_synchronize_borrelreservation_to_tantalus_no_association_set(self, _get_tantalus_client_mock: MagicMock):
        _get_tantalus_client_mock.return_value = None
        self.borrel_reservation.association = None
        self.borrel_reservation.save()

        def throw_exception():
            services.synchronize_borrelreservation_to_tantalus(self.borrel_reservation)

        self.assertRaises(TantalusException, throw_exception)

    @patch("tantalus.services.get_tantalus_client")
    def test_synchronize_borrelreservation_to_tantalus_no_tantalus_association_set(
        self, _get_tantalus_client_mock: MagicMock
    ):
        _get_tantalus_client_mock.return_value = None
        association_without_tantalus = Association.objects.create(name="No tantalus association set")
        self.borrel_reservation.association = association_without_tantalus
        self.borrel_reservation.save()

        def throw_exception():
            services.synchronize_borrelreservation_to_tantalus(self.borrel_reservation)

        self.assertRaises(TantalusException, throw_exception)

    @patch("tantalus.services.get_tantalus_client")
    def test_synchronize_borrelreservation_to_tantalus_no_amount_used_set(self, _get_tantalus_client_mock: MagicMock):
        _get_tantalus_client_mock.return_value = None
        self.set_amounts_used()
        self.reservation_item_3.amount_used = None
        self.reservation_item_3.save()

        def throw_exception():
            services.synchronize_borrelreservation_to_tantalus(self.borrel_reservation)

        self.assertRaises(TantalusException, throw_exception)

    @patch("tantalus.services.get_tantalus_client")
    def test_synchronize_borrelreservation_to_tantalus_amount_used_0(self, _get_tantalus_client_mock: MagicMock):
        self.set_amounts_used()
        self.reservation_item_4.amount_used = 0
        self.reservation_item_4.save()
        tantalus_client_mock = MagicMock()
        tantalus_client_mock.register_transaction.return_value = True
        _get_tantalus_client_mock.return_value = tantalus_client_mock
        services.synchronize_borrelreservation_to_tantalus(self.borrel_reservation)
        tantalus_client_mock.register_transaction.assert_called_with(
            self.tantalus_association,
            self.borrel_reservation.submitted_at,
            description=self.borrel_reservation.title,
            sell=[
                {
                    "id": self.tantalus_product_1.tantalus_id,
                    "amount": 5,
                },
                {
                    "id": self.tantalus_product_2.tantalus_id,
                    "amount": 18,
                },
                {
                    "id": self.tantalus_product_3.tantalus_id,
                    "amount": 9,
                },
            ],
        )

    @patch("tantalus.services.get_tantalus_client")
    def test_synchronize_borrelreservation_to_tantalus_no_borrelproduct_registered(
        self, _get_tantalus_client_mock: MagicMock
    ):
        _get_tantalus_client_mock.return_value = None
        self.set_amounts_used()
        TantalusBorrelProduct.objects.get(product=self.reservation_item_2.product).delete()

        def throw_exception():
            services.synchronize_borrelreservation_to_tantalus(self.borrel_reservation)

        self.assertRaises(TantalusException, throw_exception)

    @patch("tantalus.services.get_tantalus_client")
    def test_synchronize_borrelreservation_to_tantalus_non_submittable_product(
        self, _get_tantalus_client_mock: MagicMock
    ):
        self.set_amounts_used()
        ReservationItem.objects.create(
            reservation=self.borrel_reservation,
            product=self.product_5,
            amount_reserved=15,
        )
        tantalus_client_mock = MagicMock()
        tantalus_client_mock.register_transaction.return_value = True
        _get_tantalus_client_mock.return_value = tantalus_client_mock
        services.synchronize_borrelreservation_to_tantalus(self.borrel_reservation)
        tantalus_client_mock.register_transaction.assert_called_with(
            self.tantalus_association,
            self.borrel_reservation.submitted_at,
            description=self.borrel_reservation.title,
            sell=[
                {
                    "id": self.tantalus_product_1.tantalus_id,
                    "amount": 5,
                },
                {
                    "id": self.tantalus_product_2.tantalus_id,
                    "amount": 18,
                },
                {
                    "id": self.tantalus_product_3.tantalus_id,
                    "amount": 9,
                },
                {
                    "id": self.tantalus_product_4.tantalus_id,
                    "amount": 1,
                },
            ],
        )

    @patch("tantalus.services.get_tantalus_client")
    def test_synchronize_borrelreservation_to_tantalus_non_reservable_product(
        self, _get_tantalus_client_mock: MagicMock
    ):
        self.set_amounts_used()
        ReservationItem.objects.create(
            reservation=self.borrel_reservation, product=self.product_6, amount_reserved=15, amount_used=17
        )
        tantalus_client_mock = MagicMock()
        tantalus_client_mock.register_transaction.return_value = True
        _get_tantalus_client_mock.return_value = tantalus_client_mock
        services.synchronize_borrelreservation_to_tantalus(self.borrel_reservation)
        tantalus_client_mock.register_transaction.assert_called_with(
            self.tantalus_association,
            self.borrel_reservation.submitted_at,
            description=self.borrel_reservation.title,
            sell=[
                {
                    "id": self.tantalus_product_1.tantalus_id,
                    "amount": 5,
                },
                {
                    "id": self.tantalus_product_2.tantalus_id,
                    "amount": 18,
                },
                {
                    "id": self.tantalus_product_3.tantalus_id,
                    "amount": 9,
                },
                {
                    "id": self.tantalus_product_4.tantalus_id,
                    "amount": 1,
                },
                {
                    "id": self.tantalus_product_6.tantalus_id,
                    "amount": 17,
                },
            ],
        )
