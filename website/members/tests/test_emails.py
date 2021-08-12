from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from freezegun import freeze_time

from members import emails
from members.models import Member, Profile, Membership


@override_settings(SUSPEND_SIGNALS=True)
class EmailsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member_no_mail = Member.objects.create(
            username="no_mail_test", first_name="Nomail", last_name="Example"
        )
        Profile.objects.create(user=cls.member_no_mail,)
        Membership.objects.create(
            user=cls.member_no_mail,
            type=Membership.MEMBER,
            since=timezone.now().replace(year=2017, month=9, day=1),
            until=timezone.now().replace(year=2018, month=9, day=1),
        )
        cls.year_member_nl = Member.objects.create(
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
        )
        Profile.objects.create(user=cls.year_member_nl)
        Membership.objects.create(
            user=cls.year_member_nl,
            type=Membership.MEMBER,
            since=timezone.now().replace(year=2017, month=9, day=1),
            until=timezone.now().replace(year=2018, month=9, day=1),
        )
        cls.year_member_en = Member.objects.create(
            username="test2",
            first_name="Test2",
            last_name="Example",
            email="test2@example.org",
        )
        Profile.objects.create(user=cls.year_member_en)
        Membership.objects.create(
            user=cls.year_member_en,
            type=Membership.MEMBER,
            since=timezone.now().replace(year=2017, month=9, day=1),
            until=timezone.now().replace(year=2018, month=9, day=1),
        )
        cls.year_member_no_expiry = Member.objects.create(
            username="test3",
            first_name="Test3",
            last_name="Example",
            email="test3@example.org",
        )
        Profile.objects.create(user=cls.year_member_no_expiry,)
        Membership.objects.create(
            user=cls.year_member_no_expiry,
            type=Membership.MEMBER,
            since=timezone.now().replace(year=2017, month=9, day=1),
            until=timezone.now().replace(year=2019, month=9, day=1),
        )
        cls.study_member = Member.objects.create(
            username="test4",
            first_name="Test4",
            last_name="Example",
            email="test4@example.org",
        )
        Profile.objects.create(user=cls.study_member,)
        Membership.objects.create(
            user=cls.study_member,
            type=Membership.MEMBER,
            since=timezone.now().replace(year=2017, month=9, day=1),
            until=None,
        )
        cls.study_member_2 = Member.objects.create(
            username="test5",
            first_name="Test5",
            last_name="Example",
            email="test5@example.org",
        )
        Profile.objects.create(user=cls.study_member_2,)
        Membership.objects.create(
            user=cls.study_member_2,
            type=Membership.MEMBER,
            since=timezone.now().replace(year=2016, month=9, day=1),
            until=timezone.now().replace(year=2017, month=9, day=1),
        )
        Membership.objects.create(
            user=cls.study_member_2,
            type=Membership.MEMBER,
            since=timezone.now().replace(year=2017, month=9, day=6),
            until=None,
        )
        cls.benefactor = Member.objects.create(
            username="test6",
            first_name="Test6",
            last_name="Example",
            email="test6@example.org",
        )
        Membership.objects.create(
            user=cls.benefactor,
            type=Membership.BENEFACTOR,
            since=timezone.now().replace(year=2017, month=9, day=1),
            until=timezone.now().replace(year=2018, month=9, day=1),
        )
        Profile.objects.create(user=cls.benefactor,)
        cls.honorary_member = Member.objects.create(
            username="test7",
            first_name="Test7",
            last_name="Example",
            email="test7@example.org",
        )
        Profile.objects.create(user=cls.honorary_member,)
        Membership.objects.create(
            user=cls.honorary_member,
            type=Membership.HONORARY,
            since=timezone.now().replace(year=2016, month=12, day=6),
            until=timezone.now().replace(year=2017, month=6, day=12),
        )
        Membership.objects.create(
            user=cls.honorary_member,
            type=Membership.HONORARY,
            since=timezone.now().replace(year=2017, month=6, day=12),
            until=None,
        )
        cls.old_member = Member.objects.create(
            username="test8",
            first_name="Test8",
            last_name="Example",
            email="test8@example.org",
        )
        Profile.objects.create(user=cls.old_member,)
        Membership.objects.create(
            user=cls.old_member,
            type=Membership.MEMBER,
            since=timezone.now().replace(year=2016, month=12, day=6),
            until=timezone.now().replace(year=2017, month=6, day=12),
        )
        cls.future_member = Member.objects.create(
            username="test9",
            first_name="Test9",
            last_name="Example",
            email="test9@example.org",
        )
        Profile.objects.create(user=cls.future_member,)
        Membership.objects.create(
            user=cls.future_member,
            type=Membership.MEMBER,
            since=timezone.now().replace(year=2018, month=9, day=1),
            until=None,
        )

    @freeze_time("2017-10-01")
    def test_send_membership_announcement(self):
        emails.send_membership_announcement()

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, ["test4@example.org"])
        self.assertEqual(mail.outbox[1].to, ["test5@example.org"])

    @freeze_time("2017-10-01")
    def test_send_information_request(self):
        emails.send_information_request()

        self.assertEqual(len(mail.outbox), 8)
        self.assertEqual(mail.outbox[0].to, ["test1@example.org"])
        self.assertEqual(
            mail.outbox[0].subject, "[THALIA] Membership information check"
        )
        self.assertEqual(mail.outbox[1].to, ["test2@example.org"])
        self.assertEqual(
            mail.outbox[1].subject, "[THALIA] Membership information check"
        )
        self.assertEqual(mail.outbox[2].to, ["test3@example.org"])
        self.assertEqual(mail.outbox[3].to, ["test4@example.org"])
        self.assertEqual(mail.outbox[4].to, ["test5@example.org"])
        self.assertEqual(mail.outbox[5].to, ["test6@example.org"])
        self.assertEqual(mail.outbox[6].to, ["test7@example.org"])
        self.assertEqual(mail.outbox[7].to, ["test9@example.org"])

    @freeze_time("2018-08-15")
    def test_send_expiration_announcement(self):
        emails.send_expiration_announcement()

        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(mail.outbox[0].to, ["test1@example.org"])
        self.assertEqual(
            mail.outbox[0].subject, "[THALIA] Membership expiration announcement"
        )
        self.assertEqual(mail.outbox[1].to, ["test2@example.org"])
        self.assertEqual(
            mail.outbox[1].subject, "[THALIA] Membership expiration announcement"
        )
        self.assertEqual(mail.outbox[2].to, ["test6@example.org"])

    @freeze_time("2018-08-15")
    def test_send_welcome_message(self):
        emails.send_welcome_message(self.year_member_nl, "password1")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["test1@example.org"])
        self.assertEqual(mail.outbox[0].subject, "Welcome to Study Association Thalia")
