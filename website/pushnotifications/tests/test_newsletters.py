from django.test import TestCase

from members.models import Member, Membership
from newsletters.models import Newsletter
from newsletters.services import send_newsletter
from pushnotifications.models import Message


class TestNewsletterNotifications(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.create(username="johndoe")

        Membership.objects.create(
            user=cls.member, type=Membership.MEMBER, since="2000-01-01"
        )
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
