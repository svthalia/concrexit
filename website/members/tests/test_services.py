from datetime import timedelta, date
from django.test import TestCase
from django.utils import timezone
from unittest import mock

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
        memberships = [Membership(user_id=i, type="member")
                       for i in range(10)]
        Membership.objects.bulk_create(memberships)
        profiles = [Profile(user_id=i) for i in range(10)]
        Profile.objects.bulk_create(profiles)

    def sum_members(self, members, type=None):
        if type is None:
            return sum(sum(i.values()) for i in members)
        else:
            return sum(map(lambda x: x[type], members))

    def sum_member_types(self, members):
        return sum(members.values())

    def test_gen_stats_year_no_members(self):
        member_types = ["member", "supporter", "honorary"]
        result = gen_stats_year(member_types)
        self.assertEqual(0, self.sum_members(result))

    def test_gen_stats_active(self):
        """
        Testing if active and non-active objects are counted correctly
        """
        member_types = ["member", "supporter", "honorary"]
        current_year = datetime_to_lectureyear(date.today())

        # Set start date to current year - 1:
        for m in Member.objects.all():
            m.profile.starting_year = current_year - 1
            m.profile.save()
        result = gen_stats_year(member_types)
        self.assertEqual(10, self.sum_members(result))
        self.assertEqual(10, self.sum_members(result, "member"))

        result = gen_stats_member_type(member_types)
        self.assertEqual(10, self.sum_member_types(result))

        # Change one membership to supporter should decrease amount of members
        m = Membership.objects.all()[0]
        m.type = "supporter"
        m.save()

        result = gen_stats_year(member_types)
        self.assertEqual(10, self.sum_members(result))
        self.assertEqual(9, self.sum_members(result, "member"))
        self.assertEqual(1, self.sum_members(result, "supporter"))

        result = gen_stats_member_type(member_types)
        self.assertEqual(10, self.sum_member_types(result))
        self.assertEqual(9, result["member"])
        self.assertEqual(1, result["supporter"])

        # Same for honorary members
        m = Membership.objects.all()[1]
        m.type = "honorary"
        m.save()

        result = gen_stats_year(member_types)
        self.assertEqual(10, self.sum_members(result))
        self.assertEqual(8, self.sum_members(result, "member"))
        self.assertEqual(1, self.sum_members(result, "supporter"))
        self.assertEqual(1, self.sum_members(result, "honorary"))

        result = gen_stats_member_type(member_types)
        self.assertEqual(10, self.sum_member_types(result))
        self.assertEqual(8, result["member"])
        self.assertEqual(1, result["supporter"])
        self.assertEqual(1, result["honorary"])

        # Terminate one membership by setting end date to current_year -1,
        # should decrease total amount and total members
        m = Membership.objects.all()[2]
        m.until = timezone.now() - timedelta(days=365)
        m.save()
        result = gen_stats_year(member_types)
        self.assertEqual(9, self.sum_members(result))
        self.assertEqual(7, self.sum_members(result, "member"))
        self.assertEqual(1, self.sum_members(result, "supporter"))
        self.assertEqual(1, self.sum_members(result, "honorary"))

        result = gen_stats_member_type(member_types)
        self.assertEqual(9, self.sum_member_types(result))
        self.assertEqual(7, result["member"])
        self.assertEqual(1, result["supporter"])
        self.assertEqual(1, result["honorary"])

    def test_gen_stats_different_years(self):
        member_types = ["member", "supporter", "honorary"]
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
        self.assertEqual(4, self.sum_members(result, "member"))

        # one first year student
        self.assertEqual(1, result[0]['member'])

        # one second year student
        self.assertEqual(1, result[1]['member'])

        # no third year students
        self.assertEqual(0, result[2]['member'])

        # one fourth year student
        self.assertEqual(1, result[3]['member'])

        # no fifth year students
        self.assertEqual(0, result[4]['member'])

        # one >5 year student
        self.assertEqual(1, result[5]['member'])


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
