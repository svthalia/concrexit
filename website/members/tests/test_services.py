
from datetime import timedelta, date
from django.test import TestCase
from django.utils import timezone
from unittest import mock

from freezegun import freeze_time

from members import services
from members.models import Member, Membership, Profile, EmailChange
from members.services import gen_stats_year, gen_stats_member_type
from utils.snippets import datetime_to_lectureyear


class StatisticsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Add 10 members with default membership
        members = [Member(id=i, username=i) for i in range(10)]
        Member.objects.bulk_create(members)
        memberships = [Membership(user_id=i, type=Membership.MEMBER)
                       for i in range(10)]
        Membership.objects.bulk_create(memberships)
        profiles = [Profile(user_id=i) for i in range(10)]
        Profile.objects.bulk_create(profiles)

    def sum_members(self, members, type=None):
        if type is None:
            return sum(sum(list(i.values())[1:]) for i in members)
        else:
            return sum(map(lambda x: x[type], members))

    def sum_member_types(self, members):
        return sum(members.values())

    def test_gen_stats_year_no_members(self):
        member_types = [t[0] for t in Membership.MEMBERSHIP_TYPES]
        result = gen_stats_year(member_types)
        self.assertEqual(0, self.sum_members(result))

    def test_gen_stats_active(self):
        """
        Testing if active and non-active objects are counted correctly
        """
        member_types = [t[0] for t in Membership.MEMBERSHIP_TYPES]
        current_year = datetime_to_lectureyear(date.today())

        # Set start date to current year - 1:
        for m in Member.objects.all():
            m.profile.starting_year = current_year - 1
            m.profile.save()
        result = gen_stats_year(member_types)
        self.assertEqual(10, self.sum_members(result))
        self.assertEqual(10, self.sum_members(result, Membership.MEMBER))

        result = gen_stats_member_type(member_types)
        self.assertEqual(10, self.sum_member_types(result))

        # Change one membership to benefactor should decrease amount of members
        m = Membership.objects.all()[0]
        m.type = Membership.BENEFACTOR
        m.save()

        result = gen_stats_year(member_types)
        self.assertEqual(10, self.sum_members(result))
        self.assertEqual(9, self.sum_members(result, Membership.MEMBER))
        self.assertEqual(1, self.sum_members(result, Membership.BENEFACTOR))

        result = gen_stats_member_type(member_types)
        self.assertEqual(10, self.sum_member_types(result))
        self.assertEqual(9, result[Membership.MEMBER])
        self.assertEqual(1, result[Membership.BENEFACTOR])

        # Same for honorary members
        m = Membership.objects.all()[1]
        m.type = Membership.HONORARY
        m.save()

        result = gen_stats_year(member_types)
        self.assertEqual(10, self.sum_members(result))
        self.assertEqual(8, self.sum_members(result, Membership.MEMBER))
        self.assertEqual(1, self.sum_members(result, Membership.BENEFACTOR))
        self.assertEqual(1, self.sum_members(result, Membership.HONORARY))

        result = gen_stats_member_type(member_types)
        self.assertEqual(10, self.sum_member_types(result))
        self.assertEqual(8, result[Membership.MEMBER])
        self.assertEqual(1, result[Membership.BENEFACTOR])
        self.assertEqual(1, result[Membership.HONORARY])

        # Terminate one membership by setting end date to current_year -1,
        # should decrease total amount and total members
        m = Membership.objects.all()[2]
        m.until = timezone.now() - timedelta(days=365)
        m.save()
        result = gen_stats_year(member_types)
        self.assertEqual(9, self.sum_members(result))
        self.assertEqual(7, self.sum_members(result, Membership.MEMBER))
        self.assertEqual(1, self.sum_members(result, Membership.BENEFACTOR))
        self.assertEqual(1, self.sum_members(result, Membership.HONORARY))

        result = gen_stats_member_type(member_types)
        self.assertEqual(9, self.sum_member_types(result))
        self.assertEqual(7, result[Membership.MEMBER])
        self.assertEqual(1, result[Membership.BENEFACTOR])
        self.assertEqual(1, result[Membership.HONORARY])

    def test_gen_stats_different_years(self):
        member_types = [t[0] for t in Membership.MEMBERSHIP_TYPES]
        current_year = datetime_to_lectureyear(date.today())

        # postgres does not define random access directly on unsorted querysets
        members = [member for member in Member.objects.all()]

        # one first year student
        m = members[0]
        m.profile.starting_year = current_year
        m.profile.save()

        # one second year student
        m = members[1]
        m.profile.starting_year = current_year - 1
        m.profile.save()

        # no third year students

        # one fourth year student
        m = members[2]
        m.profile.starting_year = current_year - 3
        m.profile.save()

        # no fifth year students

        # one >5 year student
        m = members[3]
        m.profile.starting_year = current_year - 5
        m.profile.save()

        # 4 active members
        result = gen_stats_year(member_types)
        self.assertEqual(4, self.sum_members(result))
        self.assertEqual(4, self.sum_members(result, Membership.MEMBER))

        # one first year student
        self.assertEqual(1, result[0][Membership.MEMBER])

        # one second year student
        self.assertEqual(1, result[1][Membership.MEMBER])

        # no third year students
        self.assertEqual(0, result[2][Membership.MEMBER])

        # one fourth year student
        self.assertEqual(1, result[3][Membership.MEMBER])

        # no fifth year students
        self.assertEqual(0, result[4][Membership.MEMBER])

        # one >5 year student
        self.assertEqual(1, result[5][Membership.MEMBER])


