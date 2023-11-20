from unittest import mock
from unittest.mock import MagicMock, Mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.http import HttpResponse
from django.template.defaultfilters import floatformat
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from members.models import Member, Membership, Profile
from registrations import views
from registrations.models import Entry, Reference, Registration, Renewal
from registrations.views import RenewalFormView


def _get_mock_user(is_staff=False, is_authenticated=False, perms=None):
    user = mock.MagicMock()
    user.pk = 1
    user.is_staff = is_staff
    user.is_authenticated = is_authenticated

    user.is_superuser = False
    user.user_permissions = perms
    user.has_perm = lambda x: x in perms

    return user


class EntryAdminViewTest(TestCase):
    pass


class ConfirmEmailViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.registration = Registration.objects.create(
            first_name="John",
            last_name="Doe",
            email="johndoe@example.com",
            programme="computingscience",
            student_number="s1234567",
            starting_year=2014,
            address_street="Heyendaalseweg 135",
            address_street2="",
            address_postal_code="6525AJ",
            address_city="Nijmegen",
            address_country="NL",
            phone_number="06123456789",
            birthday=timezone.now().replace(year=1990, day=1).date(),
            length=Entry.MEMBERSHIP_YEAR,
            contribution=7.5,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_CONFIRM,
        )

    def test_incorrect_uuid(self):
        response = self.client.get(
            reverse(
                "registrations:confirm-email",
                args=["11111111-2222-3333-4444-555555555555"],
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_confirm_email(self):
        with self.subTest("Member registration."):
            response = self.client.get(
                reverse("registrations:confirm-email", args=[self.registration.pk])
            )

            self.assertContains(response, "Your email address has been confirmed.")
            self.registration.refresh_from_db()
            self.assertEqual(self.registration.status, Entry.STATUS_REVIEW)
            self.assertEqual(len(mail.outbox), 1)

        self.registration.status = Entry.STATUS_CONFIRM
        self.registration.membership_type = Membership.BENEFACTOR
        self.registration.save()
        mail.outbox = []

        with self.subTest("Benefactor registration."):
            response = self.client.get(
                reverse(
                    "registrations:confirm-email",
                    args=[self.registration.pk],
                )
            )

            self.assertContains(response, "Your email address has been confirmed.")
            self.registration.refresh_from_db()
            self.assertEqual(self.registration.status, Entry.STATUS_REVIEW)
            self.assertEqual(len(mail.outbox), 2)

        self.registration.status = Entry.STATUS_CONFIRM
        self.registration.no_references = True
        self.registration.save()
        mail.outbox = []

        with self.subTest("Benefacor that doesn't need references."):
            response = self.client.get(
                reverse("registrations:confirm-email", args=[self.registration.pk]),
                follow=True,
            )

            self.assertContains(response, "Your email address has been confirmed.")
            self.registration.refresh_from_db()
            self.assertEqual(self.registration.status, Entry.STATUS_REVIEW)
            self.assertEqual(len(mail.outbox), 1)

    def test_already_confirmed(self):
        self.registration.status = Entry.STATUS_REVIEW
        self.registration.save()

        with self.subTest("In review."):
            response = self.client.get(
                reverse("registrations:confirm-email", args=[self.registration.pk])
            )

            self.assertContains(response, "Your email address has been confirmed.")
            self.assertEqual(len(mail.outbox), 0)

        self.registration.status = Entry.STATUS_ACCEPTED
        self.registration.save()

        with self.subTest("Reviewed."):
            response = self.client.get(
                reverse("registrations:confirm-email", args=[self.registration.pk])
            )
            self.assertEqual(response.status_code, 404)
            self.assertEqual(len(mail.outbox), 0)


class BecomeAMemberViewTest(TestCase):
    def setUp(self):
        self.view = views.BecomeAMemberView()

    def test_get_context_data(self):
        context = self.view.get_context_data()
        self.assertEqual(len(context), 3)
        self.assertEqual(
            context["year_fees"],
            floatformat(settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_YEAR], 2),
        )
        self.assertEqual(
            context["study_fees"],
            floatformat(settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_STUDY], 2),
        )


