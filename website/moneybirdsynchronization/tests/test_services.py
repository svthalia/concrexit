from random import randint
from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone

from freezegun import freeze_time

from events.models.event import Event
from members.models import Member
from moneybirdsynchronization import services
from moneybirdsynchronization.administration import Administration
from moneybirdsynchronization.models import (
    MoneybirdContact,
    MoneybirdExternalInvoice,
    MoneybirdPayment,
)
from payments.models import BankAccount, Payment
from payments.services import create_payment
from pizzas.models import FoodEvent, FoodOrder
from pizzas.models import Product as FoodProduct
from registrations.models import Renewal
from sales.models.order import Order, OrderItem
from sales.models.product import Product as SalesProduct
from sales.models.product import ProductList
from sales.models.shift import Shift


# Each test method has a mock_api argument that is a MagicMock instance, replacing the
# MoneybirdAPIService *class*. To check calls or set behaviour of a MoneybirdAPIService
# *instance*, use `mock_api.return_value.<MoneybirdAPIService method>`.
@mock.patch("moneybirdsynchronization.moneybird.MoneybirdAPIService", autospec=True)
@override_settings(  # Settings needed to enable synchronization.
    MONEYBIRD_START_DATE="2023-09-01",
    MONEYBIRD_ADMINISTRATION_ID="123",
    MONEYBIRD_API_KEY="foo",
    MONEYBIRD_SYNC_ENABLED=True,
    SUSPEND_SIGNALS=True,
)
class ServicesTest(TestCase):
    fixtures = ["members.json", "bank_accounts.json", "products.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.get(pk=1)
        cls.member2 = Member.objects.get(pk=2)
        cls.member3 = Member.objects.get(pk=3)
        cls.member4 = Member.objects.get(pk=4)
        cls.bank_account = cls.member.bank_accounts.first()

    def test_create_or_update_contact_with_mandate(self, mock_api):
        """Creating/updating a contact with a mandate excludes the mandate if it starts today.

        This is a limitation imposed by the Moneybird API.
        See: https://github.com/svthalia/concrexit/issues/3295.
        """
        # Drop the fixtures, we create our own bank account here.
        BankAccount.objects.all().delete()

        mock_create_contact = mock_api.return_value.create_contact
        mock_update_contact = mock_api.return_value.update_contact

        mock_create_contact.return_value = {"id": "1", "sepa_mandate_id": ""}
        mock_update_contact.return_value = {"id": "1", "sepa_mandate_id": ""}

        # Bank account is valid from 2016-07-07.
        with freeze_time("2016-07-07"):
            bank_account = BankAccount.objects.create(
                owner=self.member,
                iban="NL12ABNA1234567890",
                initials="J.",
                last_name="Doe",
                valid_from=timezone.now().date(),
                signature="base64,png",
                mandate_no="1-1",
            )

            with self.subTest("Creating a contact does not push today's SEPA mandate."):
                services.create_or_update_contact(self.member)
                mock_create_contact.assert_called_once()
                mock_update_contact.assert_not_called()

                data = mock_create_contact.call_args[0][0]
                self.assertNotIn("sepa_mandate_id", data["contact"])

                moneybird_contact = self.member.moneybird_contact
                self.assertEqual(moneybird_contact.moneybird_sepa_mandate_id, None)

            mock_create_contact.reset_mock()
            mock_update_contact.reset_mock()

            with self.subTest("Updating a contact does not push today's SEPA mandate."):
                services.create_or_update_contact(self.member)
                mock_create_contact.assert_not_called()
                mock_update_contact.assert_called_once()

                data = mock_update_contact.call_args[0][1]
                self.assertEqual(mock_update_contact.call_args[0][0], "1")
                self.assertNotIn("sepa_mandate_id", data["contact"])

                moneybird_contact.refresh_from_db()
                self.assertEqual(moneybird_contact.moneybird_sepa_mandate_id, None)

        moneybird_contact.delete()
        mock_create_contact.reset_mock()
        mock_update_contact.reset_mock()
        mock_create_contact.return_value = {"id": "1", "sepa_mandate_id": "1-1"}
        mock_update_contact.return_value = {"id": "1", "sepa_mandate_id": "1-1"}

        with freeze_time("2016-07-08"):
            with self.subTest("Creating a contact pushes past SEPA mandate."):
                services.create_or_update_contact(self.member)
                mock_create_contact.assert_called_once()
                mock_update_contact.assert_not_called()

                data = mock_create_contact.call_args[0][0]
                self.assertEqual(data["contact"]["sepa_mandate_id"], "1-1")

                moneybird_contact = self.member.moneybird_contact
                self.assertEqual(moneybird_contact.moneybird_sepa_mandate_id, "1-1")

            mock_create_contact.reset_mock()
            mock_update_contact.reset_mock()

            with self.subTest("Updating a contact pushes past SEPA mandate."):
                services.create_or_update_contact(self.member)
                mock_create_contact.assert_not_called()
                mock_update_contact.assert_called_once()

                data = mock_update_contact.call_args[0][1]
                self.assertEqual(mock_update_contact.call_args[0][0], "1")
                self.assertEqual(data["contact"]["sepa_mandate_id"], "1-1")

                moneybird_contact.refresh_from_db()
                self.assertEqual(moneybird_contact.moneybird_sepa_mandate_id, "1-1")

    @mock.patch("moneybirdsynchronization.services.create_or_update_contact")
    def test_sync_contacts_with_outdated_mandates(
        self, mock_create_or_update_contact, mock_api
    ):
        # Drop the fixtures, we create our own bank account here.
        BankAccount.objects.all().delete()

        # Valid and already pushed.
        ba1 = BankAccount.objects.create(
            owner=self.member,
            iban="NL12ABNA1234567890",
            initials="J.",
            last_name="Doe",
            valid_from=timezone.now().date() - timezone.timedelta(days=1),
            signature="base64,png",
            mandate_no="1-1",
        )
        # Valid and new.
        ba2 = BankAccount.objects.create(
            owner=self.member2,
            iban="NL12ABNA1234567891",
            initials="J.",
            last_name="Doe",
            valid_from=timezone.now().date() - timezone.timedelta(days=1),
            signature="base64,png",
            mandate_no="2-1",
        )

        # Outdated and already pushed.
        BankAccount.objects.create(
            owner=self.member3,
            iban="NL12ABNA1234567892",
            initials="J.",
            last_name="Doe",
            valid_from=timezone.now().date() - timezone.timedelta(days=10),
            valid_until=timezone.now().date() - timezone.timedelta(days=2),
            signature="base64,png",
            mandate_no="3-1",
        )
        # Valid and an outdated mandate already pushed.
        BankAccount.objects.create(
            owner=self.member3,
            iban="NL12ABNA1234567892",
            initials="J.",
            last_name="Doe",
            valid_from=timezone.now().date() - timezone.timedelta(days=1),
            signature="base64,png",
            mandate_no="3-2",
        )

        MoneybirdContact.objects.create(
            member=self.member, moneybird_id="1", moneybird_sepa_mandate_id="1-1"
        )
        MoneybirdContact.objects.create(
            member=self.member2, moneybird_id="2", moneybird_sepa_mandate_id=None
        )
        MoneybirdContact.objects.create(
            member=self.member3, moneybird_id="3", moneybird_sepa_mandate_id="3-1"
        )
        MoneybirdContact.objects.create(member=self.member4, moneybird_id="4")

        services._sync_contacts_with_outdated_mandates()

        self.assertEqual(mock_create_or_update_contact.call_count, 2)
        members = [x[0][0].pk for x in mock_create_or_update_contact.call_args_list]
        self.assertCountEqual(members, [self.member2.pk, self.member3.pk])

    def test_delete_invoices(self, mock_api):
        """Invoices marked for deletion are deleted."""
        renewal1 = Renewal.objects.create(
            member=self.member, length=Renewal.MEMBERSHIP_YEAR
        )
        renewal2 = Renewal.objects.create(
            member=self.member2, length=Renewal.MEMBERSHIP_YEAR
        )
        invoice1 = MoneybirdExternalInvoice.objects.create(
            payable_object=renewal1,
            needs_synchronization=False,
            moneybird_invoice_id="1",
        )
        invoice2 = MoneybirdExternalInvoice.objects.create(
            payable_object=renewal2,
            needs_synchronization=False,
            moneybird_invoice_id="2",
        )

        # _delete_invoices calls the delete_external_invoice API directly.
        mock_delete_invoice = mock_api.return_value.delete_external_invoice

        with self.subTest("Invoices without needs_deletion are not deleted."):
            services._delete_invoices()
            self.assertEqual(mock_delete_invoice.call_count, 0)

        invoice1.needs_deletion = True
        invoice2.needs_deletion = True
        invoice1.save()
        invoice2.save()

        mock_delete_invoice.reset_mock()
        mock_delete_invoice.side_effect = Administration.InvalidData(400)

        with self.subTest("All invoices are tried even after an exception"):
            services._delete_invoices()
            self.assertEqual(mock_delete_invoice.call_count, 2)

            # Deletion failed so the objects are still in the database.
            self.assertEqual(
                MoneybirdExternalInvoice.objects.filter(needs_deletion=True).count(), 2
            )

        mock_delete_invoice.reset_mock()
        mock_delete_invoice.side_effect = None

        invoice1.moneybird_invoice_id = None
        invoice1.needs_synchronization = True
        invoice1.save()

        with self.subTest("Invoices with needs_deletion are deleted."):
            services._delete_invoices()

            # Only one invoice has a moneybird_invoice_id, so only one call is made.
            mock_delete_invoice.assert_called_once_with(invoice2.moneybird_invoice_id)

            # The other has its object removed from the database without an API call.
            self.assertEqual(
                MoneybirdExternalInvoice.objects.filter(needs_deletion=True).count(), 0
            )

    @mock.patch("moneybirdsynchronization.services.create_or_update_external_invoice")
    def test_sync_outdated_invoices(self, mock_update_invoice, mock_api):
        """Invoices marked with needs_synchronization are updated."""
        renewal1 = Renewal.objects.create(
            member=self.member, length=Renewal.MEMBERSHIP_YEAR
        )
        renewal2 = Renewal.objects.create(
            member=self.member2, length=Renewal.MEMBERSHIP_YEAR
        )
        invoice1 = MoneybirdExternalInvoice.objects.create(payable_object=renewal1)
        invoice2 = MoneybirdExternalInvoice.objects.create(payable_object=renewal2)

        with self.subTest("Invoices with needs_synchronization are updated."):
            services._sync_outdated_invoices()
            self.assertEqual(mock_update_invoice.call_count, 2)

        mock_update_invoice.reset_mock()
        mock_update_invoice.side_effect = Administration.InvalidData(400)

        with self.subTest("All invoices are tried even after an exception"):
            services._sync_outdated_invoices()
            self.assertEqual(mock_update_invoice.call_count, 2)

        mock_update_invoice.reset_mock()
        mock_update_invoice.side_effect = None

        invoice1.needs_synchronization = False
        invoice1.save()
        invoice2.needs_synchronization = False
        invoice2.save()

        with self.subTest("Invoices without needs_synchronization are not updated."):
            services._sync_outdated_invoices()
            self.assertEqual(mock_update_invoice.call_count, 0)

    def test_sync_moneybird_payments(self, mock_api):
        """MoneybirdPayments are created for any new (non-wire) payments."""
        # Payments from before settings.MONEYBIRD_START_DATE are ignored.
        p1 = Payment.objects.create(
            type=Payment.CASH, amount=5, created_at="2000-01-01"
        )

        p2 = Payment.objects.create(
            type=Payment.CASH, amount=10, created_at="2023-10-15"
        )
        p3 = Payment.objects.create(
            type=Payment.CASH, amount=15, created_at="2023-10-15"
        )
        p4 = Payment.objects.create(
            type=Payment.TPAY,
            amount=20,
            created_at="2023-10-15",
            paid_by=self.member,
            processed_by=self.member,
        )

        # Payments that are already synchronized are ignored.
        p5 = Payment.objects.create(
            type=Payment.CARD, amount=25, created_at="2023-10-15"
        )
        MoneybirdPayment.objects.create(
            payment=p5,
            moneybird_financial_statement_id="0",
            moneybird_financial_mutation_id="0",
        )

        def side_effect(data):
            """Return a new financial statement with plausible mutations for each call."""
            return {
                "id": str(randint(1e10, 9e10)),
                "financial_mutations": [
                    {
                        "id": str(randint(1e10, 9e10)),
                        "amount": f"{float(mut['amount']):0.2f}",
                        "batch_reference": mut["batch_reference"],
                    }
                    for mut in data["financial_statement"][
                        "financial_mutations_attributes"
                    ].values()
                ],
            }

        mock_create_statement = mock_api.return_value.create_financial_statement

        mock_create_statement.side_effect = side_effect

        with freeze_time("2023-10-15"):
            services._sync_moneybird_payments()

        # Statements should be created only for TPAY and CASH payments.
        self.assertEqual(mock_create_statement.call_count, 2)

        data1 = mock_create_statement.call_args_list[0][0][0]["financial_statement"]
        data2 = mock_create_statement.call_args_list[1][0][0]["financial_statement"]

        # Check that the
        self.assertEqual(len(data1["financial_mutations_attributes"]), 2)
        self.assertEqual(len(data2["financial_mutations_attributes"]), 1)
        mut1 = data1["financial_mutations_attributes"]["0"]
        mut2 = data1["financial_mutations_attributes"]["1"]
        mut3 = data2["financial_mutations_attributes"]["0"]
        self.assertIn(mut1["batch_reference"], (str(p2.id), str(p3.id)))
        self.assertIn(mut2["batch_reference"], (str(p2.id), str(p3.id)))
        self.assertEqual(mut3["batch_reference"], str(p4.id))

        # MoneybirdPayments should now exist for all payments except p1.
        self.assertEqual(
            MoneybirdPayment.objects.filter(payment__in=[p1, p2, p3, p4, p5]).count(), 4
        )

    @mock.patch("moneybirdsynchronization.services.create_or_update_external_invoice")
    def test_sync_food_orders(self, mock_create_invoice, mock_api):
        """Invoices are made for food orders."""
        event = Event.objects.create(
            title="testevent",
            description="desc",
            start=timezone.now(),
            end=(timezone.now() + timezone.timedelta(hours=1)),
            location="test location",
            map_location="test map location",
            price=0.00,
            fine=0.00,
        )
        food_event = FoodEvent.objects.create(
            event=event,
            start=timezone.now(),
            end=(timezone.now() + timezone.timedelta(hours=1)),
        )
        product = FoodProduct.objects.create(name="foo", description="bar", price=1.00)
        order1 = FoodOrder.objects.create(
            member=Member.objects.get(pk=1),
            food_event=food_event,
            product=product,
        )
        order2 = FoodOrder.objects.create(
            name="John Doe",
            food_event=food_event,
            product=product,
        )

        services._sync_food_orders()
        self.assertEqual(mock_create_invoice.call_count, 2)

    @mock.patch("moneybirdsynchronization.services.create_or_update_external_invoice")
    def test_sync_sales_orders(self, mock_create_invoice, mock_api):
        """Invoices are created for paid sales orders."""
        beer = SalesProduct.objects.get(name="beer")
        soda = SalesProduct.objects.get(name="soda")
        shift = Shift.objects.create(
            start=timezone.now(),
            end=timezone.now() + timezone.timedelta(hours=1),
            product_list=ProductList.objects.get(name="normal"),
        )

        order1 = Order.objects.create(shift=shift, payer=self.member)
        OrderItem.objects.create(
            order=order1,
            product=shift.product_list.product_items.get(product=soda),
            amount=2,
        )

        order2 = Order.objects.create(shift=shift, payer=self.member)
        OrderItem.objects.create(
            order=order2,
            product=shift.product_list.product_items.get(product=beer),
            amount=1,
        )

        # Order 1 is free, and no invoice should be made for it.
        create_payment(order2, self.member, Payment.TPAY)

        services._sync_sales_orders()

        mock_create_invoice.assert_called_once_with(order2)

    def test_sync_renewals(self, mock_api):
        raise NotImplementedError

    def test_sync_registrations(self, mock_api):
        raise NotImplementedError

    def test_sync_event_registrations(self, mock_api):
        raise NotImplementedError
