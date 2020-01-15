from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from freezegun import freeze_time

from members.models import Member
from payments.models import BankAccount, Payment


@freeze_time("2019-01-01")
@override_settings(SUSPEND_SIGNALS=True)
class BankAccountCreateViewTest(TestCase):
    """
    Test for the BankAccountCreateView
    """

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.login_user = Member.objects.filter(last_name="Wiggers").first()
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

    def test_not_a_current_member(self):
        """
        If the logged-in user is not a member they should not be able to visit
        this page
        """
        self.client.logout()
        self.client.force_login(self.new_user)

        response = self.client.get(reverse("payments:bankaccount-add"))
        self.assertEqual(403, response.status_code)

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
    """
    Test for the BankAccountRevokeView
    """

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.login_user = Member.objects.filter(last_name="Wiggers").first()
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
        """
        If the request is not a post it should redirect to the list
        """
        response = self.client.get(
            reverse("payments:bankaccount-revoke", args=(self.account2.pk,)),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [(reverse("payments:bankaccount-list"), 302)], response.redirect_chain
        )

    def test_cannot_revoke_no_mandate(self):
        """
        If the selected account has no valid mandate it should return a 404
        """
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

    def test_revoke_successful(self):
        """
        If an account with direct debit is revoked it should
        redirect to the list with the right success message.
        """
        self.assertTrue(
            BankAccount.objects.filter(owner=self.login_user, iban="BE68539007547034",)
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
    """
    Test for the BankAccountListView
    """

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.login_user = Member.objects.filter(last_name="Wiggers").first()
        cls.account1 = BankAccount.objects.create(
            owner=cls.login_user,
            initials="J1",
            last_name="Test",
            iban="NL91ABNA0417164300",
        )
        cls.account2 = BankAccount.objects.create(
            owner=Member.objects.exclude(last_name="Wiggers").first(),
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
        """
        The page should show only accounts of the logged-in user
        """
        response = self.client.get(reverse("payments:bankaccount-list"), follow=True,)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "NL91ABNA0417164300")
        self.assertNotContains(response, "BE68539007547034")


@freeze_time("2019-04-01")
@override_settings(SUSPEND_SIGNALS=True)
class PaymentListViewTest(TestCase):
    """
    Test for the PaymentListView
    """

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.login_user = Member.objects.filter(last_name="Wiggers").first()
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
            paid_by=cls.login_user,
            notes="Testing Payment 1",
            amount=10,
            type=Payment.CARD,
            processing_date="2019-03-06",
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
        """
        Test if the view shows payments
        """
        response = self.client.get(
            reverse("payments:payment-list", kwargs={"year": 2019, "month": 3}),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Testing Payment 1")