class BaseRegistrationFormViewTest(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.view = views.BaseRegistrationFormView()

    @override_settings(GOOGLE_PLACES_API_KEY="hello")
    def test_get_context_data(self):
        self.view.request = self.rf.post("/")
        context = self.view.get_context_data()
        self.assertEqual(len(context), 5)
        self.assertEqual(
            context["year_fees"],
            floatformat(settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_YEAR], 2),
        )
        self.assertEqual(
            context["study_fees"],
            floatformat(settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_STUDY], 2),
        )
        self.assertEqual(context["google_api_key"], "hello")

    @mock.patch("django.views.generic.FormView.get")
    def test_get(self, super_get):
        super_get.return_value = HttpResponse(status=200)

        request = self.rf.get("/")
        request.user = _get_mock_user(is_authenticated=False)
        request.member = request.user
        response = self.view.get(request)
        self.assertEqual(response.status_code, 200)

        request = self.rf.get("/")
        request.user = _get_mock_user(is_authenticated=True)
        request.member = request.user
        response = self.view.get(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("registrations:renew"))

    @mock.patch("registrations.emails.send_registration_email_confirmation")
    def test_form_valid(self, send_mail):
        mock_form = MagicMock()

        return_value = self.view.form_valid(mock_form)

        mock_form.save.assert_called_once_with()
        self.assertEqual(return_value.status_code, 302)
        self.assertEqual(return_value.url, reverse("registrations:register-success"))

        send_mail.assert_called_once_with(mock_form.instance)


