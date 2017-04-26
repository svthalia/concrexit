import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from activemembers.models import Committee
from events.models import Event, Registration
from members.models import Member


class EventTest(TestCase):
    """Tests events"""

    fixtures = ['members.json', 'committees.json']

    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.create(
            title_nl='testevene',
            title_en='testevent',
            organiser=Committee.objects.get(pk=1),
            description_en='desc',
            description_nl='besch',
            start=(timezone.now() + datetime.timedelta(hours=1)),
            end=(timezone.now() + datetime.timedelta(hours=2)),
            location_en='test location',
            location_nl='test locatie',
            map_location='test map location',
            price=0.00,
            fine=0.00)
        cls.member = Member.objects.all()[0]

    def setUp(self):
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
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        with self.assertRaises(ValidationError):
            self.event.clean()

        self.event.registration_start = timezone.now()
        self.event.clean()

    def test_missing_registration_end(self):
        self.event.cancel_deadline = timezone.now()
        self.event.registration_start = timezone.now()
        with self.assertRaises(ValidationError):
            self.event.clean()

        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        self.event.clean()

    def test_missing_cancel_deadline(self):
        self.event.registration_start = timezone.now()
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        with self.assertRaises(ValidationError):
            self.event.clean()

        self.event.cancel_deadline = timezone.now()
        self.event.clean()

    def test_unnecessary_no_registration_message(self):
        self.event.registration_start = timezone.now()
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = timezone.now()
        self.event.no_registration_message_en = "Not registered"
        self.event.no_registration_message_nl = "Niet geregistreerd"
        with self.assertRaises(ValidationError):
            self.event.clean()

        self.event.no_registration_message_en = ""
        self.event.no_registration_message_nl = ""
        self.event.clean()

    def test_registration_end_after_registration_start(self):
        self.event.registration_start = (timezone.now() +
                                         datetime.timedelta(hours=1))
        self.event.registration_end = timezone.now()
        self.event.cancel_deadline = timezone.now()
        with self.assertRaises(ValidationError):
            self.event.clean()

        self.event.registration_start, self.event.registration_end = \
            self.event.registration_end, self.event.registration_start
        self.event.clean()

    def test_status_registration_not_needed(self):
        self.assertEqual(self.event.status, Event.REGISTRATION_NOT_NEEDED)

    def test_status_registration_not_yet_open(self):
        self.event.registration_start = (timezone.now() +
                                         datetime.timedelta(hours=1))
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=2))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.assertEqual(self.event.status, Event.REGISTRATION_NOT_YET_OPEN)

    def test_status_registration_open(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=1))
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.assertEqual(self.event.status, Event.REGISTRATION_OPEN)

    def test_status_registration_open_no_cancel(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=2))
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() -
                                      datetime.timedelta(hours=1))
        self.assertEqual(self.event.status, Event.REGISTRATION_OPEN_NO_CANCEL)

    def test_status_registration_closed_cancel_only(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=2))
        self.event.registration_end = (timezone.now() -
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.assertEqual(self.event.status,
                         Event.REGISTRATION_CLOSED_CANCEL_ONLY)

    def test_status_registration_closed(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=2))
        self.event.registration_end = (timezone.now() -
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() -
                                      datetime.timedelta(hours=1))
        self.assertEqual(self.event.status, Event.REGISTRATION_CLOSED)

    def test_reached_participants_limit(self):
        self.event.max_participants = 1
        self.assertFalse(self.event.reached_participants_limit())

    def test_not_reached_participants_limit(self):
        self.event.max_participants = 1
        Registration.objects.create(event=self.event, member=self.member)
        self.assertTrue(self.event.reached_participants_limit())


class RegistrationTest(TestCase):
    """Tests event registrations"""

    fixtures = ['members.json', 'committees.json']

    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.create(
            title_nl='testevene',
            title_en='testevent',
            organiser=Committee.objects.get(pk=1),
            description_en='desc',
            description_nl='besch',
            start=timezone.now(),
            end=(timezone.now() + datetime.timedelta(hours=1)),
            location_en='test location',
            location_nl='test locatie',
            map_location='test map location',
            price=0.00,
            fine=0.00)
        cls.member = Member.objects.all()[0]
        cls.r1 = Registration.objects.create(event=cls.event,
                                             member=cls.member)

    def setUp(self):
        self.r1.refresh_from_db()

    def test_is_late_registration(self):
        self.assertFalse(self.r1.is_late_cancellation())

        self.r1.date_cancelled = timezone.now()
        self.assertFalse(self.r1.is_late_cancellation())

        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.assertFalse(self.r1.is_late_cancellation())

        self.event.cancel_deadline = (timezone.now() -
                                      datetime.timedelta(hours=1))
        self.assertTrue(self.r1.is_late_cancellation())

    def test_queue_position(self):
        self.assertEqual(self.r1.queue_position(), 0)

        self.event.max_participants = 0
        self.assertEqual(self.r1.queue_position(), 1)

        self.event.max_participants = 1
        self.assertEqual(self.r1.queue_position(), 0)

    def test_registration_either_name_or_member(self):
        self.r1.clean()
        r2 = Registration.objects.create(event=self.event, name='test name')
        r2.clean()
        with self.assertRaises(ValidationError):
            r3 = Registration.objects.create(event=self.event,
                                             name='test name',
                                             member=self.member)
            r3.clean()

    def test_would_cancel_after_deadline(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=1))
        self.event.registration_end = (timezone.now() -
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() -
                                      datetime.timedelta(hours=1))

        # Test situation where the event status is REGISTRATION_CLOSED
        self.assertEqual(self.r1.would_cancel_after_deadline(), True)

        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=2))

        # Test situation where the event status is REGISTRATION_OPEN_NO_CANCEL
        self.assertEqual(self.r1.would_cancel_after_deadline(), True)
