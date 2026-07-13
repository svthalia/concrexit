from datetime import date
from unittest import mock

from django.test import TestCase, override_settings

from freezegun import freeze_time

from members import services
from members.models import EmailChange, Member, Membership
from members.services import gen_stats_year


@freeze_time("2020-01-01")
class StatisticsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        for i in range(10):
            Member.objects.create(id=i, username=i)

            Membership.objects.create(
                user_id=i,
                type=Membership.MEMBER,
                since=date(year=(2017 if i < 5 else 2018), month=1, day=1),
            )

    def test_gen_stats_year(self):
        result = gen_stats_year()

        # We should have 5 members in 2017 and 10 members in 2018
        self.assertEqual([0, 0, 5, 10], result["datasets"][0]["data"][:4])


@override_settings(SUSPEND_SIGNALS=True)
class EmailChangeTest(TestCase):
    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        # Add 10 members with default membership
        cls.member = Member.objects.get(pk=2)

    def setUp(self):
        self.member.refresh_from_db()

    def test_verify_email_change(self):
        change_request = EmailChange(member=self.member, email="new@example.org")

        with mock.patch("members.services.process_email_change") as proc:
            services.verify_email_change(change_request)
            self.assertTrue(change_request.verified)
            proc.assert_called_once_with(change_request)

    def test_confirm_email_change(self):
        change_request = EmailChange(member=self.member, email="new@example.org")

        with mock.patch("members.services.process_email_change") as proc:
            services.confirm_email_change(change_request)
            self.assertTrue(change_request.confirmed)
            proc.assert_called_once_with(change_request)

    @mock.patch("members.emails.send_email_change_completion_message")
    def test_process_email_change(self, send_message_mock):
        change_request = EmailChange(member=self.member, email="new@example.org")

        original_email = self.member.email

        with self.subTest("Uncompleted request"):
            services.process_email_change(change_request)

            self.assertEqual(self.member.email, original_email)
            send_message_mock.assert_not_called()

        with self.subTest("Completed request"):
            change_request.verified = True
            change_request.confirmed = True

            services.process_email_change(change_request)

            self.assertEqual(self.member.email, change_request.email)
            send_message_mock.assert_called_once_with(change_request)
