from unittest import mock
from unittest.mock import MagicMock, Mock, ANY, patch, PropertyMock

from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from freezegun import freeze_time

from members.models import Member
from payments import payables
from payments.exceptions import PaymentError
from payments.models import BankAccount, Payment, PaymentUser
from payments.tests.__mocks__ import MockModel
from payments.tests.test_services import MockPayable


@freeze_time("2019-01-01")
@override_settings(SUSPEND_SIGNALS=True)
class BankAccountCreateViewTest(TestCase):
    """Test for the BankAccountCreateView."""

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.login_user = PaymentUser.objects.filter(last_name="Wiggers").first()
        cls.new_user = get_user_model().objects.create_user(
            username="username", first_name="Johnny", last_name="Test"
        )
        cls.account = BankAccount.objects.create(
            owner=cls.login_user,
            initials="J",
            last_name="Test",
            iban="NL91ABNA0417164300",
        )
        BankAccount.objects.create(
            owner=None, initials="Someone", last_name="Else", iban="BE68539007547034"
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.login_user)

    def test_not_logged_in(self):
        """
        If there is no logged-in user they should redirect
        to the authentication page
        """
        self.client.logout()

        response = self.client.get(reverse("payments:bankaccount-add"), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [("/user/login/?next=" + reverse("payments:bankaccount-add"), 302)],
            response.redirect_chain,
        )

    def test_shows_correct_reference(self):
        """
        The page should show the reference that will be used to identify
        a new mandate if direct debit is enabled
        """
        response = self.client.get(reverse("payments:bankaccount-add"), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual("1-1", response.context["mandate_no"])
        self.assertContains(response, "1-1")

    def test_account_no_mandate_saves_correctly(self):
        """
        If an account with direct debit enabled is saved
        we should redirect to the account list page
        with a success alert showing. And the BankAccount should be the only
        one in the account since the previous one had no mandate.
        BankAccounts by others should be untouched.
        """
        response = self.client.post(
            reverse("payments:bankaccount-add"),
            data={
                "initials": "S",
                "last_name": "Versteeg",
                "iban": "DE12500105170648489890",
                "bic": "NBBEBEBB",
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [(reverse("payments:bankaccount-list"), 302)], response.redirect_chain
        )
        self.assertContains(response, "Bank account saved successfully.")

        self.assertEqual(1, BankAccount.objects.filter(owner=self.login_user).count())

        self.assertTrue(
            BankAccount.objects.filter(
                owner=self.login_user, iban="DE12500105170648489890"
            ).exists()
        )

        self.assertTrue(BankAccount.objects.filter(iban="BE68539007547034").exists())

    def test_account_with_mandate_saves_correctly(self):
        """
        If an account with direct debit enabled is saved
        we should redirect to the account list page
        with a success alert showing. And the BankAccount should be the only
        one in the account since the previous one had no mandate.
        BankAccounts by others should be untouched.
        """
        response = self.client.post(
            reverse("payments:bankaccount-add"),
            data={
                "initials": "S",
                "last_name": "Versteeg",
                "iban": "DE12500105170648489890",
                "bic": "NBBEBEBB",
                "direct_debit": "",
                "signature": "sig",
            },
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [(reverse("payments:bankaccount-list"), 302)], response.redirect_chain
        )
        self.assertContains(response, "Bank account saved successfully.")

        self.assertEqual(1, BankAccount.objects.filter(owner=self.login_user).count())

        self.assertTrue(
            BankAccount.objects.filter(
                owner=self.login_user, iban="DE12500105170648489890", mandate_no="1-1"
            ).exists()
        )

        self.assertTrue(BankAccount.objects.filter(iban="BE68539007547034").exists())

    def test_account_save_keeps_old_mandates(self):
        """
        If an account is saved and there are previous accounts that
        were authorised for direct debit then we should keep those
        but they should be revoked.
        """
        BankAccount.objects.create(
            owner=self.login_user,
            initials="J",
            last_name="Test",
            iban="NL91ABNA0417164300",
            valid_from="2019-03-01",
            signature="sig",
            mandate_no="11-2",
        )

        self.client.post(
            reverse("payments:bankaccount-add"),
            data={
                "initials": "S",
                "last_name": "Versteeg",
                "iban": "DE12500105170648489890",
                "bic": "NBBEBEBB",
            },
            follow=True,
        )

        self.assertEqual(2, BankAccount.objects.filter(owner=self.login_user).count())

        self.assertTrue(
            BankAccount.objects.filter(
                owner=self.login_user, iban="DE12500105170648489890"
            ).exists()
        )

        self.assertFalse(
            BankAccount.objects.filter(owner=self.login_user, iban="NL91ABNA0417164300")
            .first()
            .valid
        )


@override_settings(SUSPEND_SIGNALS=True)
class BankAccountRevokeViewTest(TestCase):
    """Test for the BankAccountRevokeView."""

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.login_user = PaymentUser.objects.filter(last_name="Wiggers").first()
        cls.account1 = BankAccount.objects.create(
            owner=cls.login_user,
            initials="J1",
            last_name="Test",
            iban="NL91ABNA0417164300",
        )
        cls.account2 = BankAccount.objects.create(
            owner=cls.login_user,
            initials="J2",
            last_name="Test",
            iban="BE68539007547034",
            bic="NBBEBEBB",
            valid_from="2019-03-01",
            signature="sig",
            mandate_no="11-2",
        )

    def setUp(self):
        self.account1.refresh_from_db()
        self.account2.refresh_from_db()
        self.client = Client()
        self.client.force_login(self.login_user)

    def test_not_logged_in(self):
        """
        If there is no logged-in user they should redirect
        to the authentication page
        """
        self.client.logout()

        response = self.client.post(
            reverse("payments:bankaccount-revoke", args=(self.account1.pk,)),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [
                (
                    "/user/login/?next="
                    + reverse("payments:bankaccount-revoke", args=(self.account1.pk,)),
                    302,
                )
            ],
            response.redirect_chain,
        )

    def test_no_post(self):
        """If the request is not a post it should redirect to the list."""
        response = self.client.get(
            reverse("payments:bankaccount-revoke", args=(self.account2.pk,)),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [(reverse("payments:bankaccount-list"), 302)], response.redirect_chain
        )

    def test_cannot_revoke_no_mandate(self):
        """If the selected account has no valid mandate it should return a 404."""
        self.account2.valid_until = "2019-04-01"
        self.account2.save()

        response = self.client.post(
            reverse("payments:bankaccount-revoke", args=(self.account1.pk,)),
            follow=True,
        )
        self.assertEqual(404, response.status_code)

        response = self.client.post(
            reverse("payments:bankaccount-revoke", args=(self.account2.pk,)),
            follow=True,
        )
        self.assertEqual(404, response.status_code)

    def test_cannot_revoke_cannot_revoke(self):
        """
        If a bank account cannot be revoked, an error should be displayed.
        """
        with patch(
            "payments.models.BankAccount.can_be_revoked", new_callable=mock.PropertyMock
        ) as can_be_revoked:
            can_be_revoked.return_value = False

            response = self.client.post(
                reverse("payments:bankaccount-revoke", args=(self.account2.pk,)),
                follow=True,
            )
            self.assertEqual(200, response.status_code)
            self.assertEqual(
                [(reverse("payments:bankaccount-list"), 302)], response.redirect_chain
            )
            self.assertContains(response, "cannot be revoked")

    def test_revoke_successful(self):
        """
        If an account with direct debit is revoked it should
        redirect to the list with the right success message.
        """
        self.assertTrue(
            BankAccount.objects.filter(
                owner=PaymentUser.objects.get(pk=self.login_user.pk),
                iban="BE68539007547034",
            )
            .first()
            .valid
        )

        response = self.client.post(
            reverse("payments:bankaccount-revoke", args=(self.account2.pk,)),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [(reverse("payments:bankaccount-list"), 302)], response.redirect_chain
        )
        self.assertContains(
            response, "Direct debit authorisation successfully revoked."
        )

        self.assertFalse(
            BankAccount.objects.filter(owner=self.login_user, iban="BE68539007547034",)
            .first()
            .valid
        )


@override_settings(SUSPEND_SIGNALS=True)
class BankAccountListViewTest(TestCase):
    """Test for the BankAccountListView."""

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.login_user = PaymentUser.objects.filter(last_name="Wiggers").first()
        cls.account1 = BankAccount.objects.create(
            owner=cls.login_user,
            initials="J1",
            last_name="Test",
            iban="NL91ABNA0417164300",
        )
        cls.account2 = BankAccount.objects.create(
            owner=PaymentUser.objects.exclude(last_name="Wiggers").first(),
            initials="J2",
            last_name="Test",
            iban="BE68539007547034",
            bic="NBBEBEBB",
            valid_from="2019-03-01",
            signature="sig",
            mandate_no="11-2",
        )

    def setUp(self):
        self.account1.refresh_from_db()
        self.account2.refresh_from_db()
        self.client = Client()
        self.client.force_login(self.login_user)

    def test_not_logged_in(self):
        """
        If there is no logged-in user they should redirect
        to the authentication page
        """
        self.client.logout()

        response = self.client.post(reverse("payments:bankaccount-list"), follow=True,)
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [("/user/login/?next=" + reverse("payments:bankaccount-list"), 302,)],
            response.redirect_chain,
        )

    def test_accounts(self):
        """The page should show only accounts of the logged-in user."""
        response = self.client.get(reverse("payments:bankaccount-list"), follow=True,)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "NL91ABNA0417164300")
        self.assertNotContains(response, "BE68539007547034")


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
            type=Payment.CARD,
        )

    def setUp(self):
        self.account1.refresh_from_db()
        self.payment1.refresh_from_db()
        self.client = Client()
        self.client.force_login(self.login_user)

    def test_not_logged_in(self):
        """
        If there is no logged-in user they should redirect
        to the authentication page
        """
        self.client.logout()

        response = self.client.post(reverse("payments:payment-list"), follow=True,)
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [("/user/login/?next=" + reverse("payments:payment-list"), 302,)],
            response.redirect_chain,
        )

    def test_contents(self):
        """Test if the view shows payments."""
        response = self.client.get(
            reverse("payments:payment-list", kwargs={"year": 2019, "month": 3}),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Testing Payment 1")


@freeze_time("2020-09-01")
@override_settings(SUSPEND_SIGNALS=True, THALIA_PAY_ENABLED_PAYMENT_METHOD=True)
@patch("payments.models.PaymentUser.tpay_allowed", PropertyMock, True)
class PaymentProcessViewTest(TestCase):
    """Test for the PaymentProcessView."""

    fixtures = ["members.json"]

    test_body = {
        "app_label": "mock_app",
        "model_name": "mock_model",
        "payable": "mock_payable_pk",
        "payable_hash": "placeholder",
        "next": "/mock_next",
    }

    @classmethod
    def setUpTestData(cls):
        cls.user = Member.objects.filter(last_name="Wiggers").first()
        cls.account1 = BankAccount.objects.create(
            owner=cls.user,
            initials="J1",
            last_name="Test",
            iban="NL91ABNA0417164300",
            valid_from="2019-03-01",
            signature="sig",
            mandate_no="11-2",
        )
        cls.user = PaymentUser.objects.get(pk=cls.user.pk)

    def setUp(self):
        payables.register(MockModel, MockPayable)

        self.account1.refresh_from_db()
        self.client = Client()
        self.client.force_login(self.user)

        self.model = MockModel(payer=self.user)

        self.original_get_model = apps.get_model
        mock_get_model = MagicMock()

        def side_effect(*args, **kwargs):
            if "app_label" in kwargs and kwargs["app_label"] == "mock_app":
                return mock_get_model
            return self.original_get_model(*args, **kwargs)

        apps.get_model = Mock(side_effect=side_effect)
        mock_get_model.objects.get.return_value = self.model

        self.test_body["payable_hash"] = str(hash(payables.get_payable(self.model)))

    def tearDown(self):
        apps.get_model = self.original_get_model

    def test_not_logged_in(self):
        """
        If there is no logged-in user they should redirect
        to the authentication page
        """
        self.client.logout()

        response = self.client.post(reverse("payments:payment-process"), follow=True,)
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [("/user/login/?next=" + reverse("payments:payment-process"), 302,)],
            response.redirect_chain,
        )

    @override_settings(THALIA_PAY_ENABLED_PAYMENT_METHOD=False)
    def test_member_has_tpay_enabled(self):
        response = self.client.post(
            reverse("payments:payment-process"), follow=True, data=self.test_body
        )
        self.assertEqual(403, response.status_code)

    @mock.patch("django.contrib.messages.error")
    def test_tpay_not_allowed(self, messages_error):
        with mock.patch("payments.Payable.tpay_allowed") as mock_tpay_allowed:
            mock_tpay_allowed.__get__ = mock.Mock(return_value=False)

            response = self.client.post(
                reverse("payments:payment-process"), follow=False, data=self.test_body
            )

            messages_error.assert_called_with(
                ANY, "You are not allowed to use Thalia Pay for this payment."
            )

            self.assertEqual(302, response.status_code)
            self.assertEqual("/mock_next", response.url)

    def test_missing_parameters(self):
        response = self.client.post(
            reverse("payments:payment-process"), follow=True, data={}
        )
        self.assertEqual(400, response.status_code)

    def test_disallowed_redirect(self):
        response = self.client.post(
            reverse("payments:payment-process"),
            follow=True,
            data={**self.test_body, "next": "https://ru.nl/"},
        )
        self.assertEqual(400, response.status_code)

    @mock.patch("django.contrib.messages.error")
    def test_different_member(self, messages_error):
        self.model.payer = PaymentUser()

        response = self.client.post(
            reverse("payments:payment-process"), follow=False, data=self.test_body
        )

        messages_error.assert_called_with(
            ANY, "You are not allowed to process this payment."
        )

        self.assertEqual(302, response.status_code)
        self.assertEqual("/mock_next", response.url)

    @mock.patch("django.contrib.messages.error")
    def test_already_paid(self, messages_error):
        self.model.payment = Payment(amount=8)

        response = self.client.post(
            reverse("payments:payment-process"), follow=False, data=self.test_body
        )

        messages_error.assert_called_with(ANY, "This object has already been paid for.")

        self.assertEqual(302, response.status_code)
        self.assertEqual("/mock_next", response.url)

    @mock.patch("django.contrib.messages.error")
    def test_zero_payment(self, messages_error):
        self.model.amount = 0

        response = self.client.post(
            reverse("payments:payment-process"), follow=False, data=self.test_body
        )

        messages_error.assert_called_with(
            ANY, "No payment required for amount of €0.00"
        )

        self.assertEqual(302, response.status_code)
        self.assertEqual("/mock_next", response.url)

    def test_renders_confirmation(self):
        response = self.client.post(
            reverse("payments:payment-process"), follow=False, data=self.test_body
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            payables.get_payable(self.model).pk, response.context_data["payable"].pk
        )
        self.assertContains(response, "Please confirm your payment.")
        self.assertContains(response, 'name="_save"')

    @mock.patch("django.contrib.messages.success")
    @mock.patch("payments.services.create_payment")
    def test_creates_payment(self, create_payment, messages_success):
        response = self.client.post(
            reverse("payments:payment-process"),
            follow=False,
            data={**self.test_body, "_save": True},
        )

        create_payment.assert_called_with(ANY, self.user, Payment.TPAY)
        self.assertEqual(create_payment.call_args.args[0].pk, self.model.pk)

        messages_success.assert_called_with(
            ANY, "Your payment has been processed successfully."
        )

        self.assertEqual(302, response.status_code)
        self.assertEqual("/mock_next", response.url)

    @mock.patch("django.contrib.messages.error")
    @mock.patch("payments.services.create_payment")
    def test_payment_create_error(self, create_payment, messages_error):
        create_payment.side_effect = PaymentError("Test error")

        response = self.client.post(
            reverse("payments:payment-process"),
            follow=False,
            data={**self.test_body, "_save": True},
        )

        messages_error.assert_called_with(ANY, "Test error")

        self.assertEqual(302, response.status_code)
        self.assertEqual("/mock_next", response.url)

    def test_payment_deleted_error(self):
        test_body = {
            "app_label": "sales",
            "model_name": "orders",
            "payable": "63be888b-2852-4811-8b72-82cd86ea0b9f",
            "payable_hash": "non_existent",
            "next": "/mock_next",
        }
        response = self.client.get(
            reverse("payments:payment-process"), follow=False, data=test_body
        )
        self.assertEqual(404, response.status_code)

    def test_payment_accept_deleted_error(self):
        test_body = {
            "app_label": "sales",
            "model_name": "order",
            "payable": "63be888b-2852-4811-8b72-82cd86ea0b9f",
            "next": "/mock_next",
            "payable_hash": "non_existent",
            "_save": True,
        }
        response = self.client.post(
            reverse("payments:payment-process"), follow=False, data=test_body
        )
        self.assertEqual(404, response.status_code)

    def test_app_does_not_exist(self):
        test_body = {
            "app_label": "payments",
            "model_name": "does_not_exist",
            "payable": "63be888b-2852-4811-8b72-82cd86ea0b9f",
            "next": "/mock_next",
            "payable_hash": "non_existent",
        }
        response = self.client.post(
            reverse("payments:payment-process"), follow=False, data=test_body
        )
        self.assertEqual(404, response.status_code)

    def test_model_does_not_exist(self):
        test_body = {
            "app_label": "does_not_exist",
            "model_name": "does_not_exist",
            "payable": "63be888b-2852-4811-8b72-82cd86ea0b9f",
            "next": "/mock_next",
            "payable_hash": "non_existent",
        }
        response = self.client.post(
            reverse("payments:payment-process"), follow=False, data=test_body
        )
        self.assertEqual(404, response.status_code)

    @mock.patch("django.contrib.messages.error")
    def test_payment_changed_payable(self, messages_error):
        body = self.test_body
        body["payable_hash"] = "987654321"
        response = self.client.post(
            reverse("payments:payment-process"),
            follow=False,
            data={**body, "_save": True},
        )
        messages_error.assert_called_with(
            ANY, "This object has been changed in the mean time. You have not paid."
        )

        self.assertEqual(302, response.status_code)
        self.assertEqual("/mock_next", response.url)
