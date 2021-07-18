import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from activemembers.models import Committee
from events.models import Event, EventRegistration
from mailinglists.models import MailingList
from members.models import Member


@override_settings(SUSPEND_SIGNALS=True)
class EventTest(TestCase):
    """Tests events."""

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.mailinglist = MailingList.objects.create(name="testmail")

        cls.committee = Committee.objects.create(
            name="committee", contact_mailinglist=cls.mailinglist,
        )

        cls.event = Event.objects.create(
            title="testevent",
            organiser=cls.committee,
            description="desc",
            start=(timezone.now() + datetime.timedelta(hours=1)),
            end=(timezone.now() + datetime.timedelta(hours=2)),
            location="test location",
            map_location="test map location",
            price=0.00,
            fine=5.00,
            optional_registrations=False,
        )
        cls.member = Member.objects.first()

    def setUp(self):
        self.mailinglist.refresh_from_db()
        self.committee.refresh_from_db()
        self.event.refresh_from_db()
        self.member.refresh_from_db()

    def test_clean_works(self):
        self.event.clean()

    def test_end_after_start(self):
        self.event.start, self.event.end = self.event.end, self.event.start
        with self.assertRaises(ValidationError):
            self.event.clean()

    def test_missing_registration_start(self):
        self.event.cancel_deadline = timezone.now()
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        with self.assertRaises(ValidationError):
            self.event.clean()

        self.event.registration_start = timezone.now()
        self.event.clean()

    def test_missing_registration_end(self):
        self.event.cancel_deadline = timezone.now()
        self.event.registration_start = timezone.now()
        with self.assertRaises(ValidationError):
            self.event.clean()

        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.clean()

    def test_missing_cancel_deadline(self):
        self.event.registration_start = timezone.now()
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        with self.assertRaises(ValidationError):
            self.event.clean()

        self.event.cancel_deadline = timezone.now()
        self.event.clean()

    def test_unnecessary_no_registration_message(self):
        self.event.registration_start = timezone.now()
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now()
        self.event.no_registration_message = "Not registered"
        with self.assertRaises(ValidationError):
            self.event.clean()

        self.event.no_registration_message = ""
        self.event.clean()

    def test_registration_end_after_registration_start(self):
        self.event.registration_start = timezone.now() + datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now()
        self.event.cancel_deadline = timezone.now()
        with self.assertRaises(ValidationError):
            self.event.clean()

        self.event.registration_start, self.event.registration_end = (
            self.event.registration_end,
            self.event.registration_start,
        )
        self.event.clean()

    def test_cancel_deadline_before_registration_start(self):
        self.event.registration_start = timezone.now()
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = self.event.start + datetime.timedelta(hours=1)
        with self.assertRaises(ValidationError):
            self.event.clean()

        self.event.cancel_deadline = self.event.start
        self.event.clean()

    def test_reached_participants_limit(self):
        self.event.max_participants = 1
        self.assertFalse(self.event.reached_participants_limit())

    def test_not_reached_participants_limit(self):
        self.event.max_participants = 1
        EventRegistration.objects.create(event=self.event, member=self.member)
        self.assertTrue(self.event.reached_participants_limit())

    def test_registration_fine_required(self):
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() - datetime.timedelta(hours=1)
        self.event.clean()
        self.event.fine = 0

        with self.assertRaises(ValidationError):
            self.event.clean()

    def test_registration_allowed(self):
        # Open
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.assertTrue(self.event.registration_allowed)

        # No cancel
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=2)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() - datetime.timedelta(hours=1)
        self.assertTrue(self.event.registration_allowed)

        # Not yet open
        self.event.registration_start = timezone.now() + datetime.timedelta(hours=1)
        self.event.registration_end = timezone.now() + datetime.timedelta(hours=2)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.assertFalse(self.event.registration_allowed)

        # Cancel only
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=2)
        self.event.registration_end = timezone.now() - datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.assertFalse(self.event.registration_allowed)

        # Registration is closed
        self.event.registration_start = timezone.now() - datetime.timedelta(hours=2)
        self.event.registration_end = timezone.now() - datetime.timedelta(hours=1)
        self.event.cancel_deadline = timezone.now() - datetime.timedelta(hours=1)
        self.assertFalse(self.event.registration_allowed)

        # Registration not needed
        self.event.registration_start = None
        self.event.registration_end = None
        self.event.cancel_deadline = None
        self.assertFalse(self.event.registration_allowed)

    def test_missing_orgination_mailinglist(self):
        self.event.clean()

        self.event.organiser.contact_mailinglist = None

        with self.assertRaises(ValidationError):
            self.event.clean()

    def test_cancellation_allowed(self):
        with self.subTest("Open"):
            self.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
            self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
            self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
            self.assertTrue(self.event.cancellation_allowed)

        with self.subTest("No cancel"):
            self.event.registration_start = timezone.now() - datetime.timedelta(hours=2)
            self.event.registration_end = timezone.now() + datetime.timedelta(hours=1)
            self.event.cancel_deadline = timezone.now() - datetime.timedelta(hours=1)
            # Allow since cancellation after deadline is possible
            self.assertTrue(self.event.cancellation_allowed)

        with self.subTest("Not yet open (now < registration start)"):
            self.event.registration_start = timezone.now() + datetime.timedelta(hours=1)
            self.event.registration_end = timezone.now() + datetime.timedelta(hours=2)
            self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
            self.assertFalse(self.event.cancellation_allowed)

        with self.subTest("Cancel only"):
            self.event.registration_start = timezone.now() - datetime.timedelta(hours=2)
            self.event.registration_end = timezone.now() - datetime.timedelta(hours=1)
            self.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
            self.assertTrue(self.event.cancellation_allowed)

        with self.subTest("Registration is closed"):
            self.event.registration_start = timezone.now() - datetime.timedelta(hours=2)
            self.event.registration_end = timezone.now() - datetime.timedelta(hours=1)
            self.event.cancel_deadline = timezone.now() - datetime.timedelta(hours=1)
            # Allow since cancellation after deadline is possible
            self.assertTrue(self.event.cancellation_allowed)

        with self.subTest("After event start"):
            self.event.registration_start = timezone.now() - datetime.timedelta(hours=4)
            self.event.registration_end = timezone.now() - datetime.timedelta(hours=3)
            self.event.cancel_deadline = timezone.now() - datetime.timedelta(hours=3)
            self.event.start = timezone.now()
            self.event.end = timezone.now() + datetime.timedelta(hours=2)
            self.assertFalse(self.event.cancellation_allowed)

        with self.subTest("Registration not required"):
            self.event.registration_start = None
            self.event.registration_end = None
            self.event.cancel_deadline = None
            self.assertFalse(self.event.cancellation_allowed)


