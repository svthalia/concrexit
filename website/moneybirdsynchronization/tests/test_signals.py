from unittest import mock

from django.test import TestCase, override_settings

from freezegun import freeze_time

from members.models import Member
from moneybirdsynchronization.models import MoneybirdExternalInvoice
from payments.models import Payment
from payments.services import create_payment
from registrations.models import Renewal
from registrations.services import execute_data_minimisation


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
class SignalsTest(TestCase):
    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.get(pk=1)
        cls.member2 = Member.objects.get(pk=2)
        cls.member3 = Member.objects.get(pk=3)
        cls.member4 = Member.objects.get(pk=4)

    def test_dataminimisation_does_not_trigger_invoice_deletion(self, mock_api):
        with freeze_time("2023-09-01"):
            renewal = Renewal.objects.create(
                member=self.member,
                length=Renewal.MEMBERSHIP_YEAR,
            )

            create_payment(renewal, self.member, Payment.CASH)
            renewal.refresh_from_db()
            renewal.status = Renewal.STATUS_COMPLETED
            renewal.save()

            invoice1 = MoneybirdExternalInvoice.objects.create(
                payable_object=renewal,
                needs_synchronization=False,
                moneybird_invoice_id="1",
            )

        with freeze_time("2023-11-01"):
            with override_settings(SUSPEND_SIGNALS=False):
                count_deleted = execute_data_minimisation()

                self.assertGreaterEqual(count_deleted, 1)

                # The invoice should not be scheduled for deletion.
                invoice1.refresh_from_db()
                self.assertFalse(invoice1.needs_deletion)
                self.assertFalse(invoice1.needs_synchronization)

            # Recreate the removed renewal.
            with freeze_time("2023-09-01"):
                renewal.status = Renewal.STATUS_COMPLETED
                renewal.save()

            with override_settings(SUSPEND_SIGNALS=False):
                # But (bulk)-deleting outside of data minimisation should still delete it.
                Renewal.objects.all().delete()

                invoice1.refresh_from_db()
                self.assertTrue(invoice1.needs_deletion)
                self.assertFalse(invoice1.needs_synchronization)
