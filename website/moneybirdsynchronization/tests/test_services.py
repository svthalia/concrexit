from random import randint
from unittest import mock

from django.test import TestCase, override_settings

from freezegun import freeze_time

from members.models import Member
from moneybirdsynchronization import services
from moneybirdsynchronization.models import MoneybirdPayment
from payments.models import Payment


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
    fixtures = ["members.json", "bank_accounts.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.get(pk=1)
        cls.bank_account = cls.member.bank_accounts.first()

    def test_create_or_update_contact_with_mandate(self, mock_api):
        """Creating/updating a contact with a mandate excludes the mandate if it starts today.

        This is a limitation imposed by the Moneybird API.
        See: https://github.com/svthalia/concrexit/issues/3295.
        """
        # TODO: set mock response values:
        mock_api.return_value.create_contact.return_value = {}
        mock_api.return_value.update_contact.return_value = {}

        # Bank account is valid from 2016-07-07.
        with freeze_time("2016-07-07"):
            with self.subTest("Creating a contact does not push today's SEPA mandate."):
                services.create_or_update_contact(self.member)
                mock_api.return_value.create_contact.assert_called_once_with(
                    {},  # TODO: fill in the expected content, i.e. without the bank account.
                    # Possibly the mock return values need to be changed between the subtests.
                )

            with self.subTest("Updating a contact does not push today's SEPA mandate."):
                raise NotImplementedError

        with freeze_time("2016-07-08"):
            with self.subTest("Creating a contact pushes past SEPA mandate."):
                raise NotImplementedError

            with self.subTest("Updating a contact pushes past SEPA mandate."):
                raise NotImplementedError

    @mock.patch("moneybirdsynchronization.services.create_or_update_contact")
    def test_sync_contacts_with_outdated_mandates(
        self, mock_api, mock_create_or_update_contact
    ):
        # TODO: setup at least a contact with an outdated mandate, one with a correct mandate, and one with no mandate at all. Perhaps also one where moneybird has a mandate, but the user has invalidated it (so it is in fact outdated, and should be removed from moneybird).

        services._sync_contacts_with_outdated_mandates()

        # TODO: check that mock_create_or_update_contact was called with the right contacts.

    def test_delete_invoices(self, mock_api):
        """Invoices marked for deletion are deleted."""
        raise NotImplementedError

    def test_sync_outdated_invoices(self, mock_api):
        """Invoices marked with needs_synchronization are updated."""
        raise NotImplementedError

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


@mock.patch("moneybirdsynchronization.moneybird.MoneybirdAPIService", autospec=True)
@override_settings(
    MONEYBIRD_START_DATE="2023-09-01",
    MONEYBIRD_ADMINISTRATION_ID="123",
    MONEYBIRD_API_KEY="foo",
    MONEYBIRD_SYNC_ENABLED=True,
    SUSPEND_SIGNALS=True,
)
class EventsSyncTest(TestCase):
    """Test the synchronization related to the events app."""

    # TODO


@mock.patch("moneybirdsynchronization.moneybird.MoneybirdAPIService", autospec=True)
@override_settings(
    MONEYBIRD_START_DATE="2023-09-01",
    MONEYBIRD_ADMINISTRATION_ID="123",
    MONEYBIRD_API_KEY="foo",
    MONEYBIRD_SYNC_ENABLED=True,
    SUSPEND_SIGNALS=True,
)
class PizzasSyncTest(TestCase):
    """Test the synchronization related to the pizzas app."""

    # TODO


@mock.patch("moneybirdsynchronization.moneybird.MoneybirdAPIService", autospec=True)
@override_settings(
    MONEYBIRD_START_DATE="2023-09-01",
    MONEYBIRD_ADMINISTRATION_ID="123",
    MONEYBIRD_API_KEY="foo",
    MONEYBIRD_SYNC_ENABLED=True,
    SUSPEND_SIGNALS=True,
)
class SalesSyncTest(TestCase):
    """Test the synchronization related to the sales app."""

    # TODO


@mock.patch("moneybirdsynchronization.moneybird.MoneybirdAPIService", autospec=True)
@override_settings(
    MONEYBIRD_START_DATE="2023-09-01",
    MONEYBIRD_ADMINISTRATION_ID="123",
    MONEYBIRD_API_KEY="foo",
    MONEYBIRD_SYNC_ENABLED=True,
    SUSPEND_SIGNALS=True,
)
class RegistrationsSyncTest(TestCase):
    """Test the synchronization related to the registrations app."""

    # TODO
