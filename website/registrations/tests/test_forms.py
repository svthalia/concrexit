from django.test import TestCase, override_settings
from django.utils import timezone

from freezegun import freeze_time

from members.models import Member, Membership
from registrations import forms
from registrations.models import Entry, Reference, Renewal


class MemberRegistrationFormTest(TestCase):
    def setUp(self):
        self.data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "johndoe@example.com",
            "programme": "computingscience",
            "student_number": "s1234567",
            "starting_year": 2014,
            "address_street": "Heyendaalseweg 135",
            "address_street2": "",
            "address_postal_code": "6525AJ",
            "address_city": "Nijmegen",
            "address_country": "NL",
            "phone_number": "06123456789",
            "birthday": timezone.now().replace(year=1990, day=1),
            "language": "en",
            "length": Entry.MEMBERSHIP_YEAR,
            "membership_type": Membership.MEMBER,
            "privacy_policy": 1,
        }

    def test_privacy_policy_checked(self):
        with self.subTest("Form is valid"):
            form = forms.MemberRegistrationForm(self.data)
            self.assertTrue(form.is_valid(), msg=dict(form.errors))
        with self.subTest("Form is not valid"):
            self.data["privacy_policy"] = 0
            form = forms.MemberRegistrationForm(self.data)
            self.assertFalse(form.is_valid(), msg=dict(form.errors))

    def test_has_privacy_policy_field(self):
        form = forms.MemberRegistrationForm(self.data)
        self.assertTrue(form.fields["privacy_policy"] is not None)


class BenefactorRegistrationFormTest(TestCase):
    def setUp(self):
        self.data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "johndoe@example.com",
            "programme": "computingscience",
            "student_number": "s1234567",
            "starting_year": 2014,
            "address_street": "Heyendaalseweg 135",
            "address_street2": "",
            "address_postal_code": "6525AJ",
            "address_city": "Nijmegen",
            "address_country": "NL",
            "phone_number": "06123456789",
            "birthday": timezone.now().replace(year=1990, day=1),
            "language": "en",
            "length": Entry.MEMBERSHIP_YEAR,
            "membership_type": Membership.BENEFACTOR,
            "privacy_policy": 1,
            "icis_employee": 1,
            "contribution": 8,
        }

    def test_privacy_policy_checked(self):
        with self.subTest("Form is valid"):
            form = forms.BenefactorRegistrationForm(self.data)
            self.assertTrue(form.is_valid(), msg=dict(form.errors))
        with self.subTest("Form is not valid"):
            self.data["privacy_policy"] = 0
            form = forms.BenefactorRegistrationForm(self.data)
            self.assertFalse(form.is_valid(), msg=dict(form.errors))

    def test_has_privacy_policy_field(self):
        form = forms.BenefactorRegistrationForm(self.data)
        self.assertTrue(form.fields["privacy_policy"] is not None)


@override_settings(SUSPEND_SIGNALS=True)
class RenewalFormTest(TestCase):
    fixtures = ["members.json"]

    def setUp(self):
        self.member = Member.objects.filter(last_name="Wiggers").first()
        self.member.membership_set.all().delete()
        self.data = {
            "member": self.member.pk,
            "length": Entry.MEMBERSHIP_STUDY,
            "contribution": 8,
            "membership_type": Membership.MEMBER,
            "privacy_policy": 1,
        }

    def test_is_valid(self):
        with self.subTest("Form is valid"):
            form = forms.RenewalForm(self.data)
            self.assertTrue(form.is_valid(), msg=dict(form.errors))
        with self.subTest("Form is not valid"):
            self.data["privacy_policy"] = 0
            form = forms.RenewalForm(self.data)
            self.assertFalse(form.is_valid(), msg=dict(form.errors))

    def test_has_privacy_policy_field(self):
        form = forms.RenewalForm(self.data)
        self.assertTrue(form.fields["privacy_policy"] is not None)


@override_settings(SUSPEND_SIGNALS=True)
class ReferenceFormTest(TestCase):
    fixtures = ["members.json"]

    def setUp(self):
        self.member = Member.objects.filter(last_name="Wiggers").first()
        self.member.membership_set.all().delete()
        self.entry = Renewal.objects.create(
            member=self.member, length=Entry.MEMBERSHIP_YEAR
        )
        self.member.membership_set.all().delete()
        self.data = {"member": self.member.pk, "entry": self.entry.pk}

    @freeze_time("2018-08-01")
    def test_clean(self):
        with self.subTest("Form is valid"):
            form = forms.ReferenceForm(self.data)
            self.assertTrue(form.is_valid())
            form.clean()
        with self.subTest("Form throws error about benefactor type"):
            m = Membership.objects.create(
                type=Membership.BENEFACTOR,
                user=self.member,
                since="2017-09-01",
                until="2018-08-31",
            )
            form = forms.ReferenceForm(self.data)
            self.assertFalse(form.is_valid())
            self.assertEqual(
                form.errors, {"__all__": ["Benefactors cannot give references."]}
            )
            m.delete()
        with self.subTest("Form throws error about membership end"):
            m = Membership.objects.create(
                type=Membership.MEMBER,
                user=self.member,
                since="2017-09-01",
                until="2018-08-31",
            )
            form = forms.ReferenceForm(self.data)
            self.assertFalse(form.is_valid())
            self.assertEqual(
                form.errors,
                {
                    "__all__": [
                        "It's not possible to give references for "
                        "memberships that start after your own "
                        "membership's end."
                    ]
                },
            )
            m.delete()
        with self.subTest("Form throws error about uniqueness"):
            Reference.objects.create(member=self.member, entry=self.entry)
            form = forms.ReferenceForm(self.data)
            self.assertFalse(form.is_valid())
            self.assertEqual(
                form.errors,
                {"__all__": ["You've already given a reference for this person."]},
            )
