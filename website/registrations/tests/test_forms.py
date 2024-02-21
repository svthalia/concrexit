from django.conf import settings
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
            "phone_number": "06 12345678",
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
            self.assertEqual(form.cleaned_data["phone_number"], "0612345678")
        with self.subTest("Form is not valid"):
            self.data["privacy_policy"] = 0
            form = forms.MemberRegistrationForm(self.data)
            self.assertFalse(form.is_valid(), msg=dict(form.errors))

    def test_has_privacy_policy_field(self):
        form = forms.MemberRegistrationForm(self.data)
        self.assertTrue(form.fields["privacy_policy"] is not None)

    def test_price_calculation(self):
        with self.subTest(length=Entry.MEMBERSHIP_YEAR):
            self.data["length"] = Entry.MEMBERSHIP_YEAR
            form = forms.MemberRegistrationForm(self.data)
            form.is_valid()
            registration = form.save()
            self.assertEqual(
                registration.contribution,
                settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_YEAR],
            )
            registration.delete()
        with self.subTest(length=Entry.MEMBERSHIP_STUDY):
            self.data["length"] = Entry.MEMBERSHIP_STUDY
            form = forms.MemberRegistrationForm(self.data)
            form.is_valid()
            registration = form.save()
            self.assertEqual(
                registration.contribution,
                settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_STUDY],
            )
            registration.delete()


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

    def test_price_calculation(self):
        form = forms.BenefactorRegistrationForm(self.data)
        form.is_valid()
        registration = form.save()
        self.assertEqual(registration.contribution, 8)


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
        with self.subTest("User is minimized"):
            profile = self.member.profile
            profile.student_number = None
            profile.phone_number = None
            profile.address_street = None
            profile.address_street2 = None
            profile.address_postal_code = None
            profile.address_city = None
            profile.address_country = None
            profile.birthday = None
            profile.emergency_contact_phone_number = None
            profile.emergency_contact = None
            profile.is_minimized = True
            profile.save()
            self.assertFalse(forms.RenewalForm(self.data).is_valid())

    def test_has_privacy_policy_field(self):
        form = forms.RenewalForm(self.data)
        self.assertTrue(form.fields["privacy_policy"] is not None)

    def test_price_calculation(self):
        membership = Membership.objects.create(
            user=self.member,
            type=Membership.MEMBER,
            since="2023-09-01",
            until="2024-08-31",
        )

        with self.subTest("Member, membership upgrade discount"):
            with freeze_time("2024-08-20"):
                self.data["length"] = Entry.MEMBERSHIP_STUDY
                self.data["membership_type"] = Membership.MEMBER
                form = forms.RenewalForm(self.data)
                self.assertTrue(form.is_valid())
                renewal = form.save()
                self.assertEqual(
                    renewal.contribution,
                    settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_STUDY]
                    - settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_YEAR],
                )
                renewal.delete()

        with self.subTest("Member, new year membership before expiry"):
            with freeze_time("2024-08-20"):
                self.data["length"] = Entry.MEMBERSHIP_YEAR
                self.data["membership_type"] = Membership.MEMBER
                form = forms.RenewalForm(self.data)
                self.assertTrue(form.is_valid())
                renewal = form.save()
                self.assertEqual(
                    renewal.contribution,
                    settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_YEAR],
                )
                renewal.delete()

        with self.subTest("Member, new year membership after expiry"):
            with freeze_time("2024-09-10"):
                self.data["length"] = Entry.MEMBERSHIP_YEAR
                self.data["membership_type"] = Membership.MEMBER
                form = forms.RenewalForm(self.data)
                self.assertTrue(form.is_valid())
                renewal = form.save()
                self.assertEqual(
                    renewal.contribution,
                    settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_YEAR],
                )
                renewal.delete()

        with self.subTest("Member, study membership after expiry"):
            with freeze_time("2024-09-10"):
                self.data["length"] = Entry.MEMBERSHIP_STUDY
                self.data["membership_type"] = Membership.MEMBER
                form = forms.RenewalForm(self.data)
                self.assertTrue(form.is_valid())
                renewal = form.save()
                self.assertEqual(
                    renewal.contribution,
                    settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_STUDY],
                )
                renewal.delete()

        with self.subTest("Member, new benefactor membership before expiry"):
            with freeze_time("2024-08-20"):
                self.data["length"] = Entry.MEMBERSHIP_YEAR
                self.data["membership_type"] = Membership.BENEFACTOR
                form = forms.RenewalForm(self.data)
                self.assertTrue(form.is_valid())
                renewal = form.save()
                self.assertEqual(renewal.contribution, 8)
                renewal.delete()

        with self.subTest("Member, new benefactor membership before expiry"):
            with freeze_time("2024-09-10"):
                self.data["length"] = Entry.MEMBERSHIP_YEAR
                self.data["membership_type"] = Membership.BENEFACTOR
                form = forms.RenewalForm(self.data)
                self.assertTrue(form.is_valid())
                renewal = form.save()
                self.assertEqual(renewal.contribution, 8)
                renewal.delete()

        membership.type = Membership.BENEFACTOR
        membership.save()

        with self.subTest("Benefactor, year benefactor membership before expiry"):
            with freeze_time("2024-08-20"):
                self.data["length"] = Entry.MEMBERSHIP_YEAR
                self.data["membership_type"] = Membership.BENEFACTOR
                form = forms.RenewalForm(self.data)
                self.assertTrue(form.is_valid())
                renewal = form.save()
                self.assertEqual(renewal.contribution, 8)
                renewal.delete()

        with self.subTest("Benefactor, year benefactor membership after expiry"):
            with freeze_time("2024-09-10"):
                self.data["length"] = Entry.MEMBERSHIP_YEAR
                self.data["membership_type"] = Membership.BENEFACTOR
                form = forms.RenewalForm(self.data)
                self.assertTrue(form.is_valid())
                renewal = form.save()
                self.assertEqual(renewal.contribution, 8)
                renewal.delete()

        with self.subTest("Benefactor, year member membership before expiry"):
            with freeze_time("2024-08-20"):
                self.data["length"] = Entry.MEMBERSHIP_YEAR
                self.data["membership_type"] = Membership.MEMBER
                form = forms.RenewalForm(self.data)
                self.assertTrue(form.is_valid())
                renewal = form.save()
                self.assertEqual(
                    renewal.contribution,
                    settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_YEAR],
                )
                renewal.delete()

        with self.subTest("Benefactor, year member membership after expiry"):
            with freeze_time("2024-09-10"):
                self.data["length"] = Entry.MEMBERSHIP_YEAR
                self.data["membership_type"] = Membership.MEMBER
                form = forms.RenewalForm(self.data)
                self.assertTrue(form.is_valid())
                renewal = form.save()
                self.assertEqual(
                    renewal.contribution,
                    settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_YEAR],
                )
                renewal.delete()

        with self.subTest("Benefactor, study membership before expiry"):
            with freeze_time("2024-08-20"):
                self.data["length"] = Entry.MEMBERSHIP_STUDY
                self.data["membership_type"] = Membership.MEMBER
                form = forms.RenewalForm(self.data)
                self.assertTrue(form.is_valid())
                renewal = form.save()
                self.assertEqual(
                    renewal.contribution,
                    settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_STUDY],
                )
                renewal.delete()

        with self.subTest("Benefactor, study membership after expiry"):
            with freeze_time("2024-09-10"):
                self.data["length"] = Entry.MEMBERSHIP_STUDY
                self.data["membership_type"] = Membership.MEMBER
                form = forms.RenewalForm(self.data)
                self.assertTrue(form.is_valid())
                renewal = form.save()
                self.assertEqual(
                    renewal.contribution,
                    settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_STUDY],
                )
                renewal.delete()


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