@override_settings(SUSPEND_SIGNALS=True)
class RegistrationTest(TestCase):
    """Tests event registrations."""

    fixtures = ["members.json", "member_groups.json"]

    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.create(
            title="testevent",
            organiser=Committee.objects.get(pk=1),
            description="desc",
            start=timezone.now(),
            end=(timezone.now() + datetime.timedelta(hours=1)),
            location="test location",
            map_location="test map location",
            price=0.00,
            fine=0.00,
        )
        cls.member1 = Member.objects.first()
        cls.member2 = Member.objects.all()[1]
        cls.r1 = EventRegistration.objects.create(event=cls.event, member=cls.member1)
        cls.r2 = EventRegistration.objects.create(event=cls.event, member=cls.member2)

    def setUp(self):
        self.r1.refresh_from_db()

    def test_is_late_registration(self):
        self.assertFalse(self.r1.is_late_cancellation())

        self.r1.date_cancelled = timezone.now()
        self.assertFalse(self.r1.is_late_cancellation())

        self.r1.event.cancel_deadline = timezone.now() + datetime.timedelta(hours=1)
        self.assertFalse(self.r1.is_late_cancellation())

        self.r1.event.cancel_deadline = timezone.now() - datetime.timedelta(hours=1)
        self.assertTrue(self.r1.is_late_cancellation())

    def test_queue_position(self):
        self.assertEqual(self.r1.queue_position, None)
        self.assertEqual(self.r2.queue_position, None)

        self.r1.event.max_participants = 0
        self.r2.event = self.r1.event
        self.assertEqual(self.r1.queue_position, 1)
        self.assertEqual(self.r2.queue_position, 2)

        self.r1.event.max_participants = 1
        self.r2.event = self.r1.event
        self.assertEqual(self.r1.queue_position, None)
        self.assertEqual(self.r2.queue_position, 1)

    def test_registration_either_name_or_member(self):
        self.r2.delete()
        self.r1.clean()
        r2 = EventRegistration.objects.create(event=self.event, name="test name")
        r2.clean()
        with self.assertRaises(ValidationError):
            r3 = EventRegistration.objects.create(
                event=self.event, name="test name", member=self.member2
            )
            r3.clean()

    def test_would_cancel_after_deadline(self):
        self.r1.event.registration_start = timezone.now() - datetime.timedelta(hours=1)
        self.r1.event.registration_end = timezone.now() - datetime.timedelta(hours=1)
        self.r1.event.cancel_deadline = timezone.now() - datetime.timedelta(hours=1)

        # Test situation where the event status is REGISTRATION_CLOSED
        self.assertFalse(self.r1.event.registration_allowed)
        self.assertTrue(self.r1.would_cancel_after_deadline())

        self.r1.event.registration_end = timezone.now() + datetime.timedelta(hours=2)

        # Test situation where the event status is REGISTRATION_OPEN_NO_CANCEL
        self.assertTrue(self.r1.event.registration_allowed)
        self.assertTrue(self.r1.would_cancel_after_deadline())
