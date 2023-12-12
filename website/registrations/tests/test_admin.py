from unittest import mock

from django.contrib.admin import AdminSite
from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import TestCase, override_settings
from django.utils import timezone

from members.models import Member
from members.models.membership import Membership
from payments.widgets import PaymentWidget
from registrations import admin, payables
from registrations.models import Entry, Reference, Registration, Renewal


def _get_mock_request(perms=None):
    if perms is None:
        perms = []

    mock_request = HttpRequest()
    mock_request.META = mock.Mock(return_value={})
    mock_request.user = mock.MagicMock()
    mock_request.user.pk = 1
    mock_request.user.is_superuser = False
    mock_request.user.user_permissions = perms
    mock_request.user.has_perm = lambda x: x in perms
    mock_request._messages = mock.Mock()
    return mock_request


@override_settings(SUSPEND_SIGNALS=True)
class RegistrationAdminTest(TestCase):
    fixtures = ["members.json"]

    def setUp(self):
        self.site = AdminSite()
        self.admin = admin.RegistrationAdmin(Registration, admin_site=self.site)
        payables.register()

    @mock.patch("django.contrib.admin.ModelAdmin.changeform_view")
    @mock.patch("registrations.models.Entry.objects.get")
    def test_changeform_view(self, entry_get, super_method):
        request = _get_mock_request()
        object_id = None
        form_url = "form://url"

        registration = Registration.objects.create(
            length=Entry.MEMBERSHIP_YEAR,
            status=Entry.STATUS_REVIEW,
            birthday=timezone.now(),
        )
        entry = registration.entry_ptr
        entry_get.return_value = entry

        self.admin.changeform_view(request, object_id, form_url)
        self.assertFalse(entry_get.called)
        super_method.assert_called_once_with(
            request,
            object_id,
            form_url,
            {
                "entry": None,
                "can_review": False,
                "can_resend": False,
                "can_revert": False,
            },
        )

        super_method.reset_mock()
        entry_get.reset_mock()
        request = _get_mock_request(perms=["registrations.review_entries"])

        self.admin.changeform_view(request, object_id, form_url)
        self.assertFalse(entry_get.called)
        super_method.assert_called_once_with(
            request,
            object_id,
            form_url,
            {
                "entry": None,
                "can_review": False,
                "can_resend": False,
                "can_revert": False,
            },
        )

        super_method.reset_mock()
        entry_get.reset_mock()
        object_id = entry.pk

        self.admin.changeform_view(request, object_id, form_url)
        self.assertTrue(entry_get.called)
        super_method.assert_called_once_with(
            request,
            object_id,
            form_url,
            {
                "entry": entry,
                "can_review": True,
                "can_resend": False,
                "can_revert": False,
            },
        )

        super_method.reset_mock()
        entry_get.reset_mock()
        registration.status = Entry.STATUS_CONFIRM
        registration.save()
        entry = registration.entry_ptr
        entry_get.return_value = entry

        self.admin.changeform_view(request, object_id, form_url)
        self.assertTrue(entry_get.called)
        super_method.assert_called_once_with(
            request,
            object_id,
            form_url,
            {
                "entry": entry,
                "can_review": False,
                "can_resend": True,
                "can_revert": False,
            },
        )

        super_method.reset_mock()
        entry_get.reset_mock()
        registration.status = Entry.STATUS_ACCEPTED
        registration.save()
        entry = registration.entry_ptr
        entry_get.return_value = entry

        self.admin.changeform_view(request, object_id, form_url)
        self.assertTrue(entry_get.called)
        super_method.assert_called_once_with(
            request,
            object_id,
            form_url,
            {
                "entry": entry,
                "can_review": False,
                "can_resend": False,
                "can_revert": True,
            },
        )

        super_method.reset_mock()
        renewal = Renewal.objects.create(
            status=Entry.STATUS_REVIEW,
            length=Entry.MEMBERSHIP_YEAR,
            member=Member.objects.filter(last_name="Wiggers").first(),
        )
        entry = renewal.entry_ptr
        entry_get.return_value = entry
        object_id = entry.pk

        self.admin.changeform_view(request, object_id, form_url)
        self.assertTrue(entry_get.called)
        super_method.assert_called_once_with(
            request,
            object_id,
            form_url,
            {
                "entry": entry,
                "can_review": True,
                "can_resend": False,
                "can_revert": False,
            },
        )

    def test_get_readonly_fields(self):
        request = _get_mock_request([])

        fields = self.admin.get_readonly_fields(request)
        self.assertEqual(fields, ["status", "created_at", "updated_at", "payment"])

        fields = self.admin.get_readonly_fields(
            request, Registration(status=Entry.STATUS_CONFIRM)
        )
        self.assertEqual(fields, ["status", "created_at", "updated_at", "payment"])

        fields = self.admin.get_readonly_fields(
            request, Registration(status=Entry.STATUS_REJECTED)
        )
        self.assertCountEqual(
            fields,
            [
                "created_at",
                "updated_at",
                "status",
                "length",
                "membership_type",
                "remarks",
                "entry_ptr",
                "username",
                "first_name",
                "last_name",
                "birthday",
                "email",
                "phone_number",
                "student_number",
                "programme",
                "starting_year",
                "address_street",
                "address_street2",
                "address_postal_code",
                "address_city",
                "address_country",
                "membership",
                "optin_mailinglist",
                "optin_birthday",
                "contribution",
                "direct_debit",
                "initials",
                "iban",
                "bic",
                "signature",
            ],
        )

        fields = self.admin.get_readonly_fields(
            request, Registration(status=Entry.STATUS_ACCEPTED)
        )
        self.assertCountEqual(
            fields,
            [
                "created_at",
                "updated_at",
                "status",
                "length",
                "membership_type",
                "remarks",
                "entry_ptr",
                "username",
                "first_name",
                "last_name",
                "birthday",
                "email",
                "phone_number",
                "student_number",
                "programme",
                "starting_year",
                "address_street",
                "address_street2",
                "address_postal_code",
                "address_city",
                "address_country",
                "membership",
                "optin_mailinglist",
                "optin_birthday",
                "contribution",
                "direct_debit",
                "initials",
                "iban",
                "bic",
                "signature",
            ],
        )

        fields = self.admin.get_readonly_fields(
            request, Registration(status=Entry.STATUS_COMPLETED)
        )
        self.assertCountEqual(
            fields,
            [
                "created_at",
                "updated_at",
                "status",
                "length",
                "membership_type",
                "remarks",
                "entry_ptr",
                "username",
                "first_name",
                "last_name",
                "birthday",
                "email",
                "phone_number",
                "student_number",
                "programme",
                "starting_year",
                "address_street",
                "address_street2",
                "address_postal_code",
                "address_city",
                "address_country",
                "membership",
                "optin_mailinglist",
                "optin_birthday",
                "contribution",
                "direct_debit",
                "initials",
                "iban",
                "bic",
                "signature",
            ],
        )

    def test_name(self):
        reg = Registration(
            first_name="John",
            last_name="Doe",
        )
        self.assertEqual(self.admin.name(reg), reg.get_full_name())

    def test_reference_count(self):
        reg = Registration.objects.create(
            length=Entry.MEMBERSHIP_YEAR,
            first_name="John",
            last_name="Doe",
            birthday=timezone.now(),
        )
        self.assertEqual(self.admin.reference_count(reg), 0)
        Reference.objects.create(entry=reg, member=Member.objects.get(pk=1))
        Reference.objects.create(entry=reg, member=Member.objects.get(pk=2))
        self.assertEqual(self.admin.reference_count(reg), 2)

    def test_formfield_for_dbfield(self):
        with self.subTest("Payment field"):
            field = self.admin.formfield_for_dbfield(
                Registration._meta.get_field("payment"), request=None
            )
            self.assertIsInstance(field.widget, PaymentWidget)
        with self.subTest("Other field"):
            field = self.admin.formfield_for_dbfield(
                Registration._meta.get_field("first_name"), request=None
            )
            self.assertNotIsInstance(field.widget, PaymentWidget)
            self.assertIsNotNone(field.widget)

    def test_save_model(self):
        reg = Registration(
            length=Entry.MEMBERSHIP_YEAR,
            status=Registration.STATUS_REVIEW,
            birthday=timezone.now(),
        )

        with self.subTest("Status review saves"):
            reg.first_name = "Test1"
            self.admin.save_model({}, reg, None, True)
            self.assertTrue(Registration.objects.filter(first_name="Test1").exists())

        with self.subTest("Status accepted, no save"):
            reg.first_name = "Test2"
            reg.status = Registration.STATUS_ACCEPTED
            self.admin.save_model({}, reg, None, True)
            self.assertFalse(Registration.objects.filter(first_name="Test2").exists())

        with self.subTest("Status reject, no save"):
            reg.first_name = "Test2"
            reg.status = Registration.STATUS_REJECTED
            self.admin.save_model({}, reg, None, True)
            self.assertFalse(Registration.objects.filter(first_name="Test2").exists())

        with self.subTest("Status completed, no save"):
            reg.first_name = "Test2"
            reg.status = Registration.STATUS_COMPLETED
            self.admin.save_model({}, reg, None, True)
            self.assertFalse(Registration.objects.filter(first_name="Test2").exists())

    def test_bulk_actions_permissions(self):
        admin = Member.objects.get(pk=1)
        self.client.force_login(Member.objects.get(pk=1))
        Registration.objects.create(
            length=Entry.MEMBERSHIP_YEAR,
            status=Entry.STATUS_REVIEW,
            birthday=timezone.now(),
        )

        Renewal.objects.create(
            length=Entry.MEMBERSHIP_YEAR,
            status=Entry.STATUS_REVIEW,
            member=Member.objects.get(pk=2),
        )

        response = self.client.get("/admin/registrations/registration/")
        self.assertContains(response, "Accept selected registrations")
        self.assertContains(response, "Reject selected registrations")

        admin.is_superuser = False
        admin.is_staff = True
        admin.save()

        admin.user_permissions.add(Permission.objects.get(codename="view_registration"))

        response = self.client.get("/admin/registrations/registration/")
        self.assertNotContains(response, "Accept selected registrations")
        self.assertNotContains(response, "Accept selected registrations")

        admin.user_permissions.add(Permission.objects.get(codename="review_entries"))

        response = self.client.get("/admin/registrations/registration/")
        self.assertContains(response, "Accept selected registrations")
        self.assertContains(response, "Reject selected registrations")

    def test_can_open_registration_change_view(self):
        # Just a sanity check and to get coverage.
        self.client.force_login(Member.objects.get(pk=1))

        registration = Registration.objects.create(
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
        response = self.client.get(
            f"/admin/registrations/registration/{registration.pk}/change/"
        )
        self.assertEqual(response.status_code, 200)


class RenewalAdminTest(TestCase):
    fixtures = ["members.json"]

    def setUp(self):
        self.site = AdminSite()
        self.admin = admin.RenewalAdmin(Renewal, admin_site=self.site)

    def test_get_readonly_fields(self):
        request = _get_mock_request([])

        fields = self.admin.get_readonly_fields(request)
        self.assertEqual(fields, ["status", "created_at", "updated_at", "payment"])

        fields = self.admin.get_readonly_fields(
            request, Renewal(status=Entry.STATUS_CONFIRM)
        )
        self.assertEqual(
            fields, ["status", "created_at", "updated_at", "payment", "member"]
        )

        fields = self.admin.get_readonly_fields(
            request, Renewal(status=Entry.STATUS_REJECTED)
        )
        self.assertCountEqual(
            fields,
            [
                "created_at",
                "updated_at",
                "status",
                "length",
                "membership_type",
                "remarks",
                "entry_ptr",
                "member",
                "membership",
                "contribution",
            ],
        )

        fields = self.admin.get_readonly_fields(
            request, Renewal(status=Entry.STATUS_ACCEPTED)
        )
        self.assertCountEqual(
            fields,
            [
                "created_at",
                "updated_at",
                "status",
                "length",
                "membership_type",
                "remarks",
                "entry_ptr",
                "member",
                "membership",
                "contribution",
            ],
        )

    def test_name(self):
        renewal = Renewal(
            member=Member(
                first_name="John",
                last_name="Doe",
            )
        )
        self.assertEqual(self.admin.name(renewal), renewal.member.get_full_name())

    def test_email(self):
        renewal = Renewal(member=Member(email="test@example.org"))
        self.assertEqual(self.admin.email(renewal), "test@example.org")

    def test_bulk_actions_permissions(self):
        admin = Member.objects.get(pk=1)
        self.client.force_login(Member.objects.get(pk=1))

        Registration.objects.create(
            length=Entry.MEMBERSHIP_YEAR,
            status=Entry.STATUS_REVIEW,
            birthday=timezone.now(),
        )

        Renewal.objects.create(
            length=Entry.MEMBERSHIP_YEAR,
            status=Entry.STATUS_REVIEW,
            member=Member.objects.get(pk=2),
        )

        response = self.client.get("/admin/registrations/renewal/")
        self.assertContains(response, "Accept selected renewals")
        self.assertContains(response, "Reject selected renewals")

        admin.is_superuser = False
        admin.is_staff = True
        admin.save()

        admin.user_permissions.add(Permission.objects.get(codename="view_renewal"))

        response = self.client.get("/admin/registrations/renewal/")
        self.assertNotContains(response, "Accept selected renewals")
        self.assertNotContains(response, "Accept selected renewals")

        admin.user_permissions.add(Permission.objects.get(codename="review_entries"))

        response = self.client.get("/admin/registrations/renewal/")
        self.assertContains(response, "Accept selected renewals")
        self.assertContains(response, "Reject selected renewals")
