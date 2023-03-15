from django.test import TestCase

from members.models import Member, Membership, Profile
from newsletters.models import Newsletter
from newsletters.services import send_newsletter
from pushnotifications.models import Message


class TestNewsletterNotifications(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.create(username="user1")
        Profile.objects.create(user=cls.member)
        Membership.objects.create(
            user=cls.member, type=Membership.MEMBER, since="2000-01-01"
        )

        cls.not_current_member = Member.objects.create(username="user2")
        Profile.objects.create(user=cls.not_current_member)

        cls.newsletter = Newsletter.objects.create(
            title="testletter",
            description="testdesc",
            sent=False,
        )

    def test_send_newsletter_sends_notification(self):
        """Sending a newsletter also sends a notification to all members."""
        send_newsletter(self.newsletter)

        self.assertTrue(
            Message.objects.filter(
                title=self.newsletter.title, sent__isnull=False
            ).exists()
        )

        message = Message.objects.get(title=self.newsletter.title)
        self.assertIn(self.member, message.users.all())
        self.assertNotIn(self.not_current_member, message.users.all())
