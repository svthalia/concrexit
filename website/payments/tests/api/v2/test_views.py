from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from freezegun import freeze_time

from payments.models import BankAccount, Batch, Payment, PaymentUser


@freeze_time("2019-04-01")
@override_settings(SUSPEND_SIGNALS=True)
class PaymentListViewTest(TestCase):
    """Test for the PaymentListView."""

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.login_user = PaymentUser.objects.filter(last_name="Wiggers").first()
        cls.account1 = BankAccount.objects.create(
            owner=cls.login_user,
            initials="J1",
            last_name="Test",
            iban="NL91ABNA0417164300",
            valid_from="2019-03-01",
            signature="sig",
            mandate_no="11-2",
        )
        cls.payment1 = Payment.objects.create(
            created_at=timezone.datetime(year=2019, month=3, day=1),
            paid_by=cls.login_user,
            processed_by=cls.login_user,
            notes="Testing Payment 1",
            amount=10,
            type=Payment.TPAY,
        )

    def setUp(self):
        self.account1.refresh_from_db()
        self.payment1.refresh_from_db()
        self.client = Client()
        self.client.force_login(self.login_user)

    def test_settled_filter(self):
        """Test if the view shows payments."""
        response = self.client.get(
            reverse("api:v2:payments:payments-list"),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Testing Payment 1")

        response = self.client.get(
            reverse("api:v2:payments:payments-list") + "?settled=yes",
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, "Testing Payment 1")

        response = self.client.get(
            reverse("api:v2:payments:payments-list") + "?settled=no",
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Testing Payment 1")

        self.payment1.batch = Batch.objects.create(processed=False)
        self.payment1.save()
        self.payment1.batch.processed = True
        self.payment1.batch.save()

        response = self.client.get(
            reverse("api:v2:payments:payments-list"),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Testing Payment 1")

        response = self.client.get(
            reverse("api:v2:payments:payments-list") + "?settled=yes",
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Testing Payment 1")

        response = self.client.get(
            reverse("api:v2:payments:payments-list") + "?settled=no",
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, "Testing Payment 1")
