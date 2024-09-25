from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from freezegun import freeze_time

from members.models import Member, Membership, Profile
from registrations import payables
from registrations.models import Entry, Reference, Registration, Renewal


@override_settings(SUSPEND_SIGNALS=True)
class EntryTest(TestCase):
    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.registration = Registration.objects.create(
            first_name="John",
            last_name="Doe",
            email="johndoe@example.com",
            programme="computingscience",
            starting_year=2014,
            address_street="Heyendaalseweg 135",
            address_street2="",
            address_postal_code="6525AJ",
            address_city="Nijmegen",
            address_country="NL",
            phone_number="06123456789",
            birthday=timezone.now().replace(year=1990),
            length=Entry.MEMBERSHIP_YEAR,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_CONFIRM,
        )
        cls.member = Member.objects.filter(last_name="Wiggers").first()
        cls.renewal = Renewal(
            member=cls.member,
            length=Entry.MEMBERSHIP_STUDY,
            membership_type=Membership.MEMBER,
        )

    def setUp(self) -> None:
        payables.register()

    def test_str(self):
        entry = Entry(registration=self.registration)
        self.assertEqual(
            str(entry),
            "{} {} ({})".format(
                self.registration.first_name,
                self.registration.last_name,
                self.registration.email,
            ),
        )

        entry = Entry(renewal=self.renewal)
        self.assertEqual(
            str(entry),
            f"{self.member.first_name} {self.member.last_name} ({self.member.email})",
        )

    @freeze_time("2019-01-01")
    def test_save(self):
        entry = Entry(length=Entry.MEMBERSHIP_YEAR, registration=self.registration)

        entry.status = Entry.STATUS_ACCEPTED
        test_value = timezone.now().replace(year=1996)
        entry.updated_at = test_value

        with self.subTest("Accepted should not update `updated_at`"):
            entry.save()
            self.assertEqual(entry.updated_at, test_value)

        entry.status = Entry.STATUS_REJECTED

        with self.subTest("Rejected should not update `updated_at`"):
            entry.save()
            self.assertEqual(entry.updated_at, test_value)

        entry.status = Entry.STATUS_REVIEW

        with self.subTest("Review should update `updated_at`"):
            entry.save()
            self.assertNotEqual(entry.updated_at, test_value)

        entry.length = Entry.MEMBERSHIP_STUDY

        with self.subTest("Type `Member` should not change length"):
            entry.save()
            self.assertEqual(entry.length, Entry.MEMBERSHIP_STUDY)

        entry.membership_type = Membership.BENEFACTOR

    def test_clean(self):
        entry = Entry(registration=self.registration)

        entry.contribution = None
        entry.length = Entry.MEMBERSHIP_YEAR
        entry.membership_type = Membership.BENEFACTOR

        with self.subTest("Type `Benefactor` should require contribution"):
            with self.assertRaises(ValidationError):
                entry.clean()
            entry.contribution = 7.5
            entry.clean()

        with self.subTest("Type `Benefactor` should require year length"):
            entry.length = Entry.MEMBERSHIP_STUDY
            with self.assertRaises(ValidationError):
                entry.clean()


