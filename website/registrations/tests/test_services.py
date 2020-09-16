from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from freezegun import freeze_time

from members.models import Member, Membership
from payments.models import Payment
from registrations import services
from registrations.models import Entry, Registration, Renewal
from utils.snippets import datetime_to_lectureyear


@override_settings(SUSPEND_SIGNALS=True)
class ServicesTest(TestCase):
    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.e0 = Entry.objects.create(
            length=Entry.MEMBERSHIP_YEAR,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_REVIEW,
        )
        cls.e1 = Registration.objects.create(
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
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_CONFIRM,
        )
        cls.e2 = Registration.objects.create(
            first_name="Paula",
            last_name="Test",
            email="ptest@example.com",
            programme="computingscience",
            student_number="s2345678",
            starting_year=2015,
            address_street="Heyendaalseweg 136",
            address_street2="",
            address_postal_code="6525AJ",
            address_city="Nijmegen",
            address_country="NL",
            phone_number="06098765432",
            birthday=timezone.now().replace(year=1992, day=2).date(),
            length=Entry.MEMBERSHIP_STUDY,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_CONFIRM,
        )
        cls.e3 = Renewal.objects.create(
            member=Member.objects.get(pk=2),
            length=Entry.MEMBERSHIP_STUDY,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_CONFIRM,
        )
        cls.e4 = Renewal.objects.create(
            member=Member.objects.get(pk=3),
            length=Entry.MEMBERSHIP_YEAR,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_ACCEPTED,
        )
        cls.e4.status = Entry.STATUS_ACCEPTED
        cls.e4.save()
        cls.e5 = Renewal.objects.create(
            member=Member.objects.get(pk=4),
            length=Entry.MEMBERSHIP_STUDY,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_ACCEPTED,
            created_at=timezone.now() - timedelta(days=10),
        )
        cls.e5.status = Entry.STATUS_ACCEPTED
        cls.e5.save()

    def setUp(self):
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()
        self.e3.refresh_from_db()
        self.e4.refresh_from_db()

    def test_generate_username(self):
        username = services._generate_username(self.e1)
        self.assertEqual(username, "jdoe")

        self.e1.last_name = (
            "famgtjbblvpcxpebclsjfamgtjbblvpcxpebcl"
            "sjfamgtjbblvpcxpebclsjfamgtjbblvpcxpeb"
            "clsjfamgtjbblvpcxpebclsjfamgtjbblvpcxp"
            "ebclsjfamgtjbblvpcxpebclsjfamgtjbblvpc"
            "xpebclsj"
        )

        username = services._generate_username(self.e1)
        self.assertEqual(
            username,
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

        for pos in possibilities:
            username = services._generate_username(
                Registration(first_name=pos[0], last_name=pos[1])
            )
            self.assertEqual(username, pos[2])

    def test_check_unique_user(self):
        user = get_user_model().objects.create_user(
            "johnnydoe", "johnnydoe@example.com"
        )

        self.assertEqual(services.check_unique_user(self.e1), True)

        user.username = "jdoe"
        user.save()

        self.assertEqual(services.check_unique_user(self.e1), False)

        user.username = "johnnydoe"
        user.email = "johndoe@example.com"
        user.save()

        self.assertEqual(services.check_unique_user(self.e1), False)

        user.username = "jdoe"
        user.email = "unique@example.com"
        user.save()
        self.e1.registration.username = "unique_username"

        self.assertEqual(services.check_unique_user(self.e1), True)

    def test_confirm_entry(self):
        self.e3.status = Entry.STATUS_REVIEW
        self.e3.save()

        rows_updated = services.confirm_entry(Entry.objects.all())

        self.assertEqual(rows_updated, 2)
        self.assertEqual(Entry.objects.filter(status=Entry.STATUS_REVIEW).count(), 4)

    def test_reject_entries(self):
        self.e2.status = Entry.STATUS_REVIEW
        self.e2.save()
        self.e3.status = Entry.STATUS_REVIEW
        self.e3.save()

        rows_updated = services.reject_entries(1, Entry.objects.all())

        self.assertEqual(rows_updated, 3)
        self.assertEqual(Entry.objects.filter(status=Entry.STATUS_REJECTED).count(), 3)
        self.assertEqual(len(mail.outbox), 2)

    def test_accept_entries(self):
        self.e2.status = Entry.STATUS_REVIEW
        self.e2.save()
        self.e3.status = Entry.STATUS_REVIEW
        self.e3.save()

        rows_updated = services.accept_entries(1, Entry.objects.all())

        self.e2.refresh_from_db()
        self.e3.refresh_from_db()

        self.assertNotEqual(self.e2.payment, None)
        self.assertNotEqual(self.e3.payment, None)

        self.assertEqual(self.e2.username, "ptest")

        self.assertEqual(rows_updated, 3)
        self.assertEqual(Entry.objects.filter(status=Entry.STATUS_ACCEPTED).count(), 5)
        self.assertEqual(len(mail.outbox), 2)

    def test_accept_entries_manual_username(self):
        self.e2.status = Entry.STATUS_REVIEW
        self.e2.username = "manual_username"
        self.e2.save()
        self.e3.status = Entry.STATUS_REVIEW
        self.e3.save()

        rows_updated = services.accept_entries(1, Entry.objects.all())

        self.e2.refresh_from_db()
        self.assertEqual(self.e2.username, "manual_username")

        self.assertEqual(rows_updated, 3)
        self.assertEqual(Entry.objects.filter(status=Entry.STATUS_ACCEPTED).count(), 5)
        self.assertEqual(len(mail.outbox), 2)

    @mock.patch("registrations.services.check_unique_user")
    def test_accept_entries_user_not_unique(self, check_unique_user):
        check_unique_user.return_value = False

        self.e2.status = Entry.STATUS_REVIEW
        self.e2.save()
        self.e3.status = Entry.STATUS_REVIEW
        self.e3.save()

        rows_updated = services.accept_entries(1, Entry.objects.all())

        self.assertEqual(rows_updated, 0)
        self.assertEqual(Entry.objects.filter(status=Entry.STATUS_ACCEPTED).count(), 2)
        self.assertEqual(len(mail.outbox), 0)

    def test_revert_entry(self):
        with self.subTest("Revert accepted entry"):
            self.e2.status = Entry.STATUS_ACCEPTED
            self.e2.payment = services._create_payment_for_entry(self.e2)
            self.e2.save()

            services.revert_entry(1, self.e2)

            self.e2.refresh_from_db()

            self.assertEqual(self.e2.status, Entry.STATUS_REVIEW)
            self.assertIsNone(self.e2.payment)

        with self.subTest("Revert rejected entry"):
            self.e3.status = Entry.STATUS_REJECTED
            self.e3.save()

            services.revert_entry(1, self.e3)

            self.e3.refresh_from_db()

            self.assertEqual(self.e3.status, Entry.STATUS_REVIEW)

        with self.subTest("Revert another rejected entry"):
            self.e0.status = Entry.STATUS_REJECTED
            self.e0.payment = services._create_payment_for_entry(self.e0)
            self.e0.save()

            services.revert_entry(1, self.e0)

            self.e0.refresh_from_db()

            self.assertEqual(self.e0.status, Entry.STATUS_REVIEW)

        with self.subTest("Does not revert completed entry"):
            self.e2.status = Entry.STATUS_COMPLETED
            self.e2.payment = services._create_payment_for_entry(self.e2)
            self.e2.save()

            services.revert_entry(1, self.e0)

            self.e2.refresh_from_db()

            self.assertEqual(self.e2.status, Entry.STATUS_COMPLETED)
            self.assertIsNotNone(self.e2.payment)

    def test_create_payment_for_entry(self):
        self.e1.username = "jdoe"
        self.e1.save()
        self.e2.username = "ptest"
        self.e2.save()

        p1 = services._create_payment_for_entry(self.e1)  # 'year' payment
        p2 = services._create_payment_for_entry(self.e2)  # 'study' payment

        lecture_year = datetime_to_lectureyear(timezone.now())
        Membership.objects.create(
            type=Membership.MEMBER,
            since=timezone.datetime(year=lecture_year, month=9, day=1),
            until=timezone.datetime(year=lecture_year + 1, month=9, day=1),
            user=self.e3.member,
        )
        Membership.objects.create(
            type=Membership.MEMBER,
            since=timezone.datetime(year=lecture_year, month=9, day=1),
            until=timezone.datetime(year=lecture_year + 1, month=9, day=1),
            user=self.e4.member,
        )
        Membership.objects.create(
            type=Membership.MEMBER,
            since=timezone.now() - timedelta(days=31),
            until=timezone.now() - timedelta(days=2),
            user=self.e5.member,
        )

        # upgrade 'study'
        p3 = services._create_payment_for_entry(self.e3)
        # upgrade 'year'
        p4 = services._create_payment_for_entry(self.e4)
        # upgrade 'study' after membership end
        p5 = services._create_payment_for_entry(self.e5)

        self.e1.membership_type = Membership.BENEFACTOR
        self.e1.contribution = 10
        p6 = services._create_payment_for_entry(self.e1)  # contribu payment

        self.assertEqual(p1.amount, settings.MEMBERSHIP_PRICES["year"])
        self.assertEqual(p1.processed, False)
        self.assertEqual(p2.amount, settings.MEMBERSHIP_PRICES["study"])
        self.assertEqual(p2.processed, False)
        self.assertEqual(
            p3.amount,
            settings.MEMBERSHIP_PRICES["study"] - settings.MEMBERSHIP_PRICES["year"],
        )
        self.assertEqual(p3.processed, False)
        self.assertEqual(p4.amount, settings.MEMBERSHIP_PRICES["year"])
        self.assertEqual(p4.processed, False)
        self.assertEqual(
            p5.amount,
            settings.MEMBERSHIP_PRICES["study"] - settings.MEMBERSHIP_PRICES["year"],
        )
        self.assertEqual(p5.processed, False)
        self.assertEqual(p6.amount, 10)
        self.assertEqual(p6.processed, False)

    @mock.patch("registrations.services.check_unique_user")
    def test_create_member_from_registration(self, check_unique_user):
        # We use capitalisation here because we want
        # to test if the username is lowercased
        self.e1.username = "JDoe"
        self.e1.save()

        check_unique_user.return_value = False
        with self.assertRaises(ValueError):
            services._create_member_from_registration(self.e1)

        check_unique_user.return_value = True
        member = services._create_member_from_registration(self.e1)

        self.assertEqual(member.username, "jdoe")
        self.assertEqual(member.first_name, "John")
        self.assertEqual(member.last_name, "Doe")
        self.assertEqual(member.email, "johndoe@example.com")
        self.assertEqual(member.email, "johndoe@example.com")

        self.assertEqual(member.profile.programme, "computingscience")
        self.assertEqual(member.profile.student_number, "s1234567")
        self.assertEqual(member.profile.starting_year, 2014)
        self.assertEqual(member.profile.address_street, "Heyendaalseweg 135")
        self.assertEqual(member.profile.address_street2, "")
        self.assertEqual(member.profile.address_postal_code, "6525AJ")
        self.assertEqual(member.profile.address_city, "Nijmegen")
        self.assertEqual(member.profile.address_country, "NL")
        self.assertEqual(member.profile.phone_number, "06123456789")
        self.assertEqual(
            member.profile.birthday, timezone.now().replace(year=1990, day=1).date()
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Welcome to Study Association Thalia")

    def test_create_membership_from_entry(self):
        self.e1.username = "jdoe"
        self.e1.save()
        self.e2.username = "ptest"
        self.e2.save()

        with freeze_time("2017-01-12"):
            lecture_year = datetime_to_lectureyear(timezone.now())
            self.assertEqual(lecture_year, 2016)

            m1 = services._create_member_from_registration(self.e1)
            m2 = services._create_member_from_registration(self.e2)

            # Registration to new 'year' membership starting today
            membership1 = services._create_membership_from_entry(self.e1, m1)

            self.assertEqual(membership1.since, timezone.now().date())
            self.assertEqual(
                membership1.until, timezone.datetime(year=2017, month=9, day=1).date()
            )
            self.assertEqual(membership1.user, m1)
            self.assertEqual(membership1.type, self.e1.membership_type)

            # Registration to new 'study' membership starting today
            membership2 = services._create_membership_from_entry(self.e2, m2)

            self.assertEqual(membership2.since, timezone.now().date())
            self.assertEqual(membership2.until, None)
            self.assertEqual(membership2.user, m2)
            self.assertEqual(membership2.type, self.e2.membership_type)

            membership2.delete()

        with freeze_time("2017-08-12"):
            # Check if since is new lecture year in august
            membership2 = services._create_membership_from_entry(self.e2, m2)

            self.assertEqual(
                membership2.since, timezone.datetime(year=2017, month=9, day=1).date()
            )
            self.assertEqual(membership2.until, None)
            self.assertEqual(membership2.user, m2)
            self.assertEqual(membership2.type, self.e2.membership_type)

        with freeze_time("2017-01-12"):
            # Renewal to new 'study' membership starting today
            self.e3.length = Entry.MEMBERSHIP_STUDY
            membership3 = services._create_membership_from_entry(self.e3)

            self.assertEqual(membership3.since, timezone.now().date())
            self.assertEqual(membership3.until, None)
            self.assertEqual(membership3.user, self.e3.member)
            self.assertEqual(membership3.type, self.e3.membership_type)

            membership3.delete()

            # Renewal to new 'year' membership starting today
            self.e3.length = Entry.MEMBERSHIP_YEAR
            membership3 = services._create_membership_from_entry(self.e3)

            self.assertEqual(membership3.since, timezone.now().date())
            self.assertEqual(
                membership3.until, timezone.datetime(month=9, day=1, year=2017).date()
            )
            self.assertEqual(membership3.user, self.e3.member)
            self.assertEqual(membership3.type, self.e3.membership_type)

            membership3.delete()

            self.e3.length = Entry.MEMBERSHIP_YEAR
            existing_membership = Membership.objects.create(
                type=Membership.MEMBER,
                since=timezone.datetime(year=2016, month=9, day=1).date(),
                until=timezone.datetime(year=2017, month=1, day=31).date(),
                user=self.e3.member,
            )

            # Renewal without length
            self.e3.length = None
            membership3 = services._create_membership_from_entry(
                self.e3, self.e3.member
            )
            self.assertEqual(membership3, None)

            # Renewal to new 'year' membership starting 1 day after
            # end of the previous membership
            self.e3.length = Entry.MEMBERSHIP_YEAR
            membership3 = services._create_membership_from_entry(self.e3)
            self.assertEqual(membership3.since, existing_membership.until)
            self.assertEqual(
                membership3.until, timezone.datetime(year=2017, month=9, day=1).date()
            )
            self.assertEqual(membership3.user, self.e3.member)
            self.assertEqual(membership3.type, self.e3.membership_type)

            membership3.delete()
            self.e3.length = Entry.MEMBERSHIP_STUDY

            # Renewal (aka upgrade) existing membership to 'study' membership
            # It doesn't work when the entry was made after the renewal
            # was due, so this is a new membership
            membership3 = services._create_membership_from_entry(self.e3)
            self.assertEqual(membership3.since, timezone.now().date())
            self.assertEqual(membership3.until, None)
            self.assertEqual(membership3.user, self.e3.member)
            self.assertEqual(membership3.type, self.e3.membership_type)

            membership3.delete()

            # But it does work when the entry was created before the renewal
            # was actually due. This modifies the existing membership
            self.e3.created_at = timezone.make_aware(timezone.datetime(2017, 1, 30))
            self.e3.save()
            membership3 = services._create_membership_from_entry(self.e3)
            self.assertEqual(membership3.since, existing_membership.since)
            self.assertEqual(membership3.until, None)
            self.assertEqual(membership3.user, self.e3.member)
            self.assertEqual(membership3.type, self.e3.membership_type)

            # Fail 'study' renewal of existing 'study' membership
            existing_membership.until = None
            existing_membership.save()
            with self.assertRaises(ValueError):
                services._create_membership_from_entry(self.e3)

            # Fail 'year' renewal of existing 'study' membership
            self.e3.length = Entry.MEMBERSHIP_YEAR
            existing_membership.until = None
            existing_membership.save()
            with self.assertRaises(ValueError):
                services._create_membership_from_entry(self.e3)

    def test_process_payment(self):
        self.e1.username = "jdoe"
        self.e1.save()
        self.e2.username = "ptest"
        self.e2.save()

        # Check that the DoesNotExist is caught
        p = Payment(amount=10, type=Payment.CARD)
        services.process_payment(p)

        p0 = services._create_payment_for_entry(self.e0)
        self.e0.payment = p0
        self.e0.save()
        p1 = services._create_payment_for_entry(self.e1)
        self.e1.payment = p1
        self.e1.save()
        p2 = services._create_payment_for_entry(self.e2)
        self.e2.payment = p2
        self.e2.save()
        p3 = services._create_payment_for_entry(self.e3)
        self.e3.payment = p3
        self.e3.save()

        Entry.objects.filter(pk__in=[self.e1.pk, self.e2.pk, self.e3.pk]).update(
            status=Entry.STATUS_ACCEPTED
        )

        payments = Payment.objects.filter(pk__in=[p0.pk, p2.pk, p3.pk])
        payments.update(type=Payment.CARD)

        for payment in Payment.objects.filter(pk__in=[p0.pk, p1.pk, p2.pk]):
            services.process_payment(payment)

        self.e0.refresh_from_db()
        self.e1.refresh_from_db()
        self.e2.refresh_from_db()

        self.assertEqual(self.e0.status, Entry.STATUS_REVIEW)
        self.assertEqual(self.e1.status, Entry.STATUS_ACCEPTED)
        self.assertEqual(self.e2.status, Entry.STATUS_COMPLETED)

        p0.type = Payment.CARD
        p0.save()
        self.e0.status = Entry.STATUS_ACCEPTED
        self.e0.save()
        services.process_payment(p0)

        self.assertEqual(self.e0.status, Entry.STATUS_ACCEPTED)

        p3.refresh_from_db()
        services.process_payment(p3)
        self.e3.refresh_from_db()

        self.assertEqual(self.e3.status, Entry.STATUS_COMPLETED)
        self.assertEqual(len(mail.outbox), 2)

    def test_process_payment_no_member_created(self):
        p1 = services._create_payment_for_entry(self.e1)
        p2 = services._create_payment_for_entry(self.e2)

        Entry.objects.filter(pk__in=[self.e1.pk, self.e2.pk]).update(
            status=Entry.STATUS_ACCEPTED
        )

        payments = Payment.objects.filter(pk__in=[p1.pk, p2.pk])
        payments.update(type=Payment.CARD)

        with mock.patch(
            "registrations.services._create_member_from_registration"
        ) as create_member:
            with mock.patch(
                "registrations.services._create_membership_from_entry"
            ) as create_membership:
                create_member.return_value = None
                for payment in Payment.objects.filter(pk__in=[p1.pk, p2.pk]):
                    services.process_payment(payment)
                    self.assertFalse(create_membership.called)

    @freeze_time("2019-01-01")
    def test_execute_data_minimisation(self):
        with self.subTest("No processed entries"):
            self.assertEqual(services.execute_data_minimisation(), 0)

        with freeze_time("2018-09-01"):
            self.e0.status = Entry.STATUS_COMPLETED
            self.e0.save()

        with self.subTest("Has processed entries when completed"):
            self.assertEqual(services.execute_data_minimisation(), 1)

        with freeze_time("2018-09-01"):
            self.e0.status = Entry.STATUS_REJECTED
            self.e0.save()

        with self.subTest("Has processed entries when rejected"):
            self.assertEqual(services.execute_data_minimisation(), 1)

        with freeze_time("2018-09-01"):
            self.e0.status = Entry.STATUS_COMPLETED
            self.e0.save()

        with self.subTest("Has processed entries when rejected with dry-run"):
            self.assertEqual(services.execute_data_minimisation(True), 1)

        self.e0.status = Entry.STATUS_COMPLETED
        self.e0.save()

        with self.subTest("No processed entries when inside 31 days"):
            self.assertEqual(services.execute_data_minimisation(), 0)

        self.e0.status = Entry.STATUS_REVIEW
        self.e0.save()
