from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from freezegun import freeze_time

from members import emails
from members.models import Member, Membership, Profile


@override_settings(SUSPEND_SIGNALS=True)
class EmailsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member_no_mail = Member.objects.create(
            username="no_mail_test", first_name="Nomail", last_name="Example"
        )
        Profile.objects.create(
            user=cls.member_no_mail,
        )
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
        Profile.objects.create(
            user=cls.year_member_no_expiry,
        )
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
        Profile.objects.create(
            user=cls.study_member,
        )
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
        Profile.objects.create(
            user=cls.study_member_2,
        )
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
        Profile.objects.create(
            user=cls.benefactor,
        )
        cls.honorary_member = Member.objects.create(
            username="test7",
            first_name="Test7",
            last_name="Example",
            email="test7@example.org",
        )
        Profile.objects.create(
            user=cls.honorary_member,
        )
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
        Profile.objects.create(
            user=cls.old_member,
        )
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
        Profile.objects.create(
            user=cls.future_member,
        )
        Membership.objects.create(
            user=cls.future_member,
            type=Membership.MEMBER,
            since=timezone.now().replace(year=2018, month=9, day=1),
            until=None,
        )

        # Member with expiring study-long membership in the next 31 days
        cls.study_long_expiring = Member.objects.create(
            username="test10",
            first_name="Test10",
            last_name="Example",
            email="test10@example.org",
        )
        Profile.objects.create(
            user=cls.study_long_expiring,
        )
        Membership.objects.create(
            user=cls.study_long_expiring,
            type=Membership.MEMBER,
            since=timezone.now().replace(year=2017, month=9, day=1),
            until=timezone.now().replace(year=2018, month=8, day=25),
            study_long=True,
        )
        # Member with expired study-long membership in +-60 days
        cls.study_long_expired = Member.objects.create(
            username="test11",
            first_name="Test11",
            last_name="Example",
            email="test11@example.org",
        )
        Profile.objects.create(
            user=cls.study_long_expired,
        )
        Membership.objects.create(
            user=cls.study_long_expired,
            type=Membership.MEMBER,
            since=timezone.now().replace(year=2017, month=9, day=1),
            until=timezone.now().replace(year=2018, month=10, day=15),
            study_long=True,
        )
        # Member with expiring study-long membership with future membership
        cls.study_long_expiring_with_future = Member.objects.create(
            username="test12",
            first_name="Test12",
            last_name="Example",
            email="test12@example.org",
        )
        Profile.objects.create(
            user=cls.study_long_expiring_with_future,
        )
        Membership.objects.create(
            user=cls.study_long_expiring_with_future,
            type=Membership.MEMBER,
            since=timezone.now().replace(year=2017, month=9, day=1),
            until=timezone.now().replace(year=2018, month=8, day=25),
            study_long=True,
        )
        # Future membership for study_long_expiring_with_future
        Membership.objects.create(
            user=cls.study_long_expiring_with_future,
            type=Membership.BENEFACTOR,
            since=timezone.now().replace(year=2018, month=9, day=1),
            until=timezone.now().replace(year=2019, month=9, day=1),
        )

    @freeze_time("2017-10-01")
    def test_send_information_request(self):
        emails.send_information_request()

        self.assertEqual(len(mail.outbox), 12)
        mails = list(sorted(mail.outbox, key=lambda x: x.to[0]))
        self.assertEqual(mails[1].to, ["test10@example.org"])
        self.assertEqual(mails[2].to, ["test11@example.org"])
        self.assertEqual(mails[3].to, ["test12@example.org"])
        self.assertEqual(mails[4].to, ["test1@example.org"])
        self.assertEqual(mails[4].subject, "[THALIA] Membership information check")
        self.assertEqual(mails[5].to, ["test2@example.org"])
        self.assertEqual(mails[5].subject, "[THALIA] Membership information check")
        self.assertEqual(mails[6].to, ["test3@example.org"])
        self.assertEqual(mails[7].to, ["test4@example.org"])
        self.assertEqual(mails[8].to, ["test5@example.org"])
        self.assertEqual(mails[9].to, ["test6@example.org"])
        self.assertEqual(mails[10].to, ["test7@example.org"])
        self.assertEqual(mails[11].to, ["test9@example.org"])

        self.assertEqual(mails[0].subject, "[THALIA] Membership information check sent")

    @freeze_time("2018-08-15")
    def test_send_expiration_announcement(self):
        emails.send_expiration_announcement()

        print(mail.outbox)
        self.assertEqual(len(mail.outbox), 4)
        self.assertEqual(mail.outbox[0].to, ["test1@example.org"])
        self.assertEqual(
            mail.outbox[0].subject, "[THALIA] Membership expiration announcement"
        )
        self.assertEqual(mail.outbox[1].to, ["test2@example.org"])
        self.assertEqual(
            mail.outbox[1].subject, "[THALIA] Membership expiration announcement"
        )
        self.assertEqual(mail.outbox[2].to, ["test6@example.org"])

        self.assertEqual(
            mail.outbox[3].subject, "[THALIA] Membership expiration announcement sent"
        )

    @freeze_time("2018-08-15")
    def test_send_welcome_message(self):
        emails.send_welcome_message(self.year_member_nl, "password1")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["test1@example.org"])
        self.assertEqual(
            mail.outbox[0].subject, "[THALIA] Welcome to Study Association Thalia"
        )

    @freeze_time("2018-08-15")
    def test_send_expiration_study_long(self):
        emails.send_expiration_study_long()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["test10@example.org"])
        self.assertEqual(
            mail.outbox[0].subject, "[THALIA] Membership expiration warning"
        )

    @freeze_time("2018-09-15")
    def test_send_expiration_study_long_reminder(self):
        emails.send_expiration_study_long_reminder()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["test10@example.org"])
        self.assertEqual(
            mail.outbox[0].subject, "[THALIA] Membership expiration warning"
        )