@override_settings(SUSPEND_SIGNALS=True)
@freeze_time("2019-01-01")
class RegistrationTest(TestCase):
    """Tests registrations."""

    @classmethod
    def setUpTestData(cls):
        cls.registration = Registration.objects.create(
            first_name="John",
            last_name="Doe",
            email="johndoe@example.com",
            programme="computingscience",
            starting_year=2014,
            address_street="Heyendaalseweg 135",
            address_street2="",
            address_postal_code="6525AJ",
            address_city="Nijmegen",
            address_country="NL",
            phone_number="06123456789",
            student_number="s1234567",
            birthday=timezone.now().replace(year=1990),
            length=Entry.MEMBERSHIP_YEAR,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_CONFIRM,
            contribution=7.5,
        )

    def setUp(self):
        self.registration.refresh_from_db()

    def test_str(self):
        self.assertEqual(
            str(self.registration),
            "{} {} ({})".format(
                self.registration.first_name,
                self.registration.last_name,
                self.registration.email,
            ),
        )

    def test_get_full_name(self):
        self.assertEqual(
            self.registration.get_full_name(),
            f"{self.registration.first_name} {self.registration.last_name}",
        )

    def test_full_clean_works(self):
        self.registration.full_clean()

    def test_clean_works(self):
        self.registration.clean()

    def test_unique_email_user(self):
        self.registration.clean()
        user = get_user_model().objects.create_user("johnnydoe", "johndoe@example.com")

        with self.assertRaises(ValidationError):
            self.registration.clean()

        user.delete()
        self.registration.clean()
        Registration.objects.create(
            length=Entry.MEMBERSHIP_YEAR,
            first_name="John",
            last_name="Doe",
            birthday=timezone.now().replace(year=1990),
            email="johndoe@example.com",
        )

        with self.assertRaises(ValidationError):
            self.registration.clean()

    def test_require_past_birthday(self):
        registration = Registration.objects.create(
            length=Entry.MEMBERSHIP_YEAR,
            first_name="John",
            last_name="Doe",
            birthday=timezone.now().date() + timezone.timedelta(weeks=52),
        )

        with self.assertRaises(ValidationError):
            registration.clean()

    def test_unique_student_number_user(self):
        self.registration.student_number = "s1234567"
        self.registration.clean()

        user = get_user_model().objects.create_user("johnnydoe", "johndoe2@example.com")
        Profile.objects.create(user=user, student_number="s1234567")

        with self.assertRaises(ValidationError):
            self.registration.clean()

        user.delete()
        self.registration.clean()
        Registration.objects.create(
            length=Entry.MEMBERSHIP_YEAR,
            first_name="John",
            last_name="Doe",
            birthday=timezone.now().replace(year=1990),
            student_number="s1234567",
        )

        with self.assertRaises(ValidationError):
            self.registration.clean()

    def test_require_student_number_members(self):
        with self.subTest("No student number entered"):
            self.registration.student_number = None
            with self.assertRaisesMessage(
                ValidationError, "{'student_number': ['This field is required.']}"
            ):
                self.registration.clean()

        with self.subTest("Type is benefactor"):
            self.registration.student_number = None
            self.registration.membership_type = Membership.BENEFACTOR
            self.registration.contribution = 7.5
            self.registration.clean()

    def test_unique_username_user(self):
        self.registration.username = "johndoe"
        self.registration.clean()

        get_user_model().objects.create_user("johndoe", "johndoe@example.com")

        with self.assertRaises(ValidationError):
            self.registration.clean()

    def test_require_programme_members(self):
        self.registration.programme = None
        with self.assertRaisesMessage(
            ValidationError, "{'programme': ['This field is required.']}"
        ):
            self.registration.clean()
        self.registration.membership_type = Membership.BENEFACTOR
        self.registration.contribution = 7.5
        self.registration.clean()

    def test_require_starting_year_members(self):
        self.registration.starting_year = None
        with self.assertRaisesMessage(
            ValidationError, "{'starting_year': ['This field is required.']}"
        ):
            self.registration.clean()
        self.registration.membership_type = Membership.BENEFACTOR
        self.registration.contribution = 7.5
        self.registration.clean()

    def test_require_bank_details(self):
        self.registration.direct_debit = True

        with self.assertRaises(ValidationError):
            self.registration.clean()

        self.registration.iban = "BE91ABNA0417164300"

        with self.assertRaises(ValidationError):
            self.registration.clean()

        self.registration.initials = "J"

        with self.assertRaises(ValidationError):
            self.registration.clean()

        self.registration.signature = "base64,png"

        with self.assertRaises(ValidationError):
            self.registration.clean()

        self.registration.bic = "ADSGBEBZ"

        self.registration.clean()

    def test_generate_default_username(self):
        registration = Registration(first_name="John", last_name="Doe")

        self.assertEqual(registration._generate_default_username(), "jdoe")

        registration.last_name = (
            "famgtjbblvpcxpebclsjfamgtjbblvpcxpebcl"
            "sjfamgtjbblvpcxpebclsjfamgtjbblvpcxpeb"
            "clsjfamgtjbblvpcxpebclsjfamgtjbblvpcxp"
            "ebclsjfamgtjbblvpcxpebclsjfamgtjbblvpc"
            "xpebclsj"
        )

        self.assertEqual(
            registration._generate_default_username(),
            "jfamgtjbblvpcxpebclsjfamgtjbblvpcxpebclsjf"
            "amgtjbblvpcxpebclsjfamgtjbblvpcxpebclsjfam"
            "gtjbblvpcxpebclsjfamgtjbblvpcxpebclsjfamgt"
            "jbblvpcxpebclsjfamgtjbbl",
        )

        possibilities = [
            ("Bram", "in 't Zandt", "bintzandt"),
            ("Astrid", "van der Jagt", "avanderjagt"),
            ("Bart", "van den Boom", "bvandenboom"),
            ("Richard", "van Ginkel", "rvanginkel"),
            ("Edwin", "de Koning", "edekoning"),
            ("Martijn", "de la Cosine", "mdelacosine"),
            ("Robert", "Hissink Muller", "rhissinkmuller"),
            ("Robert", "Al-Malak", "ralmalak"),
            ("Arthur", "Domelé", "adomele"),
            ("Ben", "Brücker", "bbrucker"),
        ]

        for first_name, last_name, username in possibilities:
            registration._generate_default_username(),
            self.assertEqual(
                Registration(
                    first_name=first_name, last_name=last_name
                )._generate_default_username(),
                username,
            )

    def test_get_username(self):
        self.assertEqual(
            Registration(first_name="John", last_name="Doe").get_username(),
            "jdoe",
        )
        self.assertEqual(
            Registration(
                first_name="John", last_name="Doe", username="johnny"
            ).get_username(),
            "johnny",
        )

    def test_check_user_is_unique(self):
        user = get_user_model().objects.create_user(
            "johnnydoe", "johnnydoe@example.com"
        )

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

        self.assertEqual(registration.check_user_is_unique(), True)

        user.username = "jdoe"
        user.save()

        self.assertEqual(registration.check_user_is_unique(), False)

        user.username = "johnnydoe"
        user.email = "johndoe@example.com"
        user.save()

        self.assertEqual(registration.check_user_is_unique(), False)

        user.username = "jdoe"
        user.email = "unique@example.com"
        user.save()

        registration.username = "unique_username"

        self.assertEqual(registration.check_user_is_unique(), True)

    def test_foreign_bankaccount_without_bic(self):
        self.registration.initials = "J"
        self.registration.signature = "base64,png"
        self.registration.iban = "XX91ABNA0123456789"
        self.registration.bic = ""
        self.registration.clean()