class EmailChangeTest(TestCase):
    fixtures = ['members.json']

    @classmethod
    def setUpTestData(cls):
        # Add 10 members with default membership
        cls.member = Member.objects.get(pk=2)

    def setUp(self):
        self.member.refresh_from_db()

    def test_verify_email_change(self):
        change_request = EmailChange(
            member=self.member,
            email='new@example.org'
        )

        with mock.patch('members.services.process_email_change') as proc:
            services.verify_email_change(change_request)
            self.assertTrue(change_request.verified)
            proc.assert_called_once_with(change_request)

    def test_confirm_email_change(self):
        change_request = EmailChange(
            member=self.member,
            email='new@example.org'
        )

        with mock.patch('members.services.process_email_change') as proc:
            services.confirm_email_change(change_request)
            self.assertTrue(change_request.confirmed)
            proc.assert_called_once_with(change_request)

    @mock.patch('members.emails.send_email_change_completion_message')
    def test_process_email_change(self, send_message_mock):
        change_request = EmailChange(
            member=self.member,
            email='new@example.org'
        )

        original_email = self.member.email

        with self.subTest('Uncompleted request'):
            services.process_email_change(change_request)

            self.assertEqual(self.member.email, original_email)
            send_message_mock.assert_not_called()

        with self.subTest('Completed request'):
            change_request.verified = True
            change_request.confirmed = True

            services.process_email_change(change_request)

            self.assertEqual(self.member.email, change_request.email)
            send_message_mock.assert_called_once_with(change_request)


@freeze_time('2018-10-2')
class DataMinimisationTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.m1 = Member.objects.create(
            username='test1',
            first_name='Test1',
            last_name='Example',
            email='test1@example.org'
        )
        Profile.objects.create(
            user=cls.m1,
            language='nl',
            student_number='s1234567'
        )
        cls.s1 = Membership.objects.create(
            user=cls.m1,
            type=Membership.MEMBER,
            since=timezone.now().replace(year=2017, month=9, day=1),
            until=timezone.now().replace(year=2018, month=9, day=1)
        )
        cls.m2 = Member.objects.create(
            username='test2',
            first_name='Test2',
            last_name='Example',
            email='test2@example.org'
        )
        Profile.objects.create(
            user=cls.m2,
            language='nl',
            student_number='s7654321'
        )
        cls.s2 = Membership.objects.create(
            user=cls.m2,
            type=Membership.MEMBER,
            since=timezone.now().replace(year=2017, month=9, day=1),
            until=timezone.now().replace(year=2018, month=9, day=1)
        )

    def test_removes_after_31_days_or_no_membership(self):
        with self.subTest('Deletes after 31 days'):
            processed = services.execute_data_minimisation(True)
            self.assertEqual(len(processed), 2)
            self.assertEqual(processed[0], self.m1)

        with self.subTest('Deletes after 31 days'):
            self.s1.until = timezone.now().replace(
                year=2018, month=11, day=1)
            self.s1.save()
            processed = services.execute_data_minimisation(True)
            self.assertEqual(len(processed), 1)

        with self.subTest('Deletes when no memberships'):
            self.s1.delete()
            processed = services.execute_data_minimisation(True)
            self.assertEqual(len(processed), 2)

    def test_dry_run(self):
        with self.subTest('With dry_run=True'):
            services.execute_data_minimisation(True)
            self.m1.refresh_from_db()
            self.assertEqual(self.m1.profile.student_number, 's1234567')
        with self.subTest('With dry_run=False'):
            services.execute_data_minimisation(False)
            self.m1.refresh_from_db()
            self.assertIsNone(self.m1.profile.student_number)

    def test_provided_queryset(self):
        processed = services.execute_data_minimisation(True,
                                                       members=Member.objects)
        self.assertEqual(len(processed), 2)
        self.assertEqual(processed[0], self.m1)

    def test_does_not_affect_current_members(self):
        with self.subTest('Membership ends in future'):
            self.s1.until = timezone.now().replace(
                year=2019, month=9, day=1)
            self.s1.save()
            processed = services.execute_data_minimisation(True)
            self.assertEqual(len(processed), 1)
        with self.subTest('Never ending membership'):
            self.s1.until = None
            self.s1.save()
            processed = services.execute_data_minimisation(True)
            self.assertEqual(len(processed), 1)
            self.s1.until = timezone.now().replace(
                year=2018, month=9, day=1)
            self.s1.save()
        with self.subTest('Newer year membership after expired one'):
            m = Membership.objects.create(
                user=self.m1,
                type=Membership.MEMBER,
                since=timezone.now().replace(year=2018, month=9, day=10),
                until=timezone.now().replace(year=2019, month=8, day=31),
            )
            processed = services.execute_data_minimisation(True)
            self.assertEqual(len(processed), 1)
            m.delete()
        with self.subTest('Newer study membership after expired one'):
            m = Membership.objects.create(
                user=self.m1,
                type=Membership.MEMBER,
                since=timezone.now().replace(year=2018, month=9, day=10),
                until=None
            )
            processed = services.execute_data_minimisation(True)
            self.assertEqual(len(processed), 1)
            m.delete()
