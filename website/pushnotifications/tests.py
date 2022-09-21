import datetime

from django.test import TestCase, override_settings
from django.utils import timezone

from activemembers.models import Committee
from events.models import Event, Member
from mailinglists.models import MailingList


@override_settings(SUSPEND_SIGNALS=True)
class PushNotificationsTest(TestCase):
    """Tests push notifications."""

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.mailinglist = MailingList.objects.create(name="testmail")

        cls.committee = Committee.objects.create(
            name="committee",
            contact_mailinglist=cls.mailinglist,
        )

        cls.event = Event.objects.create(
            title="testevent",
            description="desc",
            start=(timezone.now() + datetime.timedelta(hours=2)),
            end=(timezone.now() + datetime.timedelta(hours=3)),
            location="test location",
            map_location="test map location",
            price=0.00,
            fine=5.00,
            published=True,
        )
        cls.event.organisers.add(cls.committee)
        cls.member = Member.objects.first()

    def test_deleting_notification_for_event_doesnt_crash(self) -> None:
        self.assertIsNotNone(self.event.start_reminder)
        self.event.start_reminder.delete()