@override_settings(SUSPEND_SIGNALS=True)
@freeze_time("2019-01-01")
class RenewalTest(TestCase):
    fixtures = ["members.json"]

    def setUp(self):
        self.member = Member.objects.filter(last_name="Wiggers").first()
        self.renewal = Renewal(
            member=self.member,
            length=Entry.MEMBERSHIP_STUDY,
            contribution=8,
            membership_type=Membership.MEMBER,
        )

    def test_str(self):
        self.assertEqual(
            str(self.renewal),
            f"{self.member.first_name} {self.member.last_name} ({self.member.email})",
        )

    def test_save(self):
        self.renewal.pk = 2
        self.renewal.status = Entry.STATUS_ACCEPTED
        self.renewal.save()

        self.assertEqual(self.renewal.status, Entry.STATUS_ACCEPTED)

        self.renewal.pk = None
        self.renewal.save()

        self.assertEqual(self.renewal.status, Entry.STATUS_REVIEW)

    def test_clean_works(self):
        self.member.membership_set.all().delete()
        self.renewal.clean()

    def test_existing_renewal_in_review(self):
        Renewal.objects.create(
            member=self.member,
            length=Entry.MEMBERSHIP_STUDY,
            membership_type=Membership.MEMBER,
        )

        with self.assertRaises(ValidationError):
            self.renewal.clean()

        try:
            self.renewal.clean()
        except ValidationError as e:
            self.assertEqual(
                e.message, _("You already have a renewal request queued for review.")
            )

    def test_not_within_renew_period(self):
        membership = self.member.latest_membership
        membership.until = timezone.now().date() + timezone.timedelta(days=32)
        membership.save()

        self.renewal.length = Entry.MEMBERSHIP_YEAR

        with self.assertRaises(ValidationError):
            self.renewal.clean()

        try:
            self.renewal.clean()
        except ValidationError as e:
            self.assertCountEqual(
                e.error_dict,
                {
                    "length": "You cannot renew your membership at this moment.",
                },
            )

    def test_within_renew_period(self):
        self.renewal.length = Entry.MEMBERSHIP_YEAR

        membership = self.member.latest_membership
        membership.until = timezone.now().date() + timezone.timedelta(days=31)
        membership.save()

        self.renewal.clean()

    def test_benefactor_no_study_length(self):
        self.renewal.length = Entry.MEMBERSHIP_STUDY
        self.renewal.membership_type = Membership.BENEFACTOR
        membership = self.member.latest_membership
        membership.until = timezone.now().date()
        membership.save()

        with self.assertRaises(ValidationError):
            self.renewal.clean()

        try:
            self.renewal.clean()
        except ValidationError as e:
            self.assertCountEqual(
                e.error_dict,
                {
                    "length": "Benefactors cannot have a membership "
                    "that lasts their entire study duration.",
                },
            )

    def test_has_active_membership(self):
        membership = self.member.current_membership
        membership.until = None
        membership.save()

        with self.assertRaises(ValidationError):
            self.renewal.clean()

        try:
            self.renewal.clean()
        except ValidationError as e:
            self.assertCountEqual(
                e.error_dict,
                {
                    "length": "You currently have an active membership.",
                    "membership_type": "You currently have an active membership.",
                },
            )


@override_settings(SUSPEND_SIGNALS=True)
class ReferenceTest(TestCase):
    fixtures = ["members.json"]

    def test_str(self):
        member = Member.objects.filter(last_name="Wiggers").first()
        renewal = Renewal(
            member=member,
            length=Entry.MEMBERSHIP_YEAR,
            membership_type=Membership.MEMBER,
        )

        ref = Reference(member=member, entry=renewal)
        self.assertEqual(
            str(ref), "Reference from Thom Wiggers (thom) for Thom Wiggers ()"
        )
