from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from associations.models import Association
from silvasoft import services
from borrel.models import BorrelReservation, ReservationItem, Product as BorrelProduct
from silvasoft.models import SilvasoftAssociation, SilvasoftBorrelProduct
from silvasoft.services import SilvasoftException

User = get_user_model()


class SilvasoftServicesTests(TestCase):
    fixtures = ["users.json", "associations.json", "borrel.json", "silvasoft.json"]

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.get(pk=1)
        association = Association.objects.get(pk=1)
        cls.silvasoft_association = SilvasoftAssociation.objects.get(association=association)
        cls.association = association
        product_1 = BorrelProduct.objects.get(pk=1)
        product_2 = BorrelProduct.objects.get(pk=2)
        product_3 = BorrelProduct.objects.get(pk=3)
        product_4 = BorrelProduct.objects.get(pk=4)
        product_5 = BorrelProduct.objects.get(pk=5)
        product_6 = BorrelProduct.objects.get(pk=6)
        cls.silvasoft_product_1 = SilvasoftBorrelProduct.objects.get(product=product_1)
        cls.silvasoft_product_2 = SilvasoftBorrelProduct.objects.get(product=product_2)
        cls.silvasoft_product_3 = SilvasoftBorrelProduct.objects.get(product=product_3)
        cls.silvasoft_product_4 = SilvasoftBorrelProduct.objects.get(product=product_4)
        cls.silvasoft_product_6 = SilvasoftBorrelProduct.objects.get(product=product_6)
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

    @patch("silvasoft.services.get_silvasoft_client")
    def test_synchronize_borrelreservation_to_silvasoft(self, _get_silvasoft_client_mock: MagicMock):
        self.set_amounts_used()
        silvasoft_client_mock = MagicMock()
        silvasoft_client_mock.add_sales_invoice.return_value = True
        _get_silvasoft_client_mock.return_value = silvasoft_client_mock
        services.synchronize_borrelreservation_to_silvasoft(self.borrel_reservation, "test-identifier")
        silvasoft_client_mock.add_sales_invoice.assert_called_with(
            json={
                "CustomerNumber": self.silvasoft_association.silvasoft_customer_number,
                "InvoiceNotes": "Borrel reservation: {}<br>Date: {}<br>Responsible: {}<br>Synchronisation ID: {}".format(
                    self.borrel_reservation.id,
                    self.borrel_reservation.start.strftime("%d-%m-%Y"),
                    self.borrel_reservation.user_submitted,
                    "test-identifier",
                ),
                "Invoice_InvoiceLine": [
                {
                    "ProductNumber": self.silvasoft_product_1.silvasoft_product_number,
                    "Quantity": 5,
                    "UseArticlePrice": True,
                },
                {
                    "ProductNumber": self.silvasoft_product_2.silvasoft_product_number,
                    "Quantity": 18,
                    "UseArticlePrice": True,
                },
                {
                    "ProductNumber": self.silvasoft_product_3.silvasoft_product_number,
                    "Quantity": 9,
                    "UseArticlePrice": True,
                },
                {
                    "ProductNumber": self.silvasoft_product_4.silvasoft_product_number,
                    "Quantity": 1,
                    "UseArticlePrice": True,
                },
            ]},
        )

    @patch("silvasoft.services.SilvasoftClient.can_create_client")
    def test_synchronize_borrelreservation_to_silvasoft_no_silvasoft_client(self, _can_create_client_mock: MagicMock):
        _can_create_client_mock.return_value = False

        def throw_exception():
            services.synchronize_borrelreservation_to_silvasoft(self.borrel_reservation, "test-identifier")

        self.assertRaises(SilvasoftException, throw_exception)

    @patch("silvasoft.services.get_silvasoft_client")
    def test_synchronize_borrelreservation_to_silvasoft_no_association_set(self, _get_silvasoft_client_mock: MagicMock):
        _get_silvasoft_client_mock.return_value = None
        self.borrel_reservation.association = None
        self.borrel_reservation.save()

        def throw_exception():
            services.synchronize_borrelreservation_to_silvasoft(self.borrel_reservation, "test-identifier")

        self.assertRaises(SilvasoftException, throw_exception)

    @patch("silvasoft.services.get_silvasoft_client")
    def test_synchronize_borrelreservation_to_silvasoft_no_silvasoft_association_set(
            self, _get_silvasoft_client_mock: MagicMock
    ):
        _get_silvasoft_client_mock.return_value = None
        association_without_silvasoft = Association.objects.create(name="No silvasoft association set")
        self.borrel_reservation.association = association_without_silvasoft
        self.borrel_reservation.save()

        def throw_exception():
            services.synchronize_borrelreservation_to_silvasoft(self.borrel_reservation, "test-identifier")

        self.assertRaises(SilvasoftException, throw_exception)

    @patch("silvasoft.services.get_silvasoft_client")
    def test_synchronize_borrelreservation_to_silvasoft_no_amount_used_set(self, _get_silvasoft_client_mock: MagicMock):
        _get_silvasoft_client_mock.return_value = None
        self.set_amounts_used()
        self.reservation_item_3.amount_used = None
        self.reservation_item_3.save()

        def throw_exception():
            services.synchronize_borrelreservation_to_silvasoft(self.borrel_reservation, "test-identifier")

        self.assertRaises(SilvasoftException, throw_exception)

    @patch("silvasoft.services.get_silvasoft_client")
    def test_synchronize_borrelreservation_to_silvasoft_amount_used_0(self, _get_silvasoft_client_mock: MagicMock):
        self.set_amounts_used()
        self.reservation_item_4.amount_used = 0
        self.reservation_item_4.save()
        silvasoft_client_mock = MagicMock()
        silvasoft_client_mock.add_sales_invoice.return_value = True
        _get_silvasoft_client_mock.return_value = silvasoft_client_mock
        services.synchronize_borrelreservation_to_silvasoft(self.borrel_reservation, "test-identifier")
        silvasoft_client_mock.add_sales_invoice.assert_called_with(
            json={
                "CustomerNumber": self.silvasoft_association.silvasoft_customer_number,
                "InvoiceNotes": "Borrel reservation: {}<br>Date: {}<br>Responsible: {}<br>Synchronisation ID: {}".format(
                    self.borrel_reservation.id,
                    self.borrel_reservation.start.strftime("%d-%m-%Y"),
                    self.borrel_reservation.user_submitted,
                    "test-identifier",
                ),
                "Invoice_InvoiceLine": [
                {
                    "ProductNumber": self.silvasoft_product_1.silvasoft_product_number,
                    "Quantity": 5,
                    "UseArticlePrice": True,
                },
                {
                    "ProductNumber": self.silvasoft_product_2.silvasoft_product_number,
                    "Quantity": 18,
                    "UseArticlePrice": True,
                },
                {
                    "ProductNumber": self.silvasoft_product_3.silvasoft_product_number,
                    "Quantity": 9,
                    "UseArticlePrice": True,
                },
            ]},
        )

    @patch("silvasoft.services.get_silvasoft_client")
    def test_synchronize_borrelreservation_to_silvasoft_no_borrelproduct_registered(
            self, _get_silvasoft_client_mock: MagicMock
    ):
        self.set_amounts_used()
        SilvasoftBorrelProduct.objects.get(product=self.reservation_item_2.product).delete()

        def throw_exception():
            services.synchronize_borrelreservation_to_silvasoft(self.borrel_reservation, "test-identifier")

        self.assertRaises(SilvasoftException, throw_exception)

    @patch("silvasoft.services.get_silvasoft_client")
    def test_synchronize_borrelreservation_to_silvasoft_more_than_75_line_items(
            self, _get_silvasoft_client_mock: MagicMock
    ):
        _get_silvasoft_client_mock.return_value = None
        borrel_reservation_too_many_line_items = BorrelReservation.objects.create(
            title="Test Borrel Reservation too many line items",
            start=timezone.now() + timedelta(hours=2),
            end=timezone.now() + timedelta(hours=8),
            user_created=self.user,
            user_updated=self.user,
            association=self.association,
        )
        for i in range(0, 76):
            new_borrel_product = BorrelProduct.objects.create(
                name="Product test {}".format(i),
                price=10,
            )
            SilvasoftBorrelProduct.objects.create(
                silvasoft_product_number="test-{}".format(i),
                product=new_borrel_product,
            )
            ReservationItem.objects.create(
                reservation=borrel_reservation_too_many_line_items,
                product=new_borrel_product,
                amount_reserved=4,
                amount_used=4,
                product_name="Product test {}".format(i),
                product_price_per_unit=10,
            )
        def throw_exception():
            services.synchronize_borrelreservation_to_silvasoft(borrel_reservation_too_many_line_items, "test-identifier")

        self.assertRaises(SilvasoftException, throw_exception)

    @patch("silvasoft.services.get_silvasoft_client")
    def test_synchronize_borrelreservation_to_silvasoft_non_submittable_product(
            self, _get_silvasoft_client_mock: MagicMock
    ):
        self.set_amounts_used()
        ReservationItem.objects.create(
            reservation=self.borrel_reservation,
            product=self.product_5,
            amount_reserved=15,
        )
        silvasoft_client_mock = MagicMock()
        silvasoft_client_mock.add_sales_invoice.return_value = True
        _get_silvasoft_client_mock.return_value = silvasoft_client_mock
        services.synchronize_borrelreservation_to_silvasoft(self.borrel_reservation, "test-identifier")
        silvasoft_client_mock.add_sales_invoice.assert_called_with(
            json={
                "CustomerNumber": self.silvasoft_association.silvasoft_customer_number,
                "InvoiceNotes": "Borrel reservation: {}<br>Date: {}<br>Responsible: {}<br>Synchronisation ID: {}".format(
                    self.borrel_reservation.id,
                    self.borrel_reservation.start.strftime("%d-%m-%Y"),
                    self.borrel_reservation.user_submitted,
                    "test-identifier",
                ),
                "Invoice_InvoiceLine": [
                {
                    "ProductNumber": self.silvasoft_product_1.silvasoft_product_number,
                    "Quantity": 5,
                    "UseArticlePrice": True,
                },
                {
                    "ProductNumber": self.silvasoft_product_2.silvasoft_product_number,
                    "Quantity": 18,
                    "UseArticlePrice": True,
                },
                {
                    "ProductNumber": self.silvasoft_product_3.silvasoft_product_number,
                    "Quantity": 9,
                    "UseArticlePrice": True,
                },
                {
                    "ProductNumber": self.silvasoft_product_4.silvasoft_product_number,
                    "Quantity": 1,
                    "UseArticlePrice": True,
                },
            ]},
        )

    @patch("silvasoft.services.get_silvasoft_client")
    def test_synchronize_borrelreservation_to_silvasoft_non_reservable_product(
            self, _get_silvasoft_client_mock: MagicMock
    ):
        self.set_amounts_used()
        ReservationItem.objects.create(
            reservation=self.borrel_reservation, product=self.product_6, amount_reserved=15, amount_used=17
        )
        silvasoft_client_mock = MagicMock()
        silvasoft_client_mock.add_sales_invoice.return_value = True
        _get_silvasoft_client_mock.return_value = silvasoft_client_mock
        services.synchronize_borrelreservation_to_silvasoft(self.borrel_reservation, "test-identifier")
        silvasoft_client_mock.add_sales_invoice.assert_called_with(
            json={
                "CustomerNumber": self.silvasoft_association.silvasoft_customer_number,
                "InvoiceNotes": "Borrel reservation: {}<br>Date: {}<br>Responsible: {}<br>Synchronisation ID: {}".format(
                    self.borrel_reservation.id,
                    self.borrel_reservation.start.strftime("%d-%m-%Y"),
                    self.borrel_reservation.user_submitted,
                    "test-identifier",
                ),
                "Invoice_InvoiceLine": [{
                    "ProductNumber": self.silvasoft_product_1.silvasoft_product_number,
                    "Quantity": 5,
                    "UseArticlePrice": True,
                },
                    {
                        "ProductNumber": self.silvasoft_product_2.silvasoft_product_number,
                        "Quantity": 18,
                        "UseArticlePrice": True,
                    },
                    {
                        "ProductNumber": self.silvasoft_product_3.silvasoft_product_number,
                        "Quantity": 9,
                        "UseArticlePrice": True,
                    },
                    {
                        "ProductNumber": self.silvasoft_product_4.silvasoft_product_number,
                        "Quantity": 1,
                        "UseArticlePrice": True,
                    },
                    {
                        "ProductNumber": self.silvasoft_product_6.silvasoft_product_number,
                        "Quantity": 17,
                        "UseArticlePrice": True,
                    }],
            },
        )