class MemberRegistrationFormViewTest(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.view = views.MemberRegistrationFormView()

    @override_settings(
        THALIA_PAY_ENABLED_PAYMENT_METHOD=True, THALIA_PAY_FOR_NEW_MEMBERS=True
    )
    def test_get_context_data_tpay_enabled(self):
        context = self.view.get_context_data(form=MagicMock())
        self.assertTrue(context["tpay_enabled"])

    @override_settings(
        THALIA_PAY_ENABLED_PAYMENT_METHOD=False, THALIA_PAY_FOR_NEW_MEMBERS=False
    )
    def test_get_context_data_tpay_disabled(self):
        context = self.view.get_context_data(form=MagicMock())
        self.assertFalse(context["tpay_enabled"])

    @mock.patch("django.views.generic.FormView.post")
    def test_post(self, super_post):
        request = self.rf.post("/")
        request.LANGUAGE_CODE = "nl"
        request.user = _get_mock_user()
        request.member = request.user
        request.member.pk = 2
        self.view.request = request

        self.view.post(request)

        request = super_post.call_args[0][0]
        self.assertEqual(request.POST["language"], "nl")
        self.assertEqual(request.POST["membership_type"], Membership.MEMBER)


class BenefactorRegistrationFormViewTest(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.view = views.BenefactorRegistrationFormView()

    @override_settings(
        THALIA_PAY_ENABLED_PAYMENT_METHOD=True, THALIA_PAY_FOR_NEW_MEMBERS=True
    )
    def test_get_context_data_tpay_enabled(self):
        context = self.view.get_context_data(form=MagicMock())
        self.assertTrue(context["tpay_enabled"])

    @override_settings(
        THALIA_PAY_ENABLED_PAYMENT_METHOD=False, THALIA_PAY_FOR_NEW_MEMBERS=False
    )
    def test_get_context_data_tpay_disabled(self):
        context = self.view.get_context_data(form=MagicMock())
        self.assertFalse(context["tpay_enabled"])

    @mock.patch("django.views.generic.FormView.post")
    def test_post(self, super_post):
        request = self.rf.post("/", {})
        request.LANGUAGE_CODE = "nl"
        request.user = _get_mock_user()
        request.member = request.user
        request.member.pk = 2
        self.view.request = request

        with self.subTest("No iCIS employee"):
            self.view.post(request)

            request = super_post.call_args[0][0]
            self.assertEqual(request.POST["language"], "nl")
            self.assertEqual(request.POST["membership_type"], Membership.BENEFACTOR)
            self.assertEqual(request.POST["length"], Entry.MEMBERSHIP_YEAR)
            self.assertEqual(request.POST["remarks"], "")

        request = self.rf.post("/", {"icis_employee": True})
        request.LANGUAGE_CODE = "nl"
        request.user = _get_mock_user()
        request.member = request.user
        request.member.pk = 2
        self.view.request = request

        with self.subTest("An iCIS employee"):
            self.view.post(request)

            request = super_post.call_args[0][0]
            self.assertEqual(request.POST["language"], "nl")
            self.assertEqual(request.POST["membership_type"], Membership.BENEFACTOR)
            self.assertEqual(request.POST["length"], Entry.MEMBERSHIP_YEAR)
            self.assertEqual(request.POST["remarks"], "Registered as iCIS employee")


class RenewalFormViewTest(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.view = views.RenewalFormView()

    def test_get_context_data(self):
        membership = Membership(pk=2, type=Membership.MEMBER)
        self.view.request = MagicMock()

        with mock.patch("members.models.Membership.objects") as _membership_qs:
            Membership.objects.filter().exists.return_value = True

            with mock.patch("registrations.models.Renewal.objects") as _renewal_qs:
                Renewal.objects.filter().last.return_value = None

                context = self.view.get_context_data(form=MagicMock())
                self.assertEqual(len(context), 8)
                self.assertEqual(
                    context["year_fees"],
                    floatformat(settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_YEAR], 2),
                )
                self.assertEqual(
                    context["study_fees"],
                    floatformat(settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_STUDY], 2),
                )
                self.assertEqual(context["was_member"], True)

                Membership.objects.filter().exists.return_value = False
                context = self.view.get_context_data(form=MagicMock())
                self.assertEqual(context["was_member"], False)

                with self.subTest("With latest membership"):
                    self.view.request.member.latest_membership = membership

                    context = self.view.get_context_data(form=MagicMock())
                    self.assertEqual(context["latest_membership"], membership)

                with self.subTest("Without latest membership"):
                    self.view.request.member.latest_membership = None

                    context = self.view.get_context_data(form=MagicMock())
                    self.assertEqual(context["latest_membership"], None)

                with self.subTest("With renewal"):
                    renewal = Renewal.objects.create(
                        member=self.view.request.member, status=Entry.STATUS_ACCEPTED
                    )
                    Renewal.objects.filter().last.return_value = renewal

                    context = self.view.get_context_data(form=MagicMock())
                    self.assertEqual(context["latest_renewal"], renewal)

                with self.subTest("With minimised data"):
                    with mock.patch("django.contrib.messages.warning") as mock_messages:
                        self.view.request.member.profile.is_minimized = True
                        self.view.request.member.profile.save()

                        self.view.request.member.latest_membership = MagicMock()
                        self.view.request.member.latest_membership.is_active = (
                            MagicMock()
                        )
                        self.view.request.member.latest_membership.is_active.return_value = (
                            False
                        )

                        self.view.get_context_data(form=MagicMock())

                        mock_messages.assert_called_once()

    def test_get_form(self):
        self.view.request = self.rf.get("/")

        self.view.request.member = None
        form = self.view.get_form()
        self.assertFalse(Entry.MEMBERSHIP_YEAR in form.fields["length"].choices)

        self.view.request.member = MagicMock()
        self.view.request.member.latest_membership = None
        form = self.view.get_form()
        self.assertFalse(Entry.MEMBERSHIP_YEAR in form.fields["length"].choices)

        self.view.request.member.latest_membership = Membership(until=None)
        form = self.view.get_form()
        self.assertFalse(Entry.MEMBERSHIP_YEAR in form.fields["length"].choices)

        self.view.request.member.latest_membership = Membership(
            until=timezone.now().date()
        )
        form = self.view.get_form()
        self.assertEqual(Entry.MEMBERSHIP_YEAR, form.fields["length"].choices[1][0])

    @mock.patch("django.views.generic.FormView.post")
    def test_post(self, super_post):
        with mock.patch("members.models.Membership.objects"):
            Membership.objects.filter().exists.return_value = False
            with self.subTest("Member type"):
                request = self.rf.post("/", {"membership_type": Membership.MEMBER})
                request.member = MagicMock()
                request.member.pk = 2
                self.view.request = request

                request.member.latest_membership.type = Membership.MEMBER
                self.view.post(request)

                request = super_post.call_args[0][0]
                self.assertEqual(request.POST["member"], 2)
                self.assertEqual(request.POST["remarks"], "")
                self.assertEqual(request.POST["no_references"], True)

            with self.subTest("Forced benefactor type"):
                request = self.rf.post("/", {"membership_type": Membership.MEMBER})
                request.member = MagicMock()
                request.member.pk = 2
                self.view.request = request

                request.member.latest_membership.type = Membership.BENEFACTOR
                self.view.post(request)

                request = super_post.call_args[0][0]
                self.assertEqual(request.POST["member"], 2)
                self.assertEqual(request.POST["membership_type"], Membership.BENEFACTOR)
                self.assertEqual(request.POST["length"], Entry.MEMBERSHIP_YEAR)
                self.assertEqual(request.POST["no_references"], False)

            with self.subTest("Detects old memberships"):
                request = self.rf.post("/", {"membership_type": Membership.BENEFACTOR})
                request.member = MagicMock()
                request.member.pk = 2
                self.view.request = request

                Membership.objects.filter().exists.return_value = True
                self.view.post(request)
                request = super_post.call_args[0][0]
                self.assertEqual(
                    request.POST["remarks"], "Was a Thalia member in the past."
                )
                self.assertEqual(request.POST["no_references"], True)

            with self.subTest("Adds iCIS remark"):
                request = self.rf.post(
                    "/",
                    {"membership_type": Membership.BENEFACTOR, "icis_employee": True},
                )
                request.member = MagicMock()
                request.member.pk = 2
                self.view.request = request

                Membership.objects.filter().exists.return_value = False
                self.view.post(request)
                request = super_post.call_args[0][0]
                self.assertEqual(
                    request.POST["remarks"], "Registered as iCIS employee."
                )
                self.assertEqual(request.POST["no_references"], True)

    @mock.patch("registrations.emails.send_references_information_message")
    @mock.patch("registrations.emails.send_new_renewal_board_message")
    def test_form_valid(self, board_mail, references_mail):
        mock_form = Mock(spec=RenewalFormView)
        member = Member(
            email="test@example.org",
            first_name="John",
            last_name="Doe",
            profile=Profile(),
        )

        renewal = Renewal(pk=0, member=member)
        mock_form.save = MagicMock(return_value=renewal)

        with self.subTest("No references required"):
            renewal.no_references = True
            return_value = self.view.form_valid(mock_form)
            board_mail.assert_called_once_with(renewal)
            self.assertFalse(references_mail.called)

            self.assertEqual(return_value.status_code, 302)
            self.assertEqual(return_value.url, reverse("registrations:renew-success"))

        board_mail.reset_mock()

        with self.subTest("References required"):
            renewal.no_references = False
            return_value = self.view.form_valid(mock_form)
            board_mail.assert_called_once_with(renewal)
            references_mail.assert_called_once_with(renewal)

            self.assertEqual(return_value.status_code, 302)
            self.assertEqual(return_value.url, reverse("registrations:renew-success"))


@override_settings(SUSPEND_SIGNALS=True)
class ReferenceCreateViewTest(TestCase):
    """Test for the ReferenceCreateView."""

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.login_user = Member.objects.filter(last_name="Wiggers").first()
        cls.registration = Registration.objects.create(
            first_name="John",
            last_name="Doe",
            email="johndoe@example.com",
            programme="computingscience",
            student_number="s1234567",
            starting_year=2014,
            address_street="Heyendaalseweg 135",
            address_street2="",
            address_postal_code="6525AJ",
            address_city="Nijmegen",
            address_country="NL",
            phone_number="06123456789",
            birthday=timezone.now().replace(year=1990, day=1),
            length=Entry.MEMBERSHIP_YEAR,
            contribution=7.50,
            membership_type=Membership.BENEFACTOR,
            status=Entry.STATUS_CONFIRM,
        )
        cls.new_user = get_user_model().objects.create_user(
            username="username", first_name="Johnny", last_name="Test"
        )
        cls.renewal = Renewal.objects.create(
            length=Entry.MEMBERSHIP_YEAR,
            contribution=7.50,
            membership_type=Membership.BENEFACTOR,
            status=Entry.STATUS_CONFIRM,
            member=cls.new_user,
        )

    def setUp(self):
        self.rf = RequestFactory()
        self.view = views.ReferenceCreateView()
        self.client.force_login(self.login_user)

    def test_not_logged_in(self):
        """
        If there is no logged-in user they should redirect
        to the authentication page
        """
        self.client.logout()

        response = self.client.get(
            reverse("registrations:reference", args=(self.registration.pk,)),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [
                (
                    "/user/login/?next="
                    + reverse("registrations:reference", args=(self.registration.pk,)),
                    302,
                )
            ],
            response.redirect_chain,
        )

    def test_not_a_current_member(self):
        """
        If the logged-in user is not a member they should not be able to visit
        this page
        """
        self.client.logout()
        self.client.force_login(self.new_user)

        response = self.client.get(
            reverse("registrations:reference", args=(self.registration.pk,))
        )
        self.assertEqual(403, response.status_code)

    def test_entry_does_not_exist(self):
        """If the registration/renewal does not exist a 404 should be shown."""
        response = self.client.get(
            reverse(
                "registrations:reference",
                args=("00000000-0000-0000-0000-000000000000",),
            )
        )
        self.assertEqual(404, response.status_code)

    def test_entry_no_references_required(self):
        """
        If the registration/renewal does not require references
        a 404 should be shown
        """
        self.registration.no_references = True
        self.registration.save()

        response = self.client.get(
            reverse("registrations:reference", args=(self.registration.pk,))
        )
        self.assertEqual(404, response.status_code)

    def test_entry_no_benefactor(self):
        """
        If the registration/renewal is not a the benefactor type
        a 404 should be shown
        """
        self.registration.membership_type = Membership.MEMBER
        self.registration.save()

        response = self.client.get(
            reverse("registrations:reference", args=(self.registration.pk,))
        )
        self.assertEqual(404, response.status_code)

    def test_entry_shows_info(self):
        """
        If everything is alright the info and submission buttons should
        be shown
        """
        with self.subTest("Registration"):
            response = self.client.get(
                reverse("registrations:reference", args=(self.registration.pk,))
            )
            self.assertEqual(200, response.status_code)
            self.assertEqual("John Doe", response.context["name"])
            self.assertEqual(False, response.context["success"])
            self.assertContains(
                response, "<strong>John Doe</strong> wants to become a benefactor"
            )

        with self.subTest("Renewal"):
            response = self.client.get(
                reverse("registrations:reference", args=(self.renewal.pk,))
            )
            self.assertEqual(200, response.status_code)
            self.assertEqual("Johnny Test", response.context["name"])
            self.assertEqual(False, response.context["success"])
            self.assertContains(
                response, "<strong>Johnny Test</strong> wants to become a benefactor"
            )

    def test_entry_saves_correctly(self):
        """
        If a entry is saved it should redirect to the success page
        which should show the right content. And the Reference object
        should be saved.
        """
        response = self.client.post(
            reverse("registrations:reference", args=(self.registration.pk,)),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [
                (
                    reverse(
                        "registrations:reference-success", args=(self.registration.pk,)
                    ),
                    302,
                )
            ],
            response.redirect_chain,
        )
        self.assertEqual("John Doe", response.context["name"])
        self.assertEqual(True, response.context["success"])
        self.assertContains(response, "Your reference has been saved.")

        self.assertTrue(
            Reference.objects.filter(
                member=self.login_user, entry=self.registration
            ).exists()
        )

    def test_entry_reference_exists(self):
        """
        If there is already a reference for an entry then the page should
        show an error and not redirect.
        """
        Reference.objects.create(member=self.login_user, entry=self.registration)

        response = self.client.post(
            reverse("registrations:reference", args=(self.registration.pk,)),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual([], response.redirect_chain)
        self.assertEqual(
            {"__all__": ["You've already given a reference for this person."]},
            response.context["form"].errors,
        )
        self.assertEqual(False, response.context["success"])
        self.assertContains(
            response, "You&#x27;ve already given a reference for this person."
        )
