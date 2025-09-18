from django.db.models import Q
from django.test import TestCase
from django.utils import timezone

from freezegun import freeze_time

from members.models import Member, Membership
from registrations import apps
from registrations.models import Entry, Registration, Renewal


class DataMinimisationTest(TestCase):
    fixtures = ["members.json"]

    @classmethod
    @freeze_time("2023-08-25")
    def setUpTestData(cls):
        cls.admin = Member.objects.get(pk=2)
        cls.admin.is_superuser = True
        cls.admin.save()

        cls.member = Member.objects.get(pk=1)
        cls.member.email = "test@example.com"
        cls.member.save()

        cls.membership = cls.member.membership_set.first()
        cls.membership.until = "2023-09-01"
        cls.membership.save()

        cls.member_registration = Registration.objects.create(
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
            birthday="1990-01-01",
            length=Entry.MEMBERSHIP_YEAR,
            contribution=7.5,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_CONFIRM,
            optin_thabloid=True,
        )

        cls.honory_registration = Registration.objects.create(
            first_name="Bobby",
            last_name="Bobs",
            email="johnnydoe@examply.com",
            student_number="s1234577",
            starting_year=2014,
            address_street="Heyendaalseweg 135",
            address_street2="",
            address_postal_code="6525AJ",
            address_city="Nijmegen",
            address_country="NL",
            phone_number="06123456799",
            birthday="1990-01-01",
            length=Entry.MEMBERSHIP_STUDY,
            contribution=7.5,
            membership_type=Membership.HONORARY,
            status=Entry.STATUS_CONFIRM,
            optin_thabloid=False,
        )

        cls.benefactor_registration = Registration.objects.create(
            first_name="Jane",
            last_name="Doe",
            username="janedoe",
            email="janedoe@example.com",
            student_number="s1234568",
            starting_year=2014,
            address_street="Heyendaalseweg 135",
            address_street2="",
            address_postal_code="6525AJ",
            address_city="Nijmegen",
            address_country="NL",
            phone_number="06123456789",
            birthday="1990-01-01",
            length=Entry.MEMBERSHIP_YEAR,
            contribution=7.5,
            membership_type=Membership.BENEFACTOR,
            status=Entry.STATUS_CONFIRM,
            optin_thabloid=False,
        )

        cls.study_time_member_registration = Registration.objects.create(
            first_name="Foo",
            last_name="Bar",
            email="foobar@example.com",
            programme="computingscience",
            student_number="s1234569",
            starting_year=2014,
            address_street="Heyendaalseweg 135",
            address_street2="",
            address_postal_code="6525AJ",
            address_city="Nijmegen",
            address_country="NL",
            phone_number="06123456789",
            birthday="1990-01-01",
            length=Entry.MEMBERSHIP_STUDY,
            contribution=30,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_CONFIRM,
        )

        cls.renewal = Renewal.objects.create(
            member=cls.member,
            length=Entry.MEMBERSHIP_YEAR,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_REVIEW,
            contribution=7.5,
        )

    def test_data_minimisation(self):
        with freeze_time("2025-01-01"):
            with self.subTest("No old completed registrations."):
                self.assertEqual(
                    apps.RegistrationsConfig.execute_data_minimisation(), 0
                )

        with freeze_time("2024-09-10"):
            self.renewal.status = Entry.STATUS_COMPLETED
            self.renewal.updated_at = timezone.now()
            self.renewal.save()
            self.member_registration.status = Entry.STATUS_COMPLETED
            self.member_registration.updated_at = timezone.now()
            self.member_registration.save()

        self.assertEqual(Registration.objects.count(), 4)
        self.assertEqual(Renewal.objects.count(), 1)

        with freeze_time("2024-09-15"):
            with self.subTest("A recent completed registration and renewal."):
                apps.RegistrationsConfig.execute_data_minimisation()
                self.assertEqual(Registration.objects.count(), 4)
                self.assertEqual(Renewal.objects.count(), 1)

        with freeze_time("2024-10-15"):
            with self.subTest("Dry run."):
                apps.RegistrationsConfig.execute_data_minimisation(dry_run=True)
                self.assertEqual(Registration.objects.count(), 4)
                self.assertEqual(Renewal.objects.count(), 1)

            with self.subTest("An old completed registration and renewal."):
                apps.RegistrationsConfig.execute_data_minimisation()
                self.assertEqual(Registration.objects.count(), 3)
                self.assertEqual(Renewal.objects.count(), 0)

    def test_minimise_user_dry_run(self):
        """Test minimise_user with dry_run=True returns renewals without deleting."""
        # Create more renewals for the test user
        new_renewal1 = Renewal.objects.create(
            member=self.member,
            length=Entry.MEMBERSHIP_YEAR,
            contribution=7.5,
            status=Entry.STATUS_COMPLETED,
        )

        new_renewal2 = Renewal.objects.create(
            member=self.member,
            length=Entry.MEMBERSHIP_YEAR,
            contribution=7.5,
            status=Entry.STATUS_REJECTED,
        )

        initial_count = Renewal.objects.filter(member=self.member).count()
        expected_renewal_count = Renewal.objects.filter(
            Q(status=Entry.STATUS_COMPLETED) | Q(status=Entry.STATUS_REJECTED),
            member=self.member,
        ).count()

        # Call minimise_user with dry_run=True
        renewals = apps.RegistrationsConfig.minimise_user(self.member, dry_run=True)

        # Verify renewals were returned but not deleted
        self.assertEqual(renewals.count(), expected_renewal_count)
        self.assertEqual(
            Renewal.objects.filter(member=self.member).count(), initial_count
        )

    def test_minimise_user_actual_run(self):
        """Test minimise_user with dry_run=False properly deletes renewals."""
        new_renewal1 = Renewal.objects.create(
            member=self.member,
            length=Entry.MEMBERSHIP_YEAR,
            contribution=7.5,
            status=Entry.STATUS_COMPLETED,
        )

        new_renewal2 = Renewal.objects.create(
            member=self.member,
            length=Entry.MEMBERSHIP_YEAR,
            contribution=7.5,
            status=Entry.STATUS_REJECTED,
        )

        new_renewal3 = Renewal.objects.create(
            member=self.member,
            length=Entry.MEMBERSHIP_YEAR,
            contribution=7.5,
            status=Entry.STATUS_CONFIRM,
        )

        confirm_count_before = Renewal.objects.filter(
            member=self.member, status=Entry.STATUS_CONFIRM
        ).count()

        result = apps.RegistrationsConfig.minimise_user(self.member, dry_run=False)

        self.assertEqual(
            Renewal.objects.filter(
                member=self.member,
                status__in=[Entry.STATUS_COMPLETED, Entry.STATUS_REJECTED],
            ).count(),
            0,
        )

        self.assertEqual(
            Renewal.objects.filter(
                member=self.member, status=Entry.STATUS_CONFIRM
            ).count(),
            confirm_count_before,
        )
